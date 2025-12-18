"""
Fix Script: Update Stock Weight Ledger entries with NULL transaction_type

This script identifies and fixes Stock Weight Ledger entries that have NULL
transaction_type by determining the correct type based on the voucher type.
"""

import frappe


def execute():
	"""Fix NULL transaction_type entries"""
	# Find entries with NULL transaction_type
	null_entries = frappe.db.sql(
		"""
		SELECT name, voucher_type, qty_change, weight_change
		FROM `tabStock Weight Ledger`
		WHERE transaction_type IS NULL OR transaction_type = ''
	""",
		as_dict=1,
	)

	if not null_entries:
		print("No entries with NULL transaction_type found.")
		return

	print(f"Found {len(null_entries)} entries with NULL transaction_type")

	fixed_count = 0
	for entry in null_entries:
		# Determine transaction type based on voucher type
		if entry.voucher_type in ["Purchase Receipt", "Stock Entry"]:
			# Check if qty_change is positive (IN) or negative (OUT)
			if entry.qty_change > 0 or entry.weight_change > 0:
				transaction_type = "IN"
			else:
				transaction_type = "OUT"
		elif entry.voucher_type in ["Delivery Note", "Sales Invoice"]:
			transaction_type = "OUT"
		else:
			# Fallback: determine from sign of changes
			if entry.qty_change > 0 or entry.weight_change > 0:
				transaction_type = "IN"
			else:
				transaction_type = "OUT"

		# Update the entry
		frappe.db.set_value("Stock Weight Ledger", entry.name, "transaction_type", transaction_type)
		print(f"Fixed {entry.name}: Set transaction_type to {transaction_type}")
		fixed_count += 1

	frappe.db.commit()
	print(f"\n✅ Successfully fixed {fixed_count} entries")


if __name__ == "__main__":
	execute()
