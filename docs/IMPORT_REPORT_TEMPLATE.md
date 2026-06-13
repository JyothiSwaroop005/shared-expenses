# Import Report

**File:** `expenses_export.csv`
**Imported by:** Aisha
**Date:** 2024-01-20 14:32:00 UTC
**Session ID:** 1

---

## Summary

| Metric | Value |
|---|---|
| Total rows in CSV | 45 |
| Successfully imported | 38 |
| Skipped (blocking anomaly) | 5 |
| Pending review | 2 |
| Total anomalies detected | 12 |
| Import status | Completed |

---

## Detected Anomalies

### Blocking Anomalies (Row Skipped)

| Row | Type | Description | Raw Data |
|---|---|---|---|
| 3 | `missing_payer` | paid_by field is empty | `{description: "Hotel", amount: "5000", ...}` |
| 7 | `invalid_amount` | Cannot parse amount: 'five hundred' | `{amount: "five hundred", ...}` |
| 12 | `group_not_found` | Group 'Weekend Trip' not found in database | `{group_name: "Weekend Trip", ...}` |
| 19 | `negative_amount` | Amount is negative: -200.00 | `{amount: "-200", ...}` |
| 31 | `percentage_sum_not_100` | Percentages sum to 95, expected 100 | `{split_type: "percentage", participants: "Aisha:50,Rohan:45", ...}` |

### Non-Blocking Anomalies (Imported with Warning)

| Row | Type | Description | Action |
|---|---|---|---|
| 8 | `future_date` | Expense date is in the future: 2025-06-01 | Imported with warning |
| 22 | `invalid_currency` | Unknown currency: 'EUR'. Defaulting to INR | Imported, currency set to INR |

### Pending Human Review

| Row | Type | Description | Status |
|---|---|---|---|
| 14 | `duplicate_expense` | Possible duplicate of Expense ID 42: same description, amount, group, and payer | ⏳ Pending review |
| 27 | `settlement_as_expense` | Row looks like a settlement, not an expense: 'paid back' | ⏳ Pending review |

---

## Actions Taken

1. **5 rows skipped** due to blocking anomalies. These rows are preserved in `import_anomalies` table and can be viewed in the Anomaly Review page.

2. **2 rows imported with warnings.** The data was usable but contained non-critical issues. Warnings are visible in the anomaly log.

3. **2 rows held for review.** These require a human decision before the system takes action. Navigate to **Anomaly Review** to approve or reject them.

4. **38 rows imported cleanly** with no anomalies detected.

---

## Warnings

- The exchange rate used for USD → INR conversion was **₹83.50** (fixed rate). If your expenses used a different rate at the time, manually verify converted amounts.
- User matching is **case-sensitive** and by name. If a user name in the CSV differs from their registered name (e.g., "aisha" vs "Aisha"), it will be flagged as `user_not_found`.
- Group matching is also **case-sensitive** by name.

---

## How to Resolve Skipped Rows

1. Fix the data issue in your CSV (correct the amount, add the missing payer, etc.)
2. Re-upload only the corrected rows in a new CSV
3. The importer will create a new session and process only those rows
