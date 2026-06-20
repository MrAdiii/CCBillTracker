# CCBillTracker To-Do List

This document lists the identified improvements and features to be implemented:

- [ ] **1. Date Format Normalization**
  - Parse the email's header Date string (RFC 2822 format).
  - Format it into `DD-MMM-YYYY` (e.g., `21-Jun-2026`).
  - Write this normalized format to the Google Sheet instead of the long raw header string.

- [ ] **2. Due Date Extraction**
  - Extract the email body (plain text or HTML).
  - Use regex to search for common credit card payment due date patterns (e.g., "due date: 25 Jun 2026", "payment due date 25/06/2026").
  - Normalize the extracted due date to `DD-MMM-YYYY` where possible.
  - Insert a new column "Due Date" in the Google Sheet between "Date" and "Bank Name".

- [ ] **3. Dropdown Menu for Status Column**
  - Use Google Sheets API v4 `setDataValidation` request to set a validation rule on the Status column (Column E).
  - Restrict the options to "Paid" and "Unpaid" only, with a visual dropdown menu.
