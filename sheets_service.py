import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SheetsService:
    def __init__(self, creds, sheet_id):
        self.service = build('sheets', 'v4', credentials=creds)
        self.sheet_id = sheet_id

    def get_current_month_sheet_name(self):
        """Returns the sheet name format like Bills_Month_Year"""
        now = datetime.datetime.now()
        return now.strftime("Bills_%B_%Y")

    def ensure_sheet_exists(self, sheet_name):
        """
        Checks if the sheet exists. If not, creates it and adds headers.
        """
        try:
            # Get spreadsheet metadata
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = sheet_metadata.get('sheets', '')
            
            # Check if sheet exists
            sheet_exists = any(s.get("properties", {}).get("title") == sheet_name for s in sheets)
            
            if not sheet_exists:
                print(f"Creating new sheet: {sheet_name}")
                requests = [
                    {
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }
                ]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body={'requests': requests}
                ).execute()
                
                # Add headers
                headers = [["Date", "Bank Name", "Drive Link", "Status"]]
                body = {'values': headers}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f"{sheet_name}!A1:D1",
                    valueInputOption="RAW",
                    body=body
                ).execute()
                print("Added headers to the new sheet.")
        except HttpError as error:
            print(f"An error occurred ensuring sheet exists: {error}")

    def append_bill_record(self, date_str, bank_name, drive_link):
        """
        Appends the bill record to the current month's sheet.
        """
        sheet_name = self.get_current_month_sheet_name()
        self.ensure_sheet_exists(sheet_name)
        
        try:
            values = [[date_str, bank_name, drive_link, "Unpaid"]]
            body = {'values': values}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A:D",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            
            print(f"Appended row for {bank_name} to sheet {sheet_name}.")
            return result
        except HttpError as error:
            print(f"An error occurred appending row: {error}")
            return None
