# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class StockWeightLedger(Document):
	"""
	Stock Weight Ledger - Dual UOM tracking for poultry business.
	Tracks both quantity (Nos - number of birds) and actual weight (Kg).

	Critical: Each bird has variable weight, so conversion factors cannot be used.
	This ledger maintains actual measured weights per transaction.
	"""

	def validate(self):
		"""Validate ledger entry before saving"""
		self.validate_transaction_type()
		self.validate_stock_and_weight()
		self.calculate_average_weight()
		self.calculate_changes()
		self.calculate_value()
		self.validate_weights_list()

	def validate_transaction_type(self):
		"""Ensure transaction_type is either IN or OUT"""
		if not self.transaction_type:
			frappe.throw(_("Transaction Type is required and must be either IN or OUT"))
		if self.transaction_type not in ["IN", "OUT"]:
			frappe.throw(_("Transaction Type must be either IN or OUT"))

	def validate_stock_and_weight(self):
		"""Validate that stock_qty and weight_kg are positive"""
		if flt(self.stock_qty) <= 0:
			frappe.throw(_("Stock Qty (Nos) must be greater than 0"))

		if flt(self.weight_kg) <= 0:
			frappe.throw(_("Total Weight (Kg) must be greater than 0"))

	def calculate_average_weight(self):
		"""Calculate average weight per bird"""
		if flt(self.stock_qty) > 0:
			self.avg_weight_per_bird = flt(self.weight_kg) / flt(self.stock_qty)
		else:
			self.avg_weight_per_bird = 0

	def calculate_changes(self):
		"""
		Calculate weight_change and qty_change based on transaction_type.
		IN transactions are positive, OUT transactions are negative.
		"""
		factor = 1 if self.transaction_type == "IN" else -1

		self.weight_change = flt(self.weight_kg) * factor
		self.qty_change = flt(self.stock_qty) * factor

	def calculate_value(self):
		"""Calculate value_amount based on rate_per_kg and weight_kg"""
		if flt(self.rate_per_kg) > 0 and flt(self.weight_kg) > 0:
			self.value_amount = flt(self.rate_per_kg) * flt(self.weight_kg)
		else:
			self.value_amount = 0

	def validate_weights_list(self):
		"""Validate individual bird weights JSON if provided"""
		if self.weights_list:
			try:
				weights = (
					json.loads(self.weights_list) if isinstance(self.weights_list, str) else self.weights_list
				)

				if not isinstance(weights, list):
					frappe.throw(_("Individual Bird Weights must be a list/array"))

				# Validate that sum of individual weights matches total weight_kg
				if weights:
					total_individual_weight = sum(flt(w) for w in weights)
					# Allow small tolerance for rounding errors (0.1 kg)
					if abs(total_individual_weight - flt(self.weight_kg)) > 0.1:
						frappe.throw(
							_(
								"Sum of individual bird weights ({0} kg) does not match Total Weight ({1} kg)"
							).format(total_individual_weight, self.weight_kg)
						)

					# Validate count matches stock_qty
					if len(weights) != int(flt(self.stock_qty)):
						frappe.throw(
							_("Number of individual weights ({0}) does not match Stock Qty ({1})").format(
								len(weights), int(flt(self.stock_qty))
							)
						)

			except json.JSONDecodeError:
				frappe.throw(_("Individual Bird Weights must be valid JSON"))


@frappe.whitelist()
def get_stock_balance(item_code, warehouse, batch_no=None):
	"""
	Get current stock balance in dual UOM (Nos + Kg) for an item/warehouse/batch.

	Returns: dict with stock_qty, weight_kg, avg_weight_per_bird
	"""
	filters = {"item_code": item_code, "warehouse": warehouse}

	if batch_no:
		filters["batch_no"] = batch_no

	# Sum all qty_change and weight_change to get current balance
	result = frappe.db.sql(
		"""
		SELECT
			SUM(qty_change) as total_qty,
			SUM(weight_change) as total_weight
		FROM `tabStock Weight Ledger`
		WHERE item_code = %(item_code)s
			AND warehouse = %(warehouse)s
			{batch_condition}
	""".format(batch_condition="AND batch_no = %(batch_no)s" if batch_no else ""),
		filters,
		as_dict=True,
	)

	if result and result[0]:
		total_qty = flt(result[0].total_qty)
		total_weight = flt(result[0].total_weight)
		avg_weight = total_weight / total_qty if total_qty > 0 else 0

		return {
			"stock_qty": total_qty,
			"weight_kg": total_weight,
			"avg_weight_per_bird": avg_weight,
		}

	return {"stock_qty": 0, "weight_kg": 0, "avg_weight_per_bird": 0}


@frappe.whitelist()
def get_item_warehouse_balance_report(item_code=None, warehouse=None):
	"""
	Get stock balance report across all items/warehouses with dual UOM.

	Returns: list of dicts with item_code, warehouse, stock_qty, weight_kg, avg_weight
	"""
	conditions = []
	filters = {}

	if item_code:
		conditions.append("item_code = %(item_code)s")
		filters["item_code"] = item_code

	if warehouse:
		conditions.append("warehouse = %(warehouse)s")
		filters["warehouse"] = warehouse

	where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

	query = f"""
		SELECT
			item_code,
			warehouse,
			batch_no,
			SUM(qty_change) as stock_qty,
			SUM(weight_change) as weight_kg,
			CASE
				WHEN SUM(qty_change) > 0 THEN SUM(weight_change) / SUM(qty_change)
				ELSE 0
			END as avg_weight_per_bird
		FROM `tabStock Weight Ledger`
		{where_clause}
		GROUP BY item_code, warehouse, batch_no
		HAVING stock_qty > 0 OR weight_kg > 0
		ORDER BY item_code, warehouse, batch_no
	"""

	return frappe.db.sql(query, filters, as_dict=True)
