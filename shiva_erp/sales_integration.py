"""
Sales Integration Module for Shiva ERP

Integrates dual UOM stock tracking with Sales Invoice and Delivery Note.
Applies shop-wise pricing and discounts based on area and price type.
"""

import frappe
from frappe import _
from frappe.utils import flt


def sales_invoice_on_submit(doc, method):
	"""
	Hook: Sales Invoice on_submit
	- Apply shop pricing and discounts
	- Update Stock Weight Ledger
	- Validate stock availability
	"""
	# Update stock weight ledger for sales
	update_sales_stock_ledger(doc, "Sales Invoice")

	# Apply shop pricing if not already applied
	apply_shop_pricing(doc)


def delivery_note_on_submit(doc, method):
	"""
	Hook: Delivery Note on_submit
	- Update Stock Weight Ledger
	- Validate stock availability
	"""
	# Update stock weight ledger for deliveries
	update_sales_stock_ledger(doc, "Delivery Note")


def sales_invoice_on_cancel(doc, method):
	"""
	Hook: Sales Invoice on_cancel
	Reverse Stock Weight Ledger entries
	"""
	reverse_sales_stock_ledger(doc)


def delivery_note_on_cancel(doc, method):
	"""
	Hook: Delivery Note on_cancel
	Reverse Stock Weight Ledger entries
	"""
	reverse_sales_stock_ledger(doc)


def sales_invoice_validate(doc, method):
	"""
	Hook: Sales Invoice validate
	- Apply territory-based pricing automatically
	- Validate stock availability before submit
	- Validate weight and pricing
	"""
	# Only apply pricing if customer and items exist
	if doc.customer and doc.items:
		try:
			apply_shop_pricing(doc)
		except Exception as e:
			# Log error but don't block save
			frappe.log_error(title="Pricing Application Error", message=str(e))

	# Only validate stock on submit
	if doc.docstatus == 1:
		validate_sales_transaction(doc)


def delivery_note_validate(doc, method):
	"""
	Hook: Delivery Note validate
	- Validate stock availability
	- Validate weight data
	"""
	validate_sales_transaction(doc)


def update_sales_stock_ledger(doc, voucher_type):
	"""
	Create Stock Weight Ledger entries for sales transactions (OUT).

	Args:
		doc: Sales Invoice or Delivery Note
		voucher_type: Document type
	"""
	for item in doc.items:
		# Get dual UOM data
		weight_kg = flt(item.get("custom_total_weight_kg", 0))
		stock_qty = flt(item.get("qty", 0))

		# Skip if no weight or quantity
		if weight_kg <= 0 or stock_qty <= 0:
			continue

		# Validate stock availability
		from shiva_erp.stock_logic import validate_stock_availability

		availability = validate_stock_availability(
			item.item_code, item.warehouse, stock_qty, weight_kg, item.get("batch_no")
		)

		if not availability.get("is_available"):
			frappe.throw(_("Row #{0}: {1}").format(item.idx, availability.get("message")))

		# Create Stock Weight Ledger entry (OUT transaction)
		ledger_entry = frappe.new_doc("Stock Weight Ledger")

		# Transaction details
		ledger_entry.transaction_type = "OUT"
		ledger_entry.posting_date = doc.posting_date
		ledger_entry.voucher_type = voucher_type
		ledger_entry.voucher_no = doc.name

		# Item and warehouse
		ledger_entry.item_code = item.item_code
		ledger_entry.warehouse = item.warehouse
		ledger_entry.batch_no = item.get("batch_no")

		# Dual UOM
		ledger_entry.stock_qty = stock_qty
		ledger_entry.weight_kg = weight_kg

		# Optional individual weights
		weights_list = item.get("custom_bird_weights_json")
		if weights_list:
			ledger_entry.weights_list = weights_list

		# Remarks
		ledger_entry.remarks = f"Auto-created from {voucher_type} {doc.name} for {doc.customer}"

		# Save
		ledger_entry.insert(ignore_permissions=True)


def reverse_sales_stock_ledger(doc):
	"""
	Delete Stock Weight Ledger entries when sales transaction is cancelled.

	Args:
		doc: Sales Invoice or Delivery Note
	"""
	frappe.db.sql(
		"""
		DELETE FROM `tabStock Weight Ledger`
		WHERE voucher_type = %s AND voucher_no = %s
	""",
		(doc.doctype, doc.name),
	)

	frappe.msgprint(
		_("Reversed Stock Weight Ledger entries for {0} {1}").format(doc.doctype, doc.name),
		alert=True,
	)


def apply_shop_pricing(doc):
	"""
	Apply shop-wise pricing and discounts to Sales Invoice.

	New Architecture:
	1. Get customer's territory from Customer master
	2. Get base_price from Item Price Type (item + territory)
	3. Get discount from Shop Discount (shop + item)
	4. Calculate effective_price = base_price - discount
	5. Apply: amount = effective_price * weight_kg

	Args:
		doc: Sales Invoice document
	"""
	if doc.doctype != "Sales Invoice":
		return

	# Get customer's territory
	if not doc.customer:
		return

	customer = frappe.get_doc("Customer", doc.customer)
	territory = customer.territory

	if not territory:
		frappe.msgprint(
			_("Customer {0} has no territory assigned. Cannot apply territory-based pricing.").format(
				doc.customer
			),
			indicator="red",
			alert=True,
		)
		return

	for item in doc.items:
		# Get custom fields
		weight_kg = flt(item.get("custom_total_weight_kg", 0))

		if weight_kg <= 0:
			continue

		# 1. Get base price from Item Price Type (by territory)
		from shiva_erp.shiva_business_erp.doctype.item_price_type.item_price_type import get_base_price

		base_price_record = get_base_price(item.item_code, territory, doc.posting_date)

		if not base_price_record:
			frappe.msgprint(
				_("Row #{0}: No base price found for {1} in territory {2}").format(
					item.idx, item.item_code, territory
				),
				indicator="orange",
				alert=True,
			)
			continue

		base_price = flt(base_price_record.get("base_price_per_kg", 0))

		if base_price <= 0:
			frappe.msgprint(
				_("Row #{0}: Invalid base price for {1} in territory {2}").format(
					item.idx, item.item_code, territory
				),
				indicator="orange",
				alert=True,
			)
			continue

		# 2. Get shop-specific discount from Shop Discount
		from shiva_erp.shiva_business_erp.doctype.shop_discount.shop_discount import get_shop_discount

		discount = get_shop_discount(doc.customer, item.item_code, doc.posting_date)

		# 3. Calculate effective price
		effective_price = base_price - discount

		# Ensure effective price is not negative
		if effective_price < 0:
			frappe.msgprint(
				_(
					"Row #{0}: Discount (₹{1}/kg) exceeds base price (₹{2}/kg). Setting effective price to 0."
				).format(item.idx, discount, base_price),
				indicator="red",
				alert=True,
			)
			effective_price = 0

		# 4. Store in custom fields for reference
		item.custom_base_price_per_kg = base_price
		item.custom_discount_per_kg = discount

		# Calculate rate and amount
		# rate = effective_price_per_kg (already discounted)
		item.rate = effective_price

		# Calculate amount = rate * weight_kg
		# Note: ERPNext expects rate to be per UOM, but we're billing by weight
		# So we set qty = weight_kg and rate = effective_price_per_kg
		item.qty = weight_kg  # Override qty to weight for billing
		item.amount = effective_price * weight_kg

		frappe.msgprint(
			_("Row #{0}: Applied {1} pricing - ₹{2}/kg (discount: ₹{3}/kg) for {4} kg = ₹{5}").format(
				item.idx, territory, base_price, discount, weight_kg, item.amount
			),
			alert=True,
		)


@frappe.whitelist()
def apply_shop_pricing_manually(doc):
	"""
	Manually apply pricing from client script.

	Args:
		doc: Sales Invoice document (as dict from client)
	"""
	if isinstance(doc, str):
		import json

		doc = json.loads(doc)

	doc_obj = frappe.get_doc(doc)
	apply_shop_pricing(doc_obj)

	return doc_obj.as_dict()


@frappe.whitelist()
def apply_pricing_to_invoice(invoice_name):
	"""
	Apply territory-based pricing to a saved Sales Invoice.

	Args:
		invoice_name: Name of the Sales Invoice

	Returns:
		dict: Updated invoice data
	"""
	doc = frappe.get_doc("Sales Invoice", invoice_name)

	if doc.docstatus != 0:
		frappe.throw(_("Cannot modify submitted invoice"))

	apply_shop_pricing(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"status": "success", "message": _("Pricing applied successfully")}


def validate_sales_transaction(doc):
	"""
	Validate sales transaction before submit.

	Checks:
	- Weight data exists and is valid
	- Stock availability in dual UOM
	- Pricing data (for Sales Invoice)

	Args:
		doc: Sales Invoice or Delivery Note
	"""
	for item in doc.items:
		# Validate weight data
		weight_kg = flt(item.get("custom_total_weight_kg", 0))
		stock_qty = flt(item.get("qty", 0))

		if stock_qty > 0 and weight_kg <= 0:
			frappe.msgprint(
				_("Row #{0}: Please enter Total Weight (Kg) for {1}").format(item.idx, item.item_code),
				indicator="red",
				alert=True,
			)

		# Validate reasonable average weight (0.5 to 5 kg per bird)
		if stock_qty > 0 and weight_kg > 0:
			avg_weight = weight_kg / stock_qty
			if avg_weight < 0.5 or avg_weight > 5.0:
				frappe.msgprint(
					_("Row #{0}: Average weight {1} kg/bird seems unusual. Please verify.").format(
						item.idx, round(avg_weight, 3)
					),
					indicator="orange",
					alert=True,
				)


@frappe.whitelist()
def get_stock_and_price_details(customer, item_code, warehouse, qty, price_type="Wholesale"):
	"""
	Get stock availability and pricing details for a sales transaction.

	Uses new pricing architecture:
	- Base price from Item Price Type
	- Discount from Shop Discount
	- Effective price = base - discount

	Args:
		customer: Customer code (shop)
		item_code: Item code
		warehouse: Warehouse code
		qty: Required quantity (Nos)
		price_type: Price type (default: Wholesale)

	Returns:
		dict with stock balance, pricing, and availability
	"""
	# Get stock balance
	from shiva_erp.shiva_business_erp.doctype.stock_weight_ledger.stock_weight_ledger import get_stock_balance

	balance = get_stock_balance(item_code, warehouse)

	# Get base price from Item Price Type
	from shiva_erp.shiva_business_erp.doctype.item_price_type.item_price_type import get_base_price

	base_price = get_base_price(item_code, price_type)

	# Get shop discount
	from shiva_erp.shiva_business_erp.doctype.shop_discount.shop_discount import get_shop_discount

	discount = get_shop_discount(customer, item_code)

	# Calculate effective price
	effective_price = (base_price or 0) - (discount or 0)
	if effective_price < 0:
		effective_price = 0

	price_data = {
		"base_price_per_kg": base_price,
		"discount_per_kg": discount,
		"effective_price_per_kg": effective_price,
		"price_type": price_type,
	}

	return {
		"stock_balance": balance,
		"price_data": price_data,
	}


@frappe.whitelist()
def get_item_pricing(customer, item_code, posting_date=None, weight_kg=0):
	"""
	Get pricing for an item based on customer territory and shop discount.

	Args:
		customer: Customer name
		item_code: Item code
		posting_date: Posting date for price lookup
		weight_kg: Weight in kg for amount calculation

	Returns:
		dict with base_price, discount, effective_price, and calculated amount
	"""
	if not posting_date:
		posting_date = frappe.utils.today()

	# Get customer territory
	customer_doc = frappe.get_doc("Customer", customer)
	territory = customer_doc.territory

	if not territory:
		return {
			"base_price": 0,
			"discount": 0,
			"effective_price": 0,
			"message": f"Customer {customer} has no territory assigned",
		}

	# Get base price from Item Price Type (by territory)
	from shiva_erp.shiva_business_erp.doctype.item_price_type.item_price_type import get_base_price

	base_price_record = get_base_price(item_code, territory, posting_date)
	base_price = flt(base_price_record.get("base_price_per_kg", 0)) if base_price_record else 0

	if base_price <= 0:
		return {
			"base_price": 0,
			"discount": 0,
			"effective_price": 0,
			"message": f"No base price found for {item_code} in territory {territory}",
		}

	# Get shop-specific discount
	from shiva_erp.shiva_business_erp.doctype.shop_discount.shop_discount import get_shop_discount

	discount = flt(get_shop_discount(customer, item_code, posting_date))

	# Calculate effective price = base_price - shop_discount
	effective_price = base_price - discount

	# Ensure effective price is not negative
	if effective_price < 0:
		effective_price = 0

	weight_kg = flt(weight_kg)
	amount = effective_price * weight_kg if weight_kg > 0 else 0

	return {
		"base_price": base_price,
		"discount": discount,
		"effective_price": effective_price,
		"territory": territory,
		"amount": amount,
		"message": f"Applied {territory} pricing: ₹{base_price}/kg - ₹{discount}/kg discount = ₹{effective_price}/kg",
	}
