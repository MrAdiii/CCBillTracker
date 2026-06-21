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

## Agent Behavior Strict Rule
- **Do NOT change code based on assumptions or memory if it is not linked to the current issue you are working on.** Always preserve the existing naming conventions, file paths, and logical structures of the codebase unless explicitly requested by the user to modify them.

## Development Best Practices
- **Test & Utility Organization:** Keep all test files, test helper scripts, mock utilities, and diagnostic tools inside the `tests/` directory instead of the project root.
- **Data Privacy & Git-Ignored Assets:** Ensure any local email downloads, sample statements, or test fixtures that contain real user statements are stored under `tests/downloaded_emails/` and that this path is strictly ignored in `.gitignore`.
- **Robust Path Resolution:** Write file paths and configuration loaders (like `load_dotenv` or open files) using relative paths derived from the file's current directory (e.g., `os.path.dirname(os.path.abspath(__file__))`) rather than assuming the execution context will always be the project root.

