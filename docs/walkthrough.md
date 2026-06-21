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

## Setup & Run Instructions

> [!TIP]
> Ensure your `config.yaml` accurately maps your providers. 
> To test the new parsing logic:
> 1. Run `python src/main.py`.
> 2. Watch the console logs print out the precise ID, Due Date, and Amount for each fetched statement!
> 3. Verify the layout and Dropdown menus in your `Bills_June_2026` Google Sheet!
