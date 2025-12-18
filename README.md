### Shiva Business ERP

Custom App for SHIVA AGROVET (INDIA) PVT LTD - Poultry Industry ERP Solution

## Features

### 🐔 Dual UOM Stock Tracking (Nos + Actual Kg)

Track poultry inventory with both quantity (number of birds) and actual measured weight:
- **Stock Weight Ledger**: Maintains transaction-wise stock movements in dual UOM
- Automatic ledger updates on Purchase Receipt (IN) and Delivery Note (OUT)
- Individual bird weight tracking for batch-level analytics
- Real-time stock balance queries with average weight calculation

**Why not use conversion factors?** Each bird has variable weight, making fixed conversion factors inaccurate for poultry business.

### 💰 Shop-wise Pricing & Area-based Discounts

Flexible pricing system for different shops and territories:
- **Shop Price Master**: Configure prices by shop, area, item, and price type
- Area-wise price types (Wholesale, Retail, Premium, Bulk)
- Shop-specific discounts (INR per kg)
- Automatic price lookup on Sales Invoice creation
- Bulk price update utilities
- Validity period management for seasonal pricing

### 📊 Reports & Analytics

Production-ready reports with visual analytics:

#### **1. Stock Weight Ledger Detailed Report** ⭐ NEW
Transaction-level detail with comprehensive analytics:
- **17 Summary Cards**: Opening, IN, OUT, Closing, Net Movement, Averages
- **Interactive Charts**: Daily movement visualization (bar + line charts)
- **Running Balance**: Real-time balance after each transaction
- **Advanced Filters**: Period, Warehouse, Item, Transaction Type, Batch
- **Color-coded UI**: Green IN ⬇, Red OUT ⬆, Bold balances
- **Action Buttons**: Export, Batch Analysis, Stock Reconciliation
- **Enhanced Formatting**: Icons, badges, hover effects

#### **2. Stock Ledger Dashboard** ⭐ NEW
Visual dashboard with cards and charts:
- **6 Summary Cards**: Large visual cards with icons (Opening, IN, OUT, Closing, Net, Avg Weight)
- **4 Interactive Charts**: 
  - Daily Movement (Quantity) - Bar chart
  - Daily Movement (Weight) - Bar chart
  - Balance Trend - Line chart
  - Item Distribution - Pie chart
- **3 Detailed Tables**:
  - Top Items by Movement
  - Warehouse-wise Summary
  - Recent Transactions (Last 20)
- **Dynamic Filters**: Real-time updates on filter change
- **Responsive Design**: Mobile-optimized cards and charts

#### **3. Stock Balance Dual UOM**
Current stock summary in Nos and Kg by item/warehouse/batch

#### **4. Shop Sales Analysis**
Revenue, discounts, and quantity sold by shop/area

### 🔧 ERPNext Integration

Seamless integration with standard ERPNext modules:
- Purchase Receipt → Auto-create Stock Weight Ledger (IN)
- Delivery Note → Auto-create Stock Weight Ledger (OUT)
- Sales Invoice → Apply shop pricing + update stock ledger
- Stock availability validation before delivery
- Automatic reversal on cancellation

## Architecture

### Custom DocTypes

1. **Stock Weight Ledger** (`shiva_business_erp/doctype/stock_weight_ledger/`)
   - Fields: transaction_type, posting_date, voucher_type, voucher_no, item_code, warehouse, batch_no, stock_qty, weight_kg, avg_weight_per_bird, weights_list
   - Auto-calculates: weight_change, qty_change, avg_weight_per_bird
   - Validations: positive values, transaction_type IN/OUT, individual weights sum

2. **Shop Price Master** (`shiva_business_erp/doctype/shop_price_master/`)
   - Fields: shop (Customer), area (Territory), price_type, item_code, price_per_kg, discount_inr, effective_price_per_kg, validity dates
   - Validations: discount ≤ price, unique shop+area+item+price_type, validity date range
   - Features: Bulk price updates, price lookup API

### Custom Fields Required

**Purchase Receipt Item & Delivery Note Item:**
- `custom_total_weight_kg` (Float): Total weight for the line item

**Sales Invoice Item:**
- `custom_total_weight_kg` (Float): Total weight for billing
- `custom_price_type` (Select): Wholesale/Retail/Premium/Bulk
- `custom_base_price_per_kg` (Currency): Base price before discount
- `custom_discount_per_kg` (Currency): Discount applied

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app shiva_erp
```

After installation, create custom fields (see DEPLOYMENT.md for details).

### Configuration

1. **Create Shop Price Master records** for each shop/area/item combination
2. **Configure permissions** for Stock Manager, Sales Manager roles
3. **Set up territories** representing delivery areas
4. **Enable developer mode** for testing (optional)

See `DEPLOYMENT.md` for detailed production deployment guide.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/shiva_erp
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff (Python linting/formatting, line length: 110)
- eslint (JavaScript linting)
- prettier (JavaScript/Vue/SCSS formatting)

### Testing

Run unit tests:

```bash
cd apps/shiva_erp
python -m pytest

# OR via bench
bench --site erpnext.site run-tests --app shiva_erp
```

### CI/CD

This app uses GitHub Actions for CI:

- **CI Workflow**: Installs app and runs unit tests on every push to `main` branch
- **Linter Workflow**: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request

### Business Logic Highlights

#### Stock Movement Flow
```
Purchase Receipt (Submit)
  ↓
Stock Weight Ledger (IN: +Qty, +Weight)
  ↓
Stock Balance Updated

Delivery Note / Sales Invoice (Submit)
  ↓
Stock Availability Check
  ↓
Shop Price Lookup (Shop + Area + Item + Price Type)
  ↓
Apply Discount (price_per_kg - discount_inr)
  ↓
Calculate Amount (effective_price × weight_kg)
  ↓
Stock Weight Ledger (OUT: -Qty, -Weight)
  ↓
Stock Balance Updated
```

#### Pricing Calculation
```
Base Price per Kg: ₹150.00
Shop Discount:      ₹5.00
─────────────────────────────
Effective Price:    ₹145.00

Total Weight:       10.5 kg
─────────────────────────────
Invoice Amount:     ₹1,522.50
```

### Key Constraints

- **Never use conversion factors**: Weight is always actual measured weight per transaction
- **Dual UOM everywhere**: All stock reports and queries show both Nos and Kg
- **Billing by weight**: Sales invoices calculate amount as `effective_price_per_kg × weight_kg`
- **No core modifications**: All customizations via hooks, custom fields, and custom app

### Roadmap

- [ ] Mobile app integration for weighbridge data capture
- [ ] Batch expiry tracking with FIFO/FEFO logic
- [ ] Price trend analytics and forecasting
- [ ] Supplier performance tracking based on average bird weight
- [ ] WhatsApp notifications for shop orders and deliveries

### License

agpl-3.0

