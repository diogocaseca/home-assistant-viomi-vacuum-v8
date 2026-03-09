"""Config flow for the Viomi Vacuum V8 integration."""

from __future__ import annotations

from functools import partial
import logging

from miio import DeviceException, ViomiVacuum  # pylint: disable=import-error
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ViomiVacuumV8ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Viomi Vacuum V8."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_connection(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input[CONF_TOKEN],
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_TOKEN: user_input[CONF_TOKEN],
                        CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TOKEN): vol.All(
                    str, vol.Length(min=32, max=32)
                ),
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


async def _async_validate_connection(
    hass: HomeAssistant,
    host: str,
    token: str,
) -> None:
    """Validate connection parameters."""

    def _test_connection() -> None:
        vacuum = ViomiVacuum(host, token)
        vacuum.raw_command("get_prop", ["run_state"])

    try:
        await hass.async_add_executor_job(partial(_test_connection))
    except (DeviceException, OSError) as err:
        raise CannotConnect from err


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
