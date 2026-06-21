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
        If it exists but is empty, adds headers and validation.
        """
        try:
            # Get spreadsheet metadata
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = sheet_metadata.get('sheets', '')
            
            # Check if sheet exists
            target_sheet = None
            for s in sheets:
                if s.get("properties", {}).get("title") == sheet_name:
                    target_sheet = s
                    break
            
            if not target_sheet:
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
                response = self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body={'requests': requests}
                ).execute()
                
                sheet_id_num = response['replies'][0]['addSheet']['properties']['sheetId']
            else:
                sheet_id_num = target_sheet.get("properties", {}).get("sheetId")
            
            # Check if headers exist (row 1 is empty or missing)
            header_check = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A1:I1"
            ).execute()
            existing_headers = header_check.get('values', [])
            
            if not existing_headers or not existing_headers[0]:
                # Add headers
                headers = [["Date", "Biller Name", "Bill Type", "Bill Identifier", "Amount Due", "Due Date", "Drive Link", "Email Link", "Status"]]
                body = {'values': headers}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f"{sheet_name}!A1:I1",
                    valueInputOption="RAW",
                    body=body
                ).execute()
                print("Added headers to the sheet.")
                
            return sheet_id_num
        except HttpError as error:
            print(f"An error occurred ensuring sheet exists: {error}")
            return None

    def append_bill_record(self, date_str, biller_name, bill_type, bill_identifier, amount_due, due_date, drive_link, email_link):
        """
        Appends the bill record to the current month's sheet.
        """
        sheet_name = self.get_current_month_sheet_name()
        sheet_id_num = self.ensure_sheet_exists(sheet_name)
        
        try:
            values = [[date_str, biller_name, bill_type, bill_identifier, amount_due, due_date, drive_link if drive_link else "", email_link, "Unpaid"]]
            body = {'values': values}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A:I",
                valueInputOption="USER_ENTERED",
                insertDataOption="OVERWRITE",
                body=body
            ).execute()
            
            print(f"Appended row for {biller_name} to sheet {sheet_name}.")
            
            # Extract row number and apply validation strictly up to the current row (F2:F{row_num})
            updated_range = result.get('updates', {}).get('updatedRange', '')
            if updated_range and sheet_id_num:
                import re
                range_part = updated_range.split('!')[-1]
                row_nums = [int(x) for x in re.findall(r'\d+', range_part)]
                if row_nums:
                    end_row = max(row_nums)
                    
                    # Apply validation strictly to I2:I{end_row}
                    validation_requests = [
                        # 1. Clear validation on column I (row 2 onwards)
                        {
                            'setDataValidation': {
                                'range': {
                                    'sheetId': sheet_id_num,
                                    'startRowIndex': 1,
                                    'startColumnIndex': 8,
                                    'endColumnIndex': 9
                                }
                            }
                        },
                        # 2. Set validation strictly on I2:I{end_row}
                        {
                            'setDataValidation': {
                                'range': {
                                    'sheetId': sheet_id_num,
                                    'startRowIndex': 1,
                                    'endRowIndex': end_row,
                                    'startColumnIndex': 8,
                                    'endColumnIndex': 9
                                },
                                'rule': {
                                    'condition': {
                                        'type': 'ONE_OF_LIST',
                                        'values': [
                                            {'userEnteredValue': 'Paid'},
                                            {'userEnteredValue': 'Unpaid'}
                                        ]
                                    },
                                    'showCustomUi': True,
                                    'strict': True
                                }
                            }
                        }
                    ]
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.sheet_id,
                        body={'requests': validation_requests}
                    ).execute()
                    print(f"Ensured dropdown validation on Status column (I2:I{end_row}).")
                    
            return result
        except HttpError as error:
            print(f"An error occurred appending row: {error}")
            return None
