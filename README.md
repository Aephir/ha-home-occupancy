# Home Occupancy for Home Assistant

__OBS!__ This should be considered alpha, perhaps very early beta. I will not have much time to work on this, so this state might persist for quite some time.
You are of course welcome to fork (or ask to be added as maintainer) if you feel like you can contribute.
Otherwise, please use only if you don't need this for anything crucial. 

## Installation

### Option 1: HACS

- Go to HACS -> Integrations,
- Click the three dots in top right corner
- Select `Custom repositories`
- Add this repository url (`https://github.com/Aephir/ha-home-occupancy`)
- Select +,
- Search for ``home occupancy and install it,
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