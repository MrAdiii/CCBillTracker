# CCBillTracker To-Do List

This document lists the identified improvements and features to be implemented:

- [x] **1. Date Format Normalization**
  - Parse the email's header Date string (RFC 2822 format).
  - Format it into `DD-MMM-YYYY` (e.g., `21-Jun-2026`).
  - Write this normalized format to the Google Sheet instead of the long raw header string.

- [x] **2. Due Date Extraction**
  - Extract the email body (plain text or HTML).
  - Use regex to search for common credit card payment due date patterns (e.g., "due date: 25 Jun 2026", "payment due date 25/06/2026").
  - Normalize the extracted due date to `DD-MMM-YYYY` where possible.
  - Insert a new column "Due Date" in the Google Sheet between "Date" and "Bank Name".

- [x] **3. Dropdown Menu for Status Column**
  - Use Google Sheets API v4 `setDataValidation` request to set a validation rule on the Status column (now Column F).
  - Restrict the options to "Paid" and "Unpaid" only, with a visual dropdown menu.

- [x] **4. Generalize Bill Tracking for Utilities**
  - Refactor IMAP service to be configuration-driven (`config.yaml`).
  - Extend extraction to cover utility bills (Wifi, Electricity, Postpaid Cell).
  - Add "Bill Type" column to the Google Sheet and rename "Bank Name" to "Biller Name".
  - Make PDF attachments optional for utility bills while still logging them.

- [x] **5. Google Sheet Visual Makeover & Formatting**
  - Add visual formatting (Inter font, custom column widths, and text alignments).
  - Freeze the header row and format it with a premium deep slate background.
  - Apply subtle alternating row coloring (banding).
  - Configure status dropdown validation strictly up to the current row (Paid/Unpaid).
  - Format Drive and Email links as clean hyperlinks (`Document Link` and `Email Link`).
  - Paint Paid status rows green and Unpaid rows red using conditional formatting.
  - Fix Axis Bank credit balance parsing (correctly parses `15 Cr` as `-₹ 15` and ignores promotional amount `1,500` in email body).

- [ ] **6. PDF Statement Parser**
  - Build a PDF extractor module to parse downloaded credit card statement PDFs directly.
  - Extract key fields: Due Date, Total Amount Due, Minimum Amount Due, Statement Period, Card Number (last 4 digits).
  - This provides a reliable fallback for banks where the email body lacks structured data (e.g., HDFC, IndusInd).
  - Use a library like `pdfplumber` or `PyMuPDF` to extract text from PDF pages.
  - Implement bank-specific parsing logic since each bank's PDF layout differs.
  - Handle password-protected PDFs (SBI, IndusInd use password patterns like `XXXXDDMM`).
  - Merge PDF-extracted data with email-extracted data, preferring PDF values when both are available.

- [ ] **7. Deployment Phase**
  - [ ] Validate the `Dockerfile` for containerized execution.
  - [ ] Set up secure credentials management (`.env`, `credentials.json`, `token.json`) for the production environment.
  - [ ] Configure a task scheduler (e.g., cron or cloud service) to run the extraction process automatically on a regular basis.

- [ ] **8. Externalize Extraction Regex Logic (Future Scope)**
  - Move all provider-specific regex extraction patterns out of the Python parser classes and directly into `config.yaml`.
  - Introduce an `extraction_rules` section for each provider that maps target fields (`amount_due`, `due_date`, `bill_identifier`) to a list of regex patterns to attempt.
  - Refactor `BaseParser` to iterate through these YAML-defined regex rules automatically.
  - *Benefits:* The application will become 100% configuration-driven. New billers can be supported end-to-end (from detection to data extraction) purely by editing `config.yaml`, completely eliminating the need to write custom Python subclasses.
