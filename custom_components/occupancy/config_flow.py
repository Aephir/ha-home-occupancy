from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

import voluptuous as vol
from .const import (
    DOMAIN,
    PRESENCE_SENSOR,
    CONF_NAME,
    CONF_HOME_OCCUPANCY,
    CONF_ADD_ANOTHER
)

_LOGGER = logging.getLogger(__name__)

# The schema sort of works with vol.Required(PRESENCE_SENSOR): str
# but not so much with vol.Required(PRESENCE_SENSOR): cv.entity_id
DATA_SCHEMA = vol.Schema(
    {
        vol.Required(PRESENCE_SENSOR): str,  # cv.entity_id,
        vol.Required(CONF_NAME): str,  # cv.string,
        vol.Optional(CONF_ADD_ANOTHER): bool,  # cv.boolean,
    }
)


async def async_validate_input_entity_id(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input is valid entity_id.
    Either person.*, device_tracker.* or binary_sensor.*
    """

    _LOGGER.error("async_validate_input_entity_id")

    valid_domains = [
        "person",
        "device_tracker",
        "binary_sensor"
    ]

    entity = cv.entity_id(data[PRESENCE_SENSOR])
    entity_split = entity.split(".")
    if entity_split[0] not in valid_domains:
        raise InvalidEntityID

    return {"title": entity}


async def async_validate_input_string(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input is a string."""

    _LOGGER.error("async_validate_input_string")

    if data[CONF_NAME] is None:
        raise NoInputName
    else:
        entity = cv.string(data[CONF_NAME])

    return {"title": entity}


class HomeOccupancyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Home Occupancy."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    # This is deprecated. What to use instead??
    # CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        self.data: dict[str, dict[str, str]] = {}
        self.number_of_sensors = 0

    async def async_step_user(self, user_input=None):
        errors: dict = {}
        if user_input is not None:
            try:
                info_entity = await async_validate_input_entity_id(self.hass, user_input)
                info_name = await async_validate_input_string(self.hass, user_input)
            except InvalidEntityID:
                errors["base"] = "invalid_entity_id"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                self.number_of_sensors += 1
                self.data[f"sensor_{self.number_of_sensors}"] = {
                    PRESENCE_SENSOR: user_input[PRESENCE_SENSOR],
                    CONF_NAME: str(user_input[CONF_NAME])
                }

                # If user ticked the box show this form again to add more sensors.
                if user_input.get(CONF_ADD_ANOTHER, False):
                    return await self.async_step_user()
                else:
                    return self.async_create_entry(title=CONF_HOME_OCCUPANCY, data=self.data)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class InvalidEntityID(exceptions.InvalidEntityFormatError):
    """Error to indicate invalid entity_id."""


class NoInputName(exceptions.IntegrationError):
    """Error to indicate no input name."""
