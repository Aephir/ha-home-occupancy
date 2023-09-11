from __future__ import annotations
from typing import Any
import asyncio
from datetime import timedelta
from collections.abc import Callable
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant import config_entries, core
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
    STATE_HOME,
    STATE_NOT_HOME
)
from homeassistant.helpers.event import (
    async_track_state_change
)
from homeassistant.helpers.event import async_track_time_interval
import logging
from .const import (
    DOMAIN,
    OCCUPANCY_SENSOR,
    PRESENCE_SENSOR,
    STATE_AWAY,
    CONF_NAME,
    ATTR_FRIENDLY_NAME,
    ATTR_GUESTS,
    ATTR_KNOWN_PEOPLE,
    ATTR_LAST_TO_ARRIVE_HOME,
    ATTR_LAST_TO_LEAVE,
    ATTR_WHO_IS_HOME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
) -> None:
    """Add sensors for passed config_entry in HA."""
    _LOGGER.error("Setting up binary_sensor for Home Occupancy.")
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)

    # Initialize the binary_sensor with the configuration
    binary_sensors = [HomeOccupancyBinarySensor(hass, config)]
    async_add_entities(binary_sensors, update_before_add=True)


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: Callable,
        discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    binary_sensors = [config[OCCUPANCY_SENSOR]]
    async_add_entities(binary_sensors, update_before_add=True)


class HomeOccupancyBinarySensor(Entity):
    """Occupancy Sensor."""

    def __init__(self, hass: core.HomeAssistant, config):
        super().__init__()
        self.attrs: dict[str, Any] = {ATTR_FRIENDLY_NAME: "Home occupancy"}
        self._name = OCCUPANCY_SENSOR
        self._state = None
        self._available = True
        self._attr_unique_id = f"combined_{self._name}"
        self.config = config
        self.home_states: list[str] = [STATE_ON, STATE_HOME]
        self.away_states: list[str] = [STATE_OFF, STATE_NOT_HOME, STATE_AWAY]
        self.hass = hass
        self.presence_sensors: list[str]

    async def async_added_to_hass(self):
        """Run when entity is added to hass."""
        self.presence_sensors = [self.config[key][PRESENCE_SENSOR] for key in self.config if key.startswith("sensor_")]

        async_track_state_change(
            self.hass,
            self.presence_sensors,
            self.async_track_home,
            self.away_states,
            self.home_states
        )

        async_track_state_change(
            self.hass,
            self.presence_sensors,
            self.async_track_home,
            self.home_states,
            self.away_states
        )

        async_track_time_interval(
            self.hass,
            self.async_update,
            timedelta(minutes=10)
        )

        await asyncio.sleep(15)  # Delete once you have a better solution.
        await self.async_update()

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._attr_unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> str | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.attrs

    async def async_update(self) -> None:
        """Update binary_sensor"""

        _LOGGER.debug("Updating home occupancy sensor.")
        # _LOGGER.error(f"Config values: {self.config.values()}")
        guest_sensors = [val[PRESENCE_SENSOR] for val in self.config.values() if
                         isinstance(val, dict) and CONF_NAME in val and "guest" in val[CONF_NAME].lower()]
        if guest_sensors:
            guest_sensor_entity_id = guest_sensors[0]
        else:
            guest_sensor_entity_id = None
        if guest_sensor_entity_id:
            self.attrs[ATTR_GUESTS] = self.check_is_on(guest_sensor_entity_id)
        else:
            self.attrs[ATTR_GUESTS] = None
        self.who_is_home()

    def who_is_home(self):
        who_is_home = [
            self.config[f"sensor_{i + 1}"]["name"]
            for i in range(self.config["number_of_sensors"])
            if self.hass.states.get(self.config[f"sensor_{i + 1}"]["presence_sensor"]) and
               self.hass.states.get(self.config[f"sensor_{i + 1}"]["presence_sensor"]).state.lower() == "home"
        ]
        # who_is_home = [val[CONF_NAME] for val in self.config.values() if isinstance(val, dict) and CONF_NAME in val]
        self.attrs[ATTR_KNOWN_PEOPLE] = str(len(who_is_home))
        self.attrs[ATTR_WHO_IS_HOME] = self.comma_separated_list_to_string(who_is_home)
        _LOGGER.debug(f"Who is home: {who_is_home}.")

    async def async_track_home(self, entity_id, old_state, new_state) -> None:
        """Track state changes of associated device_tracker, persson, and binary_sensor entities"""

        _LOGGER.debug(f"Entity {entity_id} changed from {old_state} to {new_state}.")

        who_is_home = [val[CONF_NAME] for val in self.config.values() if isinstance(val, dict) and CONF_NAME in val]
        _LOGGER.debug(f"Who is home: {who_is_home}.")
        self.attrs[ATTR_KNOWN_PEOPLE] = str(len(who_is_home))
        self.attrs[ATTR_WHO_IS_HOME] = self.comma_separated_list_to_string(who_is_home)
        if new_state in self.home_states:
            self.attrs[ATTR_LAST_TO_ARRIVE_HOME] = [
                self.config[key][CONF_NAME] for key, val in self.config.items() if val[PRESENCE_SENSOR] == entity_id
            ][0]
        if new_state in self.away_states:
            self.attrs[ATTR_LAST_TO_LEAVE] = [
                self.config[key][CONF_NAME] for key, val in self.config.items() if val[PRESENCE_SENSOR] == entity_id
            ][0]

        anyone_home = any(self.check_is_on(sensor) for sensor in self.presence_sensors)
        for sensor in self.presence_sensors:
            self.check_is_on(sensor)
        self._state = STATE_ON if anyone_home else STATE_OFF
        _LOGGER.debug(f"Setting home occupancy sensor's state to: {self._state}")

        self.async_schedule_update_ha_state()

    def check_is_on(self, entity_id) -> bool:
        """Check state of entity (Synchronous version)"""
        _LOGGER.debug(f"Checking entity ID {entity_id}.")
        entity = self.hass.states.get(entity_id)
        _LOGGER.debug(f"Entity {entity_id} state: {entity.state}")
        if entity:
            is_home = entity.state in self.home_states
            _LOGGER.debug(
                f"Entity {entity_id} state: {entity.state}, considered home: {is_home}. Home states: {self.home_states}")
            return is_home
        _LOGGER.warning(f"Entity {entity_id} not found.")
        return False

    @staticmethod
    def comma_separated_list_to_string(input_list: list[str]) -> str:
        """Creates a string of a list in human-readable format"""

        who_is_home: str = ""
        length = len(input_list)

        if length == 1:
            return str(input_list)
        else:
            for i in range(length):
                if (i - 2) < length:
                    who_is_home += input_list[i] + ", "
                else:
                    who_is_home += input_list[i] + ", and " + input_list[i + 1]
                    return who_is_home
