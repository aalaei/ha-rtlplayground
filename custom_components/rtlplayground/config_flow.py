"""Config and reauth flows. Both check the MAC before saving anything."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import RtlPlaygroundClient
from .const import CONF_HOST, CONF_PASSWORD, DOMAIN
from .errors import ApiError, CannotConnect, InvalidAuth
from .parsers import SwitchInfo, parse_information


async def _async_validate(hass: Any, host: str, password: str) -> SwitchInfo:
    """Log in and read information.json. Raises the client's errors."""
    client = RtlPlaygroundClient(async_get_clientsession(hass), host, password)
    await client.async_login()
    return parse_information(await client.async_get_json("/information.json"))


class RtlPlaygroundConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a switch by host and password."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            password = user_input[CONF_PASSWORD]
            try:
                info = await _async_validate(self.hass, host, password)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ApiError:
                errors["base"] = "invalid_response"
            else:
                await self.async_set_unique_id(info.mac_address)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info.hostname or host,
                    data={CONF_HOST: host, CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                info = await _async_validate(
                    self.hass, entry.data[CONF_HOST], user_input[CONF_PASSWORD]
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ApiError:
                errors["base"] = "invalid_response"
            else:
                if entry.unique_id is not None and info.mac_address != entry.unique_id:
                    return self.async_abort(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )
