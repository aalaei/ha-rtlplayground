"""HTTP client for the RTLPlayground firmware JSON API.

Login is `POST /login` with form field `pwd`. A successful login answers
302 with a `Set-Cookie: session=...` header. A wrong password answers 302 to
`login.html` with no cookie. Every other request needs the cookie. Sessions
expire after the switch's session timeout, so a 401 triggers one re-login.

Only read endpoints and night mode are used here. See doc/api.md in the
RTLPlayground firmware repository.
"""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import REQUEST_TIMEOUT_SECONDS
from .errors import ApiError, CannotConnect, InvalidAuth


class RtlPlaygroundClient:
    """Talks to one switch. Holds the session cookie between calls."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        password: str,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self._session = session
        self._base = f"http://{host}"
        self._password = password
        self._token: str | None = None
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def async_login(self) -> None:
        """Log in and keep the session cookie. Raises InvalidAuth on a bad password."""
        self._token = None
        try:
            async with self._session.post(
                f"{self._base}/login",
                data={"pwd": self._password},
                allow_redirects=False,
                timeout=self._timeout,
            ) as resp:
                cookie = resp.cookies.get("session")
                if cookie is not None and resp.status in (200, 302):
                    self._token = cookie.value
                    return
                if resp.status in (200, 302):
                    # The firmware answers a bad password with a redirect and no cookie.
                    raise InvalidAuth("password rejected")
                raise ApiError(f"unexpected status {resp.status} from /login")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise CannotConnect(str(err) or type(err).__name__) from err

    async def async_get_json(self, path: str, params: dict[str, str] | None = None) -> Any:
        """GET a JSON endpoint, logging in again once if the session expired."""
        for attempt in range(2):
            if self._token is None:
                await self.async_login()
            status, body = await self._async_get(path, params)
            if status == 401:
                self._token = None
                if attempt == 0:
                    continue
                raise InvalidAuth("session rejected right after login")
            if status != 200:
                raise ApiError(f"unexpected status {status} from {path}")
            return body
        raise InvalidAuth("session rejected")  # pragma: no cover - loop always returns or raises

    async def _async_get(self, path: str, params: dict[str, str] | None) -> tuple[int, Any]:
        try:
            async with self._session.get(
                f"{self._base}{path}",
                params=params,
                headers={"Cookie": f"session={self._token}"},
                allow_redirects=False,
                timeout=self._timeout,
            ) as resp:
                if resp.status != 200:
                    return resp.status, None
                try:
                    return resp.status, await resp.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError) as err:
                    raise ApiError(f"invalid JSON from {path}") from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise CannotConnect(str(err) or type(err).__name__) from err

    async def async_set_night(self, on: bool) -> None:
        """Turn night mode on (all LEDs off) or off. Not saved across reboots."""
        await self.async_get_json("/night.json", {"set": "on" if on else "off"})
