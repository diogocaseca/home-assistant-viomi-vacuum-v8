"""The Viomi Vacuum V8 integration."""

PLATFORMS = ["vacuum", "sensor"]


async def async_setup(hass, config):
    """Set up the Viomi Vacuum V8 integration."""
    return True


async def async_setup_entry(hass, entry):
    """Set up Viomi Vacuum V8 from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    from .vacuum import async_remove_config_entry_device

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        async_remove_config_entry_device(hass, entry)
    return unload_ok
