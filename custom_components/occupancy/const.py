DOMAIN = "home_occupancy"
PRESENCE_SENSOR = "presence_sensor"
OCCUPANCY_SENSOR = "home_occupancy"
CONF_NAME = "name"
CONF_HOME_OCCUPANCY = "Home Occupancy"
STATE_AWAY = "away"
CONF_ADD_ANOTHER = "add_another"

ATTR_FRIENDLY_NAME = "friendly_name"
ATTR_GUESTS = "guests"
ATTR_KNOWN_PEOPLE = "known_people"
ATTR_LAST_TO_ARRIVE = "last_to_arrive"
ATTR_LAST_TO_LEAVE = "last_to_leave"
ATTR_WHO_IS_HOME = "who_is_home"

VERSION = "0.2.0"

STARTUP = """
  ___
/  _  \    ___    ___    _   _    ____      __   _   _   _      __   _    _
| | | |   / __\  / __\  | | | |  |  _  \   / _ \´ | | `´_ \   / __\ | |  | |
| |_| |  | |__  | |__   | |_| |  | |_| /  | |_| | | | |  ` | | |__  | \_/  |
\_____/   \___/  \___/   \___/   |  __/    \___´`_| |_|  |_|  \___/  \___/ |
                                 | |                                  __/ /
                                 |_|                                 /___/

An occupancy binary_sensor that incorporates any person.*, device_tracker.* or binary_senor.*
This means including e.g. a binary_senor.guest_mode in the occupancy sensor.
Additionally, it keeps a list of who is home, and who was the last to arrive/leave. 
"""