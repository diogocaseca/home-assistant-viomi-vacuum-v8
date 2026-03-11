"""Sensor platform for Viomi Vacuum V8."""
from __future__ import annotations

from functools import partial
import logging

from miio import DeviceException, ViomiVacuum  # pylint: disable=import-error

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Viomi Vacuum V8 sensors from a config entry."""
    host = config_entry.data[CONF_HOST]
    token = config_entry.data[CONF_TOKEN]
    name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)

    async_add_entities(
        [
            ViomiBatterySensor(
                name=name,
                vacuum=ViomiVacuum(host, token),
                entry_id=config_entry.entry_id,
            )
        ],
        update_before_add=True,
    )


class ViomiBatterySensor(SensorEntity):
    """Battery sensor for a Viomi Vacuum V8."""

    _attr_has_entity_name = True
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, name: str, vacuum: ViomiVacuum, entry_id: str) -> None:
        """Initialize the battery sensor."""
        self._vacuum = vacuum
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_battery"
        self._attr_native_value = None
        self._attr_available = False
        self._device_name = name

    @property
    def available(self) -> bool:
        """Return True if the sensor is available."""
        return self._attr_available

    @property
    def device_info(self) -> DeviceInfo:
        """Return shared device info to link with vacuum entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
            manufacturer="Viomi",
            model="Vacuum V8",
        )

    async def async_update(self) -> None:
        """Fetch state from the device."""

        def _get_battery() -> int:
            return int(self._vacuum.raw_command("get_prop", ["battary_life"])[0])

        try:
            self._attr_native_value = await self.hass.async_add_executor_job(
                partial(_get_battery)
            )
            self._attr_available = True
        except (DeviceException, OSError) as exc:
            self._attr_available = False
            _LOGGER.warning("Could not update battery sensor: %s", exc)
