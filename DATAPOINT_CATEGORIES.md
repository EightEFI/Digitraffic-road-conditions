# DigiTraffic Datapoint Categories

This document describes the organization of datapoints in the translation files.

## Summary

- **Total datapoints**: 212 unique datapoints (221 total entries due to some overlap)
- **Category markers**: 25 organizational sections
- **Files organized**: `fi.json` and `en.json`

## Category Structure

### Weather Station (TIESÄÄASEMA) Categories - 19 sections

1. **Sensor Status** - Sensor health and operational status indicators
2. **Temperature Sensors** - Air temperature measurements and derivatives
3. **Road Surface Sensors** - Conductivity and surface-level sensors
4. **Dew & Frost Point** - Moisture condensation measurements
5. **Wind** - Wind speed and related measurements
6. **Friction** - Road surface friction coefficients
7. **Moisture & Fiber Sensors** - Humidity and fiber optic measurements
8. **Snow Measurement** - Snow depth and coverage
9. **Ground Temperature** - Below-surface temperature readings
10. **Visibility** - Visual range measurements (DSC and standard)
11. **Optical Sensor** - Optical weather condition detection
12. **PWD Sensor** - Present Weather Detector measurements
13. **Precipitation** - Rain, snow, and precipitation intensity
14. **Salt Measurements** - Road salt concentration and amount
15. **Road Surface Condition** - Road surface state indicators
16. **Road Temperature** - Road surface temperature measurements
17. **Safety Temperature** - Temperature warnings and safety thresholds
18. **Wind Direction & Weather** - Wind direction, weather status, brightness
19. **Warnings & Water** - Warning signals and water-related measurements

### LAM/TMS (Traffic Measurement) Categories - 6 sections

1. **Average Speed Measurements** - Fixed and rolling average speeds by direction
2. **Speed by Lane** - Per-lane speed measurements (rolling/minimum)
3. **Traffic Counts 3min Rolling** - Vehicle counts with 3-minute rolling window
4. **Traffic Counts 5min Fixed** - Vehicle counts with 5-minute fixed intervals
5. **Traffic Counts 5min Rolling** - Vehicle counts with 5-minute rolling window
6. **Traffic Counts 60min Fixed** - Hourly vehicle counts by class and direction

## File Structure

Each translation file now contains comment markers in the format:
```json
"_comment_category_N": "=== CATEGORY NAME ==="
```

These markers:
- Group related datapoints together
- Distinguish between LAM (traffic), TIESÄÄASEMA (weather station), and AJOKELI (road conditions)
- Make manual translation work easier by providing context
- Don't affect functionality (they're ignored by the translation system)

## Next Steps

The Finnish translation file (`fi.json`) contains mostly placeholder values. You'll need to:
1. Review each category section
2. Replace placeholder values with proper Finnish translations
3. Ensure consistency within each category
4. Test the translations in Home Assistant

## Categories by Type

**TIESÄÄASEMA (Weather Station)**: 19 categories - sensors, measurements, and conditions
**LAM/TMS (Traffic Measurement)**: 6 categories - speeds, counts, and traffic flow
**AJOKELI (Road Conditions)**: Integrated within weather station categories (KELI_*, road surface states)
