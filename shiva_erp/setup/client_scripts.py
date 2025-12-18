"""
Client-side script customizations for Sales Invoice

Makes rate field read-only and auto-calculates pricing based on territory.
"""

import frappe


def sales_invoice_item_script():
	"""
	Return client script for Sales Invoice Item to:
	1. Make rate field read-only (pricing is auto-calculated)
	2. Auto-calculate amount when weight is entered
	3. Show territory-based pricing info
	"""
	return """
frappe.ui.form.on('Sales Invoice Item', {
	custom_total_weight_kg: function(frm, cdt, cdn) {
		// Trigger pricing recalculation when weight changes
		if (frm.doc.customer) {
			frm.trigger('apply_shop_pricing');
		}
	},
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// Make rate read-only as it's auto-calculated
		frappe.model.set_df_property('Sales Invoice Item', 'rate', 'read_only', 1, cdn);
	}
});

frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		// Make rate column read-only in grid
		frm.fields_dict['items'].grid.update_docfield_property('rate', 'read_only', 1);

		// Add custom button to apply pricing
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Apply Territory Pricing'), function() {
				frappe.call({
					method: 'shiva_erp.sales_integration.apply_shop_pricing_manually',
					args: {
						doc: frm.doc
					},
					callback: function(r) {
						frm.reload_doc();
						frappe.show_alert(__('Pricing applied successfully'));
					}
				});
			});
		}
	},

	customer: function(frm) {
		// Auto-apply pricing when customer changes
		if (frm.doc.items && frm.doc.items.length > 0) {
			setTimeout(function() {
				frm.trigger('apply_shop_pricing');
			}, 500);
		}
	},

	apply_shop_pricing: function(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.customer) {
			frappe.call({
				method: 'shiva_erp.sales_integration.apply_shop_pricing_manually',
				args: {
					doc: frm.doc
				},
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		}
	}
});
"""
