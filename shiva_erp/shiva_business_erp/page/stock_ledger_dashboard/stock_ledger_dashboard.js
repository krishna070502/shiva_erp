// Copyright (c) 2025, Gopalakrishna Reddy Gogulamudi and contributors
// For license information, please see license.txt

frappe.pages['stock-ledger-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Stock Ledger Dashboard',
		single_column: true
	});

	frappe.stock_ledger_dashboard = new StockLedgerDashboard(page);
}

class StockLedgerDashboard {
	constructor(page) {
		this.page = page;
		this.filters = {};
		this.setup_page();
		this.setup_filters();
		this.load_dashboard();
	}

	setup_page() {
		this.page.add_inner_button(__('Refresh'), () => {
			this.load_dashboard();
		});

		this.page.add_inner_button(__('Export Data'), () => {
			this.export_dashboard_data();
		});

		// Create main container
		this.$container = $('<div class="stock-ledger-dashboard"></div>').appendTo(this.page.main);
	}

	setup_filters() {
		// Date range filter
		this.page.add_field({
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date',
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			change: () => this.load_dashboard()
		});

		this.page.add_field({
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date',
			default: frappe.datetime.get_today(),
			change: () => this.load_dashboard()
		});

		// Item filter
		this.page.add_field({
			fieldname: 'item_code',
			label: __('Item'),
			fieldtype: 'Link',
			options: 'Item',
			change: () => this.load_dashboard()
		});

		// Warehouse filter
		this.page.add_field({
			fieldname: 'warehouse',
			label: __('Warehouse'),
			fieldtype: 'Link',
			options: 'Warehouse',
			change: () => this.load_dashboard()
		});
	}

	load_dashboard() {
		// Get filter values
		this.filters = {
			from_date: this.page.fields_dict.from_date.get_value(),
			to_date: this.page.fields_dict.to_date.get_value(),
			item_code: this.page.fields_dict.item_code.get_value(),
			warehouse: this.page.fields_dict.warehouse.get_value()
		};

		// Load data
		frappe.call({
			method: 'shiva_erp.shiva_business_erp.page.stock_ledger_dashboard.stock_ledger_dashboard.get_dashboard_data',
			args: { filters: this.filters },
			callback: (r) => {
				if (r.message) {
					this.render_dashboard(r.message);
				}
			}
		});
	}

	render_dashboard(data) {
		this.$container.empty();

		// Render summary cards
		this.render_summary_cards(data.summary);

		// Render charts
		this.render_charts(data.chart_data);

		// Render detailed tables
		this.render_detailed_tables(data.details);
	}

	render_summary_cards(summary) {
		let $cards_container = $(`
			<div class="dashboard-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
			</div>
		`).appendTo(this.$container);

		const cards = [
			{
				title: 'Opening Stock',
				weight: summary.opening_weight,
				value: summary.opening_value,
				icon: 'fa-database',
				color: '#6c757d'
			},
			{
				title: 'Total IN',
				weight: summary.total_in_weight,
				value: summary.total_in_value,
				icon: 'fa-arrow-down',
				color: '#28a745'
			},
			{
				title: 'Total OUT',
				weight: summary.total_out_weight,
				value: summary.total_out_value,
				icon: 'fa-arrow-up',
				color: '#dc3545'
			},
			{
				title: 'Closing Stock',
				weight: summary.closing_weight,
				value: summary.closing_value,
				icon: 'fa-check-circle',
				color: '#007bff'
			},
			{
				title: 'Net Movement',
				weight: summary.net_weight,
				value: summary.net_value,
				icon: 'fa-exchange',
				color: summary.net_weight >= 0 ? '#28a745' : '#dc3545'
			}
		];

		cards.forEach(card => {
			let $card = $(`
				<div class="summary-card" style="background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid ${card.color};">
					<div style="display: flex; justify-content: space-between; align-items: center;">
						<div>
							<div style="color: #6c757d; font-size: 14px; margin-bottom: 8px;">${card.title}</div>
							<div style="font-size: 28px; font-weight: bold; color: ${card.color};">${card.weight.toFixed(2)} <span style="font-size: 16px;">Kg</span></div>
							<div style="font-size: 20px; font-weight: 600; color: ${card.color}; margin-top: 5px;">₹ ${card.value.toFixed(2)}</div>
						</div>
						<div>
							<i class="fa ${card.icon}" style="font-size: 48px; color: ${card.color}; opacity: 0.2;"></i>
						</div>
					</div>
				</div>
			`).appendTo($cards_container);
		});
	}

	render_charts(chart_data) {
		let $charts_container = $(`
			<div class="dashboard-charts" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; margin: 20px 0;">
			</div>
		`).appendTo(this.$container);

		// Daily IN/OUT Weight Chart
		this.render_chart($charts_container, {
			title: 'Daily Stock Movement (Weight)',
			data: chart_data.daily_movement_weight,
			type: 'bar'
		});

		// Daily IN/OUT Value Chart
		this.render_chart($charts_container, {
			title: 'Daily Stock Movement (Value)',
			data: chart_data.daily_movement_value,
			type: 'bar'
		});

		// Balance Trend Chart (Weight and Value)
		this.render_chart($charts_container, {
			title: 'Stock Balance Trend (Weight & Value)',
			data: chart_data.balance_trend,
			type: 'line'
		});

		// Item-wise Distribution (if multiple items)
		if (chart_data.item_distribution && chart_data.item_distribution.labels.length > 1) {
			this.render_chart($charts_container, {
				title: 'Item-wise Distribution (by Weight)',
				data: chart_data.item_distribution,
				type: 'pie'
			});
		}
	}

	render_chart($container, config) {
		let $chart_card = $(`
			<div class="chart-card" style="background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
				<h4 style="margin-bottom: 15px; color: #333;">${config.title}</h4>
				<div class="chart-container"></div>
			</div>
		`).appendTo($container);

		new frappe.Chart($chart_card.find('.chart-container')[0], {
			data: config.data,
			type: config.type,
			height: 250,
			colors: ['#28a745', '#dc3545', '#007bff', '#ffc107', '#6f42c1']
		});
	}

	render_detailed_tables(details) {
		let $tables_container = $(`
			<div class="dashboard-tables" style="margin: 20px 0;">
			</div>
		`).appendTo(this.$container);

		// Top items by weight movement
		if (details.top_items && details.top_items.length > 0) {
			this.render_table($tables_container, 'Top Items by Weight & Value Movement', details.top_items, [
				{ label: 'Item', field: 'item_code' },
				{ label: 'Transactions', field: 'transaction_count' },
				{ label: 'Total Weight (Kg)', field: 'total_weight' },
				{ label: 'Total Value (₹)', field: 'total_value' }
			]);
		}

		// Warehouse-wise summary
		if (details.warehouse_summary && details.warehouse_summary.length > 0) {
			this.render_table($tables_container, 'Warehouse-wise Summary', details.warehouse_summary, [
				{ label: 'Warehouse', field: 'warehouse' },
				{ label: 'IN Weight (Kg)', field: 'in_weight' },
				{ label: 'OUT Weight (Kg)', field: 'out_weight' },
				{ label: 'Balance Weight (Kg)', field: 'balance_weight' },
				{ label: 'IN Value (₹)', field: 'in_value' },
				{ label: 'OUT Value (₹)', field: 'out_value' },
				{ label: 'Balance Value (₹)', field: 'balance_value' }
			]);
		}

		// Recent transactions
		if (details.recent_transactions && details.recent_transactions.length > 0) {
			this.render_table($tables_container, 'Recent Transactions', details.recent_transactions, [
				{ label: 'Date', field: 'posting_date' },
				{ label: 'Type', field: 'transaction_type' },
				{ label: 'Voucher', field: 'voucher_no' },
				{ label: 'Item', field: 'item_code' },
				{ label: 'Weight Change (Kg)', field: 'weight_change' },
				{ label: 'Rate/Kg (₹)', field: 'rate_per_kg' },
				{ label: 'Value (₹)', field: 'value_amount' }
			]);
		}
	}

	render_table($container, title, data, columns) {
		let $table_card = $(`
			<div class="table-card" style="background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
				<h4 style="margin-bottom: 15px; color: #333;">${title}</h4>
				<div class="table-responsive"></div>
			</div>
		`).appendTo($container);

		let $table = $('<table class="table table-bordered table-hover"></table>').appendTo($table_card.find('.table-responsive'));

		// Header
		let $thead = $('<thead style="background: #f8f9fa;"></thead>').appendTo($table);
		let $tr = $('<tr></tr>').appendTo($thead);
		columns.forEach(col => {
			$tr.append(`<th>${col.label}</th>`);
		});

		// Body
		let $tbody = $('<tbody></tbody>').appendTo($table);
		data.forEach(row => {
			let $row = $('<tr></tr>').appendTo($tbody);
			columns.forEach(col => {
				let value = row[col.field];
				if (typeof value === 'number') {
					value = value.toFixed(2);
				}
				$row.append(`<td>${value || ''}</td>`);
			});
		});
	}

	export_dashboard_data() {
		frappe.msgprint(__('Dashboard data export feature coming soon...'));
	}
}
