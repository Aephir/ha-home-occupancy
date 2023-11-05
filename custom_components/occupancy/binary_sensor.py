from __future__ import annotations
from typing import Any
import asyncio
from datetime import timedelta
from collections.abc import Callable
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant import config_entries, core
from homeassistant.core import CoreState, callback
from homeassistant.const import EVENT_HOMEASSISTANT_START
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
    _LOGGER.debug("Setting up entry for Home Occupancy.")
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
    _LOGGER.debug("Setting up platform for Home Occupancy.")
    binary_sensors = [config[OCCUPANCY_SENSOR]]
    async_add_entities(binary_sensors, update_before_add=True)


class HomeOccupancyBinarySensor(Entity):
    """Occupancy Sensor."""

    def __init__(self, hass: core.HomeAssistant, config):
        _LOGGER.debug("Initializing HomeOccupancyBinarySensor class for Home Occupancy.")
        super().__init__()
        self.attrs: dict[str, Any] = {ATTR_FRIENDLY_NAME: "Home occupancy"}
        self._name = OCCUPANCY_SENSOR
        self.entity_id = f"binary_sensor.{DOMAIN}_{self._name}"
        self._attr_unique_id = f"{DOMAIN}_{self._name}_unique_id"
        self._state = None
        self._available = True
        self._attr_unique_id = f"combined_{self._name}"
        self.config = config
        self.home_states: list[str] = [STATE_ON, STATE_HOME]
        self.away_states: list[str] = [STATE_OFF, STATE_NOT_HOME, STATE_AWAY]
        self.hass = hass
        self.presence_sensors: list[str] = []
        self.last_to_leave = None
        self.last_to_arrive = None

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

        async_track_time_interval(
            self.hass,
            self.async_update,
            timedelta(minutes=10)
        )

        # await asyncio.sleep(15)  # Delete once you have a better solution.
        # await self.async_update()
        if self.hass.state == CoreState.running:
            await self.async_update()
        else:
            @callback
            def _async_set_initial_state(_):
                self.hass.async_create_task(self.async_update())

            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_set_initial_state)

        _LOGGER.debug(f"Presence sensors list: {self.presence_sensors}")

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

    # @property
    # def extra_state_attributes(self) -> dict[str, Any]:
    #     return self.attrs

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            'last_to_leave': self.last_to_leave,
            'last_to_arrive': self.last_to_arrive,
            **self.attrs  # Include other attributes already set in self.attrs
        }

    async def async_update(self, now=None) -> None:
        """Update binary_sensor"""

        # Retrieve guest sensor state
        guest_sensors = [val[PRESENCE_SENSOR] for val in self.config.values() if
                         isinstance(val, dict) and CONF_NAME in val and "guest" in val[CONF_NAME].lower()]
        guest_sensor_entity_id = guest_sensors[0] if guest_sensors else None
        guest_present = self.check_is_on(guest_sensor_entity_id) if guest_sensor_entity_id else None

        # Calculate who is home and other attributes
        new_attrs = self.who_is_home()
        new_attrs[ATTR_GUESTS] = guest_present

        # Determine if anyone is home
        anyone_home = any(self.check_is_on(sensor) for sensor in self.presence_sensors)
        new_state = STATE_ON if anyone_home else STATE_OFF

        # Check for changes in attributes and state
        attributes_changed = any(self.attrs.get(attr) != new_attrs.get(attr) for attr in new_attrs)
        state_changed = self._state != new_state

        # Update state and attributes if there are changes
        if state_changed or attributes_changed:
            self._state = new_state
            self.attrs.update(new_attrs)
            self.async_write_ha_state()  # This will schedule an update to HA

    def who_is_home(self) -> dict:
        """Determine who is home and return attributes."""
        who_is_home = [
            self.config[f"sensor_{i + 1}"]["name"]
            for i in range(self.config["number_of_sensors"])
            if self.hass.states.get(self.config[f"sensor_{i + 1}"][PRESENCE_SENSOR]) and
               self.hass.states.get(self.config[f"sensor_{i + 1}"][PRESENCE_SENSOR]).state.lower() == "home"
        ]

        # Construct the dictionary of attributes
        attributes = {
            ATTR_KNOWN_PEOPLE: str(len(who_is_home)),
            ATTR_WHO_IS_HOME: self.comma_separated_list_to_string(who_is_home),
            # Include other attributes like last_to_leave and last_to_arrive if needed
        }

        return attributes

    async def async_track_home(self, entity_id, old_state, new_state) -> None:
        """Track state changes of associated device_tracker, person, and binary_sensor entities"""

        if old_state == new_state:
            return

        # Retrieve the person's name associated with the entity_id from self.config
        person_name = next((config[CONF_NAME] for key, config in self.config.items()
                            if PRESENCE_SENSOR in config and config[PRESENCE_SENSOR] == entity_id), "unknown")

        # Get current attributes and see if they will change
        new_attrs = self.who_is_home()
        if new_state.state in self.home_states:
            new_attrs[ATTR_LAST_TO_ARRIVE_HOME] = person_name
        if new_state.state in self.away_states:
            new_attrs[ATTR_LAST_TO_LEAVE] = person_name

        # Check for changes in attributes
        attributes_changed = any(self.attrs.get(attr) != new_attrs.get(attr) for attr in new_attrs)

        # Determine if anyone is home
        anyone_home = any(self.check_is_on(sensor) for sensor in self.presence_sensors)
        new_sensor_state = STATE_ON if anyone_home else STATE_OFF

        # Check if the state or any attributes have changed before updating
        if self._state != new_sensor_state or attributes_changed:
            self._state = new_sensor_state
            self.attrs.update(new_attrs)
            self.async_write_ha_state()

    def check_is_on(self, entity_id) -> bool:
        """Check state of entity (Synchronous version)"""
        entity = self.hass.states.get(entity_id)
        if entity:
            is_home = entity.state in self.home_states
            return is_home
        return False

    @staticmethod
    def comma_separated_list_to_string(input_list: list[str]) -> str:
        """Creates a string of a list in human-readable format"""

        who_is_home: str = ""
        length = len(input_list)

        if length == 1:
            who_is_home = input_list[0]
        elif length == 2:
            who_is_home = input_list[0] + " and " + input_list[1]
        else:
            for i in range(length):
                if (i - 2) < length:
                    who_is_home += input_list[i] + ", "
                else:
                    who_is_home += input_list[i] + ", and " + input_list[i + 1]
        return who_is_home
