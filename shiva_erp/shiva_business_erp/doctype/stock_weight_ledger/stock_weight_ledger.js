// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

/**
 * Stock Weight Ledger Client Script
 * Handles dual UOM (Nos + Kg) calculations and validations
 */

frappe.ui.form.on("Stock Weight Ledger", {
	refresh(frm) {
		// Add custom button to view current stock balance
		if (!frm.is_new()) {
			frm.add_custom_button(__("View Stock Balance"), function () {
				view_stock_balance(frm);
			});
		}

		// Set color indicator based on transaction type
		if (frm.doc.transaction_type === "IN") {
			frm.set_indicator_color("IN", "green");
		} else if (frm.doc.transaction_type === "OUT") {
			frm.set_indicator_color("OUT", "red");
		}
	},

	stock_qty(frm) {
		calculate_average_weight(frm);
	},

	weight_kg(frm) {
		calculate_average_weight(frm);
	},

	transaction_type(frm) {
		// Update field descriptions based on transaction type
		if (frm.doc.transaction_type === "IN") {
			frm.set_df_property("stock_qty", "description", "Number of birds received");
			frm.set_df_property("weight_kg", "description", "Total weight of birds received");
		} else if (frm.doc.transaction_type === "OUT") {
			frm.set_df_property("stock_qty", "description", "Number of birds dispatched");
			frm.set_df_property("weight_kg", "description", "Total weight of birds dispatched");
		}
	},

	item_code(frm) {
		// Auto-refresh warehouse options based on item
		if (frm.doc.item_code) {
			frm.set_query("warehouse", function () {
				return {
					filters: {
						is_group: 0,
					},
				};
			});
		}
	},

	warehouse(frm) {
		// Show current balance when warehouse is selected
		if (frm.doc.item_code && frm.doc.warehouse) {
			show_current_balance(frm);
		}
	},

	validate(frm) {
		// Client-side validation before save
		if (frm.doc.stock_qty <= 0) {
			frappe.msgprint(__("Stock Qty must be greater than 0"));
			frappe.validated = false;
		}

		if (frm.doc.weight_kg <= 0) {
			frappe.msgprint(__("Total Weight must be greater than 0"));
			frappe.validated = false;
		}

		// Validate average weight is reasonable (0.5 to 5 kg per bird)
		const avg_weight = frm.doc.weight_kg / frm.doc.stock_qty;
		if (avg_weight < 0.5 || avg_weight > 5.0) {
			frappe.msgprint({
				title: __("Warning"),
				message: __(
					"Average weight per bird is {0} kg. Please verify if this is correct.",
					[avg_weight.toFixed(3)]
				),
				indicator: "orange",
			});
		}
	},
});

/**
 * Calculate and display average weight per bird
 */
function calculate_average_weight(frm) {
	if (frm.doc.stock_qty > 0 && frm.doc.weight_kg > 0) {
		const avg_weight = frm.doc.weight_kg / frm.doc.stock_qty;
		frm.set_value("avg_weight_per_bird", avg_weight);

		// Show info message
		frappe.show_alert({
			message: __("Avg Weight: {0} kg/bird", [avg_weight.toFixed(3)]),
			indicator: "blue",
		});
	}
}

/**
 * Show current stock balance for selected item/warehouse
 */
function show_current_balance(frm) {
	frappe.call({
		method: "shiva_erp.shiva_business_erp.doctype.stock_weight_ledger.stock_weight_ledger.get_stock_balance",
		args: {
			item_code: frm.doc.item_code,
			warehouse: frm.doc.warehouse,
			batch_no: frm.doc.batch_no || null,
		},
		callback: function (r) {
			if (r.message) {
				const balance = r.message;
				frappe.show_alert({
					message: __(
						"Current Balance: {0} Nos ({1} Kg) | Avg: {2} kg/bird",
						[
							balance.stock_qty.toFixed(2),
							balance.weight_kg.toFixed(3),
							balance.avg_weight_per_bird.toFixed(3),
						]
					),
					indicator: "blue",
				});
			}
		},
	});
}

/**
 * View detailed stock balance in a dialog
 */
function view_stock_balance(frm) {
	frappe.call({
		method: "shiva_erp.shiva_business_erp.doctype.stock_weight_ledger.stock_weight_ledger.get_stock_balance",
		args: {
			item_code: frm.doc.item_code,
			warehouse: frm.doc.warehouse,
			batch_no: frm.doc.batch_no || null,
		},
		callback: function (r) {
			if (r.message) {
				const balance = r.message;

				const d = new frappe.ui.Dialog({
					title: __("Stock Balance: {0} @ {1}", [frm.doc.item_code, frm.doc.warehouse]),
					fields: [
						{
							fieldtype: "HTML",
							fieldname: "balance_html",
						},
					],
				});

				const html = `
					<div class="row">
						<div class="col-sm-12">
							<table class="table table-bordered">
								<tr>
									<th>Stock Qty (Nos)</th>
									<td>${balance.stock_qty.toFixed(2)}</td>
								</tr>
								<tr>
									<th>Total Weight (Kg)</th>
									<td>${balance.weight_kg.toFixed(3)}</td>
								</tr>
								<tr>
									<th>Avg Weight per Bird (Kg)</th>
									<td>${balance.avg_weight_per_bird.toFixed(3)}</td>
								</tr>
							</table>
						</div>
					</div>
				`;

				d.fields_dict.balance_html.$wrapper.html(html);
				d.show();
			}
		},
	});
}

