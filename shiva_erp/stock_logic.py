"""
Stock Logic Module for Shiva ERP

Handles dual UOM (Nos + actual Kg) stock tracking for poultry business.
Critical: Cannot use conversion factors - each bird has variable weight.
"""

import frappe
from frappe import _
from frappe.utils import flt


def update_weight_ledger(doc, method):
	"""
	Create Stock Weight Ledger entries when Purchase Receipt or Delivery Note is submitted.

	Args:
		doc: Purchase Receipt or Delivery Note document
		method: on_submit hook method

	Transaction Types:
		- Purchase Receipt: IN (adds stock)
		- Delivery Note: OUT (reduces stock)
	"""
	# Determine transaction type based on doctype
	transaction_type = "IN" if doc.doctype == "Purchase Receipt" else "OUT"

	# Loop through the items in the transaction
	for item in doc.items:
		# Get custom fields for dual UOM tracking
		weight_kg = flt(item.get("custom_total_weight_kg", 0))
		stock_qty = flt(item.get("qty", 0))

		# Skip if no weight or quantity
		if weight_kg <= 0 or stock_qty <= 0:
			continue

		# Get optional individual bird weights if available
		weights_list = item.get("custom_bird_weights_json")  # JSON field with individual weights

		# Create Stock Weight Ledger entry
		ledger_entry = frappe.new_doc("Stock Weight Ledger")

		# Transaction details
		ledger_entry.transaction_type = transaction_type
		ledger_entry.posting_date = doc.posting_date
		ledger_entry.voucher_type = doc.doctype
		ledger_entry.voucher_no = doc.name

		# Item and warehouse details
		ledger_entry.item_code = item.item_code
		ledger_entry.warehouse = item.warehouse
		ledger_entry.batch_no = item.get("batch_no")

		# Dual UOM: Stock Qty (Nos) and Weight (Kg)
		ledger_entry.stock_qty = stock_qty
		ledger_entry.weight_kg = weight_kg

		# Valuation: Capture rate per kg
		# For Purchase Receipt, use rate from the item row
		# For Delivery Note, we'll use a weighted average or item valuation rate
		if doc.doctype == "Purchase Receipt":
			# Calculate rate per kg from item amount and weight
			if weight_kg > 0:
				base_amount = flt(item.get("base_amount", 0))
				amount = flt(item.get("amount", 0))
				base_rate = flt(item.get("base_rate", 0))
				rate = flt(item.get("rate", 0))

				# Prefer base_amount (company currency) > amount > calculated from rate
				if base_amount > 0:
					ledger_entry.rate_per_kg = base_amount / weight_kg
				elif amount > 0:
					ledger_entry.rate_per_kg = amount / weight_kg
				elif base_rate > 0:
					total_amount = base_rate * stock_qty
					ledger_entry.rate_per_kg = total_amount / weight_kg
				elif rate > 0:
					total_amount = rate * stock_qty
					ledger_entry.rate_per_kg = total_amount / weight_kg
		else:
			# For Delivery Note, get valuation rate from item master or use weighted average
			valuation_rate = flt(item.get("incoming_rate", 0)) or flt(item.get("valuation_rate", 0))
			if valuation_rate > 0:
				# Convert from rate per Nos to rate per Kg
				if stock_qty > 0:
					rate_per_bird = valuation_rate
					ledger_entry.rate_per_kg = (rate_per_bird * stock_qty) / weight_kg if weight_kg > 0 else 0
			else:
				# Fallback: Get last purchase rate for this item
				last_rate = frappe.db.get_value(
					"Stock Weight Ledger",
					{"item_code": item.item_code, "transaction_type": "IN", "rate_per_kg": (">", 0)},
					"rate_per_kg",
					order_by="posting_date desc",
				)
				if last_rate:
					ledger_entry.rate_per_kg = last_rate

		# Optional: Individual bird weights for batch analytics
		if weights_list:
			ledger_entry.weights_list = weights_list

		# Remarks
		ledger_entry.remarks = f"Auto-created from {doc.doctype} {doc.name}"

		# Save the ledger entry
		# The validate() method will calculate avg_weight, weight_change, qty_change
		ledger_entry.insert(ignore_permissions=True)

		frappe.msgprint(
			_("Stock Weight Ledger updated: {0} Nos ({1} Kg) for {2} in {3}").format(
				stock_qty, weight_kg, item.item_code, item.warehouse
			),
			alert=True,
		)


def reverse_weight_ledger(doc, method):
	"""
	Delete Stock Weight Ledger entries when Purchase Receipt or Delivery Note is cancelled.

	Args:
		doc: Purchase Receipt or Delivery Note document
		method: on_cancel hook method
	"""
	# Delete all ledger entries for this voucher
	deleted_count = frappe.db.sql(
		"""
		DELETE FROM `tabStock Weight Ledger`
		WHERE voucher_type = %s AND voucher_no = %s
	""",
		(doc.doctype, doc.name),
	)

	frappe.msgprint(
		_("Reversed {0} Stock Weight Ledger entries for {1} {2}").format(
			deleted_count, doc.doctype, doc.name
		),
		alert=True,
	)


@frappe.whitelist()
def validate_stock_availability(item_code, warehouse, required_qty, required_weight_kg, batch_no=None):
	"""
	Validate if sufficient stock is available in dual UOM before sale/delivery.

	Args:
		item_code: Item code
		warehouse: Warehouse code
		required_qty: Required quantity in Nos
		required_weight_kg: Required weight in Kg
		batch_no: Optional batch number

	Returns:
		dict with is_available, available_qty, available_weight, message

	Raises:
		frappe.ValidationError if insufficient stock
	"""
	from shiva_erp.shiva_business_erp.doctype.stock_weight_ledger.stock_weight_ledger import get_stock_balance

	balance = get_stock_balance(item_code, warehouse, batch_no)

	available_qty = flt(balance.get("stock_qty", 0))
	available_weight = flt(balance.get("weight_kg", 0))

	is_available = available_qty >= flt(required_qty) and available_weight >= flt(required_weight_kg)

	message = ""
	if not is_available:
		message = _("Insufficient stock: Required {0} Nos ({1} Kg), Available {2} Nos ({3} Kg)").format(
			required_qty, required_weight_kg, available_qty, available_weight
		)

	return {
		"is_available": is_available,
		"available_qty": available_qty,
		"available_weight": available_weight,
		"message": message,
	}
