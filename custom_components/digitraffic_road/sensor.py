"""Sensor platform for DigiTraffic."""
import logging
import re
from datetime import timedelta
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import DOMAIN, CONF_ROAD_SECTION, CONF_ROAD_SECTION_ID, CONF_TMS_ID, SENSOR_TYPE_CONDITIONS, SENSOR_TYPE_FORECAST
from .coordinator import DigitraficDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator: DigitraficDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Support both road-section based entries and TMS-based entries.
    # If this is a TMS/LAM entry, create LAM-specific sensors instead of
    # the generic current conditions and forecast sensors.
    tms_id = config_entry.data.get(CONF_TMS_ID)
    if tms_id:
        section_name = config_entry.data.get(CONF_ROAD_SECTION) or str(tms_id)

        # List of LAM measurement keys the user requested. These are measurement
        # constants often available from the TMS measurement feeds.
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

        entities = []

        # Sensors for sensor-constant values (VVAPAAS etc.) will be created
        # dynamically based on what the coordinator fetches. We create a
        # sensor entity per requested measurement key — the entity will look
        # up values in the coordinator data when available.
        for key in lam_measurement_keys:
            entities.append(DigitraficTmsMeasurementSensor(coordinator, tms_id, section_name, key))

        # Additionally create sensors for sensor constant values returned by
        # the /sensor-constants endpoint (VVAPAAS, MS1/MS2, etc.)
        entities.append(DigitraficTmsConstantsSensor(coordinator, tms_id, section_name))

        async_add_entities(entities)
        return

    # Default behavior: create the two generic sensors for road section forecasts
    section_id = config_entry.data.get(CONF_ROAD_SECTION_ID)
    section_name = config_entry.data.get(CONF_ROAD_SECTION) or section_id

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
        self._attr_name = f"{section_name} - Current Conditions"

    @property
    def state(self) -> str | None:
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


def format_measurement_key(key: str) -> str:
    """Format measurement key tokens according to agreed rules.

    Rules:
    - Keep underscores.
    - Keep `VVAPAAS` and `MS1/MS2` uppercase.
    - Convert `5MIN`/`60MIN` -> `5min`/`60min`.
    - Title-case other tokens (e.g., `KESKINOPEUS` -> `Keskinopeus`, `LIUKUVA` -> `Liukuva`).
    """
    if not key:
        return ""
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
    return "_".join(out)


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
        self._attr_name = f"{section_name} - Forecast"

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
        self._attr_name = f"{format_station_name(station_name)} - {format_measurement_key(measure_key)}"

    @property
    def state(self) -> str | None:
        data = self.coordinator.data or {}
        # Try sensor constants first (some keys like VVAPAAS may be constants)
        sc = data.get("sensor_constants") or {}
        vals = sc.get("sensorConstantValues") if isinstance(sc, dict) else None
        if vals:
            for v in vals:
                if v.get("name") == self.measure_key:
                    return v.get("value")

        # Next try station measurements if coordinator provides them under 'measurements'
        measurements = data.get("measurements") or {}
        if isinstance(measurements, dict) and self.measure_key in measurements:
            m = measurements.get(self.measure_key)
            if isinstance(m, dict) and "value" in m:
                val = m.get("value")
                return str(val) if val is not None else None
            return str(m) if m is not None else None

        # No data available yet
        return None

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        return "mdi:counter"
