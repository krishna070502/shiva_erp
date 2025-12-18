// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Weight Ledger Detailed"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function() {
				return {
					filters: { "is_stock_item": 1 }
				};
			}
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"get_query": function() {
				return {
					filters: { "is_group": 0 }
				};
			}
		},
		{
			"fieldname": "transaction_type",
			"label": __("Transaction Type"),
			"fieldtype": "Select",
			"options": ["", "IN", "OUT"],
			"default": ""
		},
		{
			"fieldname": "batch_no",
			"label": __("Batch"),
			"fieldtype": "Link",
			"options": "Batch"
		}
	],

	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Color code transaction type with icons
		if (column.fieldname == "transaction_type") {
			if (value && value.includes("IN")) {
				value = `<span style="color: #28a745; font-weight: bold; padding: 3px 8px; background: #d4edda; border-radius: 3px;">
					<i class="fa fa-arrow-down"></i> IN
				</span>`;
			} else if (value && value.includes("OUT")) {
				value = `<span style="color: #dc3545; font-weight: bold; padding: 3px 8px; background: #f8d7da; border-radius: 3px;">
					<i class="fa fa-arrow-up"></i> OUT
				</span>`;
			}
		}

		// Color code and format changes with better styling
		if (column.fieldname == "qty_change" || column.fieldname == "weight_change") {
			let numValue = parseFloat(data[column.fieldname]);
			let precision = column.fieldname == "qty_change" ? 2 : 3;
			
			if (numValue > 0) {
				value = `<span style="color: #28a745; font-weight: 600;">
					<i class="fa fa-plus-circle"></i> ${Math.abs(numValue).toFixed(precision)}
				</span>`;
			} else if (numValue < 0) {
				value = `<span style="color: #dc3545; font-weight: 600;">
					<i class="fa fa-minus-circle"></i> ${Math.abs(numValue).toFixed(precision)}
				</span>`;
			}
		}

		// Style actual quantities with subtle background
		if (column.fieldname == "stock_qty" || column.fieldname == "weight_kg") {
			let numValue = parseFloat(data[column.fieldname]);
			let precision = column.fieldname == "stock_qty" ? 2 : 3;
			if (!isNaN(numValue)) {
				value = `<span style="background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-weight: 500;">
					${numValue.toFixed(precision)}
				</span>`;
			}
		}

		// Bold and highlight balance columns
		if (column.fieldname == "balance_qty" || column.fieldname == "balance_weight") {
			let numValue = parseFloat(data[column.fieldname]);
			let precision = column.fieldname == "balance_qty" ? 2 : 3;
			if (!isNaN(numValue)) {
				let color = numValue > 0 ? "#0066cc" : "#999";
				value = `<span style="font-weight: bold; color: ${color}; font-size: 1.05em;">
					${numValue.toFixed(precision)}
				</span>`;
			}
		}

		// Style average weight
		if (column.fieldname == "avg_weight_per_bird") {
			let numValue = parseFloat(data[column.fieldname]);
			if (!isNaN(numValue)) {
				value = `<span style="color: #6c757d; font-style: italic;">
					${numValue.toFixed(3)}
				</span>`;
			}
		}

		// Truncate long remarks with tooltip
		if (column.fieldname == "remarks" && value && value.length > 50) {
			let fullText = value.replace(/<[^>]*>/g, '');
			value = `<span title="${fullText}">${fullText.substring(0, 47)}...</span>`;
		}

		return value;
	},

	"onload": function(report) {
		// Add custom button for export detailed summary
		report.page.add_inner_button(__("Export Summary"), function() {
			let summary_data = report.data;
			if (!summary_data || summary_data.length === 0) {
				frappe.msgprint(__("No data to export"));
				return;
			}

			frappe.msgprint({
				title: __("Export Options"),
				message: __("Summary will be exported with transaction details"),
				primary_action: {
					label: __("Download Excel"),
					action: function() {
						report.export_report();
					}
				}
			});
		});

		// Add button to view batch details
		report.page.add_inner_button(__("Batch Analysis"), function() {
			frappe.set_route("query-report", "Stock Balance Dual UOM");
		}, __("View"));

		// Add button to create stock reconciliation
		report.page.add_inner_button(__("Stock Reconciliation"), function() {
			frappe.new_doc("Stock Reconciliation");
		}, __("Create"));
	},

	"after_datatable_render": function(datatable) {
		// Add hover effect for better UX
		$(datatable.wrapper).find('.dt-cell').hover(
			function() {
				$(this).css('background-color', '#f0f8ff');
			},
			function() {
				$(this).css('background-color', '');
			}
		);
	},

	"get_datatable_options": function(options) {
		return Object.assign(options, {
			checkboxColumn: true,
			inlineFilters: true,
		});
	}
};
