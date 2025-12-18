# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today


class TestItemPriceType(FrappeTestCase):
	"""Test cases for Item Price Type"""

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

	def test_base_price_validation(self):
		"""Test that base price must be positive"""
		price = frappe.get_doc(
			{
				"doctype": "Item Price Type",
				"item_code": "Test Broiler",
				"territory": "All Territories",
				"base_price_per_kg": 0,  # Invalid
				"is_active": 1,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			price.insert()

	def test_duplicate_prevention(self):
		"""Test that duplicate item+territory is rejected"""
		# Create first price
		price1 = frappe.get_doc(
			{
				"doctype": "Item Price Type",
				"item_code": "Test Broiler",
				"territory": "North India",
				"base_price_per_kg": 160.00,
				"is_active": 1,
			}
		).insert()

		# Try to create duplicate
		price2 = frappe.get_doc(
			{
				"doctype": "Item Price Type",
				"item_code": "Test Broiler",
				"territory": "North India",  # Same
				"base_price_per_kg": 170.00,
				"is_active": 1,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			price2.insert()

		# Cleanup
		price1.delete()

	def test_validity_dates(self):
		"""Test validity date validation"""
		price = frappe.get_doc(
			{
				"doctype": "Item Price Type",
				"item_code": "Test Broiler",
				"territory": "South India",
				"base_price_per_kg": 180.00,
				"valid_from": today(),
				"valid_till": add_days(today(), -10),  # Invalid
				"is_active": 1,
			}
		)

		with self.assertRaises(frappe.ValidationError):
			price.insert()

	def tearDown(self):
		"""Clean up test data"""
		frappe.db.delete("Item Price Type", {"item_code": "Test Broiler"})
