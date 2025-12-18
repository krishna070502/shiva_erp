# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate


def execute(filters=None):
	"""
	Supplier Statement Report - Clean statement with correct totals

	Shows:
	- Opening Balance (before from_date)
	- All transactions in period
	- Closing Balance
	- Correct running totals (doesn't double-count)
	"""
	if not filters:
		filters = {}

	if not filters.get("supplier"):
		frappe.throw(_("Please select a Supplier"))

	columns = get_columns()
	data = get_data(filters)

	# Get summary and chart data
	summary = get_summary(filters, data)
	chart = get_chart(filters, data)

	return columns, data, None, chart, summary


def get_columns():
	"""Define report columns"""
	return [
		{"fieldname": "posting_date", "label": _("Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "voucher_type", "label": _("Voucher Type"), "fieldtype": "Data", "width": 140},
		{
			"fieldname": "voucher_no",
			"label": _("Voucher No"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 160,
		},
		{
			"fieldname": "item_code",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 150},
		{"fieldname": "qty", "label": _("Qty"), "fieldtype": "Float", "width": 80},
		{
			"fieldname": "weight_kg",
			"label": _("Weight (Kg)"),
			"fieldtype": "Float",
			"width": 100,
			"precision": 2,
		},
		{"fieldname": "rate", "label": _("Rate"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency", "width": 110},
		{"fieldname": "debit", "label": _("Debit"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "credit", "label": _("Credit"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "balance", "label": _("Balance"), "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	"""Get supplier statement data with correct balances"""
	supplier = filters.get("supplier")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	company = filters.get("company") or frappe.defaults.get_user_default("Company")

	# Get opening balance (before from_date)
	opening_balance = get_opening_balance(supplier, from_date, company)

	# Get transactions in period
	transactions = get_transactions(supplier, from_date, to_date, company)

	# Get item details for each transaction
	item_details = get_item_details(transactions)

	# Build result with running balance
	data = []
	running_balance = opening_balance

	# Add opening row (only if there's an opening balance or if from_date is specified)
	if from_date:
		data.append(
			{
				"posting_date": "",
				"voucher_type": "",
				"voucher_no": "",
				"item_code": "",
				"item_name": "<b>Opening Balance</b>",
				"qty": "",
				"weight_kg": "",
				"rate": "",
				"amount": "",
				"debit": "",
				"credit": "",
				"balance": running_balance,
				"is_opening": 1,
			}
		)

	# Add transactions with running balance
	total_debit = 0
	total_credit = 0

	for txn in transactions:
		debit = flt(txn.debit)
		credit = flt(txn.credit)

		# Update running balance (credit increases liability, debit decreases)
		running_balance += credit - debit

		total_debit += debit
		total_credit += credit

		# Get items for this voucher
		voucher_items = item_details.get(txn.voucher_no, [])

		if voucher_items:
			# Add header row for voucher
			data.append(
				{
					"posting_date": txn.posting_date,
					"voucher_type": txn.voucher_type,
					"voucher_no": txn.voucher_no,
					"item_code": "",
					"item_name": "",
					"qty": "",
					"rate": "",
					"amount": "",
					"debit": debit,
					"credit": credit,
					"balance": running_balance,
					"indent": 0,
				}
			)

			# Add item rows (indented)
			for item in voucher_items:
				data.append(
					{
						"posting_date": "",
						"voucher_type": "",
						"voucher_no": "",
						"item_code": item.item_code,
						"item_name": item.item_name,
						"qty": item.qty,
						"weight_kg": item.get("weight_kg", ""),
						"rate": item.rate,
						"amount": item.amount,
						"debit": "",
						"credit": "",
						"balance": "",
						"indent": 1,
					}
				)
		else:
			# No items (e.g., Payment Entry) - show single row
			data.append(
				{
					"posting_date": txn.posting_date,
					"voucher_type": txn.voucher_type,
					"voucher_no": txn.voucher_no,
					"item_code": "",
					"item_name": "",
					"qty": "",
					"rate": "",
					"amount": "",
					"debit": debit,
					"credit": credit,
					"balance": running_balance,
					"indent": 0,
				}
			)

	# Add closing balance row
	data.append(
		{
			"posting_date": "",
			"voucher_type": "",
			"voucher_no": "",
			"item_code": "",
			"item_name": "<b>Closing Balance</b>",
			"qty": "",
			"weight_kg": "",
			"rate": "",
			"amount": "",
			"debit": "",
			"credit": "",
			"balance": running_balance,
			"is_closing": 1,
		}
	)

	return data


def get_opening_balance(supplier, from_date, company):
	"""Calculate opening balance before from_date"""
	if not from_date:
		return 0.0

	conditions = ["party_type = 'Supplier'", "party = %(supplier)s", "company = %(company)s"]

	conditions.append("posting_date < %(from_date)s")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT 
			COALESCE(SUM(credit - debit), 0) as opening_balance
		FROM 
			`tabGL Entry`
		WHERE 
			{where_clause}
			AND is_cancelled = 0
	"""

	result = frappe.db.sql(
		query, {"supplier": supplier, "company": company, "from_date": from_date}, as_dict=1
	)

	return flt(result[0].opening_balance) if result else 0.0


def get_transactions(supplier, from_date, to_date, company):
	"""Get all GL transactions for supplier in period"""
	conditions = ["party_type = 'Supplier'", "party = %(supplier)s", "company = %(company)s"]

	if from_date:
		conditions.append("posting_date >= %(from_date)s")

	if to_date:
		conditions.append("posting_date <= %(to_date)s")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT 
			posting_date,
			voucher_type,
			voucher_no,
			remarks,
			debit,
			credit,
			against_voucher
		FROM 
			`tabGL Entry`
		WHERE 
			{where_clause}
			AND is_cancelled = 0
		ORDER BY 
			posting_date ASC,
			creation ASC
	"""

	return frappe.db.sql(
		query,
		{"supplier": supplier, "company": company, "from_date": from_date, "to_date": to_date},
		as_dict=1,
	)


def get_item_details(transactions):
	"""Get item details for Purchase Receipt, Purchase Invoice"""
	item_details = {}

	for txn in transactions:
		voucher_type = txn.voucher_type
		voucher_no = txn.voucher_no

		items = []

		if voucher_type == "Purchase Invoice":
			items = frappe.db.sql(
				"""
				SELECT 
					pii.item_code,
					pii.item_name,
					pii.qty,
					COALESCE(pri.custom_total_weight_kg, 0) as weight_kg,
					pii.rate,
					pii.amount
				FROM `tabPurchase Invoice Item` pii
				LEFT JOIN `tabPurchase Receipt Item` pri ON pri.name = pii.pr_detail
				WHERE pii.parent = %(voucher_no)s
				ORDER BY pii.idx
			""",
				{"voucher_no": voucher_no},
				as_dict=1,
			)

		elif voucher_type == "Purchase Receipt":
			try:
				items = frappe.db.sql(
					"""
					SELECT 
						item_code,
						item_name,
						qty,
						COALESCE(custom_total_weight_kg, 0) as weight_kg,
						rate,
						amount
					FROM `tabPurchase Receipt Item`
					WHERE parent = %(voucher_no)s
					ORDER BY idx
				""",
					{"voucher_no": voucher_no},
					as_dict=1,
				)
			except Exception:
				items = frappe.db.sql(
					"""
					SELECT 
						item_code,
						item_name,
						qty,
						0 as weight_kg,
						rate,
						amount
					FROM `tabPurchase Receipt Item`
					WHERE parent = %(voucher_no)s
					ORDER BY idx
				""",
					{"voucher_no": voucher_no},
					as_dict=1,
				)

		elif voucher_type == "Purchase Order":
			try:
				items = frappe.db.sql(
					"""
					SELECT 
						item_code,
						item_name,
						qty,
						COALESCE(custom_total_weight_kg, 0) as weight_kg,
						rate,
						amount
					FROM `tabPurchase Order Item`
					WHERE parent = %(voucher_no)s
					ORDER BY idx
				""",
					{"voucher_no": voucher_no},
					as_dict=1,
				)
			except Exception:
				items = frappe.db.sql(
					"""
					SELECT 
						item_code,
						item_name,
						qty,
						0 as weight_kg,
						rate,
						amount
					FROM `tabPurchase Order Item`
					WHERE parent = %(voucher_no)s
					ORDER BY idx
				""",
					{"voucher_no": voucher_no},
					as_dict=1,
				)

		if items:
			item_details[voucher_no] = items

	return item_details


def get_summary(filters, data):
	"""Generate summary cards showing key metrics"""
	if not data:
		return []

	opening_balance = 0
	closing_balance = 0
	total_debit = 0
	total_credit = 0
	total_qty = 0
	total_weight = 0
	total_amount = 0

	for row in data:
		if row.get("is_opening"):
			opening_balance = flt(row.get("balance", 0))
		elif row.get("is_closing"):
			closing_balance = flt(row.get("balance", 0))
		else:
			total_debit += flt(row.get("debit", 0))
			total_credit += flt(row.get("credit", 0))
			total_qty += flt(row.get("qty", 0))
			total_weight += flt(row.get("weight_kg", 0))
			total_amount += flt(row.get("amount", 0))

	return [
		{
			"value": closing_balance,
			"label": _("Outstanding Balance"),
			"datatype": "Currency",
			"indicator": "Red" if closing_balance > 0 else "Green",
		},
		{
			"value": total_credit,
			"label": _("Total Purchases"),
			"datatype": "Currency",
			"indicator": "Blue",
		},
		{
			"value": total_debit,
			"label": _("Total Payments"),
			"datatype": "Currency",
			"indicator": "Green",
		},
		{
			"value": total_qty,
			"label": _("Total Quantity (Nos)"),
			"datatype": "Float",
			"indicator": "Gray",
		},
		{
			"value": total_weight,
			"label": _("Total Weight (Kg)"),
			"datatype": "Float",
			"indicator": "Orange",
		},
		{
			"value": total_amount,
			"label": _("Total Value"),
			"datatype": "Currency",
			"indicator": "Purple",
		},
	]


def get_chart(filters, data):
	"""Generate chart showing balance trend over time"""
	if not data:
		return None

	# Extract date-wise balance data
	dates = []
	balances = []

	for row in data:
		if row.get("posting_date") and not row.get("is_opening") and not row.get("is_closing"):
			# Only include rows with actual dates and balances
			if row.get("balance") is not None and row.get("indent") == 0:
				dates.append(str(row.get("posting_date")))
				balances.append(flt(row.get("balance", 0)))

	if not dates:
		return None

	return {
		"data": {
			"labels": dates,
			"datasets": [
				{
					"name": _("Outstanding Balance"),
					"values": balances,
				}
			],
		},
		"type": "line",
		"colors": ["#fc4f51"],
		"axisOptions": {"xIsSeries": 1},
		"lineOptions": {"regionFill": 1, "hideDots": 0},
	}
