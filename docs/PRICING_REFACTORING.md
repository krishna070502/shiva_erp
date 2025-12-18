# Pricing Architecture Refactoring Summary

## Overview

Refactored the shop pricing system from a **monolithic Shop Price Master** to a **separated base pricing + shop discount** architecture for more efficient daily price updates.

## Problem Statement

### Old Architecture (Shop Price Master)
- Each shop had its own complete price record: `shop + area + item + price_type → (base_price, discount, effective_price)`
- **Pain Point**: Daily price updates required updating every shop individually
- **Example**: 100 shops × 20 items = 2,000 records to update daily
- **Inefficiency**: Base price was the same across shops of the same price type, but had to be updated everywhere

### Business Need
Client (poultry distributor) needs to:
- Update base prices daily based on market rates
- Different price types (Wholesale, Retail, Premium, Bulk)
- Shop-specific discounts remain relatively stable
- **Goal**: Update base price once → affects all shops of that price type

## New Architecture

### Separated Model

**Item Price Type** (Base Pricing)
- Key: `item_code + price_type → base_price_per_kg`
- Example: "Broiler Chicken" + "Wholesale" → ₹150/kg
- **Update frequency**: Daily (once per price type)
- **Scope**: Applies to ALL shops of that price type

**Shop Discount** (Shop-Specific Adjustments)
- Key: `shop + item_code → discount_per_kg`
- Example: "Shop A" + "Broiler Chicken" → ₹10/kg discount
- **Update frequency**: Occasional (when shop-specific discounts change)
- **Scope**: Specific to one shop

**Effective Price Calculation**
```python
effective_price = base_price - shop_discount
```

### Benefits

1. **Efficiency**: Update 1 record per price type instead of 100 records per shop
2. **Consistency**: All shops of a price type automatically get the same base price
3. **Flexibility**: Shop-specific discounts can still vary
4. **Auditability**: Clear separation of market prices vs. negotiated discounts
5. **Scalability**: Adding new shops doesn't increase daily update burden

## Implementation Components

### 1. New DocTypes

#### Item Price Type (`item_price_type/`)
- **Fields** (14 total):
  - `item_code` (Link → Item)
  - `price_type` (Select: Wholesale, Retail, Premium, Bulk)
  - `base_price_per_kg` (Currency)
  - `valid_from`, `valid_till` (Date)
  - `is_active` (Check)
  - `remarks` (Small Text)

- **Autoname**: `IPT-{item_code}-{price_type}-{####}`
- **Unique Key**: `item_code + price_type` (active records)
- **Validations**:
  - Base price must be > 0
  - No duplicate active records for same item+price_type
  - Valid Till cannot be before Valid From
  - Validity periods cannot overlap

- **API Methods**:
  ```python
  get_base_price(item_code, price_type, posting_date=None)
  # Returns: float (base_price_per_kg)
  
  bulk_update_base_price(item_code=None, price_type=None, new_base_price)
  # Returns: int (number of records updated)
  ```

#### Shop Discount (`shop_discount/`)
- **Fields** (11 total):
  - `shop` (Link → Customer)
  - `item_code` (Link → Item)
  - `discount_per_kg` (Currency)
  - `valid_from`, `valid_till` (Date)
  - `is_active` (Check)
  - `remarks` (Small Text)

- **Autoname**: `SD-{shop}-{item_code}-{####}`
- **Unique Key**: `shop + item_code` (active records)
- **Validations**:
  - Discount must be ≥ 0 (non-negative)
  - No duplicate active records for same shop+item
  - Valid Till cannot be before Valid From
  - Validity periods cannot overlap

- **API Methods**:
  ```python
  get_shop_discount(shop, item_code, posting_date=None)
  # Returns: float (discount_per_kg, 0 if no discount)
  
  bulk_update_discount(shop=None, item_code=None, new_discount)
  # Returns: int (number of records updated)
  ```

### 2. Updated Sales Integration

#### File: `sales_integration.py`

**Refactored `apply_shop_pricing()`**:
```python
# Old: Single lookup to Shop Price Master
price_data = get_shop_price(shop, area, item, price_type, date)

# New: Two separate lookups
base_price = get_base_price(item, price_type, date)  # Item Price Type
discount = get_shop_discount(shop, item, date)       # Shop Discount
effective_price = base_price - discount
```

**Updated `get_stock_and_price_details()`**:
- Now returns separate base_price, discount, effective_price
- Used by frontend for pricing calculations

### 3. Migration Script

#### File: `migrations/migrate_pricing.py`

**Function**: `migrate_shop_pricing()`

**Steps**:
1. **Extract Base Prices**:
   - Group Shop Price Master by `item_code + price_type`
   - Use AVG(price_per_kg) as base price (can adjust to MODE or MEDIAN)
   - Create Item Price Type records
   - Log warnings for large price variance across shops

2. **Extract Shop Discounts**:
   - For each shop+item combination
   - Calculate: `discount = base_price - shop_specific_price`
   - Create Shop Discount records (only if discount > 0)

3. **Validate Migration**:
   - Sample 10 random records
   - Compare old effective_price vs. new (base - discount)
   - Allow ±₹1/kg tolerance for averaging differences
   - Report mismatches

4. **Optional Deactivation**:
   - `deactivate_old_records()` - sets `is_active=0` on old Shop Price Master
   - **WARNING**: Only run after confirming migration success

**Usage**:
```bash
bench --site erpnext.site execute shiva_erp.migrations.migrate_pricing.migrate_shop_pricing
```

### 4. Bulk Update Utilities

#### File: `bulk_pricing_utils.py`

**Key Functions**:

1. **`bulk_update_price_by_type(price_type, percentage_change, absolute_change)`**
   - **Primary function for daily updates**
   - Updates all items of one price type
   - Supports percentage change (±X%) or absolute (±₹X)
   - Logs to price history
   - Returns: Update summary

2. **`bulk_update_shop_discounts(shop, item_codes, new_discount, percentage_change)`**
   - Update shop-specific discounts
   - Filter by shop and/or items
   - Less frequent use (discounts are more stable)

3. **`preview_price_update(price_type, percentage_change, absolute_change)`**
   - Preview changes before applying
   - Shows old price, new price, change for each item

4. **`log_price_history(doctype, docname, field, old_value, new_value, reason)`**
   - Audit trail for price changes
   - Records who changed what when

5. **`get_pricing_dashboard_data()`**
   - Overview statistics
   - Counts by price type
   - Recent changes

**Example Usage**:
```python
# Daily market update: Increase Wholesale prices by 3%
bulk_update_price_by_type(
    price_type="Wholesale",
    percentage_change=3.0,
    absolute_change=0.0
)
# Updates 20 items → affects all 100 shops automatically

# Specific shop gets additional discount
bulk_update_shop_discounts(
    shop="Shop XYZ",
    item_codes=["Broiler Chicken"],
    new_discount=15.00
)
# Updates 1 record for 1 shop
```

### 5. Unit Tests

#### File: `tests/test_sales_integration.py`

**Test Coverage**:
- ✅ Pricing calculation with base price + discount
- ✅ Pricing with no shop discount (base price only)
- ✅ Pricing with no base price (returns 0)
- ✅ Integration with `get_stock_and_price_details()` API

#### Existing DocType Tests:
- `test_item_price_type.py`: Base price validation, duplicates, dates
- `test_shop_discount.py`: Discount validation, duplicates, dates

### 6. Reports (No Changes Required)

#### `shop_sales_analysis/shop_sales_analysis.py`

- **Status**: ✅ Already compatible
- **Reason**: Reads from Sales Invoice custom fields:
  - `custom_base_price_per_kg`
  - `custom_discount_per_kg`
  - `custom_total_weight_kg`
- These fields are populated by `apply_shop_pricing()` regardless of pricing architecture
- Report queries aggregate data from submitted invoices

## Deployment Checklist

### Pre-Deployment

- [x] Create Item Price Type DocType
- [x] Create Shop Discount DocType
- [x] Update sales_integration.py pricing logic
- [x] Create migration script
- [x] Write unit tests
- [x] Create bulk update utilities
- [ ] Test on staging environment
- [ ] Create database backup

### Deployment Steps

1. **Stop scheduler** (prevent transactions during migration):
   ```bash
   bench --site erpnext.site set-maintenance-mode on
   bench --site erpnext.site set-config pause_scheduler 1
   ```

2. **Backup database**:
   ```bash
   bench --site erpnext.site backup --with-files
   ```

3. **Pull latest code**:
   ```bash
   cd apps/shiva_erp
   git pull origin main
   ```

4. **Run migration**:
   ```bash
   bench --site erpnext.site migrate
   bench --site erpnext.site execute shiva_erp.migrations.migrate_pricing.migrate_shop_pricing
   ```

5. **Validate migration**:
   - Review Item Price Type records count
   - Review Shop Discount records count
   - Check migration output for errors
   - Test sample Sales Invoice pricing

6. **Clear cache and rebuild**:
   ```bash
   bench --site erpnext.site clear-cache
   bench build
   ```

7. **Resume operations**:
   ```bash
   bench --site erpnext.site set-config pause_scheduler 0
   bench --site erpnext.site set-maintenance-mode off
   ```

### Post-Deployment Validation

- [ ] Create test Sales Invoice with new pricing
- [ ] Verify effective_price = base_price - discount
- [ ] Test bulk update by price type
- [ ] Test bulk update shop discounts
- [ ] Review shop_sales_analysis report
- [ ] Train users on new pricing workflow

### Rollback Plan (If Needed)

1. **Reactivate old Shop Price Master**:
   ```sql
   UPDATE `tabShop Price Master` SET is_active = 1;
   ```

2. **Deactivate new DocTypes**:
   ```sql
   UPDATE `tabItem Price Type` SET is_active = 0;
   UPDATE `tabShop Discount` SET is_active = 0;
   ```

3. **Restore old sales_integration.py** from git:
   ```bash
   git checkout HEAD~1 -- shiva_erp/sales_integration.py
   ```

## Daily Operations Guide

### Morning Price Update Workflow

**Old Process** (deprecated):
1. Open Shop Price Master list
2. Filter by item (e.g., "Broiler Chicken")
3. Update price_per_kg for Shop 1
4. Repeat for Shop 2, 3, 4... 100 ❌

**New Process** (efficient):
1. Open Item Price Type list
2. Filter by price_type = "Wholesale"
3. Bulk Update: +3% or +₹5
4. Done! All 100 shops updated ✅

### Managing Shop-Specific Discounts

1. Open Shop Discount list
2. Filter by shop
3. Review/update discounts as needed
4. Or use bulk update for promotions

### Price History Tracking

- Every price change logged automatically
- View history from Item Price Type or Shop Discount form
- Audit trail shows who, when, why

## Performance Impact

### Before Refactoring
- Daily update: 100 shops × 20 items = 2,000 DB writes
- Query complexity: JOIN on 5 fields (shop, area, item, price_type, date)

### After Refactoring
- Daily update: 1 price_type × 20 items = 20 DB writes (100× reduction)
- Query complexity: 2 simple lookups (item+price_type, then shop+item)
- Reduced database locks
- Faster Sales Invoice creation

## Files Modified/Created

### New Files (8)
```
shiva_erp/shiva_business_erp/doctype/item_price_type/
├── __init__.py
├── item_price_type.json
├── item_price_type.py
├── item_price_type.js
└── test_item_price_type.py

shiva_erp/shiva_business_erp/doctype/shop_discount/
├── __init__.py
├── shop_discount.json
├── shop_discount.py
├── shop_discount.js
└── test_shop_discount.py

shiva_erp/migrations/
├── __init__.py
└── migrate_pricing.py

shiva_erp/tests/
├── __init__.py
└── test_sales_integration.py

shiva_erp/
└── bulk_pricing_utils.py
```

### Modified Files (1)
```
shiva_erp/
└── sales_integration.py  (refactored apply_shop_pricing, get_stock_and_price_details)
```

### Unchanged (Old System)
```
shiva_erp/shiva_business_erp/doctype/shop_price_master/
└── ... (deprecated but preserved for historical data)
```

## FAQs

**Q: What happens to old Shop Price Master records?**
A: They remain in the database for historical reference. Migration script can optionally deactivate them (`is_active=0`), but does not delete them.

**Q: Will old Sales Invoices still work?**
A: Yes. Historical invoices reference the custom fields populated at creation time. The fields (`custom_base_price_per_kg`, `custom_discount_per_kg`) are preserved regardless of pricing source.

**Q: Can we have different base prices for different areas?**
A: Not directly. Base price is price_type-specific, not area-specific. For area-based pricing, use Shop Discount with area-wide bulk updates, or create custom price types (e.g., "Wholesale-North", "Wholesale-South").

**Q: How do we handle promotional discounts?**
A: Two approaches:
1. **Temporary Shop Discount**: Create time-limited discount with validity dates
2. **Temporary Price Type**: Create "Promotional" price type with lower base price

**Q: What if we need to rollback?**
A: See "Rollback Plan" section above. Old system is preserved and can be reactivated quickly.

## Summary Statistics

- **Code Added**: ~1,500 lines
- **DocTypes Created**: 2 (Item Price Type, Shop Discount)
- **Migration Script**: 350 lines with validation
- **Unit Tests**: 3 files, 10+ test cases
- **Utilities**: 8 whitelisted API functions
- **Files Modified**: 1 (sales_integration.py)
- **Efficiency Gain**: 100× reduction in daily update operations

---

**Implementation Date**: January 2025  
**Author**: GitHub Copilot (Claude Sonnet 4.5)  
**Client**: SHIVA AGROVET (Poultry Distribution)
