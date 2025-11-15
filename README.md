# DigiTraffic Road Conditions and TMS data

A Home Assistant custom integration that provides real-time road conditions and traffic data from Finland's Digitraffic service (https://www.digitraffic.fi/).

## Features

### 🚗 Road Conditions Monitoring
- **Current Conditions**: Real-time driving conditions for specific road sections
- **Weather Forecast**: Time-stamped hourly forecasts with road condition predictions
- **Smart Resolution**: Automatically finds road sections by entering road names or titles from the Fintraffic map
- **Bilingual Support**: Full Finnish and English language support

### 📊 Traffic Measurement Stations (TMS/LAM)
- **Speed Measurements**: Rolling and fixed average speeds in both directions
- **Traffic Counts**: Vehicle overtaking counts per direction and lane
- **Sensor Constants**: Access to station-specific calibration values (VVAPAAS, lane references)
- **Per-Station Metrics**: Multiple sensors per station for comprehensive traffic monitoring

### ⚙️ Integration Features
- **Multi-language UI**: Choose between Finnish and English during setup
- **Flexible Search**: Search by road number (e.g., "VT4"), location name, or exact road section title
- **Multiple Instances**: Monitor unlimited road sections and TMS stations simultaneously
- **Auto-updates**: Data refreshes every 5 minutes
- **Reliability Indicators**: Shows data quality percentage for road conditions

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **⋮** (menu) → **Custom repositories**
3. Add repository URL: `https://github.com/EightEFI/DigiTraffic`
4. Category: **Integration**
5. Click **Download** on the DigiTraffic integration
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract and copy the `custom_components/digitraffic_road` folder to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

## Configuration

### Adding Road Condition Monitoring

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**DigiTraffic**"
3. **Select Language**: Choose Finnish or English
4. **Choose Type**: Select "Ajokeli tieosuudella" (Road conditions)
5. **Find Your Road Section**:
   - Open [Fintraffic road conditions map](https://liikennetilanne.fintraffic.fi/kartta/)
   - Click on any road section to see its details
   - Copy the title shown (e.g., "Tie 3: Valtatie 3 3.250")
   - Paste into the integration setup
6. If multiple matches are found, select the exact section from the dropdown

The integration will create two entities:
- **Current Conditions** sensor (e.g., `sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä`)
- **Forecast** sensor (e.g., `sensor.valtatie_3_3_250_ennuste`)

### Adding Traffic Measurement Station (TMS/LAM)

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**DigiTraffic**"
3. **Select Language**: Choose Finnish or English
4. **Choose Type**: Select "Liikenteen automaattinen mittausasema (LAM)"
5. **Search for Station**: Enter road name and location (e.g., "Tie 3 Vaasa")
6. Select the desired station from search results

The integration creates multiple sensors per station:
- Speed measurements (rolling/fixed averages, both directions)
- Traffic counts (overtakes per direction and lane)
- Sensor constants (calibration values)

## Entities

### Road Condition Sensors

#### Current Conditions Sensor
**Entity ID**: `sensor.<road_section>_ajokeli_tällä_hetkellä` (Finnish) / `sensor.<road_section>_current_conditions` (English)

**State**: Current road condition text
- Finnish examples: "Kuiva", "Märkä", "Jäätä", "Hyvä ajokeli"
- English examples: "Dry", "Wet", "Ice", "Good driving conditions"

**Attributes**:
- `reliability`: Data reliability percentage (0-100)
- `last_updated`: ISO timestamp of last data update

#### Forecast Sensor
**Entity ID**: `sensor.<road_section>_ennuste` (Finnish) / `sensor.<road_section>_forecast` (English)

**State**: Multi-line forecast with times and conditions
```
10:00 Hyvä ajokeli, kuiva
12:00 Hyvä ajokeli, märkä
14:00 Huono ajokeli, jäätä
16:00 Erittäin huono ajokeli, lunta
```

**Attributes**:
- `forecast_data`: List of forecast entries with `time` and `condition` fields

### TMS/LAM Measurement Sensors

Each TMS station creates multiple sensors for different measurements:

#### Speed Sensors
- `sensor.<station>_keskinopeus_5min_liukuva_suunta1` - Rolling avg speed 5min direction 1
- `sensor.<station>_keskinopeus_5min_liukuva_suunta2` - Rolling avg speed 5min direction 2
- `sensor.<station>_keskinopeus_60min_kiintea_suunta1` - Fixed avg speed 60min direction 1
- And more variations with percentage of free-flow speed

#### Traffic Count Sensors
- `sensor.<station>_ohitukset_5min_liukuva_suunta1` - Rolling count overtakes 5min direction 1
- `sensor.<station>_ohitukset_60min_kiintea_suunta1` - Fixed count overtakes 60min direction 1
- Lane-specific counts (MS1, MS2) for detailed traffic analysis

#### Sensor Constants
- `sensor.<station>_sensor_constants` - Station calibration values as attributes

## Road Condition Reference

### Finnish Conditions (API Values → Display Text)
- **DRY** → Kuiva (Dry road surface)
- **WET** → Märkä (Wet road surface)
- **MOIST** → Kostea (Damp road surface)
- **FROST** → Kuuraa (Hoarfrost on road)
- **ICE** → Jäätä (Ice on road)
- **PARTLY_ICY** → Osittain jäätä (Patches of ice)
- **SLUSH** → Loskaa (Slush on road)
- **SNOW** → Lunta (Snow on road)

### Overall Driving Conditions
- **NORMAL_CONDITION** → Hyvä ajokeli / Good driving conditions
- **POOR_CONDITION** → Huono ajokeli / Poor driving conditions
- **EXTREMELY_POOR_CONDITION** → Erittäin huono ajokeli / Extremely poor driving conditions

## Usage Examples

### Automation: Poor Road Conditions Alert

```yaml
automation:
  - alias: "Alert on icy road conditions"
    trigger:
      - platform: state
        entity_id: sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä
    condition:
      - condition: template
        value_template: >
          {{ 'jäätä' in trigger.to_state.state.lower() or 
             'huono ajokeli' in trigger.to_state.state.lower() }}
    action:
      - service: notify.mobile_app_phone
        data:
          title: "⚠️ Road Conditions Alert"
          message: "{{ trigger.to_state.state }} - Drive carefully!"
```

### Automation: Slow Traffic Alert (TMS)

```yaml
automation:
  - alias: "Traffic slowdown notification"
    trigger:
      - platform: numeric_state
        entity_id: sensor.vt4_marostenmaki_keskinopeus_5min_liukuva_suunta1
        below: 60
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Traffic slowdown on VT4: {{ states('sensor.vt4_marostenmaki_keskinopeus_5min_liukuva_suunta1') }} km/h"
```

### Template Sensor: Combined Road Status

```yaml
template:
  - sensor:
      - name: "Road Status Summary"
        unique_id: road_status_summary
        state: >
          {% set condition = states('sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä') %}
          {% set reliability = state_attr('sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä', 'reliability') %}
          {{ condition }} ({{ reliability }}% reliable)
        icon: >
          {% if 'jäätä' in states('sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä').lower() %}
            mdi:snowflake-alert
          {% elif 'märkä' in states('sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä').lower() %}
            mdi:water
          {% else %}
            mdi:road
          {% endif %}
```

### Dashboard Card

```yaml
type: vertical-stack
cards:
  - type: entities
    title: VT3 Road Conditions
    entities:
      - entity: sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä
        name: Current
      - type: attribute
        entity: sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä
        attribute: reliability
        name: Reliability
        suffix: "%"
  
  - type: markdown
    content: |
      ## 6-Hour Forecast
      {{ states('sensor.valtatie_3_3_250_ennuste') }}
```

## Technical Details

### Data Sources

The integration fetches data from official Digitraffic API endpoints:

**Road Conditions**:
- Forecast sections: `https://tie.digitraffic.fi/api/weather/v1/forecast-sections/forecasts`
- Metadata: `https://tie.digitraffic.fi/api/weather/v1/forecast-sections`

**TMS Stations**:
- Stations list: `https://tie.digitraffic.fi/api/tms/v1/stations`
- Station data: `https://tie.digitraffic.fi/api/tms/v1/stations/{id}/data`
- Sensor constants: `https://tie.digitraffic.fi/api/tms/v1/stations/{id}/sensor-constants`

### Update Interval

Data is fetched every **5 minutes** (300 seconds). This can be modified in `custom_components/digitraffic_road/const.py`:

```python
UPDATE_INTERVAL = 300  # seconds
```

### Smart Section Resolution

The integration uses intelligent matching to find road sections:

1. **Exact match**: Checks for exact normalized description matches
2. **Numeric parsing**: Extracts road number and km marker (e.g., "Valtatie 3 3.250" → road 3, section 250)
3. **Token overlap**: Scores sections by matching words from your search
4. **Forecast tie-breaking**: When multiple sections match equally, prefers those with active forecast data

## Troubleshooting

### Cannot Connect During Setup

**Issue**: Integration shows connection error when adding

**Solutions**:
1. Check Home Assistant has internet access
2. Verify firewall allows connections to `tie.digitraffic.fi`
3. Check logs: **Settings** → **System** → **Logs**, search for `digitraffic_road`
4. Try again in a few minutes (API may be temporarily unavailable)

### No Road Section Found

**Issue**: Search returns no results

**Solutions**:
1. Try a simpler search term (e.g., "Tie 3" instead of full title)
2. Try road number only (e.g., "VT4" or "3")
3. Check spelling of location names
4. Verify the section exists on [Fintraffic map](https://liikennetilanne.fintraffic.fi/kartta/)

### Entities Show "Unavailable"

**Issue**: Sensors created but show no data

**Solutions**:
1. Enable debug logging:
   ```yaml
   logger:
     logs:
       custom_components.digitraffic_road: debug
   ```
2. Restart Home Assistant
3. Wait 5 minutes for first data update
4. Check logs for API errors
5. Verify the section ID is valid (check logs for resolved ID)

### TMS Measurements Not Updating

**Issue**: TMS sensors show no values or old data

**Solutions**:
1. Verify the TMS station is active on Digitraffic
2. Some measurements may not be available for all stations
3. Check `sensor.<station>_sensor_constants` attributes to see what the station provides
4. Enable debug logging to see API responses

## Debug Logging

Enable detailed logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.digitraffic_road: debug
    custom_components.digitraffic_road.client: debug
    custom_components.digitraffic_road.coordinator: debug
```

Then check **Settings** → **System** → **Logs** for detailed information.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests on GitHub.

**Repository**: https://github.com/EightEFI/DigiTraffic

## License

This project is licensed under the terms specified in the LICENSE file.

## Disclaimer

This integration is **not officially affiliated** with:
- Finnish Transport Infrastructure Agency (Väylävirasto)
- Fintraffic Ltd
- Digitraffic service

The data is provided as-is from the public Digitraffic API. Always use official sources and your own judgment for critical driving decisions. This integration is for informational purposes only.

---

**Data provided by**: [Digitraffic](https://www.digitraffic.fi/) - Licensed under CC 4.0 BY  
**Made with ❤️ for the Home Assistant community**
