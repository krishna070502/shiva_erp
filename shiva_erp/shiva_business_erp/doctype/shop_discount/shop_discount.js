// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Discount", {
	refresh(frm) {
		// Add custom button for bulk update
		if (!frm.is_new()) {
			frm.add_custom_button(__("Bulk Update Discount"), function () {
				show_bulk_update_dialog(frm);
			});
		}

		// Set color indicator
		if (frm.doc.is_active) {
			frm.set_indicator_color("Active", "green");
		} else {
			frm.set_indicator_color("Inactive", "red");
		}

		// Show discount prominently
		if (frm.doc.discount_per_kg) {
			frm.dashboard.add_indicator(
				__("Discount: ₹{0}/kg for {1}", [frm.doc.discount_per_kg.toFixed(2), frm.doc.shop]),
				"orange"
			);
		}
	},

	discount_per_kg(frm) {
		validate_discount(frm);
	},

	valid_from(frm) {
		validate_validity_dates(frm);
	},

	valid_till(frm) {
		validate_validity_dates(frm);
	},

	validate(frm) {
		if (frm.doc.discount_per_kg < 0) {
			frappe.msgprint(__("Discount cannot be negative"));
			frappe.validated = false;
		}
	},
});

function validate_discount(frm) {
	if (frm.doc.discount_per_kg < 0) {
		frappe.msgprint({
			title: __("Invalid Discount"),
			message: __("Discount cannot be negative"),
			indicator: "red",
		});
		frm.set_value("discount_per_kg", 0);
	}
}

function validate_validity_dates(frm) {
	if (frm.doc.valid_from && frm.doc.valid_till) {
		if (frm.doc.valid_till < frm.doc.valid_from) {
			frappe.msgprint({
				title: __("Invalid Date Range"),
				message: __("Valid Till cannot be before Valid From"),
				indicator: "red",
			});
		}
	}
}

function show_bulk_update_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Bulk Update Discount"),
		fields: [
			{
				label: __("Filters"),
				fieldtype: "Section Break",
			},
			{
				label: __("Shop"),
				fieldname: "shop",
				fieldtype: "Link",
				options: "Customer",
			},
			{
				label: __("Item Code"),
				fieldname: "item_code",
				fieldtype: "Link",
				options: "Item",
			},
			{
				fieldtype: "Section Break",
				label: __("New Value"),
			},
			{
				label: __("New Discount per Kg"),
				fieldname: "new_discount",
				fieldtype: "Currency",
				reqd: 1,
			},
		],
		primary_action_label: __("Update"),
		primary_action(values) {
			frappe.call({
				method: "shiva_erp.shiva_business_erp.doctype.shop_discount.shop_discount.bulk_update_discount",
				args: {
					shop: values.shop,
					item_code: values.item_code,
					new_discount: values.new_discount,
				},
				callback: function (r) {
					if (r.message) {
						frappe.msgprint(__("Updated {0} discount records", [r.message]));
						frm.reload_doc();
					}
					d.hide();
				},
			});
		},
	});

	d.show();
}
