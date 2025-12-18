// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Poultry Sales Invoice", {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Apply Territory Pricing"), function() {
				frm.save();
			});
		}
		
		if (frm.doc.docstatus === 1) {
			// Add print button
			frm.add_custom_button(__("Print"), function() {
				frappe.utils.print(
					frm.doctype,
					frm.docname
				);
			});
		}
	},
	
	customer: function(frm) {
		// When customer changes, fetch territory and recalculate
		if (frm.doc.customer) {
			frappe.db.get_value("Customer", frm.doc.customer, "territory", function(r) {
				frm.set_value("territory", r.territory);
				frm.save();
			});
		}
	}
});

frappe.ui.form.on("Poultry Sales Invoice Item", {
	item_code: function(frm, cdt, cdn) {
		// Let standard item fetch complete
		let item = locals[cdt][cdn];
		if (item.item_code) {
			// Set default warehouse if not set
			if (!item.warehouse) {
				frappe.model.set_value(cdt, cdn, "warehouse", "Stores - SA PVT LTD");
			}
			
			// Apply pricing if weight is already entered
			if (item.weight_kg > 0) {
				apply_pricing_for_item(frm, item);
			}
		}
	},
	
	weight_kg: function(frm, cdt, cdn) {
		// Fetch pricing when weight is entered
		let item = locals[cdt][cdn];
		if (item.item_code && item.weight_kg > 0 && frm.doc.customer) {
			apply_pricing_for_item(frm, item);
		} else if (item.weight_kg > 0 && item.rate > 0) {
			// Just recalculate amount if rate already exists
			frappe.model.set_value(cdt, cdn, "amount", item.weight_kg * item.rate);
		}
		calculate_totals(frm);
	},
	
	rate: function(frm, cdt, cdn) {
		// Recalculate amount when rate changes
		let item = locals[cdt][cdn];
		if (item.weight_kg > 0 && item.rate > 0) {
			frappe.model.set_value(cdt, cdn, "amount", item.weight_kg * item.rate);
		}
		calculate_totals(frm);
	},
	
	items_remove: function(frm) {
		calculate_totals(frm);
	}
});

function calculate_totals(frm) {
	let total_qty = 0;
	let total_weight = 0;
	let total_amount = 0;
	
	frm.doc.items.forEach(function(item) {
		total_qty += flt(item.qty);
		total_weight += flt(item.weight_kg);
		total_amount += flt(item.amount);
	});
	
	frm.set_value("total_qty", total_qty);
	frm.set_value("total_weight", total_weight);
	frm.set_value("total_amount", total_amount);
}

function apply_pricing_for_item(frm, item) {
	if (!frm.doc.customer || !item.item_code) {
		return;
	}
	
	// Call server to get pricing
	frappe.call({
		method: "shiva_erp.sales_integration.get_item_pricing",
		args: {
			customer: frm.doc.customer,
			item_code: item.item_code,
			posting_date: frm.doc.posting_date || frappe.datetime.get_today(),
			weight_kg: item.weight_kg || 0
		},
		callback: function(r) {
			if (r.message) {
				let pricing = r.message;
				
				// Update item with pricing
				frappe.model.set_value(item.doctype, item.name, "base_price_per_kg", pricing.base_price);
				frappe.model.set_value(item.doctype, item.name, "discount_per_kg", pricing.discount);
				frappe.model.set_value(item.doctype, item.name, "rate", pricing.effective_price);
				
				// Calculate amount
				if (item.weight_kg > 0) {
					frappe.model.set_value(item.doctype, item.name, "amount", pricing.effective_price * item.weight_kg);
				}
				
				calculate_totals(frm);
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
