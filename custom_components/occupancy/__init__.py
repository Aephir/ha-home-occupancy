"""
Based on https://github.com/scaarup/aula/blob/main/custom_components/aula/__init__.py
"""

from homeassistant.loader import async_get_integration
import asyncio
from homeassistant import config_entries, core
from homeassistant.const import EVENT_HOMEASSISTANT_START
from .const import DOMAIN, STARTUP, PRESENCE_SENSOR
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: core.HomeAssistant,
        entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)

    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)

    # Store a reference to the unsubscribe function to clean up if an entry is unloaded.
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )

    def determine_initial_state(event):
        """
        Should not be necessary. This is a workaround.
        I should look at the `async_update` method, as this should be enough..
        """
        tracked_data = entry.data  # Fetching the entry data which contains your entities
        tracked_entity_ids = [data[PRESENCE_SENSOR] for key, data in tracked_data.items() if key.startswith("sensor_")]

        for entity_id in tracked_entity_ids:
            entity = hass.states.get(entity_id)  # Fetch the entity using its entity_id
            if entity:
                entity.async_update()  # Or entity.async_schedule_update_ha_state(True) if async_update contains `await`

        # After updating the tracked entities, update the binary_sensor.occupancy_sensor as well
        occupancy_sensor = hass.states.get("binary_sensor.occupancy_sensor")
        if occupancy_sensor:
            occupancy_sensor.async_update()  # Or occupancy_sensor.async_schedule_update_ha_state(True) if async_update contains `await`

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, determine_initial_state)

    entry.add_update_listener(async_reload_entry)

    return True


async def options_update_listener(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
        hass: core.HomeAssistant,
        entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass, entry):
    # Unload the old entities and services, etc.
    await hass.config_entries.async_reload(entry.entry_id)