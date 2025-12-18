# Quick Start Guide - Shiva ERP Development

## Overview

Shiva ERP is a dual-UOM poultry inventory and sales management system built on Frappe/ERPNext.

## Key Features

1. **Dual UOM Tracking**: Stock in both Nos (quantity) and Kg (actual weight)
2. **Shop Pricing**: Area-based pricing with shop-specific discounts
3. **Weight-based Billing**: Invoice amount = effective_price_per_kg × weight_kg
4. **Stock Integration**: Auto-update ledger on Purchase/Sales transactions

## Development Workflow

### 1. Start Development Server

```bash
cd /workspace/frappe-bench
bench start
```

Access UI at: http://localhost:8000

### 2. Make Code Changes

Example: Modify Stock Weight Ledger validation

```bash
# Edit Python controller
code apps/shiva_erp/shiva_erp/shiva_business_erp/doctype/stock_weight_ledger/stock_weight_ledger.py

# Edit client script
code apps/shiva_erp/shiva_erp/shiva_business_erp/doctype/stock_weight_ledger/stock_weight_ledger.js
```

### 3. Apply Changes

```bash
# Clear cache
bench --site erpnext.site clear-cache

# Rebuild JS/CSS
bench build

# Migrate database (if schema changed)
bench --site erpnext.site migrate
```

### 4. Test Changes

```bash
# Run unit tests
cd apps/shiva_erp
python -m pytest

# Run specific test
python -m pytest shiva_erp/shiva_business_erp/doctype/stock_weight_ledger/test_stock_weight_ledger.py

# Test via bench
bench --site erpnext.site run-tests --app shiva_erp
```

## Creating Custom Fields

Custom fields are required for dual UOM tracking. Create them via:

### Option 1: Via UI

1. Go to **Customize Form**
2. Select DocType (e.g., "Purchase Receipt Item")
3. Add field:
   - Label: "Total Weight (Kg)"
   - Field Name: `custom_total_weight_kg`
   - Field Type: Float
   - Precision: 3

### Option 2: Via Console

```python
bench --site erpnext.site console

# Create custom field
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

create_custom_field("Purchase Receipt Item", {
    "label": "Total Weight (Kg)",
    "fieldname": "custom_total_weight_kg",
    "fieldtype": "Float",
    "precision": 3,
    "insert_after": "qty"
})

frappe.db.commit()
```

## Common Tasks

### Add New Report

1. Create report directory:
```bash
mkdir -p apps/shiva_erp/shiva_erp/shiva_business_erp/report/my_new_report
```

2. Create files:
- `my_new_report.json` (metadata)
- `my_new_report.py` (query logic)
- `__init__.py`

3. Register in hooks.py (optional for custom reports)

### Modify DocType Schema

1. Edit JSON file:
```bash
code apps/shiva_erp/shiva_erp/shiva_business_erp/doctype/stock_weight_ledger/stock_weight_ledger.json
```

2. Apply changes:
```bash
bench --site erpnext.site migrate
bench --site erpnext.site clear-cache
```

### Debug Hooks

Check if hooks are firing:

```python
# Add logging in stock_logic.py
import frappe

def update_weight_ledger(doc, method):
    frappe.log_error(f"Hook fired for {doc.name}", "Stock Logic Debug")
    # ... rest of code
```

View logs:
```bash
tail -f sites/erpnext.site/logs/erpnext-web.log
```

## Testing Scenarios

### Scenario 1: Purchase Receipt Flow

1. Create Purchase Receipt
   - Add item: "Broiler Chicken"
   - Qty: 100 Nos
   - Custom Total Weight: 150 Kg
2. Submit PR
3. Verify Stock Weight Ledger created:
   - Transaction Type: IN
   - Stock Qty: 100
   - Weight Kg: 150
   - Avg Weight: 1.5 kg/bird
4. Check Stock Balance Dual UOM report

### Scenario 2: Shop Pricing Flow

1. Create Shop Price Master:
   - Shop: "ABC Meat Shop"
   - Area: "Mumbai"
   - Item: "Broiler Chicken"
   - Price Type: "Wholesale"
   - Price per Kg: ₹150
   - Discount: ₹5
2. Create Sales Invoice:
   - Customer: "ABC Meat Shop"
   - Item: "Broiler Chicken"
   - Qty: 50 Nos
   - Custom Total Weight: 75 Kg
   - Custom Price Type: "Wholesale"
3. Submit SI
4. Verify:
   - Rate = ₹145 (150 - 5)
   - Amount = ₹10,875 (145 × 75)
   - Stock Weight Ledger shows OUT transaction

### Scenario 3: Stock Validation

1. Create Sales Invoice with qty > available stock
2. Try to submit
3. Should fail with: "Insufficient stock: Required X Nos (Y Kg), Available A Nos (B Kg)"

## Code Patterns

### Create Stock Weight Ledger Entry

```python
ledger = frappe.new_doc("Stock Weight Ledger")
ledger.transaction_type = "IN"  # or "OUT"
ledger.posting_date = frappe.utils.today()
ledger.voucher_type = "Purchase Receipt"
ledger.voucher_no = "PR-0001"
ledger.item_code = "Broiler Chicken"
ledger.warehouse = "Main Store"
ledger.stock_qty = 100
ledger.weight_kg = 150.5
ledger.insert(ignore_permissions=True)
```

### Get Stock Balance

```python
from shiva_erp.shiva_business_erp.doctype.stock_weight_ledger.stock_weight_ledger import get_stock_balance

balance = get_stock_balance("Broiler Chicken", "Main Store")
print(f"Stock: {balance['stock_qty']} Nos, {balance['weight_kg']} Kg")
print(f"Avg: {balance['avg_weight_per_bird']} kg/bird")
```

### Lookup Shop Price

```python
from shiva_erp.shiva_business_erp.doctype.shop_price_master.shop_price_master import get_shop_price

price = get_shop_price(
    shop="ABC Meat Shop",
    area="Mumbai",
    item_code="Broiler Chicken",
    price_type="Wholesale"
)

print(f"Base: ₹{price['price_per_kg']}")
print(f"Discount: ₹{price['discount_inr']}")
print(f"Effective: ₹{price['effective_price_per_kg']}")
```

## Troubleshooting

### Issue: Changes not reflecting

```bash
# Clear all caches
bench --site erpnext.site clear-cache
bench build --force
bench restart
```

### Issue: Migration errors

```bash
# Check migration status
bench --site erpnext.site migrate --skip-failing

# Reset DocType (CAUTION: data loss)
bench --site erpnext.site console
frappe.delete_doc("DocType", "Stock Weight Ledger", force=True)
frappe.db.commit()
```

### Issue: Hooks not firing

1. Check hooks.py syntax
2. Restart bench
3. Verify app installed: `bench --site erpnext.site list-apps`
4. Check error logs

## Best Practices

1. **Always validate input**: Check weight_kg > 0, stock_qty > 0
2. **Use transactions**: Wrap multiple operations in `frappe.db.begin()` / `commit()`
3. **Handle errors gracefully**: Use `frappe.throw()` for validation errors
4. **Log important events**: Use `frappe.log_error()` for debugging
5. **Write tests**: Test both happy path and edge cases
6. **Document code**: Add docstrings for all functions
7. **Follow conventions**: Use snake_case for Python, camelCase for JS

## Resources

- Frappe Documentation: https://frappeframework.com/docs
- ERPNext API: https://docs.erpnext.com/docs/user/manual/en
- Pre-commit hooks: `.pre-commit-config.yaml`
- Test coverage: Run `pytest --cov=shiva_erp`
