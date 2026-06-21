import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class DriveService:
    def __init__(self, creds):
        self.service = build('drive', 'v3', credentials=creds)

    def upload_pdf(self, file_path, folder_id):
        """
        Uploads a PDF file to a specific Google Drive folder.
        Returns the webViewLink of the uploaded file.
        """
        try:
            file_name = os.path.basename(file_path)
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
            
            # Create the file and request webViewLink in the response fields
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            print(f"Uploaded {file_name} to Drive. File ID: {file.get('id')}")
            return file.get('webViewLink')
        except Exception as e:
            print(f"Error uploading file to Drive: {e}")
            return None
