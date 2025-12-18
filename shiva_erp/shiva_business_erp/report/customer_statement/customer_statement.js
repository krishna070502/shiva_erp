// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Statement"] = {
	filters: [
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Bold formatting for opening/closing balance rows
		if (data && (data.is_opening || data.is_closing)) {
			value = value.bold();
		}

		// Color balance based on value
		if (column.fieldname === "balance" && data && !data.is_opening && !data.is_closing) {
			if (data.balance > 0) {
				value = `<span style="color: green;">${value}</span>`;
			} else if (data.balance < 0) {
				value = `<span style="color: red;">${value}</span>`;
			}
		}

		return value;
	},
};
