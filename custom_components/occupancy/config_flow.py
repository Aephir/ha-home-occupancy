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
    CONF_HOME_OCCUPANCY
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(PRESENCE_SENSOR): cv.entity_id,
        vol.Required(CONF_NAME): cv.string,
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # Validate the data can be used to set up a connection.

    # This is a simple example to show an error in the UI for a short hostname
    # The exceptions are defined at the end of this file, and are used in the
    # `async_step_user` method below.
    valid_domains = [
        "person",
        "device_tracker",
        "binary_sensor"
    ]
    try:
        entity_split = data[PRESENCE_SENSOR].split(".")
        if entity_split[0] not in valid_domains:
            raise InvalidEntityID

    return {"title": data[PRESENCE_SENSOR]}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH



    def __init__(self):
        self.data: dict[str, dict[str, str]] = {}
        self.number_of_sensors = 0

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
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
                if user_input.get("add_another", True):
                    return await self.async_step_user(user_input)
                else:
                    return self.async_create_entry(title=CONF_HOME_OCCUPANCY, data=user_input)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class InvalidEntityID(exceptions.InvalidEntityFormatError):
    """Error to indicate invalid entity_id."""

