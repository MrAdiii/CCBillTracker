# Project Status

## Scope
Automated Credit Card Statement Processing service.
- Fetches credit card e-statements from Gmail via IMAP.
- Processes attachments (PDFs) from target banks (HDFC, Axis, ICICI, IndusInd, SBI, YES Bank).
- Handles forwarded emails correctly.
- Uploads PDFs to Google Drive using Google API Service Account / OAuth.
- Logs details to Google Sheets into monthly sheets named "Bills".

## Architecture
- `imap_service.py`: Connects to IMAP with App Passwords, fetches from "Unprocessed" label, moves to "Processed" label.
- `drive_service.py`: Uploads file to Drive via Google APIs.
- `sheets_service.py`: Updates Sheet via Google APIs, creating "Bills" sheets per month.
- `main.py`: Orchestrates the fetch -> upload -> log -> move flow.

## Next Steps
- Verify services and set up production environment.

## Security & Agent Guidelines
- Do NOT write actual emails, passwords, API keys, credentials, or other sensitive data into files that are not ignored in `.gitignore`. Use environment variables or place actual secrets only in `.env`.
