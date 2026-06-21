# CC Bill Tracker Service

Generate a lightweight, automated Python service that fetches credit card e-statements from Gmail, saves the attached PDFs to a specific Google Drive folder, and logs the bill details into a Google Sheet tracker. It must handle forwarded emails appropriately.

## User Review Required

> [!IMPORTANT]
> You will need to create a project in Google Cloud Console, enable Gmail, Drive, and Sheets APIs, and download the OAuth client ID as `credentials.json` into the root directory before running the code.

> [!TIP]
> The Drive folder ID and Sheets ID must be set up in the `.env` file to correctly upload the PDFs and log the entries.

## Open Questions

> [!NOTE]
> - What should be the default Sheet tab/name or range to append rows to? I will default to `Sheet1!A:D` if unspecified.
> - Would you like a specific email labeling strategy (e.g. creating a "Processed" label) or simply marking the emails as read by removing the "UNREAD" label?

## Proposed Changes

### Configuration & Docs

#### [NEW] [requirements.txt](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/requirements.txt)
Contains all Python dependencies (`google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `python-dotenv`).

#### [NEW] [.env.example](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/.env.example)
Template for environmental variables like `GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_SHEET_ID`, `SHEET_RANGE`.

#### [NEW] [.gitignore](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/.gitignore)
Standard Python gitignore, ignoring `token.json`, `credentials.json`, `.env`, and `__pycache__`.

#### [NEW] [Dockerfile](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/Dockerfile)
Docker configuration to run the app as a container.

#### [NEW] [.agents/STATUS.md](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/.agents/STATUS.md)
Agentic file to store project scope, status, and instructions for future AI sessions.

---

### Python Source Code

#### [NEW] [google_auth.py](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/google_auth.py)
Handles OAuth 2.0 desktop flow, saving and reusing `token.json`. Requests scopes for Gmail (modify), Drive (file upload), and Sheets (spreadsheets append).

#### [NEW] [gmail_service.py](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/gmail_service.py)
Queries the Gmail API for unread emails with attachments from specific bank addresses, including forwarded emails. Extracts the original sender bank from the forwarded body and downloads the PDF attachments.

#### [NEW] [drive_service.py](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/drive_service.py)
Uploads extracted PDFs to a target Google Drive folder, returning the `webViewLink`.

#### [NEW] [sheets_service.py](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/sheets_service.py)
Appends a row to the Google Sheet tracker with columns: `Date`, `Bank Name`, `Drive Link`, and `Status` ("Unpaid").

#### [NEW] [main.py](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/main.py)
The orchestration loop. Fetches emails, loops through them, uploads attachments, updates the sheet, and modifies Gmail labels to mark emails as read/processed with appropriate error handling and logging.

## Verification Plan

### Manual Verification
- After generating the files, the user will need to place `credentials.json` in the root folder.
- Run `python main.py` locally to complete the one-time OAuth desktop flow.
- Verify that matching unread emails are processed, PDFs appear in the Drive folder, and a new row is appended to the Sheet.

## Deployment Phase

> [!NOTE]
> The project focus is now shifting to deployment.

### Proposed Deployment Steps
- **Containerization:** Ensure the provided `Dockerfile` builds a reliable and slim image.
- **Credentials Management:** Securely mount or inject `.env`, `credentials.json`, and `token.json` into the production environment.
- **Scheduling:** Configure a task scheduler (like cron, GitHub Actions, or Google Cloud Scheduler) to run the container periodically to fetch and process new statements.
