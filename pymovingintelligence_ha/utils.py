"""Home Assistant Python 3 API wrapper for Moving Intelligence."""
import hashlib
import logging
import secrets
import time
from typing import Optional

from aiohttp import ClientSession, ClientTimeout

_LOGGER = logging.getLogger("pymovingintelligence_ha")


class Utils:
    """Utilities for Moving Intelligence."""

    def __init__(self, username, apikey):
        self._username = username
        self._apikey = apikey
        self._timeout = ClientTimeout(total=10)

    @staticmethod
    def clean_request_params(params: dict) -> dict:
        """Create clean parameters."""
        clean_params = {}
        for key, value in params.items():
            if value is not None:
                clean_params[key] = str(value)

        return clean_params

    def _create_headers(self, endpoint: str, params: dict) -> str:
        """Return signature."""
        params_string = ""
        nonce = secrets.token_hex(10)
        timestamp = int(time.time())

        if params:
            params_string = "&".join([f"{key}={val}" for key, val in params.items()])
            endpoint = f"{endpoint}?{params_string}"

        sha512str = (
            "sha512 "
            + hashlib.sha512(
                str(
                    endpoint + self._username + nonce + str(timestamp) + self._apikey
                ).encode("utf-8")
            ).hexdigest()
        )
        headers = {
            "X-Mi-User": self._username,
            "X-Mi-Nonce": nonce,
            "X-Mi-Timestamp": str(timestamp),
            "X-Signature": sha512str,
        }

        return headers

    async def request(
        self, method: str, endpoint: str, params: dict = None
    ) -> Optional[str]:
        """Makes a request to the movingintelligence API."""

        headers = self._create_headers(endpoint, params)
        url = f"https://api-app.movingintelligence.com{endpoint}"

        _LOGGER.debug(
            "Making request to %s endpoint url: %s, headers: %s, params: %s",
            endpoint,
            url,
            headers,
            params,
        )

        async with ClientSession() as session:
            async with session.request(
                method, url, headers=headers, params=params, timeout=self._timeout
            ) as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    logging.debug("Response: %s", resp_json)
                    return resp_json
                if resp.status == 401:
                    resp_json = await resp.json()
                    status = resp_json["status"]
                    message = resp_json["message"]
                    if status == "UNAUTHORIZED":
                        pass
                    else:
                        _LOGGER.debug(
                            "Error occurred %s %s",
                            resp.status,
                            message,
                        )
                if resp.status == 500:
                    raise InvalidAuthError("Invalid credentials")

                return None


class InvalidAuthError(Exception):
    """Raised when API returns a code indicating invalid credentials."""


class InvalidPermissionsError(Exception):
    """Raised when API returns a code indicating not enough permissions."""
