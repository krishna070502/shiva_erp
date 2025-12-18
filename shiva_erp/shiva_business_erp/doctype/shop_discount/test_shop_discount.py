# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today


class TestShopDiscount(FrappeTestCase):
	"""Test cases for Shop Discount"""

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

		# Create test customer if not exists
		if not frappe.db.exists("Customer", "Test Shop A"):
			frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": "Test Shop A",
					"customer_type": "Company",
					"territory": "All Territories",
				}
			).insert(ignore_if_duplicate=True)

	def test_discount_validation(self):
		"""Test that discount cannot be negative"""
		discount = frappe.get_doc(
			{
				"doctype": "Shop Discount",
				"shop": "Test Shop A",
				"item_code": "Test Broiler",
				"discount_per_kg": -5.00,  # Invalid
				"is_active": 1,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			discount.insert()

	def test_duplicate_prevention(self):
		"""Test that duplicate shop+item is rejected"""
		# Create first discount
		discount1 = frappe.get_doc(
			{
				"doctype": "Shop Discount",
				"shop": "Test Shop A",
				"item_code": "Test Broiler",
				"discount_per_kg": 5.00,
				"is_active": 1,
			}
		).insert()

		# Try to create duplicate
		discount2 = frappe.get_doc(
			{
				"doctype": "Shop Discount",
				"shop": "Test Shop A",  # Same
				"item_code": "Test Broiler",  # Same
				"discount_per_kg": 7.00,
				"is_active": 1,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			discount2.insert()

		# Cleanup
		discount1.delete()

	def test_validity_dates(self):
		"""Test validity date validation"""
		discount = frappe.get_doc(
			{
				"doctype": "Shop Discount",
				"shop": "Test Shop A",
				"item_code": "Test Broiler",
				"discount_per_kg": 10.00,
				"valid_from": today(),
				"valid_till": add_days(today(), -10),  # Invalid
				"is_active": 1,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			discount.insert()

	def tearDown(self):
		"""Clean up test data"""
		frappe.db.delete("Shop Discount", {"shop": "Test Shop A"})
