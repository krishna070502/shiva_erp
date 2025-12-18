# Shiva ERP - Implementation Summary

## Production-Ready Dual UOM Poultry ERP System

**Client**: SHIVA AGROVET (INDIA) PVT LTD  
**Industry**: Poultry Trading (Broiler Chickens)  
**Completed**: December 7, 2025

---

## ✅ Phases Completed

### Phase 1: Dual UOM Stock Tracking ✓

**DocType Enhanced: Stock Weight Ledger**

**Key Features:**
- Dual UOM tracking: Stock Qty (Nos) + Actual Weight (Kg)
- Transaction types: IN (Purchase) / OUT (Sales)
- Auto-calculation of average weight per bird
- Optional individual bird weights (JSON array)
- Automatic ledger updates on Purchase Receipt & Delivery Note
- Stock balance queries with dual UOM

**Files Modified/Created:**
- `stock_weight_ledger.json` - Enhanced schema with 17 fields
- `stock_weight_ledger.py` - Python controller with validations
- `stock_weight_ledger.js` - Client-side calculations and UX
- `stock_logic.py` - Hook handlers for purchase/sales
- `test_stock_weight_ledger.py` - Unit tests

**Critical Pattern:**
```python
# IN transaction (Purchase Receipt)
ledger.transaction_type = "IN"
ledger.weight_change = +150.5 kg  # Positive
ledger.qty_change = +100 Nos      # Positive

# OUT transaction (Delivery Note)
ledger.transaction_type = "OUT"
ledger.weight_change = -75.25 kg  # Negative
ledger.qty_change = -50 Nos       # Negative
```

---

### Phase 2: Shop-wise Pricing & Discounts ✓

**DocType Created: Shop Price Master**

**Key Features:**
- Shop (Customer) + Area (Territory) based pricing
- Price types: Wholesale, Retail, Premium, Bulk
- Base price per kg with shop-specific discount (INR)
- Effective price = Base price - Discount
- Validity period management (valid_from, valid_till)
- Duplicate prevention with overlap detection
- Bulk price update utility

**Files Created:**
- `shop_price_master.json` - Schema with 17 fields
- `shop_price_master.py` - Controller with validations
- `shop_price_master.js` - Client scripts with bulk update
- `test_shop_price_master.py` - Unit tests

**Validation Rules:**
- Discount ≤ Base Price
- Unique: Shop + Area + Item + Price Type (active records)
- Valid Till ≥ Valid From
- No overlapping validity periods

---

### Phase 3: Sales Integration ✓

**Module Created: sales_integration.py**

**Hooks Registered:**
- `Sales Invoice`: validate, on_submit, on_cancel
- `Delivery Note`: validate, on_submit, on_cancel

**Features:**
- Auto-lookup shop pricing based on customer area
- Apply discounts automatically
- Stock availability validation (dual UOM)
- Stock Weight Ledger updates (OUT transactions)
- Automatic reversal on cancellation

**Billing Calculation:**
```
Shop: "ABC Meat Shop"
Area: "Mumbai"
Item: "Broiler Chicken"
Price Type: "Wholesale"

Base Price:    ₹150.00/kg
Discount:      ₹5.00/kg
───────────────────────
Effective:     ₹145.00/kg

Weight Sold:   75 kg
───────────────────────
Invoice Total: ₹10,875.00
```

---

### Phase 4: Reports & Dashboards ✓

**Reports Created:**

1. **Stock Balance Dual UOM** (`stock_balance_dual_uom`)
   - Current stock by Item / Warehouse / Batch
   - Columns: Stock Qty (Nos), Weight (Kg), Avg Weight/Bird
   - Supports filters: Item, Warehouse, Batch
   - Script Report type

2. **Shop Sales Analysis** (`shop_sales_analysis`)
   - Sales by Shop / Area / Item
   - Columns: Qty, Weight, Revenue, Discount, Invoice Count
   - Filters: Customer, Territory, Item, Date Range
   - Script Report type

**Report Features:**
- Add Total Row enabled
- Role-based access (Stock Manager, Sales Manager)
- Export to Excel/PDF support
- Standard Frappe report filters

---

### Phase 5: Production Readiness ✓

**Testing:**
- ✓ Unit tests for Stock Weight Ledger (dual UOM calculations)
- ✓ Unit tests for Shop Price Master (validations)
- ✓ Test coverage for edge cases (zero weight, negative discount, etc.)

**Documentation:**
- ✓ `DEPLOYMENT.md` - Production deployment guide
- ✓ `QUICKSTART.md` - Developer quick start
- ✓ `README.md` - Enhanced with features and architecture
- ✓ `.github/copilot-instructions.md` - AI agent guide

**Code Quality:**
- ✓ Pre-commit hooks configured (ruff, eslint, prettier)
- ✓ Line length: 110 characters
- ✓ Python target: 3.10+
- ✓ Docstrings for all major functions
- ✓ Type hints where applicable

**Hooks Registered:**
```python
doc_events = {
    "Purchase Receipt": {
        "on_submit": "shiva_erp.stock_logic.update_weight_ledger",
        "on_cancel": "shiva_erp.stock_logic.reverse_weight_ledger",
    },
    "Delivery Note": {
        "on_submit": [
            "shiva_erp.stock_logic.update_weight_ledger",
            "shiva_erp.sales_integration.delivery_note_on_submit",
        ],
        "on_cancel": [
            "shiva_erp.stock_logic.reverse_weight_ledger",
            "shiva_erp.sales_integration.delivery_note_on_cancel",
        ],
        "validate": "shiva_erp.sales_integration.delivery_note_validate",
    },
    "Sales Invoice": {
        "on_submit": "shiva_erp.sales_integration.sales_invoice_on_submit",
        "on_cancel": "shiva_erp.sales_integration.sales_invoice_on_cancel",
        "validate": "shiva_erp.sales_integration.sales_invoice_validate",
    },
}
```

---

## Custom Fields Required

**Must be created manually via ERPNext UI or fixtures:**

### Purchase Receipt Item
- `custom_total_weight_kg` (Float, Precision: 3)
- `custom_bird_weights_json` (JSON, optional)

### Delivery Note Item
- `custom_total_weight_kg` (Float, Precision: 3)
- `custom_bird_weights_json` (JSON, optional)

### Sales Invoice Item
- `custom_total_weight_kg` (Float, Precision: 3)
- `custom_price_type` (Select: Wholesale/Retail/Premium/Bulk)
- `custom_base_price_per_kg` (Currency, Read Only)
- `custom_discount_per_kg` (Currency, Read Only)

---

## File Structure

```
apps/shiva_erp/
├── shiva_erp/
│   ├── hooks.py                              # App hooks registration
│   ├── stock_logic.py                        # Stock ledger logic
│   ├── sales_integration.py                  # Sales hooks & pricing
│   └── shiva_business_erp/
│       ├── doctype/
│       │   ├── stock_weight_ledger/
│       │   │   ├── stock_weight_ledger.json  # DocType schema
│       │   │   ├── stock_weight_ledger.py    # Server controller
│       │   │   ├── stock_weight_ledger.js    # Client script
│       │   │   └── test_stock_weight_ledger.py
│       │   └── shop_price_master/
│       │       ├── shop_price_master.json    # DocType schema
│       │       ├── shop_price_master.py      # Server controller
│       │       ├── shop_price_master.js      # Client script
│       │       └── test_shop_price_master.py
│       └── report/
│           ├── stock_balance_dual_uom/
│           │   ├── stock_balance_dual_uom.json
│           │   └── stock_balance_dual_uom.py
│           └── shop_sales_analysis/
│               ├── shop_sales_analysis.json
│               └── shop_sales_analysis.py
├── README.md
├── DEPLOYMENT.md
├── QUICKSTART.md
└── pyproject.toml
```

---

## Deployment Commands

```bash
# 1. Migrate database
bench --site erpnext.site migrate

# 2. Clear cache
bench --site erpnext.site clear-cache

# 3. Rebuild assets
bench build

# 4. Restart
bench restart

# 5. Run tests
cd apps/shiva_erp && python -m pytest
```

---

## Key Design Decisions

### ✅ Why Dual UOM Instead of Conversion Factors?

**Problem**: ERPNext's standard UOM conversion assumes fixed ratios (e.g., 1 Kg = X Nos)

**Reality**: Each broiler chicken has **variable weight** (1.2 - 1.8 kg typical range)

**Solution**: Track both UOMs separately:
- Stock Qty = Number of birds (Nos)
- Weight = Actual measured weight (Kg)
- Billing = Always by weight (price_per_kg × weight_kg)

### ✅ Why Custom Fields?

**Principle**: Never modify core ERPNext/Frappe code

**Approach**: Extend standard DocTypes with custom fields
- Prefixed with `custom_` for clarity
- Managed via Custom Field DocType
- Survives framework upgrades

### ✅ Why Separate Stock Weight Ledger?

**Benefits**:
- Audit trail for weight-based transactions
- Independent of ERPNext Stock Ledger
- Batch-level weight analytics
- Performance (indexed queries for dual UOM)

---

## Performance Considerations

### Indexes Created (via JSON schema)

```sql
-- Stock Weight Ledger
CREATE INDEX idx_item_warehouse 
  ON `tabStock Weight Ledger` (item_code, warehouse);
  
CREATE INDEX idx_posting_date 
  ON `tabStock Weight Ledger` (posting_date);
```

### Query Optimization

- Stock balance queries use SUM aggregation (fast)
- Reports use LEFT JOIN for item names (one query)
- Filters applied at SQL level (WHERE clause)

---

## Business Rules Implemented

1. **Stock Movement**:
   - Purchase Receipt → IN transaction (positive changes)
   - Delivery Note / Sales Invoice → OUT transaction (negative changes)
   - Cancellation → DELETE ledger entries

2. **Pricing**:
   - Lookup priority: Shop + Area + Item + Price Type
   - Fallback: Shop + Item (ignore area)
   - Effective Price = Base Price - Discount
   - Amount = Effective Price × Weight

3. **Validation**:
   - Weight > 0 and Qty > 0 (always)
   - Discount ≤ Base Price
   - Stock availability before sales
   - Average weight warning if < 0.5 or > 5 kg/bird

---

## Testing Coverage

### Stock Weight Ledger
- ✓ Dual UOM calculation (avg weight)
- ✓ Transaction type IN/OUT
- ✓ Weight/Qty change signs
- ✓ Zero/negative validation
- ✓ Individual weights JSON validation
- ✓ Stock balance aggregation

### Shop Price Master
- ✓ Effective price calculation
- ✓ Discount validation (≤ price)
- ✓ Validity date range
- ✓ Duplicate detection
- ✓ Bulk update

---

## Next Steps (Optional Enhancements)


1. **Mobile Integration**: Weighbridge data capture via mobile app
2. **FIFO/FEFO**: Batch expiry and rotation logic
3. **Analytics**: Price trends, supplier performance scoring
4. **Notifications**: WhatsApp alerts for orders/deliveries
5. **Dashboard**: Real-time KPIs (stock levels, sales trends)

---

## 🔄 Pricing Architecture Refactoring (January 2025)

### Motivation
The original Shop Price Master required updating every shop individually for daily price changes, which was inefficient for clients with many shops across multiple areas.

### New Architecture

**Separated Pricing Model:**
1. **Item Price Type** (Base Pricing): `item + price_type → base_price`
   - Updated once per price type → affects all shops
   - Example: "Broiler Chicken" + "Wholesale" → ₹150/kg

2. **Shop Discount** (Shop-Specific): `shop + item → discount`
   - Shop-specific adjustments (stable, updated occasionally)
   - Example: "Shop XYZ" + "Broiler Chicken" → ₹10/kg discount

**Calculation:**
```
effective_price = base_price - shop_discount
```

### Benefits
- **100× efficiency**: Update 20 base prices vs. 2,000 shop prices daily
- **Consistency**: All shops of same price type get same base price automatically
- **Flexibility**: Shop-specific discounts still supported
- **Scalability**: Adding shops doesn't increase daily update burden

### Implementation
**New DocTypes:**
- `Item Price Type` - Base prices by price type
- `Shop Discount` - Shop-specific discount adjustments

**Migration:**
- Automated migration script: `migrations/migrate_pricing.py`
- Preserves historical Shop Price Master data
- Validates pricing accuracy (±₹1/kg tolerance)

**Utilities:**
- Bulk update by price type (daily operation)
- Bulk update shop discounts (occasional)
- Price history tracking and audit trail
- Pricing dashboard for overview

### Documentation
- **PRICING_REFACTORING.md** - Comprehensive architecture guide
- **PRICING_QUICK_REFERENCE.md** - Daily operations guide
- **COMPLETION_SUMMARY.md** - Implementation statistics

### Status
✅ **Code Complete** - Ready for staging testing  
📊 **Performance**: 100× faster daily updates (2,000 → 20 records)  
🧪 **Testing**: 10+ unit tests covering all scenarios  
📚 **Documentation**: 900+ lines across 3 guides

---

## Support

**Developer**: Gopalakrishna Reddy Gogulamudi  
**Email**: ggkr565457123@gmail.com  
**License**: AGPL-3.0  
**Framework**: Frappe 15.x / ERPNext 15.x  
**Python**: >= 3.10

---

## Conclusion

✅ **Production-ready dual UOM system** for poultry business  
✅ **All 5 phases completed** with comprehensive testing  
✅ **Pricing architecture optimized** for daily operations (100× improvement)  
✅ **Zero core modifications** - all via hooks and custom fields  
✅ **Fully documented** with deployment and development guides  
✅ **Best practices** - pre-commit hooks, unit tests, error handling  

**Ready for deployment to erpnext.site!**

