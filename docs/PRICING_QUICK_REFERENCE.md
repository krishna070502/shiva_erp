# Quick Reference: New Pricing System

## Daily Price Update (Most Common Task)

### Update All Wholesale Prices by 3%

**Method 1: Using Bulk Update Utility (Recommended)**
```python
# From bench console
bench --site erpnext.site console

# In Python console
from shiva_erp.bulk_pricing_utils import bulk_update_price_by_type

bulk_update_price_by_type(
    price_type="Wholesale",
    percentage_change=3.0,
    absolute_change=0.0
)
```

**Method 2: Using Item Price Type Bulk Update Dialog**
1. Navigate to: **Item Price Type** list
2. Filter: `Price Type = Wholesale`
3. Click any record → **Bulk Update Base Price** button
4. Enter: `New Base Price per Kg` OR `Percentage Change`
5. Click **Update**

### Update Specific Item Price

1. Go to **Item Price Type** list
2. Filter: `Item Code = Broiler Chicken`, `Price Type = Wholesale`
3. Click to open record
4. Edit `Base Price per Kg`
5. Save

**Effect**: All shops using "Wholesale" price type get new price immediately

## Shop-Specific Discounts

### Add Discount for One Shop

1. Go to **Shop Discount** list
2. Click **New**
3. Fill:
   - Shop: Select customer
   - Item Code: Select item
   - Discount per Kg: Enter amount (e.g., 10.00)
   - Valid From/Till: Optional
   - Is Active: Check
4. Save

### Bulk Update Discounts for Multiple Shops

```python
# From bench console
from shiva_erp.bulk_pricing_utils import bulk_update_shop_discounts

# Update all discounts for one shop
bulk_update_shop_discounts(
    shop="Shop XYZ",
    item_codes=None,  # All items
    new_discount=15.00
)

# Update discount for specific item across all shops
bulk_update_shop_discounts(
    shop=None,  # All shops
    item_codes=["Broiler Chicken"],
    percentage_change=10.0  # Increase discount by 10%
)
```

## Sales Invoice Pricing (Automatic)

When creating a Sales Invoice:

1. Select **Customer** (shop)
2. Add **Item**
3. Enter **Qty** (Nos) and **Total Weight Kg** in custom fields
4. Select **Price Type** (Wholesale/Retail/Premium/Bulk)
5. System automatically:
   - Fetches base_price from Item Price Type
   - Fetches discount from Shop Discount
   - Calculates: `effective_price = base_price - discount`
   - Populates `Rate` and `Amount`

**Custom Fields on Sales Invoice Item**:
- `custom_price_type`: Price type for this item
- `custom_total_weight_kg`: Total weight in kg
- `custom_base_price_per_kg`: Auto-filled base price
- `custom_discount_per_kg`: Auto-filled discount
- `Rate`: Effective price per kg (base - discount)
- `Amount`: Rate × Weight

## Common Scenarios

### Scenario 1: Daily Market Price Update

**Old Way** (100 shops):
- Update Shop Price Master for Shop 1 → 20 items
- Update Shop Price Master for Shop 2 → 20 items
- ... repeat 100 times
- Total: 2,000 updates ❌

**New Way**:
- Bulk update Item Price Type for Wholesale → 20 items
- Done! All 100 wholesale shops updated automatically
- Total: 20 updates ✅

### Scenario 2: New Customer with Special Discount

**Steps**:
1. Customer exists in ERPNext (created as usual)
2. Create Shop Discount records for items they buy
3. Set discount amount (e.g., ₹12/kg for bulk buyer)
4. When creating Sales Invoice, system uses:
   - Base price from Item Price Type (same as other shops)
   - Minus special discount (₹12/kg)

### Scenario 3: Promotional Discount

**Option A: Temporary Shop Discount**
1. Create Shop Discount with validity dates
2. Set discount amount
3. After promotion ends, discount automatically expires

**Option B: Promotional Price Type**
1. Create new Item Price Type records with `Price Type = "Promotional"`
2. Set lower base price
3. Use "Promotional" price type in Sales Invoices during promotion
4. After promotion, deactivate promotional price types

### Scenario 4: Area-Based Pricing

**Current Architecture**: Base price is NOT area-specific

**Workaround**:
- Option 1: Create price types like "Wholesale-North", "Wholesale-South"
- Option 2: Use Shop Discount for area-wide adjustments
  ```python
  # Give all shops in Area X a ₹5 discount
  shops_in_area = frappe.get_all("Customer", filters={"territory": "Area X"}, pluck="name")
  for shop in shops_in_area:
      bulk_update_shop_discounts(shop=shop, new_discount=5.00)
  ```

## Price History & Audit

### View Price Change History

**For Item Price Type**:
1. Open Item Price Type record
2. Click **Version History** or use:
   ```python
   from shiva_erp.bulk_pricing_utils import get_price_history
   get_price_history("Item Price Type", "IPT-Broiler Chicken-Wholesale-0001")
   ```

**For Shop Discount**:
1. Open Shop Discount record
2. Click **Version History** or use:
   ```python
   get_price_history("Shop Discount", "SD-Shop XYZ-Broiler Chicken-0001")
   ```

### Pricing Dashboard

```python
from shiva_erp.bulk_pricing_utils import get_pricing_dashboard_data

data = get_pricing_dashboard_data()
# Returns:
# - Total base prices count
# - Total shop discounts count
# - Counts by price type
# - Average prices by price type
# - Recent changes
```

## Troubleshooting

### "No base price found" on Sales Invoice

**Cause**: No active Item Price Type for selected item + price_type

**Fix**:
1. Go to Item Price Type
2. Create new record:
   - Item Code: [missing item]
   - Price Type: [selected price type]
   - Base Price per Kg: [market price]
   - Is Active: Yes

### Effective Price is Negative

**Cause**: Discount exceeds base price

**Fix**: System automatically sets effective price to 0, but review:
- Is the base price correct?
- Is the shop discount too high?

### Pricing Not Applied on Sales Invoice

**Cause**: Pricing hook not running

**Check**:
1. Is `custom_total_weight_kg` filled? (Required for pricing)
2. Is `custom_price_type` selected? (Defaults to "Wholesale")
3. Check hooks registration in `hooks.py`:
   ```python
   doc_events = {
       "Sales Invoice": {
           "on_submit": "shiva_erp.sales_integration.sales_invoice_on_submit",
           "validate": "shiva_erp.sales_integration.sales_invoice_validate",
       }
   }
   ```

## API Reference

### Get Base Price
```python
from shiva_erp.shiva_business_erp.doctype.item_price_type.item_price_type import get_base_price

price = get_base_price(
    item_code="Broiler Chicken",
    price_type="Wholesale",
    posting_date=None  # Defaults to today
)
# Returns: float (e.g., 150.00)
```

### Get Shop Discount
```python
from shiva_erp.shiva_business_erp.doctype.shop_discount.shop_discount import get_shop_discount

discount = get_shop_discount(
    shop="Shop XYZ",
    item_code="Broiler Chicken",
    posting_date=None  # Defaults to today
)
# Returns: float (e.g., 10.00) or 0 if no discount
```

### Get Combined Price Details
```python
from shiva_erp.sales_integration import get_stock_and_price_details

result = get_stock_and_price_details(
    customer="Shop XYZ",
    item_code="Broiler Chicken",
    warehouse="Main Warehouse",
    qty=100,
    price_type="Wholesale"
)
# Returns:
# {
#     "stock_balance": {"stock_qty": 500, "weight_kg": 1250},
#     "price_data": {
#         "base_price_per_kg": 150.00,
#         "discount_per_kg": 10.00,
#         "effective_price_per_kg": 140.00,
#         "price_type": "Wholesale"
#     }
# }
```

## Migration from Old System

**Status**: Migration script ready at `shiva_erp/migrations/migrate_pricing.py`

**Run Migration**:
```bash
# 1. Backup database
bench --site erpnext.site backup --with-files

# 2. Set maintenance mode
bench --site erpnext.site set-maintenance-mode on

# 3. Run migration
bench --site erpnext.site execute shiva_erp.migrations.migrate_pricing.migrate_shop_pricing

# 4. Verify results (check output for counts and warnings)

# 5. Exit maintenance mode
bench --site erpnext.site set-maintenance-mode off
```

**What Migration Does**:
- Extracts unique item+price_type combinations → Item Price Type
- Uses AVG(price_per_kg) across shops as base price
- Extracts shop+item discounts → Shop Discount
- Validates effective prices match (±₹1/kg tolerance)
- Preserves old Shop Price Master for reference

## Performance Notes

- **Daily updates**: 100× faster (20 updates vs. 2,000)
- **Query complexity**: Reduced (2 simple lookups vs. 1 complex JOIN)
- **Database locks**: Fewer concurrent writes
- **Sales Invoice creation**: Marginally faster (simpler pricing lookup)

---

**Last Updated**: January 2025  
**For Support**: Contact ERP team or refer to `PRICING_REFACTORING.md`
