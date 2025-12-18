"""
Bulk Update Utilities for Pricing Management

Provides utilities for:
1. Daily base price updates by price type (affects all shops)
2. Bulk discount updates for specific shops
3. Price history tracking and audit trails
"""

import frappe
from frappe import _
from frappe.utils import getdate, today


@frappe.whitelist()
def bulk_update_price_by_type(price_type, percentage_change=0.0, absolute_change=0.0):
	"""
	Bulk update base prices for all items of a specific price type

	This is the primary function for daily price updates.
	Updates once per price type → affects all shops automatically

	Args:
	    price_type: Price type to update (Wholesale/Retail/Premium/Bulk)
	    percentage_change: Percentage change (e.g., 5 for +5%, -3 for -3%)
	    absolute_change: Absolute change in INR (e.g., 10 for +₹10, -5 for -₹5)

	Returns:
	    dict with update summary
	"""
	if not price_type:
		frappe.throw(_("Price Type is required"))

	# Get all active base prices for this price type
	prices = frappe.get_all(
		"Item Price Type",
		filters={"price_type": price_type, "is_active": 1},
		fields=["name", "item_code", "base_price_per_kg"],
	)

	if not prices:
		frappe.msgprint(_("No active prices found for {0}").format(price_type))
		return {"updated": 0, "items": []}

	updated_items = []

	for price in prices:
		old_price = price.base_price_per_kg

		# Calculate new price
		new_price = old_price
		if percentage_change:
			new_price += old_price * percentage_change / 100
		if absolute_change:
			new_price += absolute_change

		# Ensure price is positive
		if new_price <= 0:
			frappe.msgprint(
				_("Skipping {0}: New price would be ₹{1} (non-positive)").format(price.item_code, new_price),
				indicator="orange",
			)
			continue

		# Update price
		doc = frappe.get_doc("Item Price Type", price.name)
		doc.base_price_per_kg = new_price
		doc.save(ignore_permissions=True)

		updated_items.append(
			{
				"item_code": price.item_code,
				"old_price": old_price,
				"new_price": new_price,
				"change": new_price - old_price,
			}
		)

		# Log to Price History
		log_price_history(
			doctype="Item Price Type",
			docname=price.name,
			field="base_price_per_kg",
			old_value=old_price,
			new_value=new_price,
			change_reason=f"Bulk update: {percentage_change}% + ₹{absolute_change}",
		)

	frappe.db.commit()

	summary = {
		"updated": len(updated_items),
		"price_type": price_type,
		"percentage_change": percentage_change,
		"absolute_change": absolute_change,
		"items": updated_items,
	}

	frappe.msgprint(_("Updated {0} base prices for {1}").format(len(updated_items), price_type), alert=True)

	return summary


@frappe.whitelist()
def bulk_update_shop_discounts(shop=None, item_codes=None, new_discount=None, percentage_change=0.0):
	"""
	Bulk update discounts for specific shops or items

	Args:
	    shop: Customer code (optional, updates all shops if None)
	    item_codes: List of item codes (optional, updates all items if None)
	    new_discount: Set absolute discount value (overrides percentage_change)
	    percentage_change: Percentage change to existing discount

	Returns:
	    dict with update summary
	"""
	filters = {"is_active": 1}

	if shop:
		filters["shop"] = shop

	if item_codes:
		if isinstance(item_codes, str):
			item_codes = [x.strip() for x in item_codes.split(",")]
		filters["item_code"] = ["in", item_codes]

	discounts = frappe.get_all(
		"Shop Discount", filters=filters, fields=["name", "shop", "item_code", "discount_per_kg"]
	)

	if not discounts:
		frappe.msgprint(_("No matching discount records found"))
		return {"updated": 0, "discounts": []}

	updated_discounts = []

	for discount in discounts:
		old_discount = discount.discount_per_kg

		# Calculate new discount
		if new_discount is not None:
			new_discount_value = float(new_discount)
		else:
			new_discount_value = old_discount + (old_discount * percentage_change / 100)

		# Ensure discount is non-negative
		if new_discount_value < 0:
			new_discount_value = 0

		# Update discount
		doc = frappe.get_doc("Shop Discount", discount.name)
		doc.discount_per_kg = new_discount_value
		doc.save(ignore_permissions=True)

		updated_discounts.append(
			{
				"shop": discount.shop,
				"item_code": discount.item_code,
				"old_discount": old_discount,
				"new_discount": new_discount_value,
				"change": new_discount_value - old_discount,
			}
		)

		# Log to Price History
		log_price_history(
			doctype="Shop Discount",
			docname=discount.name,
			field="discount_per_kg",
			old_value=old_discount,
			new_value=new_discount_value,
			change_reason=f"Bulk update: {percentage_change}% change",
		)

	frappe.db.commit()

	summary = {"updated": len(updated_discounts), "shop": shop, "discounts": updated_discounts}

	frappe.msgprint(_("Updated {0} shop discount records").format(len(updated_discounts)), alert=True)

	return summary


@frappe.whitelist()
def preview_price_update(price_type, percentage_change=0.0, absolute_change=0.0):
	"""
	Preview base price updates without actually updating

	Args:
	    price_type: Price type to preview
	    percentage_change: Percentage change
	    absolute_change: Absolute change in INR

	Returns:
	    list of items with old and new prices
	"""
	prices = frappe.get_all(
		"Item Price Type",
		filters={"price_type": price_type, "is_active": 1},
		fields=["item_code", "base_price_per_kg"],
	)

	preview_data = []

	for price in prices:
		old_price = price.base_price_per_kg
		new_price = old_price

		if percentage_change:
			new_price += old_price * percentage_change / 100
		if absolute_change:
			new_price += absolute_change

		preview_data.append(
			{
				"item_code": price.item_code,
				"old_price": old_price,
				"new_price": max(0, new_price),
				"change": new_price - old_price,
				"change_percent": ((new_price - old_price) / old_price * 100) if old_price > 0 else 0,
			}
		)

	return preview_data


def log_price_history(doctype, docname, field, old_value, new_value, change_reason=""):
	"""
	Log price changes to audit trail

	Args:
	    doctype: Source DocType (Item Price Type or Shop Discount)
	    docname: Document name
	    field: Field that changed
	    old_value: Old value
	    new_value: New value
	    change_reason: Reason for change
	"""
	try:
		history = frappe.get_doc(
			{
				"doctype": "Price Change History",
				"reference_doctype": doctype,
				"reference_name": docname,
				"field_name": field,
				"old_value": old_value,
				"new_value": new_value,
				"change_date": today(),
				"change_by": frappe.session.user,
				"change_reason": change_reason,
			}
		)
		history.insert(ignore_permissions=True)
	except Exception as e:
		# Don't fail the main operation if history logging fails
		frappe.log_error(
			title="Price History Logging Failed",
			message=f"Failed to log price change for {doctype} {docname}: {e!s}",
		)


@frappe.whitelist()
def get_price_history(doctype, docname, limit=10):
	"""
	Get price change history for a document

	Args:
	    doctype: Item Price Type or Shop Discount
	    docname: Document name
	    limit: Number of records to fetch

	Returns:
	    list of price changes
	"""
	history = frappe.get_all(
		"Price Change History",
		filters={"reference_doctype": doctype, "reference_name": docname},
		fields=["*"],
		order_by="change_date desc, creation desc",
		limit=limit,
	)

	return history


@frappe.whitelist()
def get_pricing_dashboard_data():
	"""
	Get dashboard data for pricing overview

	Returns:
	    dict with counts and statistics
	"""
	data = {
		"total_base_prices": frappe.db.count("Item Price Type", {"is_active": 1}),
		"total_shop_discounts": frappe.db.count("Shop Discount", {"is_active": 1}),
		"price_types": {},
		"recent_changes": [],
	}

	# Count by price type
	price_type_counts = frappe.db.sql(
		"""
        SELECT price_type, COUNT(*) as count, AVG(base_price_per_kg) as avg_price
        FROM `tabItem Price Type`
        WHERE is_active = 1
        GROUP BY price_type
    """,
		as_dict=True,
	)

	for row in price_type_counts:
		data["price_types"][row.price_type] = {"count": row.count, "average_price": row.avg_price}

	# Get recent changes (if history exists)
	try:
		data["recent_changes"] = frappe.get_all(
			"Price Change History", fields=["*"], order_by="change_date desc, creation desc", limit=5
		)
	except Exception:
		pass

	return data
