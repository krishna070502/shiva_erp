"""
Install Client Scripts for Sales Invoice auto-pricing
"""

import frappe


def install_client_scripts():
	"""Create Client Script for Sales Invoice to make rate read-only and auto-apply pricing"""

	# Check if already exists
	if frappe.db.exists("Client Script", "Sales Invoice - Territory Pricing"):
		print("Client Script already exists, updating...")
		doc = frappe.get_doc("Client Script", "Sales Invoice - Territory Pricing")
	else:
		doc = frappe.new_doc("Client Script")
		doc.name = "Sales Invoice - Territory Pricing"

	doc.dt = "Sales Invoice"
	doc.view = "Form"
	doc.enabled = 1
	doc.script = """
frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		// Make rate column read-only in grid
		frm.fields_dict['items'].grid.update_docfield_property('rate', 'read_only', 1);
		// Add button to apply pricing
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Apply Territory Pricing'), function() {
				frappe.call({
					method: 'shiva_erp.sales_integration.apply_pricing_to_invoice',
					args: {
						invoice_name: frm.doc.name
					},
					callback: function(r) {
						frm.reload_doc();
						frappe.show_alert({
							message: __('Pricing applied successfully'),
							indicator: 'green'
						});
					}
				});
			});
		}
	},
	before_save: function(frm) {
		// Auto-apply pricing before save
		if (frm.doc.customer && frm.doc.items) {
			return frappe.call({
				method: 'shiva_erp.sales_integration.apply_pricing_to_invoice',
				args: {
					invoice_name: frm.doc.name
				},
				async: false
			});
		}
	}
});

frappe.ui.form.on('Sales Invoice Item', {
	item_code: function(frm, cdt, cdn) {
		// Make rate read-only for this row
		frappe.model.set_df_property('Sales Invoice Item', 'rate', 'read_only', 1, cdn);
	}
});
"""

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	print(f"✓ Client Script '{doc.name}' installed successfully")


if __name__ == "__main__":
	install_client_scripts()
