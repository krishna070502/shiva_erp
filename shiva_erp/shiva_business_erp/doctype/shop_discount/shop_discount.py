# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class ShopDiscount(Document):
	def validate(self):
		"""Validate shop discount"""
		self.validate_discount_value()
		self.validate_duplicate()
		self.check_validity_overlap()
		self.validate_validity_dates()

	def validate_discount_value(self):
		"""Validate discount is non-negative"""
		if self.discount_per_kg < 0:
			frappe.throw(_("Discount per Kg cannot be negative"))

	def validate_duplicate(self):
		"""Prevent duplicate shop+item combinations for active records"""
		if not self.is_active:
			return

		filters = {
			"shop": self.shop,
			"item_code": self.item_code,
			"is_active": 1,
			"name": ("!=", self.name),
		}

		existing = frappe.db.exists("Shop Discount", filters)
		if existing:
			frappe.throw(
				_("Active discount already exists for Shop {0} and Item {1}: {2}").format(
					self.shop, self.item_code, existing
				)
			)

	def check_validity_overlap(self):
		"""Check for overlapping validity periods"""
		if not self.is_active or not self.valid_from or not self.valid_till:
			return

		overlapping = frappe.db.sql(
			"""
			SELECT name
			FROM `tabShop Discount`
			WHERE shop = %s
				AND item_code = %s
				AND is_active = 1
				AND name != %s
				AND (
					(valid_from <= %s AND valid_till >= %s)
					OR (valid_from <= %s AND valid_till >= %s)
					OR (valid_from >= %s AND valid_till <= %s)
				)
		""",
			(
				self.shop,
				self.item_code,
				self.name,
				self.valid_from,
				self.valid_from,
				self.valid_till,
				self.valid_till,
				self.valid_from,
				self.valid_till,
			),
		)

		if overlapping:
			frappe.throw(_("Validity period overlaps with existing discount: {0}").format(overlapping[0][0]))

	def validate_validity_dates(self):
		"""Validate validity date range"""
		if self.valid_from and self.valid_till:
			if getdate(self.valid_till) < getdate(self.valid_from):
				frappe.throw(_("Valid Till cannot be before Valid From"))


@frappe.whitelist()
def get_shop_discount(shop, item_code, posting_date=None):
	"""
	Get discount for shop and item on a specific date

	Args:
		shop: Customer (shop) name
		item_code: Item code
		posting_date: Date for which to get discount (default: today)

	Returns:
		float: Discount per kg in INR (0 if no discount found)
	"""
	if not posting_date:
		posting_date = frappe.utils.today()

	# Get shop discount with validity date filtering
	discount = frappe.db.sql(
		"""
		SELECT discount_per_kg
		FROM `tabShop Discount`
		WHERE shop = %s
			AND item_code = %s
			AND is_active = 1
			AND (valid_from IS NULL OR valid_from <= %s)
			AND (valid_till IS NULL OR valid_till >= %s)
		ORDER BY valid_from DESC
		LIMIT 1
	""",
		(shop, item_code, posting_date, posting_date),
		as_dict=True,
	)

	if discount:
		return discount[0].discount_per_kg

	return 0.0


@frappe.whitelist()
def bulk_update_discount(shop=None, item_code=None, new_discount=0.0):
	"""
	Bulk update discounts for matching records

	Args:
		shop: Filter by shop (optional)
		item_code: Filter by item (optional)
		new_discount: New discount value in INR

	Returns:
		int: Number of records updated
	"""
	if new_discount < 0:
		frappe.throw(_("Discount cannot be negative"))

	filters = {"is_active": 1}
	if shop:
		filters["shop"] = shop
	if item_code:
		filters["item_code"] = item_code

	discounts = frappe.get_all("Shop Discount", filters=filters, pluck="name")

	for name in discounts:
		doc = frappe.get_doc("Shop Discount", name)
		doc.discount_per_kg = new_discount
		doc.save(ignore_permissions=True)

	frappe.db.commit()
	return len(discounts)
