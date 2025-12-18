# Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class ItemPriceType(Document):
	"""
	Item Price Type - Territory specific base pricing.

	Stores base price per kg for each Item + Territory combination.
	This allows updating prices once per territory instead of per shop.

	Example:
		Item: "Broiler Chicken"
		Territory: "North Region"
		Base Price: ₹150/kg
		→ All customers in "North Region" use this base price
	"""

	def validate(self):
		"""Validate before saving"""
		self.validate_base_price()
		self.validate_duplicate()
		self.validate_validity_dates()

	def validate_base_price(self):
		"""Ensure base price is positive"""
		if flt(self.base_price_per_kg) <= 0:
			frappe.throw(_("Base Price per Kg must be greater than 0"))

	def validate_duplicate(self):
		"""Prevent duplicate active entries for same item+territory"""
		if not self.is_active:
			return

		filters = {
			"item_code": self.item_code,
			"territory": self.territory,
			"is_active": 1,
			"name": ["!=", self.name],
		}

		# Check for overlapping validity periods
		existing = frappe.db.get_all(
			"Item Price Type",
			filters=filters,
			fields=["name", "valid_from", "valid_till"],
		)

		if existing:
			for record in existing:
				if self.check_validity_overlap(record):
					frappe.throw(
						_("Active price record already exists for {0} ({1}): {2}").format(
							self.item_code, self.territory, record.name
						)
					)

	def check_validity_overlap(self, existing_record):
		"""Check if validity periods overlap"""
		# If either record has no validity dates, consider it overlapping
		if not self.valid_from or not self.valid_till:
			return True

		if not existing_record.get("valid_from") or not existing_record.get("valid_till"):
			return True

		self_from = getdate(self.valid_from)
		self_till = getdate(self.valid_till)
		existing_from = getdate(existing_record.get("valid_from"))
		existing_till = getdate(existing_record.get("valid_till"))

		# Check for overlap
		return not (self_till < existing_from or self_from > existing_till)

	def validate_validity_dates(self):
		"""Ensure valid_till is after valid_from"""
		if self.valid_from and self.valid_till:
			if getdate(self.valid_till) < getdate(self.valid_from):
				frappe.throw(_("Valid Till date cannot be before Valid From date"))


@frappe.whitelist()
def get_base_price(item_code, territory, posting_date=None):
	"""
	Get base price for an item and territory.

	Args:
		item_code: Item code
		territory: Territory from customer master
		posting_date: Date to check validity (default: today)

	Returns:
		dict with base_price_per_kg, currency, name
	"""
	if not posting_date:
		posting_date = frappe.utils.today()

	filters = {
		"item_code": item_code,
		"territory": territory,
		"is_active": 1,
	}

	# Build validity condition
	validity_condition = """
		AND (
			(valid_from IS NULL OR valid_from <= %(posting_date)s)
			AND (valid_till IS NULL OR valid_till >= %(posting_date)s)
		)
	"""

	price_records = frappe.db.sql(
		f"""
		SELECT
			base_price_per_kg,
			currency,
			name
		FROM `tabItem Price Type`
		WHERE item_code = %(item_code)s
			AND territory = %(territory)s
			AND is_active = 1
			{validity_condition}
		ORDER BY modified DESC
		LIMIT 1
	""",
		{**filters, "posting_date": posting_date},
		as_dict=True,
	)

	if price_records:
		return price_records[0]

	return None


@frappe.whitelist()
def bulk_update_base_price(item_code=None, territory=None, new_base_price=None):
	"""
	Bulk update base price for items matching filters.

	Args:
		item_code: Filter by item (optional)
		territory: Filter by territory (optional)
		new_base_price: New base price value (required)

	Returns:
		Number of records updated
	"""
	if not new_base_price:
		frappe.throw(_("Please provide new base price"))

	filters = {"is_active": 1}

	if item_code:
		filters["item_code"] = item_code

	if territory:
		filters["territory"] = territory

	records = frappe.db.get_all("Item Price Type", filters=filters, pluck="name")

	updated_count = 0
	for record_name in records:
		doc = frappe.get_doc("Item Price Type", record_name)
		doc.base_price_per_kg = flt(new_base_price)
		doc.save(ignore_permissions=True)
		updated_count += 1

	return updated_count
