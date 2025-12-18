# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestSalesIntegration(FrappeTestCase):
	"""Test cases for Sales Integration with new pricing architecture"""

	def setUp(self):
		"""Create test data"""
		# Create test customer
		if not frappe.db.exists("Customer", "Test Shop A"):
			frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": "Test Shop A",
					"customer_type": "Company",
					"territory": "All Territories",
				}
			).insert(ignore_if_duplicate=True)

		# Create test item
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

		# Create test warehouse
		if not frappe.db.exists("Warehouse", "Test Warehouse"):
			frappe.get_doc(
				{
					"doctype": "Warehouse",
					"warehouse_name": "Test Warehouse",
					"warehouse_type": "Transit",
				}
			).insert(ignore_if_duplicate=True)

		# Create base price (Item Price Type)
		if not frappe.db.exists(
			"Item Price Type", {"item_code": "Test Broiler", "price_type": "Wholesale", "is_active": 1}
		):
			frappe.get_doc(
				{
					"doctype": "Item Price Type",
					"item_code": "Test Broiler",
					"price_type": "Wholesale",
					"base_price_per_kg": 150.00,
					"is_active": 1,
				}
			).insert(ignore_permissions=True)

		# Create shop discount
		if not frappe.db.exists(
			"Shop Discount", {"shop": "Test Shop A", "item_code": "Test Broiler", "is_active": 1}
		):
			frappe.get_doc(
				{
					"doctype": "Shop Discount",
					"shop": "Test Shop A",
					"item_code": "Test Broiler",
					"discount_per_kg": 10.00,
					"is_active": 1,
				}
			).insert(ignore_permissions=True)

	def test_pricing_calculation(self):
		"""Test pricing calculation with base price and discount"""
		from shiva_erp.sales_integration import get_stock_and_price_details

		result = get_stock_and_price_details(
			customer="Test Shop A",
			item_code="Test Broiler",
			warehouse="Test Warehouse",
			qty=100,
			price_type="Wholesale",
		)

		price_data = result.get("price_data", {})

		self.assertEqual(price_data.get("base_price_per_kg"), 150.00)
		self.assertEqual(price_data.get("discount_per_kg"), 10.00)
		self.assertEqual(price_data.get("effective_price_per_kg"), 140.00)

	def test_pricing_with_no_discount(self):
		"""Test pricing when no shop discount exists"""
		# Create a customer with no discount
		if not frappe.db.exists("Customer", "Test Shop B"):
			frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": "Test Shop B",
					"customer_type": "Company",
					"territory": "All Territories",
				}
			).insert(ignore_if_duplicate=True)

		from shiva_erp.sales_integration import get_stock_and_price_details

		result = get_stock_and_price_details(
			customer="Test Shop B",
			item_code="Test Broiler",
			warehouse="Test Warehouse",
			qty=100,
			price_type="Wholesale",
		)

		price_data = result.get("price_data", {})

		self.assertEqual(price_data.get("base_price_per_kg"), 150.00)
		self.assertEqual(price_data.get("discount_per_kg"), 0.00)
		self.assertEqual(price_data.get("effective_price_per_kg"), 150.00)

	def test_pricing_with_no_base_price(self):
		"""Test pricing when no base price exists"""
		# Create test item without base price
		if not frappe.db.exists("Item", "Test Item No Price"):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": "Test Item No Price",
					"item_name": "Test Item No Price",
					"item_group": "Products",
					"stock_uom": "Nos",
				}
			).insert(ignore_if_duplicate=True)

		from shiva_erp.sales_integration import get_stock_and_price_details

		result = get_stock_and_price_details(
			customer="Test Shop A",
			item_code="Test Item No Price",
			warehouse="Test Warehouse",
			qty=100,
			price_type="Wholesale",
		)

		price_data = result.get("price_data", {})

		# Should return 0 when no base price
		self.assertEqual(price_data.get("effective_price_per_kg"), 0.00)

	def tearDown(self):
		"""Clean up test data"""
		frappe.db.delete("Shop Discount", {"shop": "Test Shop A"})
		frappe.db.delete("Item Price Type", {"item_code": "Test Broiler"})
