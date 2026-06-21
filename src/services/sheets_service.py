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
            # Get spreadsheet metadata with explicit fields to retrieve styling metadata
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id,
                fields="sheets(properties,bandedRanges,conditionalFormats)"
            ).execute()
            sheets = sheet_metadata.get('sheets', '')
            
            # Check if sheet exists
            target_sheet = None
            for s in sheets:
                if s.get("properties", {}).get("title") == sheet_name:
                    target_sheet = s
                    break
            
            should_format = False
            has_banding = False
            has_conditional_formats = False
            
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
                should_format = True
            else:
                sheet_id_num = target_sheet.get("properties", {}).get("sheetId")
                
                # Check if it has conditional formatting
                has_conditional_formats = len(target_sheet.get("conditionalFormats", [])) > 0
                
                # Check if it has banding
                has_banding = len(target_sheet.get("bandedRanges", [])) > 0
                
                # If either banding or conditional formatting is missing, format it
                should_format = not (has_banding and has_conditional_formats)
            
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
                should_format = True
                
            if should_format:
                self.apply_formatting(sheet_name, sheet_id_num, target_sheet, has_banding, has_conditional_formats)
                
            return sheet_id_num
        except HttpError as error:
            print(f"An error occurred ensuring sheet exists: {error}")
            return None

    def apply_formatting(self, sheet_name, sheet_id_num, target_sheet=None, has_banding=False, has_conditional_formats=False):
        """
        Applies aesthetic styles to the Google Sheet.
        """
        requests = []
        
        # Get sheet row count to avoid index out of bounds
        row_count = 1000
        if target_sheet:
            grid_properties = target_sheet.get("properties", {}).get("gridProperties", {})
            row_count = grid_properties.get("rowCount", 1000)
            
        # 1. Freeze the first row
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id_num,
                    'gridProperties': {
                        'frozenRowCount': 1
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        })
        
        # 2. Format Header Row (row 1, range A1:I1)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id_num,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 9
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.118,
                            'green': 0.161,
                            'blue': 0.231
                        },
                        'textFormat': {
                            'foregroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 1.0
                            },
                            'fontFamily': 'Inter',
                            'fontSize': 10,
                            'bold': True
                        },
                        'horizontalAlignment': 'CENTER',
                        'verticalAlignment': 'MIDDLE'
                      }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
            }
        })
        
        # 3. Format Data Rows (rows 2 onwards)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id_num,
                    'startRowIndex': 1,
                    'endRowIndex': row_count,
                    'startColumnIndex': 0,
                    'endColumnIndex': 9
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'fontFamily': 'Inter',
                            'fontSize': 10
                        },
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(textFormat,verticalAlignment)'
            }
        })
        
        # 4. Set row height: Header = 40px, Data = 28px
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id_num,
                    'dimension': 'ROWS',
                    'startIndex': 0,
                    'endIndex': 1
                },
                'properties': {
                    'pixelSize': 40
                },
                'fields': 'pixelSize'
            }
        })
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id_num,
                    'dimension': 'ROWS',
                    'startIndex': 1,
                    'endIndex': row_count
                },
                'properties': {
                    'pixelSize': 28
                },
                'fields': 'pixelSize'
            }
        })
        
        # 5. Set column alignments
        alignments = {
            'CENTER': [(0, 1), (2, 3), (5, 6), (8, 9)], # Date, Bill Type, Due Date, Status
            'RIGHT': [(4, 5)] # Amount Due
        }
        for align, cols in alignments.items():
            for start_col, end_col in cols:
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': start_col,
                            'endColumnIndex': end_col
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'horizontalAlignment': align
                            }
                        },
                        'fields': 'userEnteredFormat.horizontalAlignment'
                    }
                })
                
        # 6. Clip long URLs in Link columns (Drive Link = 6, Email Link = 7)
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id_num,
                    'startRowIndex': 1,
                    'endRowIndex': row_count,
                    'startColumnIndex': 6,
                    'endColumnIndex': 8
                },
                'cell': {
                    'userEnteredFormat': {
                        'wrapStrategy': 'CLIP'
                    }
                },
                'fields': 'userEnteredFormat.wrapStrategy'
            }
        })
        
        # 7. Set custom column widths
        col_widths = [100, 160, 120, 140, 110, 110, 100, 100, 90]
        for col_idx, width in enumerate(col_widths):
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id_num,
                        'dimension': 'COLUMNS',
                        'startIndex': col_idx,
                        'endIndex': col_idx + 1
                    },
                    'properties': {
                        'pixelSize': width
                    },
                    'fields': 'pixelSize'
                }
            })
            
        # 8. Set Status dropdown validation (column I / Index 8, whole column)
        requests.append({
            'setDataValidation': {
                'range': {
                    'sheetId': sheet_id_num,
                    'startRowIndex': 1,
                    'endRowIndex': row_count,
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
        })
        
        # 9. Add alternating row colors (Banding) if not already applied
        if not has_banding:
            requests.append({
                'addBanding': {
                    'bandedRange': {
                        'range': {
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': 0,
                            'endColumnIndex': 9
                        },
                        'rowProperties': {
                            'firstBandColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 1.0
                            },
                            'secondBandColor': {
                                'red': 0.973,
                                'green': 0.980,
                                'blue': 0.988
                            }
                        }
                    }
                }
            })
            
        # 10. Add conditional formatting for Paid/Unpaid Status if not already applied
        if not has_conditional_formats:
            requests.append({
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': 8,
                            'endColumnIndex': 9
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'TEXT_EQ',
                                'values': [{'userEnteredValue': 'Paid'}]
                            },
                            'format': {
                                'backgroundColor': {
                                    'red': 0.863,
                                    'green': 0.988,
                                    'blue': 0.906
                                },
                                'textFormat': {
                                    'foregroundColor': {
                                        'red': 0.086,
                                        'green': 0.396,
                                        'blue': 0.204
                                    },
                                    'bold': True
                                }
                            }
                        }
                    },
                    'index': 0
                }
            })
            requests.append({
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': 8,
                            'endColumnIndex': 9
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'TEXT_EQ',
                                'values': [{'userEnteredValue': 'Unpaid'}]
                            },
                            'format': {
                                'backgroundColor': {
                                    'red': 0.996,
                                    'green': 0.886,
                                    'blue': 0.886
                                },
                                'textFormat': {
                                    'foregroundColor': {
                                        'red': 0.600,
                                        'green': 0.106,
                                        'blue': 0.106
                                    },
                                    'bold': True
                                }
                            }
                        }
                    },
                    'index': 1
                }
            })
            
        print(f"Applying visual formatting requests to sheet {sheet_name}...")
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.sheet_id,
            body={'requests': requests}
        ).execute()
        print("Applied visual formatting successfully.")

    def append_bill_record(self, date_str, biller_name, bill_type, bill_identifier, amount_due, due_date, drive_link, email_link):
        """
        Appends the bill record to the current month's sheet.
        """
        sheet_name = self.get_current_month_sheet_name()
        self.ensure_sheet_exists(sheet_name)
        
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
            return result
        except HttpError as error:
            print(f"An error occurred appending row: {error}")
            return None
