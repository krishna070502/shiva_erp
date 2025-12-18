# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, today


class TestStockWeightLedger(FrappeTestCase):
	"""Test cases for Stock Weight Ledger - Dual UOM tracking"""

	def setUp(self):
		"""Create test data"""
		# Create test item if not exists
		if not frappe.db.exists("Item", "Test Broiler"):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": "Test Broiler",
					"item_name": "Test Broiler Chicken",
					"item_group": "Products",
					"stock_uom": "Nos",
				}
			).insert(ignore_if_duplicate=True)

		# Create test warehouse if not exists
		if not frappe.db.exists("Warehouse", "Test Warehouse - TC"):
			frappe.get_doc(
				{
					"doctype": "Warehouse",
					"warehouse_name": "Test Warehouse",
					"company": "Test Company",
				}
			).insert(ignore_if_duplicate=True)

	def test_dual_uom_calculation(self):
		"""Test that average weight per bird is calculated correctly"""
		ledger = frappe.get_doc(
			{
				"doctype": "Stock Weight Ledger",
				"transaction_type": "IN",
				"posting_date": today(),
				"voucher_type": "Purchase Receipt",
				"voucher_no": "PR-TEST-001",
				"item_code": "Test Broiler",
				"warehouse": "Test Warehouse - TC",
				"stock_qty": 100,
				"weight_kg": 150.5,
			}
		)

		ledger.insert()

		# Check average weight calculation
		expected_avg = 150.5 / 100
		self.assertEqual(flt(ledger.avg_weight_per_bird, 3), flt(expected_avg, 3))

		# Check weight_change and qty_change for IN transaction
		self.assertEqual(ledger.weight_change, 150.5)
		self.assertEqual(ledger.qty_change, 100)

		# Cleanup
		ledger.delete()

	def test_transaction_type_out(self):
		"""Test OUT transaction creates negative changes"""
		ledger = frappe.get_doc(
			{
				"doctype": "Stock Weight Ledger",
				"transaction_type": "OUT",
				"posting_date": today(),
				"voucher_type": "Delivery Note",
				"voucher_no": "DN-TEST-001",
				"item_code": "Test Broiler",
				"warehouse": "Test Warehouse - TC",
				"stock_qty": 50,
				"weight_kg": 75.25,
			}
		)

		ledger.insert()

		# Check negative changes for OUT transaction
		self.assertEqual(ledger.weight_change, -75.25)
		self.assertEqual(ledger.qty_change, -50)

		# Cleanup
		ledger.delete()

	def tearDown(self):
		"""Clean up test data"""
		frappe.db.delete("Stock Weight Ledger", {"item_code": "Test Broiler"})
