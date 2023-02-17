from __future__ import annotations
from typing import Any, List
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
    STATE_NOT_HOME,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE
)
from homeassistant.helpers.event import (
    async_track_state_change
)

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


async def async_setup_entry(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
) -> None:
    """Add sensors for passed config_entry in HA."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)
    device_class = BinarySensorDeviceClass.OCCUPANCY
    binary_sensors = [config[OCCUPANCY_SENSOR]]
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

    def __int__(self, hass: core.HomeAssistant, config):
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

        presence_sensors: list[str] = [self.config[f"sensor_{i}"][PRESENCE_SENSOR] for i in range(len(self.config))]

        home_handle = async_track_state_change(
            self.hass,
            presence_sensors,
            self.async_track_home,
            self.away_states,
            self.home_states
        )

        away_handle = async_track_state_change(
            self.hass,
            presence_sensors,
            self.async_track_home,
            self.home_states,
            self.away_states
        )

        self.attrs[ATTR_GUESTS] = self.async_is_on(
            [val[PRESENCE_SENSOR] for val in self.config.values() if "guest" in val[CONF_NAME].lower()][0]
        )

    async def async_track_home(self, entity_id, old_state, new_state) -> None:
        """Track state changes of associated device_tracker, persson, and binary_sensor entities"""

        who_is_home = [self.config[f"sensor_{i}"][CONF_NAME] for i in range(len(self.config))]
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

    async def async_is_on(self, entity_id) -> bool:
        """Check state of entity"""

        entity_state = self.hass.states.get(entity_id).state

        return entity_state in self.home_states

    def comma_separated_list_to_string(self, input_list: list[str]) -> str:
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
