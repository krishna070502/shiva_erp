// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier Statement"] = {
	"filters": [
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			reqd: 1
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today()
		}
	],
	
	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Style for opening, total, and closing rows
		if (data && (data.is_opening || data.is_total || data.is_closing)) {
			value = `<span style="font-weight: bold;">${value}</span>`;
			
			// Color code the balance
			if (column.fieldname === "balance" && data.balance) {
				let color = data.balance < 0 ? "red" : "green";
				value = `<span style="font-weight: bold; color: ${color};">${value}</span>`;
			}
		}
		
		return value;
	}
};
