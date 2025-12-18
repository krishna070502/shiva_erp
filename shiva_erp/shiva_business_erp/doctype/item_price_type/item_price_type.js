// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Price Type", {
	refresh(frm) {
		// Add custom button for bulk update
		if (!frm.is_new()) {
			frm.add_custom_button(__("Bulk Update Base Price"), function () {
				show_bulk_update_dialog(frm);
			});
		}

		// Set color indicator
		if (frm.doc.is_active) {
			frm.set_indicator_color("Active", "green");
		} else {
			frm.set_indicator_color("Inactive", "red");
		}

		// Show base price prominently
		if (frm.doc.base_price_per_kg) {
			frm.dashboard.add_indicator(
				__("Base Price: ₹{0}/kg ({1})", [frm.doc.base_price_per_kg.toFixed(2), frm.doc.territory]),
				"blue"
			);
		}
	},

	base_price_per_kg(frm) {
		validate_base_price(frm);
	},

	valid_from(frm) {
		validate_validity_dates(frm);
	},

	valid_till(frm) {
		validate_validity_dates(frm);
	},

	validate(frm) {
		if (frm.doc.base_price_per_kg <= 0) {
			frappe.msgprint(__("Base Price must be greater than 0"));
			frappe.validated = false;
		}
	},
});

function validate_base_price(frm) {
	if (frm.doc.base_price_per_kg <= 0) {
		frappe.msgprint({
			title: __("Invalid Price"),
			message: __("Base Price must be greater than 0"),
			indicator: "red",
		});
		frm.set_value("base_price_per_kg", 0);
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
		title: __("Bulk Update Base Price"),
		fields: [
			{
				label: __("Filters"),
				fieldtype: "Section Break",
			},
			{
				label: __("Item Code"),
				fieldname: "item_code",
				fieldtype: "Link",
				options: "Item",
			},
			{
				label: __("Territory"),
				fieldname: "territory",
				fieldtype: "Link",
				options: "Territory",
			},
			{
				fieldtype: "Section Break",
				label: __("New Value"),
			},
			{
				label: __("New Base Price per Kg"),
				fieldname: "new_base_price",
				fieldtype: "Currency",
				reqd: 1,
			},
		],
		primary_action_label: __("Update"),
		primary_action(values) {
			frappe.call({
				method: "shiva_erp.shiva_business_erp.doctype.item_price_type.item_price_type.bulk_update_base_price",
				args: {
					item_code: values.item_code,
					territory: values.territory,
					new_base_price: values.new_base_price,
				},
				callback: function (r) {
					if (r.message) {
						frappe.msgprint(__("Updated {0} price records", [r.message]));
						frm.reload_doc();
					}
					d.hide();
				},
			});
		},
	});

	d.show();
}
