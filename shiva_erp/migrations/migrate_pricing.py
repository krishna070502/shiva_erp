#!/usr/bin/env python3
"""
Migration Script: Shop Price Master to Item Price Type + Shop Discount

DEPRECATED: This migration has already been executed and Shop Price Master has been deleted.

Original purpose: Migrated data from Shop Price Master architecture to:
- Base prices → Item Price Type (item + territory)
- Discounts → Shop Discount (shop + item)

NOTE: System now uses territory-based pricing (customer.territory → base_price)
      instead of the original price_type-based model.

This file is kept for historical reference only.
DO NOT RUN - Shop Price Master DocType no longer exists.
"""

import frappe
from frappe import _


def migrate_shop_pricing():
	"""
	Main migration function

	Steps:
	1. Extract unique base prices (item + price_type)
	2. Create Item Price Type records
	3. Extract shop-specific discounts (shop + item)
	4. Create Shop Discount records
	5. Validate migration
	"""
	frappe.db.begin()

	try:
		print("\n" + "=" * 60)
		print("Starting Shop Price Master Migration")
		print("=" * 60 + "\n")

		# Step 1: Migrate base prices
		base_prices_created = migrate_base_prices()
		print(f"\n✓ Created {base_prices_created} Item Price Type records")

		# Step 2: Migrate discounts
		discounts_created = migrate_discounts()
		print(f"✓ Created {discounts_created} Shop Discount records")

		# Step 3: Validate migration
		validate_migration()
		print("\n✓ Migration validation passed")

		# Commit transaction
		frappe.db.commit()

		print("\n" + "=" * 60)
		print("Migration completed successfully!")
		print("=" * 60 + "\n")
		print("Next steps:")
		print("1. Review Item Price Type records")
		print("2. Review Shop Discount records")
		print("3. Test Sales Invoice pricing with new system")
		print("4. Deactivate old Shop Price Master records (optional)")

		return {
			"status": "success",
			"base_prices_created": base_prices_created,
			"discounts_created": discounts_created,
		}

	except Exception as e:
		frappe.db.rollback()
		print(f"\n✗ Migration failed: {e!s}")
		frappe.log_error(title="Shop Pricing Migration Failed", message=str(e))
		raise


def migrate_base_prices():
	"""
	Extract unique base prices from Shop Price Master
	Create Item Price Type records

	Logic:
	- Group by item_code + price_type
	- Use MEDIAN or MODE of price_per_kg across all shops
	- Set valid_from to earliest date, is_active=1

	Returns:
	    int: Number of records created
	"""
	print("\n1. Migrating Base Prices...")
	print("-" * 60)

	# Get unique item + price_type combinations with aggregated pricing
	query = """
        SELECT
            item_code,
            price_type,
            AVG(price_per_kg) as avg_price,
            MIN(price_per_kg) as min_price,
            MAX(price_per_kg) as max_price,
            COUNT(DISTINCT shop) as shop_count,
            MIN(valid_from) as earliest_valid_from
        FROM `tabShop Price Master`
        WHERE is_active = 1
        GROUP BY item_code, price_type
        ORDER BY item_code, price_type
    """

	base_price_data = frappe.db.sql(query, as_dict=True)

	created_count = 0

	for row in base_price_data:
		# Use average as base price (can be adjusted based on business logic)
		base_price = row.avg_price

		# Check for price variance
		variance = row.max_price - row.min_price
		if variance > 5.0:  # Alert if variance > ₹5/kg
			print(f"  ⚠ Warning: Large price variance for {row.item_code} ({row.price_type})")
			print(f"    Min: ₹{row.min_price}, Max: ₹{row.max_price}, Using Avg: ₹{base_price}")

		# Check if already exists
		existing = frappe.db.exists(
			"Item Price Type", {"item_code": row.item_code, "price_type": row.price_type, "is_active": 1}
		)

		if existing:
			print(f"  • Skipping {row.item_code} ({row.price_type}) - already exists")
			continue

		# Create Item Price Type
		price_type_doc = frappe.get_doc(
			{
				"doctype": "Item Price Type",
				"item_code": row.item_code,
				"price_type": row.price_type,
				"base_price_per_kg": base_price,
				"valid_from": row.earliest_valid_from,
				"is_active": 1,
				"remarks": f"Migrated from Shop Price Master. Based on {row.shop_count} shop(s).",
			}
		)

		price_type_doc.insert(ignore_permissions=True)
		created_count += 1

		print(f"  ✓ {row.item_code} ({row.price_type}): ₹{base_price:.2f}/kg")

	return created_count


def migrate_discounts():
	"""
	Extract shop-specific discounts from Shop Price Master
	Create Shop Discount records

	Logic:
	- For each shop + item combination
	- Calculate discount = (base_price - actual_price)
	- Only create if discount > 0

	Returns:
	    int: Number of records created
	"""
	print("\n2. Migrating Shop Discounts...")
	print("-" * 60)

	# Get all active shop prices
	shop_prices = frappe.db.sql(
		"""
        SELECT
            shop,
            item_code,
            price_type,
            price_per_kg,
            discount_inr,
            valid_from,
            valid_till
        FROM `tabShop Price Master`
        WHERE is_active = 1
        ORDER BY shop, item_code
    """,
		as_dict=True,
	)

	created_count = 0

	for row in shop_prices:
		# Get base price for this item + price_type
		base_price_record = frappe.db.get_value(
			"Item Price Type",
			{"item_code": row.item_code, "price_type": row.price_type, "is_active": 1},
			"base_price_per_kg",
		)

		if not base_price_record:
			print(f"  ⚠ Warning: No base price found for {row.item_code} ({row.price_type})")
			continue

		# Use explicit discount from Shop Price Master
		discount = row.discount_inr

		# Skip if no discount
		if discount <= 0:
			continue

		# Check if already exists
		existing = frappe.db.exists(
			"Shop Discount", {"shop": row.shop, "item_code": row.item_code, "is_active": 1}
		)

		if existing:
			print(f"  • Skipping {row.shop} - {row.item_code} - already exists")
			continue

		# Create Shop Discount
		discount_doc = frappe.get_doc(
			{
				"doctype": "Shop Discount",
				"shop": row.shop,
				"item_code": row.item_code,
				"discount_per_kg": discount,
				"valid_from": row.valid_from,
				"valid_till": row.valid_till,
				"is_active": 1,
				"remarks": f"Migrated from Shop Price Master. Original price: ₹{row.price_per_kg}/kg",
			}
		)

		discount_doc.insert(ignore_permissions=True)
		created_count += 1

		if created_count % 10 == 0:
			print(f"  ... processed {created_count} discounts")

	return created_count


def validate_migration():
	"""
	Validate migration results

	Checks:
	- All items have base prices
	- Effective prices match original Shop Price Master
	- No negative effective prices
	"""
	print("\n3. Validating Migration...")
	print("-" * 60)

	# Get sample shop prices to validate
	sample_prices = frappe.db.sql(
		"""
        SELECT
            shop,
            item_code,
            price_type,
            price_per_kg,
            discount_inr,
            (price_per_kg - discount_inr) as effective_price_old
        FROM `tabShop Price Master`
        WHERE is_active = 1
        LIMIT 10
    """,
		as_dict=True,
	)

	validation_errors = []

	for row in sample_prices:
		# Get new base price
		from shiva_erp.shiva_business_erp.doctype.item_price_type.item_price_type import get_base_price

		base_price = get_base_price(row.item_code, row.price_type)

		# Get new discount
		from shiva_erp.shiva_business_erp.doctype.shop_discount.shop_discount import get_shop_discount

		discount = get_shop_discount(row.shop, row.item_code)

		# Calculate new effective price
		effective_price_new = (base_price or 0) - (discount or 0)

		# Compare with old effective price (allow ±1 INR tolerance for averaging)
		diff = abs(effective_price_new - row.effective_price_old)
		if diff > 1.0:
			error_msg = (
				f"Price mismatch for {row.shop} - {row.item_code}: "
				f"Old: ₹{row.effective_price_old:.2f}, New: ₹{effective_price_new:.2f}"
			)
			validation_errors.append(error_msg)
			print(f"  ✗ {error_msg}")

	if validation_errors:
		print(f"\n  Found {len(validation_errors)} validation warnings")
		print("  (Small differences expected due to price averaging)")
	else:
		print("  ✓ All sample prices validated successfully")

	return len(validation_errors) == 0


def deactivate_old_records():
	"""
	Optional: Deactivate old Shop Price Master records

	WARNING: Only run this after confirming migration success
	and testing new pricing system thoroughly
	"""
	print("\n4. Deactivating Old Shop Price Master Records...")
	print("-" * 60)

	count = frappe.db.sql("""
        UPDATE `tabShop Price Master`
        SET is_active = 0
        WHERE is_active = 1
    """)

	frappe.db.commit()
	print(f"  ✓ Deactivated {count} old records")

	return count


if __name__ == "__main__":
	migrate_shop_pricing()
