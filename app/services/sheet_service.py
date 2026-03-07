# app/services/sheet_service.py - Google Sheets Integration (Stub)
"""
Google Sheets integration service.

This is a stub implementation. To use:
1. Set up Google Sheets API credentials
2. Set GOOGLE_SHEETS_CREDENTIALS and SPREADSHEET_ID in .env
3. Install gspread: uv add gspread oauth2client

Usage:
    from app.services.sheet_service import SheetService
    service = SheetService()
    service.write_data("Sheet1", data_list)
"""

from app.config import Config
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    pass


class SheetService:
    """Service for reading/writing data to Google Sheets."""

    def __init__(self):
        """Initialize Google Sheets service."""
        self.credentials_path = Config.GOOGLE_SHEETS_CREDENTIALS
        self.spreadsheet_id = Config.SPREADSHEET_ID
        self._client = None

    def _get_client(self):
        """Get or create Google Sheets client.

        Returns:
            Authorized gspread client.

        Raises:
            ImportError: If gspread is not installed.
            Exception: If credentials are invalid.
        """
        if self._client is not None:
            return self._client

        try:
            # ensure imports succeeded
            gspread
            ServiceAccountCredentials
        except NameError:
            raise ImportError(
                "Google Sheets integration requires gspread and oauth2client. "
                "Install with: uv add gspread oauth2client"
            )

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_path, scope
        )
        self._client = gspread.authorize(creds)
        return self._client

    def write_data(
        self, sheet_name: str, data: list[list], start_cell: str = "A1"
    ) -> bool:
        """Write data to a Google Sheet.

        Args:
            sheet_name: Name of the worksheet tab.
            data: 2D list of values to write.
            start_cell: Starting cell (e.g., 'A1').

        Returns:
            True if successful, False otherwise.
        """
        try:
            client = self._get_client()
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.update(start_cell, data)
            print(f"✅ Data written to sheet '{sheet_name}'")
            return True
        except Exception as e:
            print(f"❌ Error writing to Google Sheet: {e}")
            return False

    def read_data(self, sheet_name: str) -> list[list]:
        """Read all data from a Google Sheet.

        Args:
            sheet_name: Name of the worksheet tab.

        Returns:
            2D list of cell values.
        """
        try:
            client = self._get_client()
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            return worksheet.get_all_values()
        except Exception as e:
            print(f"❌ Error reading from Google Sheet: {e}")
            return []
