# Home Occupancy for Home Assistant

Keeps track of home occupancy using the following:
- Any number of `device_tracker` or `person` entity IDs.
- Any number in `input_boolean`, e.g., an `input.boolean.guest_mode`.

Provides the following:

| Name           | Possible states | Explanation                                                                                 |
|----------------|-----------------|---------------------------------------------------------------------------------------------|
| State          | on, off         | whether anyone is home                                                                      |
| Last to arrive | $NAME           | $NAME of last person to arrive                                                              |
| Last to leave  | $NAME           | $NAME of last person to leave                                                               |
| Known people   | integer         | Number of known people home. "Known people" are from `person` or `deveice_tracker` entities |
| Who is home    | $NAME_LIST      | List of $NAME of everyone home. Taken from `person` or `deveice_tracker` name               |
| Guests         | bool            | Whether an entity ID with the string "guest" in it is home/on                               |

## Installation

### Option 1: HACS

- Go to HACS -> Integrations,
- Click the three dots in top right corner
- Select `Custom repositories`
- Add this repository url (`https://github.com/Aephir/ha-home-occupancy`)
- Select +,
- Search for "home occupancy" and install it,
- Restart Home Assistant

### Option 2: Manual

Download the latest release

```
cd YOUR_HASS_CONFIG_DIRECTORY- # same place as configuration.yaml
mkdir -p custom_components/home_occupancy
cd custom_components/home_occupancy
unzip ha-home-occupancy-X.Y.Z.zip
mv ha-home-occupancy-X.Y.Z/custom_components/home_occupancy/* .  
```

- Restart Home Assistant

## Setup

- Go to Settings -> Devices & Services
- Select + Add Integration
- Search for `home occupancy` and select it
- Fill in the required values (see below) and press Submit

### Current setup values
You will be asked to provide one or more inputs. These must be Home Assistant entity IDs. Currently, the following are supported:
- `binary_sensor`
- `person`
- `device_tracker`

For each, provide a valid sensor and name.

__OBS!__ This integration does not take into account that several sensors could belong to the same person. As such, it's probably most sensible to use either `person.*` or create your own combined presence sensor, if you have more trackers for each person. 