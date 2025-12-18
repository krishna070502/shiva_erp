# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	"""
	Shop Sales Analysis Report

	Analyzes sales by shop with:
	- Total quantity sold (Nos)
	- Total weight sold (Kg)
	- Base price, discount, and effective price
	- Revenue breakdown
	"""
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "customer",
			"label": _("Shop (Customer)"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		},
		{
			"fieldname": "customer_name",
			"label": _("Shop Name"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "territory",
			"label": _("Area"),
			"fieldtype": "Link",
			"options": "Territory",
			"width": 120,
		},
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"fieldname": "total_qty",
			"label": _("Total Qty (Nos)"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"fieldname": "total_weight_kg",
			"label": _("Total Weight (Kg)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 3,
		},
		{
			"fieldname": "avg_price_per_kg",
			"label": _("Avg Price/Kg (INR)"),
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"fieldname": "total_discount",
			"label": _("Total Discount (INR)"),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "total_revenue",
			"label": _("Total Revenue (INR)"),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "invoice_count",
			"label": _("No. of Invoices"),
			"fieldtype": "Int",
			"width": 120,
		},
	]


def get_data(filters):
	"""
	Get shop-wise sales data with dual UOM and discount analysis

	Args:
		filters: dict with customer, territory, item_code, from_date, to_date

	Returns:
		list of dicts with sales analysis data
	"""
	conditions = ["si.docstatus = 1"]  # Only submitted invoices
	params = {}

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		params["customer"] = filters["customer"]

	if filters.get("territory"):
		conditions.append("si.territory = %(territory)s")
		params["territory"] = filters["territory"]

	if filters.get("item_code"):
		conditions.append("sii.item_code = %(item_code)s")
		params["item_code"] = filters["item_code"]

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	where_clause = "WHERE " + " AND ".join(conditions)

	query = f"""
		SELECT
			si.customer,
			si.customer_name,
			si.territory,
			sii.item_code,
			SUM(sii.qty) as total_qty,
			SUM(IFNULL(sii.custom_total_weight_kg, 0)) as total_weight_kg,
			AVG(sii.rate) as avg_price_per_kg,
			SUM(IFNULL(sii.custom_discount_per_kg, 0) * IFNULL(sii.custom_total_weight_kg, 0)) as total_discount,
			SUM(sii.amount) as total_revenue,
			COUNT(DISTINCT si.name) as invoice_count
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		{where_clause}
		GROUP BY si.customer, si.territory, sii.item_code
		ORDER BY total_revenue DESC
	"""

	data = frappe.db.sql(query, params, as_dict=True)

	return data
