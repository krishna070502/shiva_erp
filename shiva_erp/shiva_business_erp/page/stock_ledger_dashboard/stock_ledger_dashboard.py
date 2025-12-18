# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


@frappe.whitelist()
def get_dashboard_data(filters=None):
	"""
	Get comprehensive dashboard data for stock ledger

	Args:
		filters: dict with from_date, to_date, item_code, warehouse

	Returns:
		dict with summary, chart_data, and details
	"""
	if isinstance(filters, str):
		import json

		filters = json.loads(filters)

	if not filters:
		filters = {}

	# Get ledger data
	ledger_data = get_ledger_data(filters)

	# Calculate summary metrics
	summary = calculate_summary_metrics(ledger_data, filters)

	# Prepare chart data
	chart_data = prepare_chart_data(ledger_data)

	# Get detailed breakdowns
	details = get_detailed_breakdowns(ledger_data, filters)

	return {"summary": summary, "chart_data": chart_data, "details": details}


def get_ledger_data(filters):
	"""Get all ledger entries based on filters"""
	conditions = []
	params = {}

	if filters.get("from_date"):
		conditions.append("posting_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("posting_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	if filters.get("item_code"):
		conditions.append("item_code = %(item_code)s")
		params["item_code"] = filters["item_code"]

	if filters.get("warehouse"):
		conditions.append("warehouse = %(warehouse)s")
		params["warehouse"] = filters["warehouse"]

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	query = f"""
		SELECT
			name, posting_date, transaction_type, voucher_type, voucher_no,
			item_code, warehouse, batch_no, stock_qty, weight_kg,
			qty_change, weight_change, avg_weight_per_bird,
			rate_per_kg, value_amount
		FROM
			`tabStock Weight Ledger`
		WHERE
			{where_clause}
		ORDER BY
			posting_date ASC, creation ASC
	"""

	return frappe.db.sql(query, params, as_dict=1)


def calculate_summary_metrics(ledger_data, filters):
	"""Calculate summary metrics from ledger data - Weight and Value"""
	total_in_weight = 0
	total_out_weight = 0
	total_in_value = 0
	total_out_value = 0

	for row in ledger_data:
		if row.transaction_type == "IN":
			total_in_weight += abs(flt(row.weight_change))
			total_in_value += abs(flt(row.value_amount))
		elif row.transaction_type == "OUT":
			total_out_weight += abs(flt(row.weight_change))
			total_out_value += abs(flt(row.value_amount))
		else:
			# If transaction_type is NULL/empty, determine from weight_change sign
			if flt(row.weight_change) > 0:
				total_in_weight += abs(flt(row.weight_change))
				total_in_value += abs(flt(row.value_amount))
			else:
				total_out_weight += abs(flt(row.weight_change))
				total_out_value += abs(flt(row.value_amount))

	# Get opening balance
	opening = get_opening_balance(filters)
	opening_weight = opening.get("weight", 0)
	opening_value = opening.get("value", 0)

	# Calculate closing
	closing_weight = opening_weight + total_in_weight - total_out_weight
	closing_value = opening_value + total_in_value - total_out_value

	return {
		"opening_weight": opening_weight,
		"opening_value": opening_value,
		"total_in_weight": total_in_weight,
		"total_in_value": total_in_value,
		"total_out_weight": total_out_weight,
		"total_out_value": total_out_value,
		"closing_weight": closing_weight,
		"closing_value": closing_value,
		"net_weight": total_in_weight - total_out_weight,
		"net_value": total_in_value - total_out_value,
		"total_transactions": len(ledger_data),
	}


def get_opening_balance(filters):
	"""Get opening balance before from_date"""
	conditions = []
	params = {}

	if filters.get("from_date"):
		conditions.append("posting_date < %(from_date)s")
		params["from_date"] = filters["from_date"]
	else:
		return {"qty": 0, "weight": 0}

	if filters.get("item_code"):
		conditions.append("item_code = %(item_code)s")
		params["item_code"] = filters["item_code"]

	if filters.get("warehouse"):
		conditions.append("warehouse = %(warehouse)s")
		params["warehouse"] = filters["warehouse"]

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			COALESCE(SUM(weight_change), 0) as opening_weight,
			COALESCE(SUM(
				CASE 
					WHEN transaction_type = 'IN' THEN value_amount
					WHEN transaction_type = 'OUT' THEN -value_amount
					ELSE 0
				END
			), 0) as opening_value
		FROM
			`tabStock Weight Ledger`
		WHERE
			{where_clause}
	"""

	result = frappe.db.sql(query, params, as_dict=1)
	return (
		{"weight": flt(result[0].opening_weight), "value": flt(result[0].opening_value)}
		if result
		else {"weight": 0, "value": 0}
	)


def prepare_chart_data(ledger_data):
	"""Prepare data for charts"""
	# Group by date
	date_wise = {}

	for row in ledger_data:
		date = str(row.posting_date)
		if date not in date_wise:
			date_wise[date] = {
				"in_weight": 0,
				"out_weight": 0,
				"balance_weight": 0,
				"in_value": 0,
				"out_value": 0,
				"balance_value": 0,
			}

		if row.transaction_type == "IN":
			date_wise[date]["in_weight"] += abs(flt(row.weight_change))
			date_wise[date]["in_value"] += abs(flt(row.value_amount))
		else:
			date_wise[date]["out_weight"] += abs(flt(row.weight_change))
			date_wise[date]["out_value"] += abs(flt(row.value_amount))

	# Calculate running balance
	sorted_dates = sorted(date_wise.keys())
	balance_weight = 0
	balance_value = 0

	for date in sorted_dates:
		balance_weight += date_wise[date]["in_weight"] - date_wise[date]["out_weight"]
		balance_value += date_wise[date]["in_value"] - date_wise[date]["out_value"]
		date_wise[date]["balance_weight"] = balance_weight
		date_wise[date]["balance_value"] = balance_value

	# Format for charts
	labels = sorted_dates
	in_weight_data = [date_wise[d]["in_weight"] for d in labels]
	out_weight_data = [date_wise[d]["out_weight"] for d in labels]
	balance_weight_data = [date_wise[d]["balance_weight"] for d in labels]
	in_value_data = [date_wise[d]["in_value"] for d in labels]
	out_value_data = [date_wise[d]["out_value"] for d in labels]
	balance_value_data = [date_wise[d]["balance_value"] for d in labels]

	# Item-wise distribution by weight and value
	item_wise_weight = {}
	item_wise_value = {}
	for row in ledger_data:
		if row.item_code not in item_wise_weight:
			item_wise_weight[row.item_code] = 0
			item_wise_value[row.item_code] = 0
		item_wise_weight[row.item_code] += abs(flt(row.weight_change))
		item_wise_value[row.item_code] += abs(flt(row.value_amount))

	return {
		"daily_movement_weight": {
			"labels": labels,
			"datasets": [
				{"name": "IN (Kg)", "values": in_weight_data},
				{"name": "OUT (Kg)", "values": out_weight_data},
			],
		},
		"daily_movement_value": {
			"labels": labels,
			"datasets": [
				{"name": "IN (₹)", "values": in_value_data},
				{"name": "OUT (₹)", "values": out_value_data},
			],
		},
		"balance_trend": {
			"labels": labels,
			"datasets": [
				{"name": "Weight Balance (Kg)", "values": balance_weight_data},
				{"name": "Value Balance (₹)", "values": balance_value_data},
			],
		},
		"item_distribution": {
			"labels": list(item_wise_weight.keys()),
			"datasets": [
				{"name": "Weight (Kg)", "values": list(item_wise_weight.values())},
				{"name": "Value (₹)", "values": list(item_wise_value.values())},
			],
		},
	}


def get_detailed_breakdowns(ledger_data, filters):
	"""Get detailed breakdowns for tables"""
	# Top items by weight and value movement
	item_stats = {}
	for row in ledger_data:
		if row.item_code not in item_stats:
			item_stats[row.item_code] = {
				"item_code": row.item_code,
				"transaction_count": 0,
				"total_weight": 0,
				"total_value": 0,
			}

		item_stats[row.item_code]["transaction_count"] += 1
		item_stats[row.item_code]["total_weight"] += abs(flt(row.weight_change))
		item_stats[row.item_code]["total_value"] += abs(flt(row.value_amount))

	top_items = sorted(item_stats.values(), key=lambda x: x["total_weight"], reverse=True)[:10]

	# Warehouse-wise summary
	warehouse_stats = {}
	for row in ledger_data:
		if row.warehouse not in warehouse_stats:
			warehouse_stats[row.warehouse] = {
				"warehouse": row.warehouse,
				"in_weight": 0,
				"out_weight": 0,
				"balance_weight": 0,
				"in_value": 0,
				"out_value": 0,
				"balance_value": 0,
			}

		if row.transaction_type == "IN":
			warehouse_stats[row.warehouse]["in_weight"] += abs(flt(row.weight_change))
			warehouse_stats[row.warehouse]["in_value"] += abs(flt(row.value_amount))
		else:
			warehouse_stats[row.warehouse]["out_weight"] += abs(flt(row.weight_change))
			warehouse_stats[row.warehouse]["out_value"] += abs(flt(row.value_amount))

	# Get current balance for each warehouse
	for wh in warehouse_stats:
		balance = get_current_balance(filters.get("item_code"), wh, filters.get("to_date"))
		warehouse_stats[wh]["balance_weight"] = balance.get("weight", 0)
		warehouse_stats[wh]["balance_value"] = balance.get("value", 0)

	# Recent transactions
	recent_transactions = ledger_data[-20:] if len(ledger_data) > 20 else ledger_data
	recent_transactions.reverse()

	return {
		"top_items": top_items,
		"warehouse_summary": list(warehouse_stats.values()),
		"recent_transactions": recent_transactions,
	}


def get_current_balance(item_code, warehouse, to_date=None):
	"""Get current balance for item-warehouse"""
	conditions = []
	params = {}

	if item_code:
		conditions.append("item_code = %(item_code)s")
		params["item_code"] = item_code

	if warehouse:
		conditions.append("warehouse = %(warehouse)s")
		params["warehouse"] = warehouse

	if to_date:
		conditions.append("posting_date <= %(to_date)s")
		params["to_date"] = to_date

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	query = f"""
		SELECT
			COALESCE(SUM(weight_change), 0) as balance_weight,
			COALESCE(SUM(
				CASE 
					WHEN transaction_type = 'IN' THEN value_amount
					WHEN transaction_type = 'OUT' THEN -value_amount
					ELSE 0
				END
			), 0) as balance_value
		FROM
			`tabStock Weight Ledger`
		WHERE
			{where_clause}
	"""

	result = frappe.db.sql(query, params, as_dict=1)
	return (
		{"weight": flt(result[0].balance_weight), "value": flt(result[0].balance_value)}
		if result
		else {"weight": 0, "value": 0}
	)
