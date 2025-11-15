# Digitraffic Road Conditions Integration

A custom Home Assistant integration that fetches real-time road condition data from the Finnish Digitraffic service (https://www.digitraffic.fi/).

## Features

- **Real-time road conditions**: Get current driving conditions for your selected road section
- **12-hour forecast**: View weather and road condition forecasts for the next 12 hours
- **Multiple road sections**: Add multiple instances to monitor different road sections
- **Automatic updates**: Data refreshes every 5 minutes (configurable)
- **Reliability indicator**: Shows data reliability percentage for informed decision making
- **Finnish localization**: All road conditions displayed in Finnish

## Installation

### Via HACS

1. Open HACS in Home Assistant
2. Click on "Custom repositories"
3. Add `https://github.com/EightEFI/Digitraffic-road-conditions` as repository with category "Integration"
4. Click "Install"
5. Restart Home Assistant

### Manual Installation

1. Copy the `digitraffic_road` folder to `custom_components/` in your Home Assistant configuration directory
2. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **Create Integration** and search for "Digitraffic Road Conditions"
3. Open the [Fintraffic road conditions map](https://liikennetilanne.fintraffic.fi/kartta/)
4. Click on any specific road section you want to monitor
5. Copy the exact title shown (e.g., "Tie 4: Kemintie 4.421")
6. Paste it into the integration setup form
7. The integration will create two entities for this specific section:
   - **Current Conditions**: Shows the current road conditions in Finnish
   - **12h Forecast**: Shows the road condition forecast for the next 12 hours

## Entities

### Sensor: Current Conditions
- **Entity ID**: `sensor.<section_name>_current_conditions`
- **State**: Current road condition in Finnish (e.g., "Tienpinta on kuiva", "Tienpinnassa on märkää")
- **Attributes**:
  - `reliability`: Data reliability percentage (0-100)
  - `last_updated`: Last update timestamp from the API

### Sensor: 12h Forecast
- **Entity ID**: `sensor.<section_name>_12h_forecast`
- **State**: Multi-line forecast showing times and Finnish road conditions
- **Attributes**:
  - `forecast_data`: Structured forecast data with time and condition

Example forecast output:
```
10:00 Tienpinta on kuiva
12:00 Tienpinnassa on märkää
14:00 Tienpinnassa on paikoin jäätä
16:00 Liukasta, tienpinnassa on jäätä tai lunta
```

## Available Road Sections

You can monitor **any specific road section** from Finland by copying the exact title from the [Fintraffic road conditions map](https://liikennetilanne.fintraffic.fi/kartta/).

Simply:
1. Click on a road section in the map
2. Copy the title (e.g., "Tie 4: Kemintie 4.421")
3. Paste it into the integration setup

This gives you precise, location-specific driving conditions rather than broad road regions.

## Road Condition Descriptions

The integration uses Finnish road condition descriptions:

- **Tienpinta on kuiva** - Road surface is dry
- **Tienpinnassa on märkää** - Road is wet
- **Tienpinnassa on paikoin jäätä** - Patches of ice on road
- **Tienpinnassa on mahdollisesti kuuraa** - Possible hoarfrost on road
- **Liukasta, tienpinnassa on jäätä tai lunta** - Slippery, ice or snow on road
- **Lumisade tai rankka sade** - Snow or heavy rain
- **Raskas lumisade** - Heavy snow
- **Hyvät ajokeli** - Good driving conditions
- **Huonot ajokeli** - Poor driving conditions

## Usage Examples

### Automations

Alert when poor road conditions are detected:

```yaml
automation:
  - alias: "Alert on poor road conditions"
    trigger:
      platform: state
      entity_id: sensor.kemintie_current_conditions
      to:
        - "Liukasta, tienpinnassa on jäätä tai lunta"
        - "Raskas lumisade"
        - "Huonot ajokeli"
    action:
      service: notify.mobile_app
      data:
        message: "Poor conditions on Kemintie!"
```

### Template Sensors

Create a reliability indicator:

```yaml
template:
  - sensor:
      - name: "E18 Reliability"
        unique_id: e18_reliability
        state: "{{ state_attr('sensor.e18_current_conditions', 'reliability') }}%"
```

### Dashboard Card

Display road conditions on your dashboard:

```yaml
type: entities
entities:
  - entity: sensor.kemintie_current_conditions
  - entity: sensor.kemintie_12h_forecast
title: Road Conditions - Kemintie
```

## Data Update Interval

By default, road condition data is updated every 5 minutes. To modify this, you can edit the `UPDATE_INTERVAL` constant in `const.py`.

## Troubleshooting

### "Cannot Connect" Error During Setup

1. Check Home Assistant logs: Settings → System → Logs, search for `digitraffic_road`
2. Verify your Home Assistant instance has internet access
3. Try restarting Home Assistant
4. Check if any firewall is blocking connections to digitraffic.fi

### Entities Not Showing Data

1. Enable debug logging in your `configuration.yaml`:
   ```yaml
   logger:
     logs:
       custom_components.digitraffic_road: debug
   ```
2. Restart Home Assistant and check Settings → System → Logs
3. Wait up to 5 minutes for the first data update

### Integration Not Appearing in Add Integration

1. Restart Home Assistant
2. Clear your browser cache
3. Verify the integration files are in `custom_components/digitraffic_road/`

## Debug Logging

Enable detailed logging for troubleshooting:

```yaml
logger:
  logs:
    custom_components.digitraffic_road: debug
```

Restart Home Assistant and check the logs for diagnostic information.

## Support

For issues, feature requests, or contributions:
https://github.com/EightEFI/Digitraffic-road-conditions/issues

## License

See the LICENSE file for details.

## Disclaimer

This integration is not affiliated with the Finnish Transport Infrastructure Agency (Väylävirasto). The data is provided as-is from the Digitraffic API. Use at your own discretion for informational purposes.
