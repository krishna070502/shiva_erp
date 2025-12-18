# Stock Weight Ledger Detailed Report - User Guide

## Overview

The **Stock Weight Ledger Detailed** report provides a comprehensive transaction-wise view of all stock movements with dual UOM (Quantity in Nos + Weight in Kg) tracking. This report shows running balance after each transaction, making it easy to track stock flow over time.

## Key Features

✅ **Transaction-wise Detail**: See every IN and OUT movement  
✅ **Running Balance**: Track cumulative stock after each transaction  
✅ **Period Selection**: Filter by date range  
✅ **Warehouse Filter**: View specific warehouse movements  
✅ **Transaction Type Filter**: Show only IN, OUT, or both  
✅ **Batch Tracking**: Filter by specific batch numbers  
✅ **Dual UOM Display**: Both quantity (Nos) and weight (Kg) visible  

## How to Access

**Navigation:** Shiva Business ERP → Reports → Stock Weight Ledger Detailed

## Report Filters

### 1. **From Date** (Required)
- Start date for the report period
- Default: 1 month before today
- Opening balance calculated from transactions before this date

### 2. **To Date** (Required)
- End date for the report period
- Default: Today

### 3. **Item** (Optional)
- Filter by specific item code
- Leave blank to show all items

### 4. **Warehouse** (Optional)
- Filter by specific warehouse
- Leave blank to show all warehouses

### 5. **Transaction Type** (Optional)
- **IN**: Show only incoming stock (Purchase Receipts)
- **OUT**: Show only outgoing stock (Delivery Notes, Sales Invoices)
- **Blank**: Show both IN and OUT transactions

### 6. **Batch** (Optional)
- Filter by specific batch number
- Useful for batch-wise tracking

## Report Columns

| Column | Description |
|--------|-------------|
| **Date** | Transaction posting date |
| **Type** | IN (green ⬇) or OUT (red ⬆) |
| **Voucher Type** | Purchase Receipt, Delivery Note, etc. |
| **Voucher No** | Clickable link to source document |
| **Item Code** | Item being transacted |
| **Item Name** | Item description |
| **Warehouse** | Stock location |
| **Batch** | Batch number (if applicable) |
| **Qty Change (Nos)** | Change in quantity (+green for IN, -red for OUT) |
| **Weight Change (Kg)** | Change in weight (+green for IN, -red for OUT) |
| **Actual Qty (Nos)** | Quantity in this transaction |
| **Actual Weight (Kg)** | Weight in this transaction |
| **Avg Wt/Bird (Kg)** | Average weight per bird in this transaction |
| **Balance Qty (Nos)** | Running balance quantity (bold) |
| **Balance Wt (Kg)** | Running balance weight (bold) |
| **Remarks** | Additional notes |

## Sample Report Output

```
Date       | Type | Voucher Type     | Voucher No      | Item         | Warehouse | Qty Change | Wt Change | Balance Qty | Balance Wt
-----------|------|------------------|-----------------|--------------|-----------|------------|-----------|-------------|------------
2025-12-01 | IN   | Purchase Receipt | PR-001          | BROILER-001  | Main WH   | +500.00    | +750.00   | 500.00      | 750.00
2025-12-03 | OUT  | Delivery Note    | DN-001          | BROILER-001  | Main WH   | -100.00    | -145.00   | 400.00      | 605.00
2025-12-05 | IN   | Purchase Receipt | PR-002          | BROILER-001  | Main WH   | +300.00    | +420.00   | 700.00      | 1,025.00
2025-12-07 | OUT  | Sales Invoice    | SI-001          | BROILER-001  | Main WH   | -150.00    | -218.00   | 550.00      | 807.00
```

## Use Cases

### 1. **Daily Stock Reconciliation**
**Filter:**
- From Date: Today
- To Date: Today
- Warehouse: Main Warehouse

**Result:** All transactions for today with running balance

### 2. **Item Movement Analysis**
**Filter:**
- From Date: 01-12-2025
- To Date: 31-12-2025
- Item: BROILER-LIVE-001

**Result:** Complete movement history for specific item over the month

### 3. **Audit Trail for Batch**
**Filter:**
- Batch: BATCH-151225-A

**Result:** All transactions affecting this specific batch

### 4. **Warehouse Stock Flow**
**Filter:**
- From Date: 01-12-2025
- To Date: 15-12-2025
- Warehouse: Cold Storage - Mumbai
- Transaction Type: IN

**Result:** All incoming stock to Cold Storage warehouse

### 5. **Verify Sales Transactions**
**Filter:**
- From Date: Last week
- To Date: Today
- Transaction Type: OUT

**Result:** All outgoing stock (deliveries and sales)

## Color Coding

- **Green ⬇ IN**: Incoming stock transactions
- **Red ⬆ OUT**: Outgoing stock transactions
- **+Green numbers**: Positive changes (stock added)
- **-Red numbers**: Negative changes (stock removed)
- **Bold numbers**: Running balance columns

## Tips

1. **Opening Balance**: The report automatically calculates opening balance from all transactions before the "From Date"

2. **Running Balance**: Balance columns show cumulative stock after each transaction in chronological order

3. **Export to Excel**: Use the export button to download detailed data for further analysis

4. **Voucher Links**: Click on voucher numbers to open the source document

5. **Multi-item Reports**: Leave Item filter blank to see all items. Running balance is calculated separately for each item-warehouse-batch combination.

## Troubleshooting

**Q: Balance doesn't match physical stock?**
- Check if all Purchase Receipts have `custom_total_weight_kg` filled
- Verify all transactions are properly submitted (not in draft)
- Run the report with no filters to see complete history

**Q: Missing transactions?**
- Ensure date range covers the transaction period
- Check if warehouse filter is excluding transactions
- Verify transaction type filter isn't hiding records

**Q: Opening balance is zero but should have stock?**
- Transactions before "From Date" contribute to opening balance
- Extend "From Date" backwards to see earlier transactions

## Related Reports

- **Stock Balance Dual UOM**: Current stock balance summary (no transaction detail)
- **Shop Sales Analysis**: Sales performance by shop and area
