# Setup Guide: Credentials and App Passwords

This guide explains how to set up the credentials required to run the Credit Card Bill Tracker service.

---

## 1. Gmail IMAP Setup & Google App Password

To allow the service to read emails via IMAP securely without using OAuth 2.0 (bypassing the 7-day token expiration and verification issues), you must use a Google App Password.

### Step 1: Enable 2-Step Verification
Google requires 2-Step Verification to be enabled on your Gmail account before you can generate App Passwords.
1. Go to your [Google Account Console](https://myaccount.google.com/).
2. Select **Security** from the left navigation menu.
3. Under the *How you sign in to Google* section, ensure **2-Step Verification** is turned **On**.

### Step 2: Generate an App Password
1. Click on **2-Step Verification**.
2. Scroll down to the bottom of the page and select **App passwords**.
3. Under **Select app**, choose *Other (Custom name)* and type a name (e.g., `CC Bill Tracker`).
4. Click **Generate**.
5. Google will display a **16-character password** in a yellow box (e.g., `abcd efgh ijkl mnop`). Copy this password immediately (it will not be shown again).

### Step 3: Configure `.env`
In the root directory of your project, copy `.env.example` to `.env` and fill in the values:
```env
EMAIL_ACCOUNT=your_email@gmail.com
APP_PASSWORD=abcdefghijklmnop  # Paste the 16-character password here (remove spaces if any)
EMAIL_UNPROCESSED_LABEL=Unprocessed  # (Optional) Mailbox label to fetch statements from (defaults to Unprocessed)
EMAIL_PROCESSED_LABEL=Processed      # (Optional) Mailbox label to move processed emails to (defaults to Processed)
```

### Step 4: Handling Nested Labels

In Gmail, nested labels are represented as a string with `/` separators in the Gmail API and IMAP.

For example, if you create a label hierarchy like this in Gmail:

```text
Projects
   └── ClientA
         └── Reports
```

The Gmail API will return them as:

```text
Projects
Projects/ClientA
Projects/ClientA/Reports
```

Make sure to use this format if your `EMAIL_UNPROCESSED_LABEL` or `EMAIL_PROCESSED_LABEL` are nested.

---

## 2. Google OAuth 2.0 Setup (`credentials.json`)

To upload PDFs to Google Drive and log entries to Google Sheets, you need to configure OAuth 2.0 desktop credentials.

### Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown in the top bar and select **New Project**.
3. Enter a project name (e.g., `CC-Bill-Tracker`) and click **Create**.

### Step 2: Enable Google Drive & Sheets APIs
1. In the Google Cloud Console, navigate to **APIs & Services** > **Library**.
2. Search for and enable **Google Drive API**.
3. Go back to the Library, search for and enable **Google Sheets API**.

### Step 3: Configure the OAuth Consent Screen
1. Go to **APIs & Services** > **OAuth consent screen**.
2. Select **User Type** as **External** and click **Create**.
3. Fill in the required fields:
   - **App name**: `CC Bill Tracker`
   - **User support email**: Your Gmail address
   - **Developer contact information**: Your Gmail address
4. Click **Save and Continue** through the Scopes step (no need to manually add restricted scopes here, as desktop flow handles file-level scopes).
5. On the **Test users** step, click **Add Users** and enter your Gmail address (this is critical so your test account can log in).
6. Click **Save and Continue** and then back to Dashboard.

### Step 4: Create OAuth Credentials
1. Go to **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** at the top and select **OAuth client ID**.
3. Under **Application type**, select **Desktop app**.
4. Set the name to `CC Bill Tracker Desktop` and click **Create**.
5. Once created, click the **Download JSON** button to download your credentials.
6. Rename this downloaded file to `credentials.json` and place it in the root folder of your project.

---

## 3. Google Drive and Google Sheets IDs

1. **Google Drive Folder ID**:
   - Open Google Drive, create a folder where statements will be saved, and open it.
   - Copy the folder ID from the URL (the string of characters after `folders/` in the address bar).
   - Set this as `GOOGLE_DRIVE_FOLDER_ID` in `.env`.

2. **Google Sheet ID**:
   - Create a Google Sheet or use an existing one.
   - Copy the spreadsheet ID from the URL (the string of characters between `/d/` and `/edit` in the address bar).
   - Set this as `GOOGLE_SHEET_ID` in `.env`.

---

## 4. Initial Run

1. Open your terminal in the project directory.
2. Run the application:
   ```bash
   python main.py
   ```
3. A browser window will open asking you to authenticate. Log in with the Gmail account you configured as a **Test User**.
4. Once completed, a `token.json` file will be generated in your project root.
5. Future runs will execute automatically without opening the browser.
