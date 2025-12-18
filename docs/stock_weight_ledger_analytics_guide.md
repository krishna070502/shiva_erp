# Stock Weight Ledger - Detailed Analytics & Dashboard

## 🎯 Overview

The enhanced Stock Weight Ledger system now includes **three comprehensive views**:

1. **Stock Weight Ledger Detailed Report** - Transaction-level detail with running balance
2. **Stock Ledger Dashboard** - Visual analytics with cards and charts
3. **Stock Balance Dual UOM** - Current stock summary

---

## 📊 1. Stock Weight Ledger Detailed Report

### **Access Path**
`Shiva Business ERP → Reports → Stock Weight Ledger Detailed`

### **Key Features**

#### ✨ **Summary Cards at Top**
Displays 17 key metrics:

- **Transaction Metrics**
  - Total Transactions
  - IN Transactions (green)
  - OUT Transactions (red)

- **Opening Balance**
  - Opening Qty (Nos)
  - Opening Weight (Kg)

- **Inward Movement**
  - Total IN Qty (Nos) - green indicator
  - Total IN Weight (Kg) - green indicator

- **Outward Movement**
  - Total OUT Qty (Nos) - red indicator
  - Total OUT Weight (Kg) - red indicator

- **Net Movement**
  - Net Movement Qty (Nos) - green if positive, orange if negative
  - Net Movement Weight (Kg)

- **Closing Balance**
  - Closing Qty (Nos) - purple indicator
  - Closing Weight (Kg) - purple indicator
  - Avg Weight/Bird (Kg) - purple indicator

- **Analysis Metrics**
  - Unique Items (blue)
  - Unique Warehouses (blue)
  - Unique Batches (blue, if applicable)

#### 📈 **Interactive Charts**

**Daily Movement Chart** (Mixed Bar + Line)
```
- Green bars: IN transactions (quantity per day)
- Red bars: OUT transactions (quantity per day)  
- Blue line: Running balance (quantity)
```

**Chart Features:**
- Hover to see exact values
- Zoom and pan capabilities
- Date-wise aggregation
- Automatically updates with filters

#### 🎨 **Enhanced Visual Formatting**

**Transaction Type:**
- ⬇ IN - Green badge with down arrow icon
- ⬆ OUT - Red badge with up arrow icon

**Changes:**
- +100.00 - Green with plus icon (additions)
- -50.00 - Red with minus icon (deductions)

**Balance Columns:**
- Bold blue numbers for positive balance
- Gray for zero/low balance
- Larger font size for emphasis

**Actual Quantities:**
- Subtle gray background
- Medium weight font
- Clear differentiation from changes

#### 🔍 **Advanced Filters**

```javascript
From Date: [Required] Default: Last 1 month
To Date: [Required] Default: Today
Item: [Optional] Filtered to stock items only
Warehouse: [Optional] Filtered to non-group warehouses
Transaction Type: [Optional] "", "IN", "OUT"
Batch: [Optional] Batch number
```

#### 🛠️ **Action Buttons**

1. **Export Summary** - Export detailed data to Excel
2. **Batch Analysis** - Quick link to Stock Balance Dual UOM report
3. **Stock Reconciliation** - Create reconciliation document

#### 📋 **Data Table Features**

- ✅ Inline filters for quick search
- ✅ Checkboxes for row selection
- ✅ Clickable voucher links (opens source document)
- ✅ Hover highlighting for better UX
- ✅ Responsive design
- ✅ Sortable columns

---

## 📱 2. Stock Ledger Dashboard (NEW!)

### **Access Path**
`Shiva Business ERP → Stock Ledger Dashboard`

### **Visual Dashboard Layout**

#### 🃏 **Summary Cards Grid**

6 large cards displaying:

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│  Opening Stock      │   Total IN          │   Total OUT         │
│  500 Nos            │   300 Nos           │   200 Nos           │
│  750.00 Kg          │   450.00 Kg         │   290.00 Kg         │
│  📦 Icon            │   ⬇ Icon           │   ⬆ Icon           │
└─────────────────────┴─────────────────────┴─────────────────────┘

┌─────────────────────┬─────────────────────┬─────────────────────┐
│  Closing Stock      │   Net Movement      │   Avg Weight/Bird   │
│  600 Nos            │   +100 Nos          │   1.45 kg           │
│  910.00 Kg          │   +160.00 Kg        │                     │
│  ✓ Icon             │   ⇄ Icon           │   ⚖ Icon           │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

**Card Features:**
- Color-coded left border
- Large numbers with icons
- Dual UOM display (Nos + Kg)
- Subtle icon watermark
- Box shadow for depth

#### 📊 **Interactive Charts (4 Charts)**

**1. Daily Stock Movement (Quantity)**
```
Bar Chart
- Green bars: Daily IN quantity
- Red bars: Daily OUT quantity
- X-axis: Dates
- Y-axis: Quantity (Nos)
```

**2. Daily Stock Movement (Weight)**
```
Bar Chart
- Green bars: Daily IN weight (Kg)
- Red bars: Daily OUT weight (Kg)
- X-axis: Dates
- Y-axis: Weight (Kg)
```

**3. Stock Balance Trend**
```
Line Chart
- Blue line: Quantity balance trend
- Purple line: Weight balance trend
- Shows running balance over time
- Region fill enabled
```

**4. Item-wise Distribution** (if multiple items)
```
Pie Chart
- Each item gets a color
- Shows relative distribution
- Hover for percentages
```

#### 📑 **Detailed Data Tables**

**1. Top Items by Movement**
```
| Item Code      | Transactions | Total Qty | Total Weight |
|----------------|--------------|-----------|--------------|
| BROILER-001    | 45           | 2,500     | 3,750.00     |
| COUNTRY-001    | 32           | 1,800     | 2,340.00     |
```

**2. Warehouse-wise Summary**
```
| Warehouse        | IN Qty | OUT Qty | Balance Qty | Balance Wt |
|------------------|--------|---------|-------------|------------|
| Main WH          | 500    | 300     | 200         | 295.50     |
| Cold Storage     | 300    | 150     | 150         | 217.50     |
```

**3. Recent Transactions** (Last 20)
```
| Date       | Type | Voucher     | Item        | Qty Change | Wt Change |
|------------|------|-------------|-------------|------------|-----------|
| 2025-12-17 | OUT  | SI-001      | BROILER-001 | -50.00     | -72.50    |
| 2025-12-16 | IN   | PR-002      | BROILER-001 | +100.00    | +145.00   |
```

### **Dashboard Filters**

Top bar filters for dynamic updates:
- From Date
- To Date
- Item
- Warehouse

**Auto-refresh** when filters change!

### **Action Buttons**

1. **Refresh** - Reload dashboard data
2. **Export Data** - Download complete analysis

---

## 🎯 Use Cases & Examples

### **Use Case 1: Daily Reconciliation**

**Report:** Stock Weight Ledger Detailed

**Filters:**
```
From Date: Today
To Date: Today
Warehouse: Main Warehouse
```

**Result:**
- Summary cards show today's movements
- Chart shows hourly/transaction pattern
- All transactions listed with running balance
- Verify closing matches physical count

---

### **Use Case 2: Monthly Performance Review**

**View:** Stock Ledger Dashboard

**Filters:**
```
From Date: 01-Dec-2025
To Date: 31-Dec-2025
```

**Result:**
- Visual cards show month summary
- Daily movement charts reveal patterns
- Balance trend shows stock levels
- Top items table highlights key products
- Warehouse comparison for optimization

---

### **Use Case 3: Item Movement Analysis**

**Report:** Stock Weight Ledger Detailed

**Filters:**
```
From Date: Last 3 months
To Date: Today
Item: BROILER-LIVE-001
```

**Result:**
- Complete movement history for the item
- Identify purchase patterns
- Analyze sales velocity
- Check average weight trends
- Audit trail for compliance

---

### **Use Case 4: Warehouse Stock Flow**

**Dashboard:** Stock Ledger Dashboard

**Filters:**
```
From Date: Last week
To Date: Today
Warehouse: Cold Storage - Mumbai
```

**Result:**
- Warehouse-specific movements
- In/Out pattern visualization
- Current balance validation
- Recent transactions for quick reference

---

### **Use Case 5: Batch Tracking**

**Report:** Stock Weight Ledger Detailed

**Filters:**
```
Batch: BATCH-151225-A
```

**Result:**
- Complete lifecycle of the batch
- From purchase to final sale
- Average weight tracking
- Quality control data
- Traceability for audits

---

## 📱 UI/UX Enhancements

### **Color Scheme**

```
Green (#28a745)  : IN transactions, positive movements
Red (#dc3545)    : OUT transactions, negative movements
Blue (#007bff)   : Balance, primary info
Purple (#6f42c1) : Closing balance, averages
Gray (#6c757d)   : Opening balance, neutral data
Orange (#ffc107) : Warnings, negative net movement
```

### **Icons**

```
fa-arrow-down     : IN transactions
fa-arrow-up       : OUT transactions
fa-plus-circle    : Additions
fa-minus-circle   : Deductions
fa-database       : Opening stock
fa-check-circle   : Closing stock
fa-exchange       : Net movement
fa-balance-scale  : Average weight
```

### **Responsive Design**

- Cards: Grid auto-fits to screen width (min 250px)
- Charts: Grid auto-fits to screen width (min 500px)
- Tables: Responsive with horizontal scroll on mobile
- Filters: Stack vertically on small screens

---

## 🚀 Performance Optimizations

1. **Lazy Loading**: Charts load only when visible
2. **Date Aggregation**: Daily grouping reduces chart data points
3. **Pagination**: Recent transactions limited to 20
4. **Cached Queries**: Opening balance cached per request
5. **Indexed Queries**: Optimized SQL with proper indexes

---

## 🔒 Security & Permissions

**Role-based Access:**
- Stock Manager: Full access
- Stock User: View reports and dashboard
- Sales Manager: View-only access
- System Manager: Full admin access

**Data Security:**
- Filters enforce user permissions
- Warehouse restrictions apply
- Batch access controlled by roles

---

## 📱 Mobile Responsiveness

✅ **Mobile-Optimized Features:**
- Touch-friendly card taps
- Swipeable charts
- Collapsible filter panel
- Responsive tables with horizontal scroll
- Large touch targets for buttons
- Optimized font sizes

---

## 🎓 Tips & Best Practices

### **For Daily Operations:**
1. Start day with dashboard review
2. Use "Today" filters for current status
3. Check summary cards for quick insights
4. Verify balance against physical count

### **For Analysis:**
1. Use longer date ranges for trends
2. Compare warehouse performance
3. Identify top-moving items
4. Monitor average weight changes

### **For Audits:**
1. Use batch filters for traceability
2. Export detailed reports for records
3. Verify voucher links work correctly
4. Cross-check with source documents

### **For Management:**
1. Review dashboard monthly
2. Analyze movement patterns
3. Identify optimization opportunities
4. Monitor stock turnover ratios

---

## 🔧 Troubleshooting

**Q: Charts not showing?**
- Refresh the page
- Clear browser cache
- Check if data exists for date range

**Q: Summary cards show zero?**
- Verify date range includes transactions
- Check filter selections
- Ensure transactions are submitted (not draft)

**Q: Dashboard loads slowly?**
- Reduce date range
- Apply item/warehouse filters
- Check network connection

**Q: Export not working?**
- Check browser pop-up blocker
- Verify you have export permissions
- Try smaller date range

---

## 📞 Support

For issues or questions:
1. Check this documentation first
2. Review the User Guide (docs/)
3. Contact system administrator
4. Raise issue on GitHub repository

---

**Version:** 1.0.0  
**Last Updated:** December 17, 2025  
**Maintainer:** Shiva ERP Team
