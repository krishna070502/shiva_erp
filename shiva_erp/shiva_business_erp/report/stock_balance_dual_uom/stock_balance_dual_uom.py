# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	Stock Balance Dual UOM Report

	Shows current stock balance in both UOMs (Nos + Kg) for all items.
	Supports filtering by item, warehouse, and batch.
	"""
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 150,
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "warehouse",
			"label": _("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 120,
		},
		{
			"fieldname": "batch_no",
			"label": _("Batch No"),
			"fieldtype": "Link",
			"options": "Batch",
			"width": 100,
		},
		{
			"fieldname": "stock_qty",
			"label": _("Stock Qty (Nos)"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"fieldname": "weight_kg",
			"label": _("Total Weight (Kg)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 3,
		},
		{
			"fieldname": "avg_weight_per_bird",
			"label": _("Avg Weight/Bird (Kg)"),
			"fieldtype": "Float",
			"width": 150,
			"precision": 3,
		},
		{
			"fieldname": "last_transaction_date",
			"label": _("Last Transaction"),
			"fieldtype": "Date",
			"width": 120,
		},
	]


def get_data(filters):
	"""
	Get stock balance data with dual UOM

	Args:
		filters: dict with item_code, warehouse, batch_no

	Returns:
		list of dicts with stock balance data
	"""
	conditions = []
	params = {}

	if filters.get("item_code"):
		conditions.append("swl.item_code = %(item_code)s")
		params["item_code"] = filters["item_code"]

	if filters.get("warehouse"):
		conditions.append("swl.warehouse = %(warehouse)s")
		params["warehouse"] = filters["warehouse"]

	if filters.get("batch_no"):
		conditions.append("swl.batch_no = %(batch_no)s")
		params["batch_no"] = filters["batch_no"]

	where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

	query = f"""
		SELECT
			swl.item_code,
			item.item_name,
			swl.warehouse,
			swl.batch_no,
			SUM(swl.qty_change) as stock_qty,
			SUM(swl.weight_change) as weight_kg,
			CASE
				WHEN SUM(swl.qty_change) > 0
				THEN SUM(swl.weight_change) / SUM(swl.qty_change)
				ELSE 0
			END as avg_weight_per_bird,
			MAX(swl.posting_date) as last_transaction_date
		FROM `tabStock Weight Ledger` swl
		LEFT JOIN `tabItem` item ON item.name = swl.item_code
		{where_clause}
		GROUP BY swl.item_code, swl.warehouse, swl.batch_no
		HAVING stock_qty > 0 OR weight_kg > 0
		ORDER BY swl.item_code, swl.warehouse, swl.batch_no
	"""

	data = frappe.db.sql(query, params, as_dict=True)

	return data
