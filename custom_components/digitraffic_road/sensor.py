"""Sensor platform for DigiTraffic."""
import logging
import re
from typing import Any, Dict

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_MONITOR_TYPE,
    CONF_ROAD_SECTION,
    CONF_ROAD_SECTION_ID,
    CONF_TMS_ID,
    CONF_WEATHER_STATION_ID,
    MONITOR_CONDITIONS,
    MONITOR_TMS,
    MONITOR_WEATHER,
    SENSOR_TYPE_CONDITIONS,
    SENSOR_TYPE_FORECAST,
)
from .coordinator import DigitraficDataCoordinator

_LOGGER = logging.getLogger(__name__)


WEATHER_SENSOR_NAME_EN = {
    "ILMA": "Air temperature",
    "ILMA_DERIVAATTA": "Air temperature trend",
    "TIE_1": "Road temperature lane 1",
    "TIE_2": "Road temperature lane 2",
    "TIE_1_DERIVAATTA": "Road temperature trend lane 1",
    "TIE_2_DERIVAATTA": "Road temperature trend lane 2",
    "MAA_1": "Ground temperature sensor 1",
    "MAA_2": "Ground temperature sensor 2",
    "KASTEPISTE": "Dew point",
    "J\u00c4\u00c4TYMISPISTE_1": "Freezing point sensor 1",
    "J\u00c4\u00c4TYMISPISTE_2": "Freezing point sensor 2",
    "KESKITUULI": "Average wind speed",
    "MAKSIMITUULI": "Maximum wind speed",
    "TUULENSUUNTA": "Wind direction",
    "ILMAN_KOSTEUS": "Relative humidity",
    "SADE": "Weather description",
    "SADE_INTENSITEETTI": "Precipitation intensity",
    "SADESUMMA": "Precipitation sum",
    "SATEEN_OLOMUOTO_PWDXX": "Precipitation form",
    "N\u00c4KYVYYS_KM": "Visibility",
    "KELI_1": "Road condition lane 1",
    "KELI_2": "Road condition lane 2",
    "VAROITUS_1": "Warning 1",
    "VAROITUS_2": "Warning 2",
    "JOHTAVUUS_1": "Conductivity sensor 1",
    "JOHTAVUUS_2": "Conductivity sensor 2",
}

WEATHER_SENSOR_DEFINITIONS = {
    "ILMA": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:thermometer",
    },
    "ILMA_DERIVAATTA": {
        "icon": "mdi:thermometer-lines",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "TIE_1": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:road-variant",
    },
    "TIE_2": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:road-variant",
    },
    "TIE_1_DERIVAATTA": {
        "icon": "mdi:thermometer-lines",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "TIE_2_DERIVAATTA": {
        "icon": "mdi:thermometer-lines",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "MAA_1": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "MAA_2": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "KASTEPISTE": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water-percent",
    },
    "J\u00c4\u00c4TYMISPISTE_1": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "J\u00c4\u00c4TYMISPISTE_2": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "KESKITUULI": {
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:weather-windy",
    },
    "MAKSIMITUULI": {
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:weather-windy",
    },
    "TUULENSUUNTA": {
        "device_class": SensorDeviceClass.WIND_DIRECTION,
        "icon": "mdi:compass",
    },
    "ILMAN_KOSTEUS": {
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water-percent",
    },
    "SADE": {
        "use_description": True,
        "icon": "mdi:weather-pouring",
    },
    "SADE_INTENSITEETTI": {
        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:weather-pouring",
    },
    "SADESUMMA": {
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:water",
    },
    "SATEEN_OLOMUOTO_PWDXX": {
        "use_description": True,
        "icon": "mdi:weather-snowy-rainy",
    },
    "N\u00c4KYVYYS_KM": {
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:binoculars",
    },
    "KELI_1": {
        "use_description": True,
        "icon": "mdi:road",
    },
    "KELI_2": {
        "use_description": True,
        "icon": "mdi:road",
    },
    "VAROITUS_1": {
        "use_description": True,
        "icon": "mdi:alert-outline",
    },
    "VAROITUS_2": {
        "use_description": True,
        "icon": "mdi:alert-outline",
    },
    "JOHTAVUUS_1": {
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
    "JOHTAVUUS_2": {
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
}


def _humanize_weather_key(key: str) -> str:
    text = key.replace("_", " ")
    humanized = text.title()
    humanized = humanized.replace("Pwdxx", "PWDXX")
    humanized = humanized.replace("Km", "km")
    return humanized


def format_weather_measurement_name(key: str, language: str) -> str:
    """Return a localized display name for a weather measurement key."""
    if language == "en":
        return WEATHER_SENSOR_NAME_EN.get(key, _humanize_weather_key(key))
    return _humanize_weather_key(key)


def slugify_measurement_key(key: str) -> str:
    """Return a safe unique-id suffix derived from the measurement key."""
    normalized = key.lower()
    normalized = (
        normalized.replace("ä", "a")
        .replace("ö", "o")
        .replace("å", "a")
        .replace(" ", "_")
    )
    return re.sub(r"[^a-z0-9_]+", "_", normalized)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator: DigitraficDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    data = config_entry.data

    monitor_type = data.get(CONF_MONITOR_TYPE)
    tms_id = data.get(CONF_TMS_ID)
    weather_station_id = data.get(CONF_WEATHER_STATION_ID)

    if monitor_type is None:
        if tms_id:
            monitor_type = MONITOR_TMS
        elif weather_station_id:
            monitor_type = MONITOR_WEATHER
        else:
            monitor_type = MONITOR_CONDITIONS

    if monitor_type == MONITOR_TMS and tms_id:
        section_name = data.get(CONF_ROAD_SECTION) or str(tms_id)

        lam_measurement_keys = [
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1",
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2",
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1_VVAPAAS1",
            "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2_VVAPAAS2",
            "KESKINOPEUS_60MIN_KIINTEA_SUUNTA1",
            "KESKINOPEUS_60MIN_KIINTEA_SUUNTA2",
            "KESKINOPEUS_5MIN_KIINTEA_SUUNTA1_VVAPAAS1",
            "KESKINOPEUS_5MIN_KIINTEA_SUUNTA2_VVAPAAS2",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA1",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA2",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA1_MS1",
            "OHITUKSET_5MIN_LIUKUVA_SUUNTA2_MS2",
            "OHITUKSET_5MIN_KIINTEA_SUUNTA1_MS1",
            "OHITUKSET_5MIN_KIINTEA_SUUNTA2_MS2",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA1",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA2",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA1_MS1",
            "OHITUKSET_60MIN_KIINTEA_SUUNTA2_MS2",
        ]

        entities = [
            DigitraficTmsMeasurementSensor(coordinator, tms_id, section_name, key)
            for key in lam_measurement_keys
        ]
        entities.append(DigitraficTmsConstantsSensor(coordinator, tms_id, section_name))

        async_add_entities(entities)
        return

    if monitor_type == MONITOR_WEATHER and weather_station_id:
        station_name = data.get(CONF_ROAD_SECTION) or str(weather_station_id)
        measurement_keys = list(WEATHER_SENSOR_DEFINITIONS.keys())

        existing = coordinator.data.get("measurements") if coordinator.data else {}
        if isinstance(existing, dict):
            for key in existing.keys():
                if key not in measurement_keys:
                    measurement_keys.append(key)

        entities = [
            DigitraficWeatherMeasurementSensor(
                coordinator,
                weather_station_id,
                station_name,
                key,
                WEATHER_SENSOR_DEFINITIONS.get(key, {}),
            )
            for key in measurement_keys
        ]

        async_add_entities(entities)
        return

    section_id = data.get(CONF_ROAD_SECTION_ID)
    section_name = data.get(CONF_ROAD_SECTION) or section_id

    entities = [
        DigitraficCurrentConditionsSensor(coordinator, section_id, section_name),
        DigitraficForecastSensor(coordinator, section_id, section_name),
    ]

    async_add_entities(entities)


class DigitraficCurrentConditionsSensor(CoordinatorEntity, SensorEntity):
    """Sensor for current road conditions."""

    def __init__(
        self, 
        coordinator: DigitraficDataCoordinator, 
        section_id: str,
        section_name: str
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.section_id = section_id
        self._section_name = section_name
        self._attr_unique_id = f"{DOMAIN}_{section_id}_conditions"
        # Use language-specific label
        label = "Ajokeli tällä hetkellä" if coordinator.language == "fi" else "Current Conditions"
        self._attr_name = f"{section_name} - {label}"

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        conditions_data = self.coordinator.data.get("conditions")
        if conditions_data:
            return self.coordinator.client.parse_conditions(conditions_data)
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity extra state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
        
        conditions_data = self.coordinator.data.get("conditions")
        if conditions_data and conditions_data.get("features"):
            feature = conditions_data["features"][0]
            properties = feature.get("properties", {})
            
            if "reliability" in properties:
                attributes["reliability"] = properties.get("reliability")
            if "last_updated" in properties:
                attributes["last_updated"] = properties.get("last_updated")
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:road"


def format_station_name(raw: str) -> str:
    """Format station name for display.

    Rules:
    - If the raw name contains underscores, replace them with spaces and
      capitalize each token (e.g., 'vt4_Marostenmäki' -> 'Vt4 Marostenmäki').
    - Otherwise, title-case the words.
    """
    if not raw:
        return ""
    if "_" in raw:
        s = raw.replace("_", " ")
        tokens = s.split()
        return " ".join(t.capitalize() for t in tokens)
    # Default: title-case words (preserve numbers)
    return " ".join(t.capitalize() for t in raw.split())


def format_measurement_key(key: str, language: str = "fi") -> str:
    """Format measurement key tokens according to agreed rules.

    Args:
        key: The measurement key to format.
        language: Language code ('fi' or 'en').

    Rules:
    - Translate to English if language is 'en'.
    - Otherwise title-case Finnish tokens.
    """
    if not key:
        return ""
    
    # English translations map
    english_translations = {
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1": "Rolling avg speed 5min sliding dir 1",
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2": "Rolling avg speed 5min sliding dir 2",
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA1_VVAPAAS1": "Rolling avg speed 5min pct of free-flow dir 1",
        "KESKINOPEUS_5MIN_LIUKUVA_SUUNTA2_VVAPAAS2": "Rolling avg speed 5min pct of free-flow dir 2",
        "KESKINOPEUS_60MIN_KIINTEA_SUUNTA1": "Fixed avg speed 60min dir 1",
        "KESKINOPEUS_60MIN_KIINTEA_SUUNTA2": "Fixed avg speed 60min dir 2",
        "KESKINOPEUS_5MIN_KIINTEA_SUUNTA1_VVAPAAS1": "Fixed avg speed 5min pct of free-flow dir 1",
        "KESKINOPEUS_5MIN_KIINTEA_SUUNTA2_VVAPAAS2": "Fixed avg speed 5min pct of free-flow dir 2",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA1": "Rolling count overtakes 5min dir 1",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA2": "Rolling count overtakes 5min dir 2",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA1_MS1": "Rolling count overtakes 5min lane 1 dir 1",
        "OHITUKSET_5MIN_LIUKUVA_SUUNTA2_MS2": "Rolling count overtakes 5min lane 2 dir 2",
        "OHITUKSET_5MIN_KIINTEA_SUUNTA1_MS1": "Fixed count overtakes 5min lane 1 dir 1",
        "OHITUKSET_5MIN_KIINTEA_SUUNTA2_MS2": "Fixed count overtakes 5min lane 2 dir 2",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA1": "Fixed count overtakes 60min dir 1",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA2": "Fixed count overtakes 60min dir 2",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA1_MS1": "Fixed count overtakes 60min lane 1 dir 1",
        "OHITUKSET_60MIN_KIINTEA_SUUNTA2_MS2": "Fixed count overtakes 60min lane 2 dir 2",
    }
    
    if language == "en" and key in english_translations:
        return english_translations[key]
    
    # Finnish formatting (default)
    tokens = key.split("_")
    out = []
    for t in tokens:
        # Keep some tokens uppercase
        if t.upper().startswith("VVAPAAS"):
            out.append(t.upper())
            continue
        if t.upper() in ("MS1", "MS2"):
            out.append(t.upper())
            continue
        # Convert time window tokens like '5MIN' or '60MIN'
        m = re.match(r"^(\d+)MIN$", t, flags=re.IGNORECASE)
        if m:
            out.append(f"{m.group(1)}min")
            continue
        # Default: Title case
        out.append(t.capitalize())
    # Friendly display: join tokens with spaces for readability
    return " ".join(out)


class DigitraficForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor for road condition forecast."""

    def __init__(
        self, 
        coordinator: DigitraficDataCoordinator, 
        section_id: str,
        section_name: str
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.section_id = section_id
        self._section_name = section_name
        self._attr_unique_id = f"{DOMAIN}_{section_id}_forecast"
        # Use language-specific label
        label = "Ennuste" if coordinator.language == "fi" else "Forecast"
        self._attr_name = f"{section_name} - {label}"

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        forecast_data = self.coordinator.data.get("forecast")
        if forecast_data:
            return self.coordinator.client.parse_forecast(forecast_data)
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity extra state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes
        
        forecast_data = self.coordinator.data.get("forecast")
        if forecast_data and forecast_data.get("features"):
            # Include detailed forecast data as attributes
            forecasts = []
            for forecast in forecast_data["features"]:
                properties = forecast.get("properties", {})
                forecasts.append({
                    "time": properties.get("time"),
                    "condition": properties.get("condition")
                })
            
            if forecasts:
                attributes["forecast_data"] = forecasts
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:weather-cloudy"


class DigitraficWeatherMeasurementSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity representing a single weather-station measurement."""

    def __init__(
        self,
        coordinator: DigitraficDataCoordinator,
        station_id: int | str,
        station_name: str,
        measurement_key: str,
        metadata: Dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self.station_id = station_id
        self.measurement_key = measurement_key
        self._metadata = metadata or {}
        self._use_description = bool(self._metadata.get("use_description"))

        slug = slugify_measurement_key(measurement_key)
        self._attr_unique_id = f"{DOMAIN}_weather_{station_id}_{slug}"

        friendly_name = self._metadata.get(
            "name_fi" if coordinator.language == "fi" else "name_en"
        )
        if not friendly_name:
            friendly_name = format_weather_measurement_name(measurement_key, coordinator.language)

        self._attr_name = f"{format_station_name(str(station_name))} - {friendly_name}"

        device_class = self._metadata.get("device_class")
        state_class = self._metadata.get("state_class")
        icon = self._metadata.get("icon")

        if device_class:
            self._attr_device_class = device_class
        if state_class:
            self._attr_state_class = state_class
        if icon:
            self._attr_icon = icon

    def _get_measurement(self) -> Dict[str, Any] | None:
        data = self.coordinator.data or {}
        measurements = data.get("measurements") or {}
        if not isinstance(measurements, dict):
            return None

        measurement = measurements.get(self.measurement_key)
        if measurement is not None:
            return measurement

        for key, value in measurements.items():
            if isinstance(key, str) and key.lower() == self.measurement_key.lower():
                return value

        return None

    @property
    def available(self) -> bool:
        if not self.coordinator.last_update_success:
            return False
        return self._get_measurement() is not None

    @property
    def state(self) -> Any:
        measurement = self._get_measurement()
        if not measurement:
            return None

        if self._use_description:
            lang = self.coordinator.language or "fi"
            desc_key = "sensorValueDescriptionFi" if lang == "fi" else "sensorValueDescriptionEn"
            description = (
                measurement.get(desc_key)
                or measurement.get("sensorValueDescriptionFi")
                or measurement.get("sensorValueDescriptionEn")
            )
            return description or measurement.get("value")

        return measurement.get("value")

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self._use_description:
            return None
        measurement = self._get_measurement()
        if not measurement:
            return None
        return measurement.get("unit")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        measurement = self._get_measurement()
        if not measurement:
            return {}

        attrs: Dict[str, Any] = {
            "sensor_id": measurement.get("id"),
            "measured_time": measurement.get("measuredTime"),
        }

        if not self._use_description:
            attrs["raw_value"] = measurement.get("value")

        if measurement.get("unit"):
            attrs["unit"] = measurement.get("unit")

        desc_fi = measurement.get("sensorValueDescriptionFi")
        if desc_fi:
            attrs["description_fi"] = desc_fi

        desc_en = measurement.get("sensorValueDescriptionEn")
        if desc_en:
            attrs["description_en"] = desc_en

        data_updated = (self.coordinator.data or {}).get("data_updated_time")
        if data_updated:
            attrs["station_data_updated_time"] = data_updated

        return attrs


class DigitraficTmsConstantsSensor(CoordinatorEntity, SensorEntity):
    """Sensor that exposes TMS sensor-constant values (VVAPAAS, MS1/MS2, etc.).

    This sensor aggregates the station's sensor-constant values into a single
    JSON-serializable attribute so users can inspect LAM constants.
    """

    def __init__(self, coordinator: DigitraficDataCoordinator, station_id: int, station_name: str):
        super().__init__(coordinator)
        self.station_id = station_id
        self._station_name = station_name
        self._attr_unique_id = f"{DOMAIN}_tms_{station_id}_constants"
        self._attr_name = f"{format_station_name(station_name)} - Sensor Constants"

    @property
    def state(self) -> str | None:
        # No single scalar state — return availability indicator
        return "available" if self.coordinator.last_update_success else "unavailable"

    @property
    def extra_state_attributes(self):
        attrs = {}
        data = self.coordinator.data or {}
        sc = data.get("sensor_constants") or {}
        # Expecting sensorConstantValues list
        vals = sc.get("sensorConstantValues") if isinstance(sc, dict) else None
        if vals:
            for v in vals:
                name = v.get("name")
                value = v.get("value")
                if name:
                    attrs[name] = value
        return attrs


class DigitraficTmsMeasurementSensor(CoordinatorEntity, SensorEntity):
    """Placeholder sensor for a specific LAM/TMS measurement key.

    Currently this reads values from coordinator.data if available; if the
    integration later implements per-sensor observations fetching, the
    coordinator can populate `measurements` and this entity will pick them up.
    """

    def __init__(self, coordinator: DigitraficDataCoordinator, station_id: int, station_name: str, measure_key: str):
        super().__init__(coordinator)
        self.station_id = station_id
        self._station_name = station_name
        self.measure_key = measure_key
        self._attr_unique_id = f"{DOMAIN}_tms_{station_id}_{measure_key}"
        # Use friendly formatting for station and measurement names
        self._attr_name = f"{format_station_name(station_name)} - {format_measurement_key(measure_key, coordinator.language)}"
        # Enable HA statistics and graphing
        self._attr_state_class = "measurement"

    @property
    def state(self) -> Any:
        data = self.coordinator.data or {}
        _LOGGER.debug("Getting state for %s, data keys: %s", self.measure_key, list(data.keys()))
        
        # Try sensor constants first (some keys like VVAPAAS may be constants)
        sc = data.get("sensor_constants") or {}
        vals = sc.get("sensorConstantValues") if isinstance(sc, dict) else None
        if vals:
            for v in vals:
                if v.get("name") == self.measure_key:
                    value = v.get("value")
                    _LOGGER.debug("Found constant value for %s: %s", self.measure_key, value)
                    # Return numeric constant value as-is (int/float)
                    return value

        # Next try station measurements if coordinator provides them under 'measurements'
        measurements = data.get("measurements") or {}
        _LOGGER.debug("Measurements available: %s", list(measurements.keys()) if isinstance(measurements, dict) else "None")
        
        if isinstance(measurements, dict) and self.measure_key in measurements:
            m = measurements.get(self.measure_key)
            if isinstance(m, dict) and "value" in m:
                value = m.get("value")
                _LOGGER.debug("Found measurement value for %s: %s", self.measure_key, value)
                return value
            # If measurement entry is a raw value, return it (numeric)
            _LOGGER.debug("Found raw measurement for %s: %s", self.measure_key, m)
            return m

        # Check if there's a close match (sometimes the API returns slightly different keys)
        if isinstance(measurements, dict):
            for key, measurement in measurements.items():
                if self.measure_key.lower() in key.lower() or key.lower() in self.measure_key.lower():
                    if isinstance(measurement, dict) and "value" in measurement:
                        value = measurement.get("value")
                        _LOGGER.debug("Found fuzzy match %s -> %s: %s", self.measure_key, key, value)
                        return value

        _LOGGER.debug("No data found for %s", self.measure_key)
        # Return unavailable state instead of None to distinguish from "no data yet"
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Sensor is available if coordinator is successful AND we have data for this measurement
        if not self.coordinator.last_update_success:
            return False
            
        # Check if we have actual measurement data
        data = self.coordinator.data or {}
        measurements = data.get("measurements") or {}
        sensor_constants = data.get("sensor_constants") or {}
        
        # Available if we have either measurement data or sensor constant data
        has_measurement = isinstance(measurements, dict) and self.measure_key in measurements
        has_constant = False
        if isinstance(sensor_constants, dict):
            vals = sensor_constants.get("sensorConstantValues", [])
            has_constant = any(v.get("name") == self.measure_key for v in vals)
            
        return has_measurement or has_constant

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement from coordinator data."""
        data = self.coordinator.data or {}
        measurements = data.get("measurements") or {}
        if isinstance(measurements, dict) and self.measure_key in measurements:
            m = measurements.get(self.measure_key)
            if isinstance(m, dict) and "unit" in m:
                unit = m.get("unit")
                _LOGGER.debug("Unit for %s: %s", self.measure_key, unit)
                # Handle special unit cases (°, km/h, %, kpl/h)
                if unit == "***":
                    return "%"  # Common placeholder for percentage
                # For speed measurements, ensure we have km/h
                if "KESKINOPEUS" in self.measure_key and unit in ["km/h", "kmh", "km"]:
                    return "km/h"
                return unit
                
        # Default units based on measurement type
        if "KESKINOPEUS" in self.measure_key:
            return "km/h"
        elif "OHITUKSET" in self.measure_key:
            return "count"
        elif "VVAPAAS" in self.measure_key:
            return "%"
            
        return None

    @property
    def icon(self) -> str:
        return "mdi:counter"
