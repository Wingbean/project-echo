# app/services/base_service.py - Base Service Class
import requests
from app.config import Config


class BaseAPIService:
    """Base class for services that interact with external APIs.

    Provides generic HTTP request handling with authentication
    and error handling.
    """

    def __init__(self, base_url: str = "", api_key: str = ""):
        """Initialize the API service.

        Args:
            base_url: Base URL for API requests.
            api_key: API authentication key.
        """
        self.base_url = base_url or Config.API_BASE_URL
        self.api_key = api_key or Config.API_KEY
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict | None = None,
        params: dict | None = None,
        timeout: int = 30,
    ) -> dict:
        """Make an HTTP request to the API.

        Args:
            endpoint: API endpoint path.
            method: HTTP method (GET, POST, PUT, DELETE).
            data: JSON body data.
            params: Query parameters.
            timeout: Request timeout in seconds.

        Returns:
            Parsed JSON response as dict.

        Raises:
            requests.RequestException: On HTTP errors.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return {"status": "success", "data": response.text}
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            raise
