"""Config flow for the Viomi Vacuum V8 integration."""

from __future__ import annotations

from functools import partial
import logging

from miio import DeviceException, ViomiVacuum  # pylint: disable=import-error
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_MANUAL_SEGMENTS,
    DEFAULT_MANUAL_SEGMENTS,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ViomiVacuumV8ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Viomi Vacuum V8."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow for this handler."""
        return ViomiVacuumV8OptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
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


def _validate_manual_segments(raw_value: str) -> bool:
    """Validate manual segments format: 1:Room,2:Kitchen."""
    if not raw_value.strip():
        return True

    chunks = raw_value.replace("\n", ",").replace(";", ",").split(",")
    for chunk in chunks:
        item = chunk.strip()
        if not item:
            continue

        if ":" in item:
            seg_id, _ = item.split(":", 1)
        elif "=" in item:
            seg_id, _ = item.split("=", 1)
        else:
            seg_id = item

        if not seg_id.strip().isdigit():
            return False

    return True


class ViomiVacuumV8OptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options flow for Viomi Vacuum V8."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        super().__init__(config_entry)

    async def async_step_init(self, user_input=None):
        """Manage integration options."""
        errors = {}

        if user_input is not None:
            manual_segments = user_input.get(CONF_MANUAL_SEGMENTS, DEFAULT_MANUAL_SEGMENTS)
            if not _validate_manual_segments(manual_segments):
                errors[CONF_MANUAL_SEGMENTS] = "invalid_manual_segments"
            else:
                return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MANUAL_SEGMENTS,
                    default=self.config_entry.options.get(
                        CONF_MANUAL_SEGMENTS,
                        DEFAULT_MANUAL_SEGMENTS,
                    ),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
