// Sales Invoice Client Script - Auto-apply pricing
frappe.ui.form.on("Sales Invoice", {
	customer: function(frm) {
		// When customer changes, reapply pricing for all items
		if (frm.doc.customer) {
			apply_pricing_to_all_items(frm);
		}
	},
	
	refresh: function(frm) {
		// Add button to manually trigger pricing
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Apply Territory Pricing"), function() {
				apply_pricing_to_all_items(frm);
			});
		}
	}
});

frappe.ui.form.on("Sales Invoice Item", {
	custom_total_weight_kg: function(frm, cdt, cdn) {
		// When weight changes, recalculate rate and amount
		let item = locals[cdt][cdn];
		if (item.custom_total_weight_kg && frm.doc.customer) {
			apply_pricing_for_item(frm, item);
		}
	},
	
	qty: function(frm, cdt, cdn) {
		// Don't auto-apply pricing on qty change to avoid conflicts
		// User can manually apply pricing or enter weight
	}
});

function apply_pricing_for_item(frm, item) {
	// Get customer territory
	if (!frm.doc.customer) {
		frappe.msgprint(__("Please select a customer first"));
		return;
	}
	
	// Call server to get base price and shop discount
	frappe.call({
		method: "shiva_erp.sales_integration.get_item_pricing",
		args: {
			customer: frm.doc.customer,
			item_code: item.item_code,
			posting_date: frm.doc.posting_date || frappe.datetime.get_today(),
			weight_kg: item.custom_total_weight_kg || 0
		},
		callback: function(r) {
			if (r.message) {
				let pricing = r.message;
				
				// Update item with pricing
				frappe.model.set_value(item.doctype, item.name, "custom_base_price_per_kg", pricing.base_price);
				frappe.model.set_value(item.doctype, item.name, "custom_discount_per_kg", pricing.discount);
				frappe.model.set_value(item.doctype, item.name, "rate", pricing.effective_price);
				
				// Calculate amount = effective_price * weight_kg
				if (item.custom_total_weight_kg > 0) {
					let amount = pricing.effective_price * item.custom_total_weight_kg;
					frappe.model.set_value(item.doctype, item.name, "amount", amount);
				}
				
				frm.refresh_field("items");
				
				if (pricing.message) {
					frappe.show_alert({
						message: pricing.message,
						indicator: "green"
					});
				}
			}
		}
	});
}

function apply_pricing_to_all_items(frm) {
	if (!frm.doc.customer) {
		frappe.msgprint(__("Please select a customer first"));
		return;
	}
	
	if (!frm.doc.items || frm.doc.items.length === 0) {
		frappe.msgprint(__("No items to apply pricing to"));
		return;
	}
	
	// Apply pricing to each item
	frm.doc.items.forEach(function(item) {
		if (item.item_code) {
			apply_pricing_for_item(frm, item);
		}
	});
}
