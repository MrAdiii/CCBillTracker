import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SheetsService:
    def __init__(self, creds, sheet_id, sheet_schema, sheet_name_pattern='Bills_%B_%Y'):
        self.service = build('sheets', 'v4', credentials=creds)
        self.sheet_id = sheet_id
        self.sheet_schema = sheet_schema
        self.sheet_name_pattern = sheet_name_pattern

    def get_current_month_sheet_name(self):
        """Returns the sheet name based on the configured pattern"""
        now = datetime.datetime.now()
        return now.strftime(self.sheet_name_pattern)

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
                self.current_sheet_row_count = 1000
                should_format = True
            else:
                sheet_id_num = target_sheet.get("properties", {}).get("sheetId")
                self.current_sheet_row_count = target_sheet.get("properties", {}).get("gridProperties", {}).get("rowCount", 1000)
                
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
                # Add headers dynamically based on schema
                header_row = [col['header'] for col in self.sheet_schema]
                headers = [header_row]
                
                body = {'values': headers}
                
                # Use dynamic end column
                import string
                end_col_letter = string.ascii_uppercase[len(self.sheet_schema) - 1]
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f"{sheet_name}!A1:{end_col_letter}1",
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
        Applies aesthetic styles to the Google Sheet dynamically based on the schema.
        """
        requests = []
        
        row_count = 1000
        if target_sheet:
            grid_properties = target_sheet.get("properties", {}).get("gridProperties", {})
            row_count = grid_properties.get("rowCount", 1000)
            
        col_count = len(self.sheet_schema)
        
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
        
        # 2. Format Header Row
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id_num,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': col_count
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.118, 'green': 0.161, 'blue': 0.231},
                        'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'fontFamily': 'Inter', 'fontSize': 10, 'bold': True},
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
                    'endColumnIndex': col_count
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {'fontFamily': 'Inter', 'fontSize': 10},
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(textFormat,verticalAlignment)'
            }
        })
        
        # 4. Set row height: Header = 40px, Data = 28px
        requests.append({
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id_num, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': 1},
                'properties': {'pixelSize': 40}, 'fields': 'pixelSize'
            }
        })
        requests.append({
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id_num, 'dimension': 'ROWS', 'startIndex': 1, 'endIndex': row_count},
                'properties': {'pixelSize': 28}, 'fields': 'pixelSize'
            }
        })
        
        # 5. Set column alignments and custom widths dynamically based on type
        for i, col in enumerate(self.sheet_schema):
            align = 'LEFT'
            width = 120
            col_type = col.get('type', 'string')
            
            if col_type == 'date':
                align = 'CENTER'
                width = 100
            elif col_type == 'amount':
                align = 'RIGHT'
                width = 110
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': i,
                            'endColumnIndex': i + 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'numberFormat': {
                                    'type': 'NUMBER',
                                    'pattern': '"₹"#,##0.00;[Red]"-₹"#,##0.00'
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.numberFormat'
                    }
                })
            elif col_type == 'status':
                align = 'CENTER'
                width = 90
            elif col.get('id') in ['drive_link', 'email_link']:
                width = 100
                
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id_num,
                        'startRowIndex': 1,
                        'endRowIndex': row_count,
                        'startColumnIndex': i,
                        'endColumnIndex': i + 1
                    },
                    'cell': {'userEnteredFormat': {'horizontalAlignment': align}},
                    'fields': 'userEnteredFormat.horizontalAlignment'
                }
            })
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id_num,
                        'dimension': 'COLUMNS',
                        'startIndex': i,
                        'endIndex': i + 1
                    },
                    'properties': {'pixelSize': width},
                    'fields': 'pixelSize'
                }
            })
            
            # Clip long URLs for link fields
            if col.get('id') in ['drive_link', 'email_link']:
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': i,
                            'endColumnIndex': i + 1
                        },
                        'cell': {'userEnteredFormat': {'wrapStrategy': 'CLIP'}},
                        'fields': 'userEnteredFormat.wrapStrategy'
                    }
                })

        # 8. Add alternating row colors (Banding) if not already applied
        if not has_banding:
            requests.append({
                'addBanding': {
                    'bandedRange': {
                        'range': {
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': 0,
                            'endColumnIndex': col_count
                        },
                        'rowProperties': {
                            'firstBandColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                            'secondBandColor': {'red': 0.973, 'green': 0.980, 'blue': 0.988}
                        }
                    }
                }
            })
            
        # 9. Add conditional formatting for Paid/Unpaid Status if not already applied
        status_col_idx = next((i for i, col in enumerate(self.sheet_schema) if col.get('type') == 'status'), None)
        if not has_conditional_formats and status_col_idx is not None:
            requests.append({
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': sheet_id_num,
                            'startRowIndex': 1,
                            'endRowIndex': row_count,
                            'startColumnIndex': status_col_idx,
                            'endColumnIndex': status_col_idx + 1
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'TEXT_EQ',
                                'values': [{'userEnteredValue': 'Paid'}]
                            },
                            'format': {
                                'backgroundColor': {'red': 0.863, 'green': 0.988, 'blue': 0.906},
                                'textFormat': {'foregroundColor': {'red': 0.086, 'green': 0.396, 'blue': 0.204}, 'bold': True}
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
                            'startColumnIndex': status_col_idx,
                            'endColumnIndex': status_col_idx + 1
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'TEXT_EQ',
                                'values': [{'userEnteredValue': 'Unpaid'}]
                            },
                            'format': {
                                'backgroundColor': {'red': 0.996, 'green': 0.886, 'blue': 0.886},
                                'textFormat': {'foregroundColor': {'red': 0.600, 'green': 0.106, 'blue': 0.106}, 'bold': True}
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

    def append_bill_record(self, record_data):
        """
        Appends the bill record dynamically to the current month's sheet.
        """
        sheet_name = self.get_current_month_sheet_name()
        sheet_id_num = self.ensure_sheet_exists(sheet_name)
        
        try:
            drive_link = record_data.get('drive_link')
            email_link = record_data.get('email_link')
            record_data['drive_link'] = f'=HYPERLINK("{drive_link}", "Document Link")' if drive_link else ""
            record_data['email_link'] = f'=HYPERLINK("{email_link}", "Email Link")' if email_link else ""
            record_data['status'] = 'Unpaid'
            
            # Map dictionary strictly to schema order
            row_values = []
            for col in self.sheet_schema:
                row_values.append(record_data.get(col['id'], ""))
                
            values = [row_values]
            body = {'values': values}
            
            import string
            end_col_letter = string.ascii_uppercase[len(self.sheet_schema) - 1]
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A:{end_col_letter}",
                valueInputOption="USER_ENTERED",
                insertDataOption="OVERWRITE",
                body=body
            ).execute()
            
            biller_name = record_data.get('biller_name', 'Unknown')
            print(f"Appended row for {biller_name} to sheet {sheet_name}.")
            
            # Find status column for validation
            status_col_idx = next((i for i, col in enumerate(self.sheet_schema) if col.get('type') == 'status'), None)
            
            updated_range = result.get('updates', {}).get('updatedRange', '')
            if updated_range and sheet_id_num and status_col_idx is not None:
                import re
                # Split sheet name off so year digits in sheet name aren't parsed as row numbers
                range_part = updated_range.split('!')[-1]
                row_nums = [int(n) for n in re.findall(r'\d+', range_part)]
                if row_nums:
                    end_row = max(row_nums)
                    
                    validation_requests = [
                        {
                            'setDataValidation': {
                                'range': {
                                    'sheetId': sheet_id_num,
                                    'startRowIndex': 1,
                                    'endRowIndex': self.current_sheet_row_count,
                                    'startColumnIndex': status_col_idx,
                                    'endColumnIndex': status_col_idx + 1
                                }
                            }
                        },
                        {
                            'setDataValidation': {
                                'range': {
                                    'sheetId': sheet_id_num,
                                    'startRowIndex': 1,
                                    'endRowIndex': end_row,
                                    'startColumnIndex': status_col_idx,
                                    'endColumnIndex': status_col_idx + 1
                                },
                                'rule': {
                                    'condition': {
                                        'type': 'ONE_OF_LIST',
                                        'values': [{'userEnteredValue': 'Paid'}, {'userEnteredValue': 'Unpaid'}]
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
                    
            return result
        except HttpError as error:
            print(f"An error occurred appending the record: {error}")
            return None
