# Implementation Plan - Plug-and-Play Bill Tracker

This revised plan addresses the current structure of `config.yaml` and sets up a truly modular, plug-and-play architecture for processing various bills. 

## User Review Required

> [!IMPORTANT]
> **Consolidated Sheet Schema (9 Columns)**
> To support all data points while preserving your existing columns, the new headers will be:
> `["Date", "Biller Name", "Bill Type", "Bill Identifier", "Amount Due", "Due Date", "Drive Link", "Email Link", "Status"]`
> - This retains your existing `Biller Name`, `Bill Type`, `Drive Link`, and `Email Link`.
> - We are injecting `Bill Identifier` and `Amount Due`.
> - Status dropdown validation will be shifted to Column I (Index 8).

## Proposed Changes

### 1. Refactor Parsers into Plug-and-Play Architecture
We will create a new directory `src/services/parsers/` to hold specialized parsing logic.

#### [NEW] `src/services/parsers/base_parser.py`
- Defines a `BaseParser` class with a standard interface: `extract(msg)`. 
- Includes common helper methods like `extract_email_body()`.

#### [NEW] `src/services/parsers/credit_card_parser.py`
- Implements `CreditCardParser` extending `BaseParser`.
- Contains the regex logic for extracting Credit Card Due Dates, Minimum/Total Amounts Due, and Card identifiers (e.g. "ending in XXXX").

#### [NEW] `src/services/parsers/airtel_parser.py`
- Implements `AirtelWifiParser` and `AirtelPostpaidParser`.
- Contains regex for Airtel's specific email structures.

#### [NEW] `src/services/parsers/electricity_parser.py`
- Implements parsers for MPEB and TGSPDCL.

#### [NEW] `src/services/parsers/parser_factory.py`
- A factory method `get_parser(bill_type)` that reads the `type` from `config.yaml` (e.g. `Credit Card`, `Wifi`, `Electricity`) and returns the corresponding parser instance.

### 2. `imap_service.py` modifications

#### [MODIFY] `src/services/imap_service.py`
- Update to leverage the `parser_factory`.
- `fetch_unprocessed_statements` will match the email sender/subject against `config.yaml`.
- It will then instantiate the correct parser via `parser_factory.get_parser(provider_type)` and call `parser.extract(msg)`.
- It will return a dictionary with all 9 fields.

### 3. `sheets_service.py` modifications

#### [MODIFY] `src/services/sheets_service.py`
- Update headers list in `ensure_sheet_exists` to the 9-column schema.
- Update `append_bill_record` signature to accept `bill_identifier` and `amount_due`.
- Shift the dropdown data validation for `Status` from Column G (Index 6) to Column I (Index 8).

### 4. `main.py` modifications

#### [MODIFY] `src/main.py`
- Update the orchestration flow to simply unpack the enriched dictionary from `imap_service` and pass the 9 fields to `sheets_service.append_bill_record`.
- Because of the `parser_factory`, `main.py` will not need to change when you add new bill types to `config.yaml` in the future!

## Next Steps
Once you approve this architecture, please share the sample email texts for Airtel Wifi & Postpaid so I can begin writing their specific parser classes. I will implement the Credit Card parser first to demonstrate the structure.
