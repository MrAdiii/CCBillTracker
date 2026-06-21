# Generalized Bill Tracker Implementation Walkthrough

I have successfully updated the application from a strict Credit Card tracker into a **Generalized Plug-and-Play Utility & Bill Tracker**. It now elegantly handles multiple bill types (Credit Cards, Airtel Wi-Fi, Airtel Mobile Postpaid, and Electricity) using a robust factory pattern, and outputs highly detailed financial data to a robust 9-column Google Sheet.

## Major Architectural Upgrades

### 1. Plug-and-Play Parsers (`src/services/parsers/`)
The heavy regex processing in `imap_service.py` has been completely decoupled into specialized parser classes. 
- **`BaseParser`**: Provides standard methods for safely extracting plain text from emails and normalizing dates.
- **`CreditCardParser`**: Handles minimum & total amounts due, payment due dates, and generic card numbers.
- **`AirtelWifiParser` & `AirtelPostpaidParser`**: Purpose-built to dissect Airtel bill statements, extracting exact Total Amounts (`₹588.82`), strict due dates, and account identifiers (`075546931908_dsl` and `89895XXXXX`).
- **`ElectricityParser`**: Tailored for TGSPDCL (and expandable for MPEB), finding USC Numbers and amounts.
- **`ParserFactory`**: Reads your `config.yaml` definitions and instantiates the exact parser class needed dynamically. **To add a new provider in the future, simply update `config.yaml` and add a new parser!**

### 2. Enhanced Google Sheets Schema
The spreadsheet schema has been automatically upgraded from 7 columns to a highly informative 9-column structure:
`["Date", "Biller Name", "Bill Type", "Bill Identifier", "Amount Due", "Due Date", "Drive Link", "Email Link", "Status"]`

- `ensure_sheet_exists()` will safely write these headers for any new month.
- Column I (`Status`) now strictly enforces the dropdown data validation for `Paid` and `Unpaid`.

### 3. Google Sheets Visual Makeover & Automatic Formatting
We added aesthetic layout and styling properties to make the tracking sheet look premium:
- **Font & Size:** Standardized to `Inter` font at `10pt` for readability.
- **Header Formatting:** Tall header row (40px) frozen at the top, styled with a bold white font on a deep slate/charcoal background (`#1E293B`).
- **Alternating Rows:** Alternating background rows (even rows tinted to a very light slate `#F8FAFC`) using built-in Google Sheets Banding.
- **Clean Hyperlinks:** Google Drive and Email links are formatted using formula-based hyperlinks showing clean clickable text (`Document Link` and `Email Link`), removing long raw URLs from the sheet.
- **Alignments:** Customized by column (centered dates and status; right-aligned amounts and due dates; left-aligned biller names, bill types, bill identifiers, and link formulas).
- **Status Validation & Styles:** Validation (Paid/Unpaid dropdown) is applied strictly up to the current row to keep empty cells below it clean. Added conditional formatting rules to automatically paint `"Paid"` rows green and `"Unpaid"` rows red.

### 4. Credit Balance & Promotional Safety Fix
We resolved an issue where credit balances (e.g. `15 Cr` in Axis Bank emails) were incorrectly matched with promotional text (e.g. "convert above INR 1,500 into EMIs").
- **Axis Tabular Extractor:** Implemented a specific regex match that finds the credit amount directly under the Axis statement headers.
- **Credit Balance Support:** Amounts ending in `Cr` or prefixed with `-` are cleaned and written to the sheet as `-₹ {amount}` (credit balance).
- **Promotional Exclusions:** The fallback pattern now includes a context safety check. It scans the 30 characters before a potential amount match; if words like "above", "convert", or "greater" are present, the match is discarded.

## Setup & Run Instructions

> [!TIP]
> Ensure your `config.yaml` accurately maps your providers. 
> To test the new parsing logic and verify sheet layout:
> 1. Run `python src/main.py`.
> 2. Watch the console logs print out the precise ID, Due Date, and Amount for each fetched statement!
> 3. Verify the layout, alternate colors, and conditional dropdown formatting in your `Bills_June_2026` Google Sheet!
