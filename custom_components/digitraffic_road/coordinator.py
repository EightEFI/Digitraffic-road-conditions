"""Data coordinator for Digitraffic Road Conditions."""
import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DigitraficClient
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DigitraficDataCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Digitraffic data updates."""

    def __init__(self, hass: HomeAssistant, section_id: str, language: str = "fi"):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.section_id = section_id
        self.client = DigitraficClient(async_get_clientsession(hass))
        self.language = language
        _LOGGER.debug("Initialized coordinator for section: %s", section_id)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Digitraffic API."""
        try:
            _LOGGER.debug("Updating data for section: %s", self.section_id)
            
            conditions = await self.client.get_road_conditions(self.section_id, language=self.language)
            forecast = await self.client.get_forecast(self.section_id, language=self.language)
            
            if conditions is None:
                _LOGGER.warning("No conditions data for section: %s", self.section_id)
            if forecast is None:
                _LOGGER.warning("No forecast data for section: %s", self.section_id)
            
            data = {
                "conditions": conditions,
                "forecast": forecast,
            }
            
            _LOGGER.debug("Successfully updated data for section: %s", self.section_id)
            return data
            
        except Exception as err:
            _LOGGER.error("Error communicating with Digitraffic API: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with Digitraffic API: {err}") from err
