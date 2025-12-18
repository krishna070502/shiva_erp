import frappe


def show_weight_field():
	# Get the custom field
	field = frappe.get_doc("Custom Field", "Sales Invoice Item-custom_total_weight_kg")

	# Make sure it's visible
	field.hidden = 0
	field.in_list_view = 1
	field.allow_on_submit = 0
	field.bold = 1
	field.columns = 2

	field.save(ignore_permissions=True)
	frappe.db.commit()

	print(f"✓ Weight field updated: {field.label}")
	print(f"  - Hidden: {field.hidden}")
	print(f"  - In List View: {field.in_list_view}")
	print(f"  - Insert After: {field.insert_after}")


if __name__ == "__main__":
	show_weight_field()
