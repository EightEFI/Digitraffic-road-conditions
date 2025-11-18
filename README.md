# FinTraffic Road Conditions, TMS data and Road Weather Station data

A Home Assistant custom integration that provides real-time road conditions and traffic data from Finland's [DigiTraffic](https://www.digitraffic.fi/) service's open data sources in Finnish and English. DigiTraffic is service for the open data for application development from Finnish road, railway and marine traffic. One of the most well known services that use DigiTraffic data is the [FinnTraffic map](https://liikennetilanne.fintraffic.fi/kartta/). [FinTraffic](https://www.fintraffic.fi/fi) is a special-purpose group which is fully owned by the Finnish state.

## Features

### 🚗 Road Conditions / Ajokeli
- **Current Conditions**: Real-time driving conditions for specific road sections
- **Weather Forecast**: Time-stamped hourly forecasts with road condition predictions
- **Smart Resolution**: Automatically finds road sections by entering road names or titles from the Fintraffic map

### 📊 Traffic Measurement Stations / Liikenteen Automaattinen Mittausasema (TMS/LAM)
- **Speed Measurements**: Rolling and fixed average speeds in both directions
- **Traffic Counts**: Vehicle overtaking counts per direction and lane
- **Sensor Constants**: Access to station-specific calibration values (VVAPAAS, lane references)
- **Per-Station Metrics**: Multiple sensors per station for comprehensive traffic monitoring

### 🌡 Road Weather Stations / Tiesääasemat
- **Live Measurements**: Air, road-surface and ground temperatures, dew point, humidity, wind, precipitation, visibility, and more
- **Smart Entity Management**: Only 11 essential sensors enabled by default - enable additional sensors as needed
- **Dynamic Sensors**: Entities appear only for measurements the station actually reports, with new sensors added automatically when new data streams become active
- **Textual States**: Weather descriptions (WMO codes), precipitation forms, warnings and road-condition codes rendered in Finnish or English based on integration language
- **212 Translated Datapoints**: All measurement types have proper Finnish and English translations

### ⚙️ Integration Features
- **Multi-language UI**: Choose between Finnish and English during setup
- **Search with FinTraffic titles**: Search by road section name (e.g., "Tie 3: Valtatie 3 3.250") or TMS/LAM name (e.g., "vt4 Simo Saukkoranta")
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

### Quick Start

Before setting up the integration, find the road section(s), traffic station(s) or road weather station(s) you want to monitor:

1. **Open the Fintraffic map**: [https://liikennetilanne.fintraffic.fi/kartta/](https://liikennetilanne.fintraffic.fi/kartta/)
2. **For Road Conditions**: On the map layers, activate Road Conditions. Click on any road section you want to add to HA (colored lines on the map) and copy the title shown (e.g., "Tie 3: Valtatie 3 3.250" or "Tie 10: Turun valtatie 10.24")
3. **For Traffic Stations (LAM/TMS)**: On the map layers, activate Traffic volume, then look for two arrows (<•>), click them, and copy the station name (e.g., "vt4 Simo Saukkoranta" or "Tie 9 Orivesi, Talviainen")
4. **For Road Weather Stations**: On the map layers, activate Weather stations, select the blip icon that has something weather related usually, and copy the station name (e.g., "vt1 Espoo Nupuri")

Keep this information ready - you'll need it during the integration setup!


### Adding Road Condition Monitoring

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**DigiTraffic**
3. **Choose Type**: Select "Ajokeli tieosuudella" or "Driving condition in a road section"
4. **Enter Road Section**: Paste the road section title you copied from the [Fintraffic map](https://liikennetilanne.fintraffic.fi/kartta/) (e.g., "Tie 3: Valtatie 3 3.250")
5. If there are multiple search results, select the desired station from search results, otherwise this step is skipped automatically

The integration will create two entities in the instance of "Tie 3: Valtatie 3 3.250" for example:
- **Current Conditions** sensor (e.g., Eng `sensor.valtatie_3_3_250_current_conditions`, or Fin `sensor.valtatie_3_3_250_ajokeli_tällä_hetkellä`)
- **Forecast** sensor (e.g., Eng `sensor.valtatie_3_3_250_forecast`, or Fin `sensor.valtatie_3_3_250_ennuste`)

### Adding Traffic Measurement Station (TMS/LAM)

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**DigiTraffic**
3. **Choose Type**: Select "Liikenteen automaattinen mittausasema (LAM)" or "Traffic measuring station (TMS)"
4. **Enter Station Name**: Type the station name you noted from the [Fintraffic map under Traffic volume](https://liikennetilanne.fintraffic.fi/kartta/) (e.g., "vt4 Simo Saukkoranta")
5. If there are multiple search results, select the desired station from search results, otherwise this step is skipped automatically

The integration creates multiple sensors per station:
- Speed measurements (rolling/fixed averages, both directions)
- Traffic counts (overtakes per direction and lane)
- Sensor constants

### Adding Road Weather Station

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "**DigiTraffic**"
3. **Choose Type**: Select "Tiesääasema" or "Road weather station"
4. **Enter Station Name**: Paste the station label copied from the [Fintraffic map](https://liikennetilanne.fintraffic.fi/kartta/) (e.g., "vt1 Espoo Nupuri")
5. Pick the exact station if multiple matches are found

The integration creates one sensor per measurement reported by the station (air temperature, road temperature lanes, wind, precipitation, visibility, warnings (diagnostics about sensors), etc.). Sensors appear only for values present in the live API payload, so your entity list matches the station’s capabilities.

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

Read more about datapoints here: https://www.digitraffic.fi/tieliikenne/lam/

### Road Weather Station Sensors

Each weather station exposes entities for every measurement in the live data feed:

- **Core temperatures**: `sensor.<station>_ilma`, `sensor.<station>_tie_1`, `sensor.<station>_maa_1`, etc.
- **Derived metrics**: `sensor.<station>_ilma_derivaatta`, `sensor.<station>_tie_1_derivaatta`, dew point, freezing point
- **Atmospheric data**: humidity, wind speed/direction, visibility, precipitation intensity and amount
- **Qualitative states**: precipitation form (`sensor.<station>_sateen_olomuoto_pwdxx`), road condition lanes, warnings (values rendered as translated text)
- **Weather conditions**: `sensor.<station>_vallitseva_sää` displays human-readable WMO weather descriptions (100 codes translated in Finnish and English)

If a new measurement type starts publishing (for example an additional road-surface probe), the integration will register the matching entity automatically after the next data refresh.

#### Default Enabled Sensors

To avoid overwhelming the UI, only **11 essential weather sensors** are enabled by default:

1. **ILMA** - Air temperature
2. **ILMANPAINE** - Air pressure  
3. **ILMAN_KOSTEUS** - Air humidity
4. **JÄÄN_MÄÄRÄ1** - Ice amount
5. **JÄÄTYMISPISTE_1** - Freezing point
6. **KASTEPISTE** - Dew point
7. **MAA_1** - Ground temperature
8. **SADE_INTENSITEETTI** - Precipitation intensity
9. **VALLITSEVA_SÄÄ** - Prevailing weather (WMO code)
10. **KESKITUULI** - Average wind speed
11. **TUULENSUUNTA** - Wind direction

All other sensors are created but **disabled by default**. You can enable additional sensors in **Settings** → **Devices & Services** → select your weather station → click the entity you want to enable.

#### WMO Weather Codes

The `VALLITSEVA_SÄÄ` (Prevailing Weather) sensor translates numeric WMO Code Table 4677 values to descriptive text:

**Examples:**
- `0` → "Ei merkittävää säätä" (FI) / "No significant weather" (EN)
- `51` → "Jatkuvaa tihkua, heikko" (FI) / "Drizzle, continuous, slight" (EN)
- `61` → "Jatkuvaa vesisadetta, heikko" (FI) / "Rain, continuous, slight" (EN)
- `71` → "Jatkuvaa lumisadetta, heikko" (FI) / "Snow, continuous, slight" (EN)
- `95` → "Heikko tai kohtalainen ukkonen, vesi- tai lumisade" (FI) / "Slight or moderate thunderstorm with rain or snow" (EN)

All 100 WMO codes (0-99) are fully translated and stored in the translation files for easy maintenance.

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


### Dashboard card for Forecast using [Mushroom-template-card](https://github.com/piitaya/lovelace-mushroom)

```yaml
type: custom:mushroom-template-card
primary: Ennuste
icon: mdi:weather-partly-rainy
multiline_secondary: true
secondary: >-
  {% set fc = state_attr('sensor.kemintie_4_421_forecast', 'forecast_data') or
  [] %} {% for item in fc %} {{- '\n' if not loop.first else '' -}} {{
  item['time'] }} {{ item['condition'] }} {% endfor %}
```

![alt text](https://i.imgur.com/uygpAqu.png "Dashboard card using Mushroom-template-card")

### Dashboard card for current conditions using Markdown card

```yaml
type: markdown
content: |
  **Kemintie Vt4 ajokeli**

  {% set cond = states('sensor.kemintie_4_421_current_conditions') %}

  {% if 'Erittäin huono' in cond %}
  <ha-alert alert-type="error">Erittäin huono ajokeli</ha-alert>

  {% elif 'Huono' in cond %}
  <ha-alert alert-type="warning">Huono ajokeli</ha-alert>

  {% elif 'Hyvä' in cond %}
  <ha-alert alert-type="success">Hyvä ajokeli</ha-alert>

  {% else %}
  <ha-alert alert-type="info">{{ cond }}</ha-alert>
  {% endif %}
```

![alt text](https://i.imgur.com/AAOkigF.png "Dashboard card using Mushroom-template-card")

### Automation: Poor Road Conditions Alert

```yaml
alias: Kemintie ajokeli varoitus
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.kemintie_4_421_current_conditions
conditions: []
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: sensor.kemintie_4_421_current_conditions
            state: Huono ajokeli
        sequence:
          - action: notify.mobile_app_phone
            metadata: {}
            data:
              message: ⚠️ Driving conditions are poor
              title: Kemintie
      - conditions:
          - condition: state
            entity_id: sensor.kemintie_4_421_current_conditions
            state: Erittäin huono ajokeli
        sequence:
          - action: notify.mobile_app_phone
            metadata: {}
            data:
              message: ⚠️ Driving conditions are very poor
              title: Kemintie
mode: single
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

### Dashboard Card with ApexCharts-Card

```yaml
type: custom:apexcharts-card
graph_span: 12hours
header:
  show: true
  title: 5 minute rolling average ammount
  show_states: true
  colorize_states: true
apex_config:
  legend:
    show: false
hours_12: false
experimental:
  color_threshold: true
show:
  last_updated: true
series:
  - entity: sensor.vt4_marostenmaki_ohitukset_5min_liukuva_suunta1
    type: line
    stroke_width: 1
    unit: pcs/h
    name: Direction 1
    show:
      legend_value: false
  - entity: sensor.vt4_marostenmaki_ohitukset_5min_liukuva_suunta2
    type: line
    stroke_width: 1
    unit: pcs/h
    name: Direction 2
    show:
      legend_value: false
```
![alt text](https://i.imgur.com/SeREpr9.png "Dashboard card using ApexCharts-card")


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

### Weather Station Entities Not Disabled by Default

**Issue**: All weather station entities are enabled instead of just the 11 essential ones

**Solutions**:
1. This feature only affects **newly created entities**
2. If you added the station before v0.1.63, entities were created as enabled
3. To apply the disabled-by-default setting:
   - Remove the weather station integration instance
   - Restart Home Assistant
   - Re-add the weather station
4. Only 11 essential sensors will be enabled; enable others manually as needed

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

This project is distributed under the [MIT License](LICENSE).

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
