# Shiva ERP - Dual UOM Poultry ERP System

## Production Deployment Guide

### Custom Fields Required

Before migrating, create the following **Custom Fields** via ERPNext UI or fixtures:

#### Purchase Receipt Item (purchase_receipt_item)
- `custom_total_weight_kg` (Float, Label: "Total Weight (Kg)", Precision: 3)
- `custom_bird_weights_json` (JSON, Label: "Individual Bird Weights")

#### Delivery Note Item (delivery_note_item)
- `custom_total_weight_kg` (Float, Label: "Total Weight (Kg)", Precision: 3)
- `custom_bird_weights_json` (JSON, Label: "Individual Bird Weights")

#### Sales Invoice Item (sales_invoice_item)
- `custom_total_weight_kg` (Float, Label: "Total Weight (Kg)", Precision: 3)
- `custom_price_type` (Select, Label: "Price Type", Options: "Wholesale\nRetail\nPremium\nBulk")
- `custom_base_price_per_kg` (Currency, Label: "Base Price/Kg", Read Only)
- `custom_discount_per_kg` (Currency, Label: "Discount/Kg", Read Only)

### Deployment Steps

```bash
# 1. Pull latest code
cd /workspace/frappe-bench
git pull

# 2. Install/Update app
bench --site erpnext.site install-app shiva_erp
# OR if already installed:
bench --site erpnext.site migrate

# 3. Clear cache
bench --site erpnext.site clear-cache

# 4. Rebuild assets
bench build

# 5. Restart processes
bench restart
```

### Database Migration

The following new DocTypes will be created:
1. **Stock Weight Ledger** (Enhanced with dual UOM)
2. **Shop Price Master** (New)

Reports created:
1. **Stock Balance Dual UOM**
2. **Shop Sales Analysis**

### Post-Deployment Configuration

#### 1. Set up Shop Price Master

Create price records for each shop/area/item combination:

```python
# Via bench console
bench --site erpnext.site console

# Create sample price
frappe.get_doc({
    "doctype": "Shop Price Master",
    "shop": "SHOP-001",  # Customer code
    "area": "Mumbai",    # Territory
    "price_type": "Wholesale",
    "item_code": "Broiler Chicken",
    "price_per_kg": 150.00,
    "discount_inr": 5.00,
    "is_active": 1
}).insert()

frappe.db.commit()
```

#### 2. Permissions

Ensure the following roles have appropriate permissions:
- **Stock Manager**: Full access to Stock Weight Ledger
- **Stock User**: Read-only access to Stock Weight Ledger
- **Sales Manager**: Full access to Shop Price Master
- **Sales User**: Read-only access to Shop Price Master

#### 3. Enable Developer Mode (for testing)

```json
// sites/erpnext.site/site_config.json
{
  "developer_mode": 1,
  "live_reload": true
}
```

### Testing Checklist

- [ ] Create Purchase Receipt with `custom_total_weight_kg`
- [ ] Verify Stock Weight Ledger entry created with IN transaction
- [ ] Check Stock Balance Dual UOM report shows correct balance
- [ ] Create Shop Price Master for test customer
- [ ] Create Sales Invoice - verify shop pricing applied
- [ ] Verify Stock Weight Ledger entry created with OUT transaction
- [ ] Cancel Sales Invoice - verify ledger entries reversed
- [ ] Test individual bird weights JSON feature
- [ ] Run unit tests: `cd apps/shiva_erp && python -m pytest`

### Troubleshooting

#### Issue: Custom fields not appearing

Solution:
```bash
bench --site erpnext.site clear-cache
bench --site erpnext.site reload-doc erpnext "purchase receipt item"
bench --site erpnext.site reload-doc erpnext "sales invoice item"
bench --site erpnext.site reload-doc erpnext "delivery note item"
```

#### Issue: Stock Weight Ledger not updating

1. Check hooks.py is properly configured
2. Verify custom fields exist in database
3. Check server logs: `tail -f sites/erpnext.site/logs/erpnext-web.log`

#### Issue: Shop pricing not applied

1. Ensure Shop Price Master record exists for customer/area/item
2. Check validity dates (valid_from, valid_till)
3. Verify is_active = 1
4. Check ERPNext error logs

### Performance Optimization

For large inventories:

1. **Index Stock Weight Ledger**:
```sql
CREATE INDEX idx_item_warehouse ON `tabStock Weight Ledger` (item_code, warehouse);
CREATE INDEX idx_posting_date ON `tabStock Weight Ledger` (posting_date);
```

2. **Archive old ledger entries** (older than 2 years):
```python
# Via bench console
frappe.db.sql("""
    DELETE FROM `tabStock Weight Ledger`
    WHERE posting_date < DATE_SUB(NOW(), INTERVAL 2 YEAR)
""")
frappe.db.commit()
```

### Monitoring

Track these metrics:
- Stock Weight Ledger entry count (should grow with transactions)
- Average weight per bird (typical: 1.2-1.8 kg)
- Shop discount utilization rate
- Report generation time

### Support

For issues or questions, contact:
- Developer: Gopalakrishna Reddy Gogulamudi
- Email: ggkr565457123@gmail.com
