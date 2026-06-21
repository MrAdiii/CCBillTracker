# CCBillTracker

An automated Python script that seamlessly reads your credit card statements and utility bills from your Gmail inbox, intelligently parses the amount due and due dates, uploads the statement PDFs to Google Drive, and logs the records natively into a Google Sheet.

The application is completely configuration-driven via `config.yaml`, allowing you to add support for any new bank or utility provider without writing a single line of Python code.

## Features
- **Gmail IMAP Integration:** Fetches unseen emails based on labels.
- **Dynamic Extractor Engine:** Uses fallback regex patterns driven strictly from `config.yaml`.
- **HTML Fallback Parsing:** Pre-processes rich HTML emails to strip tricky invisible tags before regex extraction.
- **Google Drive Upload:** Automatically names and uploads statement PDFs dynamically based on `config.yaml` logic.
- **Google Sheets Integration:** Automatically creates monthly tabs (e.g. `Bills_June_2026`) and injects native `=SUM()` formulas for an instant dashboard.
- **Zero Hardcoding:** All keywords, identifiers, schema fields, and fallback logic are stored safely in `config.yaml`.

## 1. Gmail IMAP Setup & Google App Password

To allow the service to read emails via IMAP securely without using OAuth 2.0, you must use a Google App Password.

1. Go to your [Google Account Console](https://myaccount.google.com/).
2. Enable **2-Step Verification**.
3. Scroll down and select **App passwords**.
4. Create an app password and copy the 16-character string.

## 2. Google OAuth 2.0 Setup (`credentials.json`)

To upload PDFs to Google Drive and log entries to Google Sheets, configure OAuth 2.0 desktop credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a **New Project**.
3. Enable **Google Drive API** and **Google Sheets API**.
4. Configure the **OAuth consent screen** (Set User Type to External, and add your email as a Test User).
5. Create Credentials > **OAuth client ID** > **Desktop app**.
6. Click **Download JSON**, rename it to `credentials.json`, and place it in the root folder.

## 3. Configure Environment

Copy `.env.example` to `.env` and fill in the values:

```env
EMAIL_ACCOUNT=your_email@gmail.com
APP_PASSWORD=abcdefghijklmnop
EMAIL_UNPROCESSED_LABEL=Unprocessed
EMAIL_PROCESSED_LABEL=Processed
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_SHEET_ID=your_sheet_id
```

## 4. Run the Application

```bash
pip install -r requirements.txt
python src/main.py
```

On your first run, a browser window will open asking you to authenticate with Google Drive/Sheets. Once completed, a `token.json` file will be generated automatically.

## Configuration (`config.yaml`)
You can add new credit cards or utility bills by simply editing `config.yaml`. The schema is entirely dynamic. See the existing configuration for examples on writing regex patterns and extraction fallbacks.
