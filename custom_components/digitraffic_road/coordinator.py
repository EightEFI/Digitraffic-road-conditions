"""Data coordinator for DigiTraffic."""
import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DigitraficClient
from .const import DOMAIN, UPDATE_INTERVAL, MONITOR_CONDITIONS, MONITOR_TMS, MONITOR_WEATHER

_LOGGER = logging.getLogger(__name__)


class DigitraficDataCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Digitraffic data updates."""

    def __init__(self, hass: HomeAssistant, identifier: str, monitor_type: str, language: str = "fi"):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.identifier = str(identifier)
        # Preserve section_id attribute for backwards compatibility with sensors that may reference it
        self.section_id = self.identifier
        self.monitor_type = monitor_type
        self.client = DigitraficClient(async_get_clientsession(hass))
        self.language = language
        _LOGGER.debug(
            "Initialized coordinator for %s with monitor type %s",
            self.identifier,
            self.monitor_type,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Digitraffic API."""
        try:
            _LOGGER.debug(
                "Updating data for %s (monitor_type=%s)",
                self.identifier,
                self.monitor_type,
            )

            data: Dict[str, Any]

            if self.monitor_type == MONITOR_TMS:
                try:
                    station_id = int(str(self.identifier))
                except ValueError as err:
                    raise UpdateFailed(f"Invalid TMS station id: {self.identifier}") from err

                station = await self.client.async_get_tms_station(station_id)
                sensor_constants = await self.client.async_get_tms_sensor_constants(station_id)
                tms_data = await self.client.async_get_tms_station_data(station_id)

                measurements: Dict[str, Any] = {}
                sensor_values = []

                if tms_data and isinstance(tms_data, dict):
                    _LOGGER.debug("TMS data keys: %s", list(tms_data.keys()))
                    sensor_values = tms_data.get("sensorValues", []) or []
                    _LOGGER.debug(
                        "Found %d sensor values for station %s",
                        len(sensor_values),
                        self.identifier,
                    )

                    for sv in sensor_values:
                        name = sv.get("name")
                        if not name:
                            continue
                        measurements[name] = {
                            "id": sv.get("id"),
                            "value": sv.get("value"),
                            "unit": sv.get("unit"),
                            "measuredTime": sv.get("measuredTime"),
                            "timeWindowStart": sv.get("timeWindowStart"),
                            "timeWindowEnd": sv.get("timeWindowEnd"),
                        }

                if station is None and not measurements:
                    _LOGGER.warning("No TMS station data for id: %s", self.identifier)

                data = {
                    "tms_station": station,
                    "sensor_constants": sensor_constants,
                    "measurements": measurements,
                    "sensor_values": sensor_values,
                }

            elif self.monitor_type == MONITOR_WEATHER:
                try:
                    station_id = int(str(self.identifier))
                except ValueError as err:
                    raise UpdateFailed(f"Invalid weather station id: {self.identifier}") from err

                station_feature = await self.client.async_get_weather_station(station_id)
                station_data = await self.client.async_get_weather_station_data(station_id)

                measurements: Dict[str, Any] = {}
                sensor_values = []
                data_updated_time = None

                if station_data and isinstance(station_data, dict):
                    sensor_values = station_data.get("sensorValues", []) or []
                    data_updated_time = station_data.get("dataUpdatedTime")
                    for sv in sensor_values:
                        key = sv.get("name")
                        if not key:
                            continue
                        measurements[key] = sv

                if station_feature is None and not measurements:
                    _LOGGER.warning("No weather station data for id: %s", self.identifier)

                data = {
                    "weather_station": station_feature,
                    "measurements": measurements,
                    "sensor_values": sensor_values,
                    "data_updated_time": data_updated_time,
                }

            else:
                conditions = await self.client.get_road_conditions(self.identifier, language=self.language)
                forecast = await self.client.get_forecast(self.identifier, language=self.language)

                if conditions is None:
                    _LOGGER.warning("No conditions data for section: %s", self.identifier)
                if forecast is None:
                    _LOGGER.warning("No forecast data for section: %s", self.identifier)

                data = {
                    "conditions": conditions,
                    "forecast": forecast,
                }

            _LOGGER.debug(
                "Successfully updated data for %s (type=%s)",
                self.identifier,
                self.monitor_type,
            )
            return data
            
        except Exception as err:
            _LOGGER.error("Error communicating with Digitraffic API: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with Digitraffic API: {err}") from err
