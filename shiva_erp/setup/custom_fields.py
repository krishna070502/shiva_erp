"""
Custom Fields Setup for Shiva ERP

Adds custom fields to standard ERPNext DocTypes for dual UOM tracking
and territory-based pricing.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup_custom_fields():
	"""
	Create all custom fields needed for Shiva ERP functionality.

	Custom fields are added to:
	- Sales Invoice Item: For weight tracking and pricing
	- Delivery Note Item: For weight tracking
	- Purchase Receipt Item: For weight tracking
	"""
	custom_fields = {
		"Sales Invoice Item": [
			{
				"fieldname": "custom_total_weight_kg",
				"label": "Total Weight (Kg)",
				"fieldtype": "Float",
				"insert_after": "qty",
				"precision": 3,
				"in_list_view": 1,
				"reqd": 0,
				"description": "Total weight in kilograms for this line item",
			},
			{
				"fieldname": "custom_base_price_per_kg",
				"label": "Base Price per Kg",
				"fieldtype": "Currency",
				"insert_after": "custom_total_weight_kg",
				"read_only": 1,
				"in_list_view": 0,
				"description": "Territory-based base price (auto-calculated)",
			},
			{
				"fieldname": "custom_discount_per_kg",
				"label": "Discount per Kg",
				"fieldtype": "Currency",
				"insert_after": "custom_base_price_per_kg",
				"read_only": 1,
				"in_list_view": 0,
				"description": "Shop-specific discount (auto-calculated)",
			},
		],
		"Sales Order Item": [
			{
				"fieldname": "custom_total_weight_kg",
				"label": "Total Weight (Kg)",
				"fieldtype": "Float",
				"insert_after": "qty",
				"precision": 3,
				"in_list_view": 1,
				"columns": 2,
				"bold": 1,
				"reqd": 0,
				"description": "Total weight in kilograms for this line item",
			},
		],
		"Delivery Note Item": [
			{
				"fieldname": "custom_total_weight_kg",
				"label": "Total Weight (Kg)",
				"fieldtype": "Float",
				"insert_after": "qty",
				"precision": 3,
				"in_list_view": 1,
				"reqd": 0,
				"description": "Total weight in kilograms for this line item",
			},
		],
		"Purchase Receipt Item": [
			{
				"fieldname": "custom_total_weight_kg",
				"label": "Total Weight (Kg)",
				"fieldtype": "Float",
				"insert_after": "qty",
				"precision": 3,
				"in_list_view": 1,
				"reqd": 0,
				"description": "Total weight in kilograms for this line item",
			},
		],
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
	print("✓ Custom fields created successfully")


def remove_custom_fields():
	"""Remove all custom fields created by this app (for cleanup/uninstall)"""
	custom_fields_to_remove = [
		("Sales Invoice Item", "custom_total_weight_kg"),
		("Sales Invoice Item", "custom_base_price_per_kg"),
		("Sales Invoice Item", "custom_discount_per_kg"),
		("Delivery Note Item", "custom_total_weight_kg"),
		("Purchase Receipt Item", "custom_total_weight_kg"),
	]

	for dt, fieldname in custom_fields_to_remove:
		if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
			frappe.delete_doc("Custom Field", f"{dt}-{fieldname}")

	frappe.db.commit()
	print("✓ Custom fields removed successfully")
