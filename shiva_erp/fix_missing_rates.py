#!/usr/bin/env python3
"""
Fix missing rate_per_kg and value_amount in Stock Weight Ledger entries.
Backfills rates from original Purchase Receipt/Delivery Note documents.
"""

import frappe
from frappe.utils import flt


def fix_missing_rates():
	"""Update Stock Weight Ledger entries with missing rates"""

	# Get all entries with NULL or 0 rate_per_kg
	entries = frappe.db.sql(
		"""
		SELECT 
			name, voucher_type, voucher_no, item_code, 
			weight_kg, transaction_type
		FROM 
			`tabStock Weight Ledger`
		WHERE 
			rate_per_kg IS NULL OR rate_per_kg = 0
		ORDER BY 
			posting_date ASC
	""",
		as_dict=1,
	)

	print(f"\nFound {len(entries)} entries with missing rates")

	updated = 0
	errors = 0

	for entry in entries:
		try:
			rate_per_kg = 0

			if entry.voucher_type == "Purchase Receipt":
				# Get rate from Purchase Receipt Item
				pr_item = frappe.db.sql(
					"""
					SELECT 
						qty, rate, base_rate, amount, base_amount,
						custom_total_weight_kg
					FROM 
						`tabPurchase Receipt Item`
					WHERE 
						parent = %(voucher_no)s 
						AND item_code = %(item_code)s
					LIMIT 1
				""",
					{"voucher_no": entry.voucher_no, "item_code": entry.item_code},
					as_dict=1,
				)

				if pr_item and len(pr_item) > 0:
					item = pr_item[0]
					weight_kg = flt(item.custom_total_weight_kg) or flt(entry.weight_kg)

					if weight_kg > 0:
						# Try different rate fields in order of preference
						if flt(item.base_amount) > 0:
							rate_per_kg = flt(item.base_amount) / weight_kg
						elif flt(item.amount) > 0:
							rate_per_kg = flt(item.amount) / weight_kg
						elif flt(item.base_rate) > 0:
							total_amount = flt(item.base_rate) * flt(item.qty)
							rate_per_kg = total_amount / weight_kg
						elif flt(item.rate) > 0:
							total_amount = flt(item.rate) * flt(item.qty)
							rate_per_kg = total_amount / weight_kg

			elif entry.voucher_type == "Delivery Note":
				# Get valuation rate from Delivery Note Item
				dn_item = frappe.db.sql(
					"""
					SELECT 
						qty, incoming_rate, valuation_rate,
						custom_total_weight_kg
					FROM 
						`tabDelivery Note Item`
					WHERE 
						parent = %(voucher_no)s 
						AND item_code = %(item_code)s
					LIMIT 1
				""",
					{"voucher_no": entry.voucher_no, "item_code": entry.item_code},
					as_dict=1,
				)

				if dn_item and len(dn_item) > 0:
					item = dn_item[0]
					weight_kg = flt(item.custom_total_weight_kg) or flt(entry.weight_kg)
					valuation_rate = flt(item.incoming_rate) or flt(item.valuation_rate)

					if weight_kg > 0 and valuation_rate > 0:
						total_amount = valuation_rate * flt(item.qty)
						rate_per_kg = total_amount / weight_kg

			# Update the entry if we found a rate
			if rate_per_kg > 0:
				value_amount = rate_per_kg * flt(entry.weight_kg)

				frappe.db.sql(
					"""
					UPDATE `tabStock Weight Ledger`
					SET 
						rate_per_kg = %(rate_per_kg)s,
						value_amount = %(value_amount)s,
						modified = NOW(),
						modified_by = %(user)s
					WHERE 
						name = %(name)s
				""",
					{
						"name": entry.name,
						"rate_per_kg": rate_per_kg,
						"value_amount": value_amount,
						"user": frappe.session.user,
					},
				)

				updated += 1
				print(f"✓ Updated {entry.name}: Rate/Kg = ₹{rate_per_kg:.2f}, Value = ₹{value_amount:.2f}")
			else:
				print(f"⚠ No rate found for {entry.name} ({entry.voucher_type} {entry.voucher_no})")

		except Exception as e:
			errors += 1
			print(f"✗ Error updating {entry.name}: {e!s}")

	frappe.db.commit()

	print(f"\n{'=' * 60}")
	print("Summary:")
	print(f"  Total entries: {len(entries)}")
	print(f"  Updated: {updated}")
	print(f"  Errors: {errors}")
	print(f"  Skipped (no rate): {len(entries) - updated - errors}")
	print(f"{'=' * 60}\n")


if __name__ == "__main__":
	frappe.init(site="erpnext.site")
	frappe.connect()
	frappe.flags.in_patch = True

	fix_missing_rates()

	print("✓ Rate backfill completed!")
