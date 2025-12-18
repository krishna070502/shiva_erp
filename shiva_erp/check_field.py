import frappe


def check_field():
	field = frappe.db.get_value(
		"Custom Field",
		{"dt": "Sales Invoice Item", "fieldname": "custom_total_weight_kg"},
		["name", "label", "fieldtype", "insert_after"],
		as_dict=True,
	)
	print(f"Custom Field: {field}")


if __name__ == "__main__":
	check_field()
