# Generalized Bill Tracker Implementation Walkthrough

I have successfully updated the application into a **100% Configuration-Driven Plug-and-Play Utility & Bill Tracker**. It elegantly handles unlimited bill types, dynamic column schemas, and file naming structures without requiring any Python code changes!

## Major Architectural Upgrades

### 1. Dynamic YAML Extraction (`config.yaml`)
The extraction engine has been completely externalized from Python into the `config.yaml` file. 
- **`sheet_schema`**: A global spreadsheet definition dictates the exact columns, headers, and data types (e.g., `date`, `amount`, `string`, `status`). Adding a new column to your spreadsheet is as simple as adding a new entry to this YAML list.
- **`file_naming_pattern`**: Google Drive PDF filenames are dynamically constructed using variables from the configuration (e.g. `"{biller_name} {bill_type} Bill {month_year}"`).
- **`extraction_rules`**: Every provider defines their own regular expression extraction rules natively. This allows for absolute flexibility, ensuring that if a single bank changes their email format, you only need to update that one bank's YAML regex without affecting the others!

### 2. The Dynamic Parser (`src/services/parsers/dynamic_parser.py`)
All hardcoded subclass parsers (`CreditCardParser`, `AirtelWifiParser`, etc.) have been completely removed!
- Replaced by a single `DynamicParser` that reads the `extraction_rules` from the YAML file.
- It iterates through the regex patterns dynamically, capturing data and automatically formatting it based on the data type defined in the `sheet_schema` (e.g., applying `-₹` to credit balances, normalizing date strings).

### 3. Dynamic Google Sheets Generation
The spreadsheet layout is no longer hardcoded:
- `ensure_sheet_exists()` reads the `sheet_schema` from YAML and dynamically writes the exact number of headers and configures the exact grid boundaries.
- **Dynamic Alignments**: The visual styling automatically aligns `amount` types to the right, `date` and `status` types to the center, and clips long text based purely on the schema definition.
- Data appending is fully decoupled, passing a dictionary of extracted values to `append_bill_record()`, which guarantees column order perfection.

### 4. Credit Balance & Promotional Safety Fix
We resolved an issue where credit balances (e.g. `15 Cr` in Axis Bank emails) were incorrectly matched with promotional text (e.g. "convert above INR 1,500 into EMIs").
- **Promotional Exclusions (`amount_exclude`)**: A global safety list in `config.yaml` drops any amount matches if words like `above`, `greater`, or `convert` appear within 30 characters of the match.

## Setup & Run Instructions

> [!TIP]
> Ensure your `config.yaml` accurately maps your providers. You can add new utility providers instantly by just defining a new block!
> To test the new parsing logic and verify sheet layout:
> 1. Run `python src/main.py`.
> 2. Watch the console logs dynamically map extracted regex data to your schema!
> 3. Verify the layout, alternate colors, and conditional dropdown formatting in your `Bills_June_2026` Google Sheet!
