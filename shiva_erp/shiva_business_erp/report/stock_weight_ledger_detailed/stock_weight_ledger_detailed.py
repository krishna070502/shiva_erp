# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	"""
	Stock Weight Ledger Detailed Report

	Shows all IN/OUT transactions with dual UOM tracking.
	Displays transaction-wise stock movements with running balance.

	Filters:
		- From Date / To Date: Period selection
		- Item: Specific item or all
		- Warehouse: Specific warehouse or all
		- Transaction Type: IN/OUT/Both
		- Batch: Specific batch or all
	"""
	columns = get_columns()
	data = get_data(filters)

	# Generate chart data for visualization
	chart = get_chart_data(data, filters)

	# Generate summary cards
	summary = get_summary(data, filters)

	return columns, data, None, chart, summary


def get_columns():
	"""Define report columns with detailed transaction info"""
	return [
		{
			"fieldname": "posting_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"fieldname": "transaction_type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 60,
		},
		{
			"fieldname": "voucher_type",
			"label": _("Voucher Type"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "voucher_no",
			"label": _("Voucher No"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 150,
		},
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 130,
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
			"width": 130,
		},
		{
			"fieldname": "batch_no",
			"label": _("Batch"),
			"fieldtype": "Link",
			"options": "Batch",
			"width": 100,
		},
		{
			"fieldname": "qty_change",
			"label": _("Qty Change (Nos)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 2,
		},
		{
			"fieldname": "weight_change",
			"label": _("Weight Change (Kg)"),
			"fieldtype": "Float",
			"width": 140,
			"precision": 3,
		},
		{
			"fieldname": "stock_qty",
			"label": _("Actual Qty (Nos)"),
			"fieldtype": "Float",
			"width": 120,
			"precision": 2,
		},
		{
			"fieldname": "weight_kg",
			"label": _("Actual Weight (Kg)"),
			"fieldtype": "Float",
			"width": 140,
			"precision": 3,
		},
		{
			"fieldname": "avg_weight_per_bird",
			"label": _("Avg Wt/Bird (Kg)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 3,
		},
		{
			"fieldname": "rate_per_kg",
			"label": _("Rate/Kg (₹)"),
			"fieldtype": "Currency",
			"width": 110,
			"precision": 2,
		},
		{
			"fieldname": "value_amount",
			"label": _("Value (₹)"),
			"fieldtype": "Currency",
			"width": 120,
			"precision": 2,
		},
		{
			"fieldname": "balance_qty",
			"label": _("Balance Qty (Nos)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 2,
		},
		{
			"fieldname": "balance_weight",
			"label": _("Balance Wt (Kg)"),
			"fieldtype": "Float",
			"width": 130,
			"precision": 3,
		},
		{
			"fieldname": "balance_value",
			"label": _("Balance Value (₹)"),
			"fieldtype": "Currency",
			"width": 140,
			"precision": 2,
		},
		{
			"fieldname": "remarks",
			"label": _("Remarks"),
			"fieldtype": "Text",
			"width": 200,
		},
	]


def get_data(filters):
	"""
	Get detailed stock ledger data with running balance

	Args:
		filters: dict with from_date, to_date, item_code, warehouse, transaction_type, batch_no

	Returns:
		list of dicts with ledger entries and running balance
	"""
	conditions = ["1=1"]
	params = {}

	# Date range filter (mandatory)
	if filters.get("from_date"):
		conditions.append("swl.posting_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("swl.posting_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	# Item filter
	if filters.get("item_code"):
		conditions.append("swl.item_code = %(item_code)s")
		params["item_code"] = filters["item_code"]

	# Warehouse filter
	if filters.get("warehouse"):
		conditions.append("swl.warehouse = %(warehouse)s")
		params["warehouse"] = filters["warehouse"]

	# Transaction type filter
	if filters.get("transaction_type"):
		conditions.append("swl.transaction_type = %(transaction_type)s")
		params["transaction_type"] = filters["transaction_type"]

	# Batch filter
	if filters.get("batch_no"):
		conditions.append("swl.batch_no = %(batch_no)s")
		params["batch_no"] = filters["batch_no"]

	where_clause = " AND ".join(conditions)

	# Query ledger entries with item details
	query = f"""
		SELECT
			swl.name,
			swl.posting_date,
			swl.transaction_type,
			swl.voucher_type,
			swl.voucher_no,
			swl.item_code,
			item.item_name,
			swl.warehouse,
			swl.batch_no,
			swl.stock_qty,
			swl.weight_kg,
			swl.qty_change,
			swl.weight_change,
			swl.avg_weight_per_bird,
			swl.rate_per_kg,
			swl.value_amount,
			swl.remarks
		FROM
			`tabStock Weight Ledger` swl
		LEFT JOIN
			`tabItem` item ON item.name = swl.item_code
		WHERE
			{where_clause}
		ORDER BY
			swl.posting_date ASC,
			swl.creation ASC
	"""

	ledger_entries = frappe.db.sql(query, params, as_dict=1)

	# Calculate running balance per item-warehouse-batch combination
	data = calculate_running_balance(ledger_entries)

	return data


def calculate_running_balance(ledger_entries):
	"""
	Calculate running balance for each transaction

	Args:
		ledger_entries: List of ledger entries sorted by date

	Returns:
		List with running balance columns added
	"""
	# Track balance per item-warehouse-batch
	balance_tracker = {}

	result = []

	for entry in ledger_entries:
		# Create unique key for tracking
		key = f"{entry.item_code}|{entry.warehouse}|{entry.batch_no or ''}"

		# Initialize balance if not exists
		if key not in balance_tracker:
			# Get opening balance (transactions before from_date)
			balance_tracker[key] = get_opening_balance(
				entry.item_code, entry.warehouse, entry.batch_no, entry.posting_date
			)

		# Update running balance
		balance_tracker[key]["qty"] += flt(entry.qty_change)
		balance_tracker[key]["weight"] += flt(entry.weight_change)

		# Update value balance (IN adds, OUT subtracts)
		value_change = flt(entry.value_amount) if entry.transaction_type == "IN" else -flt(entry.value_amount)
		balance_tracker[key]["value"] += value_change

		# Add balance to result row
		entry["balance_qty"] = balance_tracker[key]["qty"]
		entry["balance_weight"] = balance_tracker[key]["weight"]
		entry["balance_value"] = balance_tracker[key]["value"]

		result.append(entry)

	return result


def get_opening_balance(item_code, warehouse, batch_no, from_date):
	"""
	Get opening balance before the from_date

	Args:
		item_code: Item code
		warehouse: Warehouse
		batch_no: Batch number (optional)
		from_date: Starting date for the report

	Returns:
		dict with qty and weight opening balance
	"""
	conditions = [
		"item_code = %(item_code)s",
		"warehouse = %(warehouse)s",
		"posting_date < %(from_date)s",
	]

	params = {
		"item_code": item_code,
		"warehouse": warehouse,
		"from_date": from_date,
	}

	if batch_no:
		conditions.append("batch_no = %(batch_no)s")
		params["batch_no"] = batch_no

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			COALESCE(SUM(qty_change), 0) as opening_qty,
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

	if result:
		return {
			"qty": flt(result[0].opening_qty),
			"weight": flt(result[0].opening_weight),
			"value": flt(result[0].opening_value),
		}
	else:
		return {"qty": 0.0, "weight": 0.0, "value": 0.0}


def get_chart_data(data, filters):
	"""
	Generate chart data for visual representation

	Args:
		data: Report data
		filters: Report filters

	Returns:
		Chart configuration dict
	"""
	if not data:
		return None

	# Prepare data for charts
	dates = []
	in_qty = []
	out_qty = []
	in_weight = []
	out_weight = []
	balance_qty = []
	balance_weight = []

	# Group by date and aggregate
	date_wise_data = {}

	for row in data:
		date = str(row.get("posting_date"))

		if date not in date_wise_data:
			date_wise_data[date] = {
				"in_qty": 0,
				"out_qty": 0,
				"in_weight": 0,
				"out_weight": 0,
				"balance_qty": row.get("balance_qty", 0),
				"balance_weight": row.get("balance_weight", 0),
			}

		# Aggregate IN/OUT for the date
		if row.get("transaction_type") == "IN":
			date_wise_data[date]["in_qty"] += abs(flt(row.get("qty_change", 0)))
			date_wise_data[date]["in_weight"] += abs(flt(row.get("weight_change", 0)))
		else:
			date_wise_data[date]["out_qty"] += abs(flt(row.get("qty_change", 0)))
			date_wise_data[date]["out_weight"] += abs(flt(row.get("weight_change", 0)))

		# Use last balance for the date
		date_wise_data[date]["balance_qty"] = row.get("balance_qty", 0)
		date_wise_data[date]["balance_weight"] = row.get("balance_weight", 0)

	# Sort by date
	sorted_dates = sorted(date_wise_data.keys())

	for date in sorted_dates:
		dates.append(date)
		in_qty.append(date_wise_data[date]["in_qty"])
		out_qty.append(date_wise_data[date]["out_qty"])
		in_weight.append(date_wise_data[date]["in_weight"])
		out_weight.append(date_wise_data[date]["out_weight"])
		balance_qty.append(date_wise_data[date]["balance_qty"])
		balance_weight.append(date_wise_data[date]["balance_weight"])

	# Create chart configuration
	chart = {
		"data": {
			"labels": dates,
			"datasets": [
				{
					"name": "IN Qty (Nos)",
					"values": in_qty,
					"chartType": "bar",
				},
				{
					"name": "OUT Qty (Nos)",
					"values": out_qty,
					"chartType": "bar",
				},
				{
					"name": "Balance Qty (Nos)",
					"values": balance_qty,
					"chartType": "line",
				},
			],
		},
		"type": "axis-mixed",
		"colors": ["#28a745", "#dc3545", "#007bff"],
		"axisOptions": {
			"xIsSeries": 1,
			"xAxisMode": "tick",
		},
		"barOptions": {
			"stacked": 0,
			"spaceRatio": 0.5,
		},
		"lineOptions": {
			"hideDots": 0,
			"regionFill": 1,
		},
		"height": 300,
	}

	return chart


def get_summary(data, filters):
	"""
	Generate summary cards with key metrics

	Args:
		data: Report data
		filters: Report filters

	Returns:
		List of summary card dicts
	"""
	if not data:
		return []

	# Initialize counters
	total_in_qty = 0
	total_in_weight = 0
	total_out_qty = 0
	total_out_weight = 0
	total_transactions = len(data)
	in_transactions = 0
	out_transactions = 0
	unique_items = set()
	unique_warehouses = set()
	unique_batches = set()

	# Calculate metrics
	for row in data:
		transaction_type = row.get("transaction_type")
		qty_change = flt(row.get("qty_change", 0))
		weight_change = flt(row.get("weight_change", 0))

		if transaction_type == "IN":
			total_in_qty += abs(qty_change)
			total_in_weight += abs(weight_change)
			in_transactions += 1
		else:
			total_out_qty += abs(qty_change)
			total_out_weight += abs(weight_change)
			out_transactions += 1

		# Track unique values
		if row.get("item_code"):
			unique_items.add(row.get("item_code"))
		if row.get("warehouse"):
			unique_warehouses.add(row.get("warehouse"))
		if row.get("batch_no"):
			unique_batches.add(row.get("batch_no"))

	# Get closing balance (last row values)
	closing_qty = data[-1].get("balance_qty", 0) if data else 0
	closing_weight = data[-1].get("balance_weight", 0) if data else 0

	# Calculate opening balance (first row balance - first row change)
	if data:
		opening_qty = flt(data[0].get("balance_qty", 0)) - flt(data[0].get("qty_change", 0))
		opening_weight = flt(data[0].get("balance_weight", 0)) - flt(data[0].get("weight_change", 0))
	else:
		opening_qty = 0
		opening_weight = 0

	# Calculate net movement
	net_qty = total_in_qty - total_out_qty
	net_weight = total_in_weight - total_out_weight

	# Calculate average weight per bird for closing stock
	avg_closing_weight = closing_weight / closing_qty if closing_qty > 0 else 0

	# Build summary cards
	summary = [
		{
			"value": total_transactions,
			"indicator": "Blue",
			"label": _("Total Transactions"),
			"datatype": "Int",
		},
		{
			"value": in_transactions,
			"indicator": "Green",
			"label": _("IN Transactions"),
			"datatype": "Int",
		},
		{
			"value": out_transactions,
			"indicator": "Red",
			"label": _("OUT Transactions"),
			"datatype": "Int",
		},
		{
			"value": opening_qty,
			"indicator": "Gray",
			"label": _("Opening Qty (Nos)"),
			"datatype": "Float",
		},
		{
			"value": opening_weight,
			"indicator": "Gray",
			"label": _("Opening Weight (Kg)"),
			"datatype": "Float",
		},
		{
			"value": total_in_qty,
			"indicator": "Green",
			"label": _("Total IN Qty (Nos)"),
			"datatype": "Float",
		},
		{
			"value": total_in_weight,
			"indicator": "Green",
			"label": _("Total IN Weight (Kg)"),
			"datatype": "Float",
		},
		{
			"value": total_out_qty,
			"indicator": "Red",
			"label": _("Total OUT Qty (Nos)"),
			"datatype": "Float",
		},
		{
			"value": total_out_weight,
			"indicator": "Red",
			"label": _("Total OUT Weight (Kg)"),
			"datatype": "Float",
		},
		{
			"value": net_qty,
			"indicator": "Orange" if net_qty < 0 else "Green",
			"label": _("Net Movement Qty (Nos)"),
			"datatype": "Float",
		},
		{
			"value": net_weight,
			"indicator": "Orange" if net_weight < 0 else "Green",
			"label": _("Net Movement Weight (Kg)"),
			"datatype": "Float",
		},
		{
			"value": closing_qty,
			"indicator": "Purple",
			"label": _("Closing Qty (Nos)"),
			"datatype": "Float",
		},
		{
			"value": closing_weight,
			"indicator": "Purple",
			"label": _("Closing Weight (Kg)"),
			"datatype": "Float",
		},
		{
			"value": avg_closing_weight,
			"indicator": "Purple",
			"label": _("Avg Weight/Bird (Kg)"),
			"datatype": "Float",
		},
		{
			"value": len(unique_items),
			"indicator": "Blue",
			"label": _("Unique Items"),
			"datatype": "Int",
		},
		{
			"value": len(unique_warehouses),
			"indicator": "Blue",
			"label": _("Unique Warehouses"),
			"datatype": "Int",
		},
	]

	# Add batch count if batches exist
	if unique_batches:
		summary.append(
			{
				"value": len(unique_batches),
				"indicator": "Blue",
				"label": _("Unique Batches"),
				"datatype": "Int",
			}
		)

	return summary
