"""Sensor platform for DigiTraffic."""
import logging
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
    section_id = config_entry.data.get(CONF_ROAD_SECTION_ID) or config_entry.data.get(CONF_TMS_ID)
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
