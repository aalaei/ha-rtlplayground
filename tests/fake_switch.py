"""A fake switch that serves the fixtures over real HTTP.

It follows the firmware's rules: login is `POST /login` with `pwd`, a good
login answers 302 with a `session` cookie, a bad one answers 302 to
login.html without a cookie, and any other request without a valid session
gets 401. Tests can expire sessions and count writes.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

from aiohttp import web

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str):
    return json.loads((FIXTURES / name).read_text())


class FakeSwitch:
    def __init__(self, password: str = "test-password") -> None:
        self.password = password
        self.sessions: set[str] = set()
        self.night = False
        self.night_writes = 0
        self.traffic_file = "traffic.json"
        self.app = web.Application()
        self.app.router.add_post("/login", self._login)
        self.app.router.add_get("/information.json", self._json_handler("information.json"))
        self.app.router.add_get("/ports.json", self._json_handler("ports.json"))
        self.app.router.add_get("/traffic.json", self._traffic)
        self.app.router.add_get("/night.json", self._night)

    def expire_sessions(self) -> None:
        self.sessions.clear()

    def _authed(self, request: web.Request) -> bool:
        cookie = request.cookies.get("session")
        return cookie is not None and cookie in self.sessions

    async def _login(self, request: web.Request) -> web.Response:
        form = await request.post()
        if form.get("pwd") == self.password:
            token = secrets.token_hex(8)
            self.sessions.add(token)
            resp = web.Response(status=302, headers={"Location": "index.html"})
            resp.set_cookie("session", token, samesite="Strict")
            return resp
        return web.Response(status=302, headers={"Location": "login.html"})

    def _json_handler(self, name: str):
        async def handler(request: web.Request) -> web.Response:
            if not self._authed(request):
                return web.Response(status=401)
            return web.json_response(load(name))

        return handler

    async def _traffic(self, request: web.Request) -> web.Response:
        if not self._authed(request):
            return web.Response(status=401)
        return web.json_response(load(self.traffic_file))

    async def _night(self, request: web.Request) -> web.Response:
        if not self._authed(request):
            return web.Response(status=401)
        if "set" in request.query:
            wanted = {"on": True, "off": False}.get(request.query["set"])
            if wanted is None:
                return web.Response(status=400)
            if wanted != self.night:
                self.night_writes += 1
            self.night = wanted
        return web.json_response({"night": self.night})
