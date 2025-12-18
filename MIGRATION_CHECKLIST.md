# Migration Checklist - Shiva ERP Dual UOM System

## Pre-Migration Tasks

### 1. Backup Current System
- [ ] Take full database backup: `bench --site erpnext.site backup`
- [ ] Export current Stock Weight Ledger data (if exists)
- [ ] Document current custom fields
- [ ] Save current site configuration

### 2. Verify Environment
- [ ] Python version >= 3.10: `python --version`
- [ ] Frappe version: `bench version`
- [ ] ERPNext installed and working
- [ ] Sufficient disk space (> 1 GB free)
- [ ] Database connection working

### 3. Code Review
- [ ] Pull latest code from repository
- [ ] Review all custom files in `apps/shiva_erp/`
- [ ] Check pre-commit hooks configured
- [ ] Verify no syntax errors: `python -m py_compile shiva_erp/**/*.py`

---

## Migration Steps

### Step 1: Update Codebase (5 min)

```bash
cd /workspace/frappe-bench

# Pull latest changes
cd apps/shiva_erp
git pull origin main

# Install dependencies (if any new)
cd ../..
bench setup requirements
```

**Verification:**
- [ ] Code updated successfully
- [ ] No git merge conflicts

---

### Step 2: Create Custom Fields (15 min)

#### Via ERPNext UI:

**A. Purchase Receipt Item**

1. Go to: **Customize Form** → Select "Purchase Receipt Item"
2. Add New Field:
   - Label: `Total Weight (Kg)`
   - Field Name: `custom_total_weight_kg`
   - Type: `Float`
   - Precision: `3`
   - Insert After: `qty`
3. Save

**B. Delivery Note Item**

1. Go to: **Customize Form** → Select "Delivery Note Item"
2. Add New Field:
   - Label: `Total Weight (Kg)`
   - Field Name: `custom_total_weight_kg`
   - Type: `Float`
   - Precision: `3`
   - Insert After: `qty`
3. Save

**C. Sales Invoice Item**

1. Go to: **Customize Form** → Select "Sales Invoice Item"
2. Add Fields:
   - Label: `Total Weight (Kg)`, Field Name: `custom_total_weight_kg`, Type: `Float`, Precision: `3`
   - Label: `Price Type`, Field Name: `custom_price_type`, Type: `Select`, Options: `\nWholesale\nRetail\nPremium\nBulk`
   - Label: `Base Price/Kg`, Field Name: `custom_base_price_per_kg`, Type: `Currency`, Read Only: `✓`
   - Label: `Discount/Kg`, Field Name: `custom_discount_per_kg`, Type: `Currency`, Read Only: `✓`
3. Save

**Verification:**
- [ ] All custom fields created
- [ ] Fields visible in forms
- [ ] No errors in browser console

---

### Step 3: Database Migration (10 min)

```bash
# Run migration
bench --site erpnext.site migrate

# Expected output:
# - Creating new DocTypes (Stock Weight Ledger, Shop Price Master)
# - Creating new Reports
# - Updating schema
```

**Verification:**
- [ ] Migration completed without errors
- [ ] Check logs: `tail -f sites/erpnext.site/logs/erpnext-web.log`

---

### Step 4: Clear Cache & Rebuild (5 min)

```bash
# Clear all caches
bench --site erpnext.site clear-cache

# Rebuild JS/CSS assets
bench build

# Restart all processes
bench restart
```

**Verification:**
- [ ] Cache cleared
- [ ] Assets rebuilt (check timestamps in `sites/assets/`)
- [ ] Bench restarted successfully

---

### Step 5: Verify DocTypes (10 min)

**A. Stock Weight Ledger**

1. Go to: **Stock Weight Ledger** (new menu item)
2. Click **New**
3. Verify all fields present:
   - Transaction Type (IN/OUT)
   - Item Code, Warehouse
   - Stock Qty (Nos), Weight (Kg)
   - Avg Weight per Bird (auto-calculated)
4. Try creating a test record

**B. Shop Price Master**

1. Go to: **Shop Price Master** (new menu item)
2. Click **New**
3. Verify all fields present:
   - Shop (Customer), Area (Territory)
   - Price Type, Item Code
   - Price per Kg, Discount
   - Effective Price (auto-calculated)
4. Try creating a test record

**Verification:**
- [ ] Both DocTypes accessible
- [ ] All fields visible
- [ ] Auto-calculations working
- [ ] Can save records

---

### Step 6: Test Purchase Flow (15 min)

```
1. Create Purchase Receipt
   - Supplier: [Any supplier]
   - Item: "Broiler Chicken" (or create test item)
   - Qty: 100 Nos
   - Custom Total Weight: 150 Kg
   
2. Submit Purchase Receipt
   
3. Verify Stock Weight Ledger:
   - Go to Stock Weight Ledger list
   - Find entry for this PR
   - Check: Transaction Type = IN
   - Check: Stock Qty = 100, Weight = 150 Kg
   - Check: Avg Weight = 1.5 kg/bird
   
4. Check Stock Balance Report:
   - Go to "Stock Balance Dual UOM" report
   - Filter by item
   - Verify: Shows 100 Nos, 150 Kg
```

**Verification:**
- [ ] Purchase Receipt submitted successfully
- [ ] Stock Weight Ledger entry created
- [ ] Stock balance report shows correct data

---

### Step 7: Test Pricing & Sales Flow (20 min)

```
1. Create Shop Price Master
   - Shop: [Select any customer]
   - Area: [Customer's territory]
   - Item: "Broiler Chicken"
   - Price Type: "Wholesale"
   - Price per Kg: 150.00
   - Discount: 5.00
   - Click Save
   - Verify: Effective Price = 145.00
   
2. Create Sales Invoice
   - Customer: [Same as shop above]
   - Item: "Broiler Chicken"
   - Qty: 50 Nos (for reference)
   - Custom Total Weight: 75 Kg
   - Custom Price Type: "Wholesale"
   
3. Submit Sales Invoice
   
4. Verify:
   - Rate should be 145.00 (auto-applied)
   - Amount = 145 × 75 = 10,875.00
   - Custom Base Price = 150.00
   - Custom Discount = 5.00
   
5. Check Stock Weight Ledger:
   - Find entry for this invoice
   - Transaction Type = OUT
   - Stock Qty = 50, Weight = 75 Kg (negative changes)
   
6. Check Stock Balance:
   - Stock should reduce: 100 - 50 = 50 Nos, 150 - 75 = 75 Kg
```

**Verification:**
- [ ] Shop Price Master created
- [ ] Pricing auto-applied on Sales Invoice
- [ ] Stock Weight Ledger updated (OUT)
- [ ] Stock balance reduced correctly

---

### Step 8: Test Reports (10 min)

**A. Stock Balance Dual UOM**

1. Go to: **Reports → Stock Balance Dual UOM**
2. Apply filters: Item = "Broiler Chicken"
3. Verify columns show:
   - Stock Qty (Nos)
   - Total Weight (Kg)
   - Avg Weight/Bird

**B. Shop Sales Analysis**

1. Go to: **Reports → Shop Sales Analysis**
2. Apply filters: Date range = Today
3. Verify columns show:
   - Customer, Territory, Item
   - Total Qty, Total Weight
   - Avg Price/Kg, Total Discount, Revenue

**Verification:**
- [ ] Reports load without errors
- [ ] Data is accurate
- [ ] Filters work correctly
- [ ] Export to Excel works

---

### Step 9: Test Cancellation (10 min)

```
1. Cancel the Sales Invoice created above
   
2. Verify:
   - Stock Weight Ledger entries deleted
   - Stock balance restored to original
   
3. Cancel the Purchase Receipt
   
4. Verify:
   - Stock Weight Ledger entries deleted
   - Stock balance = 0
```

**Verification:**
- [ ] Cancellation removes ledger entries
- [ ] Stock balance correct after cancellation

---

### Step 10: Run Unit Tests (10 min)

```bash
# Run all tests
cd apps/shiva_erp
python -m pytest -v

# Expected: All tests pass
```

**Verification:**
- [ ] All unit tests pass
- [ ] No errors or warnings

---

## Post-Migration Tasks

### 1. Performance Check
- [ ] Test with 1000+ Stock Weight Ledger records
- [ ] Check report load times (< 5 seconds)
- [ ] Monitor database size growth

### 2. User Training
- [ ] Train stock team on new dual UOM fields
- [ ] Train sales team on Shop Price Master
- [ ] Demonstrate reports to management

### 3. Documentation
- [ ] Create user manual for operations team
- [ ] Document shop pricing workflow
- [ ] Create troubleshooting guide

### 4. Monitoring Setup
- [ ] Set up error log monitoring
- [ ] Create alerts for low stock
- [ ] Track average bird weights (analytics)

---

## Rollback Plan (If Needed)

```bash
# 1. Restore database backup
bench --site erpnext.site restore /path/to/backup/file.sql.gz

# 2. Remove custom fields (via UI or console)
bench --site erpnext.site console
frappe.delete_doc("Custom Field", "Purchase Receipt Item-custom_total_weight_kg")
frappe.delete_doc("Custom Field", "Delivery Note Item-custom_total_weight_kg")
# ... delete other custom fields
frappe.db.commit()

# 3. Remove DocTypes
frappe.delete_doc("DocType", "Stock Weight Ledger", force=True)
frappe.delete_doc("DocType", "Shop Price Master", force=True)
frappe.db.commit()

# 4. Restart
bench restart
```

---

## Common Issues & Solutions

### Issue 1: Custom fields not appearing

**Solution:**
```bash
bench --site erpnext.site clear-cache
bench build --force
bench restart
```

### Issue 2: Migration fails

**Check:**
- Database user has CREATE/ALTER permissions
- No conflicting DocTypes with same name
- Review error in `sites/erpnext.site/logs/`

**Solution:**
```bash
bench --site erpnext.site migrate --skip-failing
# Fix specific errors, then retry
```

### Issue 3: Hooks not firing

**Check:**
- hooks.py syntax correct
- App installed: `bench --site erpnext.site list-apps`
- Restart bench after hook changes

### Issue 4: Reports showing no data

**Check:**
- Stock Weight Ledger has entries
- Report filters not too restrictive
- Database queries in report .py file

---

## Sign-off

### Completed By:
- Name: ____________________
- Date: ____________________
- Role: ____________________

### Verified By:
- Name: ____________________
- Date: ____________________
- Role: ____________________

### Production Ready: ☐ Yes ☐ No

**Notes:**
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

**Total Estimated Time: ~2 hours**

**Critical Success Factors:**
✓ All custom fields created  
✓ Both DocTypes functional  
✓ Purchase flow works (IN transaction)  
✓ Sales flow works (OUT transaction, pricing)  
✓ Reports show accurate data  
✓ Unit tests pass  
✓ No errors in logs
