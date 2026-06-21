# Custom Workspace Rules for CCBillTracker

## Project Documentation & AI Guidelines
To maintain a single source of truth and avoid redundant files, you must strictly adhere to the following file structure and updating rules:

1. **[todo.md](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/todo.md)**: This is the **single source of truth for all tasks and next steps**. Whenever a task is completed or a new phase (like Deployment) is identified, you **MUST** update this file.
2. **[docs/walkthrough.md](file:///c:/Users/Aditya/Antigravity-AgentManager/CCBillTracker/docs/walkthrough.md)**: This is the **living document for project architecture, scope, and setup instructions**. Whenever architectural changes or scope modifications are made, you **MUST** update this file to reflect the current state.
3. **Historical Plans**: `docs/implementation_plan.md` is an archived artifact from the initial project generation. Do not update it with new phases.

## Sensitive Data & Security
- **Do NOT write any actual emails, passwords, API keys, credentials, or other sensitive data** into any files that are not ignored by `.gitignore`.
- Always use environment variables or mock/placeholder data for testing.
- Place actual secrets only in `.env` (which is git-ignored).
- Refer to `.env.example` for the structure of required environment variables.

## Development Directions
- When implementing changes, ensure they align with the current architecture (IMAP fetching -> Drive uploading -> Google Sheets logging).
- Always refer to `docs/walkthrough.md` to get a comprehensive overview of the project structure and setup instructions before making large changes.
