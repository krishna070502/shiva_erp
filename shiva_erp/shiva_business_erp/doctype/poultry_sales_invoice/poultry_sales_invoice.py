# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PoultrySalesInvoice(Document):
	def validate(self):
		"""Validate and calculate totals"""
		self.calculate_pricing_for_items()
		self.calculate_totals()
		self.validate_stock()

	def on_submit(self):
		"""Create accounting and stock entries"""
		self.create_stock_entries()
		self.create_gl_entries()

	def on_cancel(self):
		"""Reverse stock and accounting entries"""
		self.reverse_stock_entries()
		self.reverse_gl_entries()

	def calculate_pricing_for_items(self):
		"""Auto-calculate pricing for each item based on territory and shop discount"""
		if not self.customer or not self.items:
			return

		# Get customer territory
		customer_doc = frappe.get_doc("Customer", self.customer)
		territory = customer_doc.territory

		if not territory:
			frappe.msgprint(_("Customer has no territory assigned"), indicator="orange", alert=True)
			return

		for item in self.items:
			if not item.item_code or item.weight_kg <= 0:
				continue

			# Get base price from Item Price Type
			from shiva_erp.shiva_business_erp.doctype.item_price_type.item_price_type import get_base_price

			base_price_record = get_base_price(item.item_code, territory, self.posting_date)
			base_price = flt(base_price_record.get("base_price_per_kg", 0)) if base_price_record else 0

			if base_price <= 0:
				continue

			# Get shop discount
			from shiva_erp.shiva_business_erp.doctype.shop_discount.shop_discount import get_shop_discount

			discount = flt(get_shop_discount(self.customer, item.item_code, self.posting_date))

			# Calculate effective price
			effective_price = base_price - discount
			if effective_price < 0:
				effective_price = 0

			# Update item fields
			item.base_price_per_kg = base_price
			item.discount_per_kg = discount
			item.rate = effective_price
			item.amount = effective_price * item.weight_kg

	def calculate_totals(self):
		"""Calculate total qty, weight, and amount"""
		self.total_qty = 0
		self.total_weight = 0
		self.total_amount = 0

		for item in self.items:
			self.total_qty += flt(item.qty)
			self.total_weight += flt(item.weight_kg)
			self.total_amount += flt(item.amount)

	def validate_stock(self):
		"""Validate sufficient stock is available"""
		from shiva_erp.stock_logic import validate_stock_availability

		for item in self.items:
			if not item.item_code or item.weight_kg <= 0:
				continue

			result = validate_stock_availability(item.item_code, item.warehouse, item.qty, item.weight_kg)

			if not result["is_available"]:
				frappe.throw(_("Row #{0}: {1}").format(item.idx, result["message"]))

	def create_stock_entries(self):
		"""Create Stock Weight Ledger entries and ERPNext Stock Ledger entries"""
		from erpnext.stock.stock_ledger import make_sl_entries

		sl_entries = []

		for item in self.items:
			if item.weight_kg <= 0:
				continue

			# Create Stock Weight Ledger entry (OUT)
			ledger_entry = frappe.new_doc("Stock Weight Ledger")
			ledger_entry.transaction_type = "OUT"
			ledger_entry.posting_date = self.posting_date
			ledger_entry.voucher_type = self.doctype
			ledger_entry.voucher_no = self.name
			ledger_entry.item_code = item.item_code
			ledger_entry.warehouse = item.warehouse
			ledger_entry.stock_qty = item.qty
			ledger_entry.weight_kg = item.weight_kg
			ledger_entry.rate_per_kg = item.rate
			ledger_entry.insert(ignore_permissions=True)

			# Create standard ERPNext Stock Ledger Entry using frappe._dict
			sl_entries.append(
				frappe._dict(
					{
						"item_code": item.item_code,
						"warehouse": item.warehouse,
						"posting_date": self.posting_date,
						"posting_time": frappe.utils.nowtime(),
						"voucher_type": self.doctype,
						"voucher_no": self.name,
						"voucher_detail_no": item.name,
						"actual_qty": -1 * flt(item.qty),  # Negative for outward
						"incoming_rate": 0,
						"company": self.company,
						"batch_no": item.get("batch_no"),
						"serial_no": item.get("serial_no"),
					}
				)
			)

		# Submit standard stock ledger entries
		if sl_entries:
			make_sl_entries(sl_entries)

	def reverse_stock_entries(self):
		"""Delete Stock Weight Ledger entries and reverse ERPNext Stock Ledger entries"""
		from erpnext.stock.stock_ledger import make_sl_entries

		# Delete Stock Weight Ledger
		frappe.db.sql(
			"""DELETE FROM `tabStock Weight Ledger` 
			WHERE voucher_no = %s""",
			(self.name,),
		)

		# Reverse standard stock ledger entries
		sl_entries = []
		for item in self.items:
			sl_entries.append(
				frappe._dict(
					{
						"item_code": item.item_code,
						"warehouse": item.warehouse,
						"posting_date": self.posting_date,
						"posting_time": frappe.utils.nowtime(),
						"voucher_type": self.doctype,
						"voucher_no": self.name,
						"voucher_detail_no": item.name,
						"actual_qty": flt(item.qty),  # Positive to reverse the negative
						"incoming_rate": 0,
						"company": self.company,
						"is_cancelled": 1,
					}
				)
			)

		if sl_entries:
			make_sl_entries(sl_entries)

	def create_gl_entries(self):
		"""Create GL entries for accounting"""
		# Get customer receivable account from Party Account
		customer_account = frappe.db.get_value(
			"Party Account", {"parent": self.customer, "company": self.company}, "account"
		)

		if not customer_account:
			# Fallback to company default
			customer_account = frappe.get_value("Company", self.company, "default_receivable_account")

		# Get income account from Company defaults
		income_account = frappe.get_value("Company", self.company, "default_income_account")

		if not customer_account or not income_account:
			frappe.msgprint(
				_("Unable to create GL entries. Please set up accounts in Company {0}").format(self.company),
				indicator="orange",
				alert=True,
			)
			return

		# Debit: Customer Account (Receivable)
		self.make_gl_entry(
			customer_account, debit=self.total_amount, credit=0, party_type="Customer", party=self.customer
		)

		# Credit: Sales Income Account
		self.make_gl_entry(income_account, debit=0, credit=self.total_amount)

	def make_gl_entry(self, account, debit=0, credit=0, party_type=None, party=None):
		"""Helper to create GL Entry"""
		gl_entry = frappe.new_doc("GL Entry")
		gl_entry.posting_date = self.posting_date
		gl_entry.account = account
		gl_entry.debit = flt(debit)
		gl_entry.credit = flt(credit)
		gl_entry.voucher_type = self.doctype
		gl_entry.voucher_no = self.name
		gl_entry.company = self.company
		gl_entry.party_type = party_type
		gl_entry.party = party

		# Get cost center for P&L accounts
		cost_center = self.get("cost_center") or frappe.get_cached_value(
			"Company", self.company, "cost_center"
		)
		if cost_center:
			gl_entry.cost_center = cost_center

		gl_entry.insert(ignore_permissions=True)

	def reverse_gl_entries(self):
		"""Delete GL entries"""
		frappe.db.sql(
			"""DELETE FROM `tabGL Entry` 
			WHERE voucher_no = %s""",
			(self.name,),
		)
