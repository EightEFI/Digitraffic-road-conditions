"""DigiTraffic integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_ROAD_SECTION_ID,
    CONF_TMS_ID,
    CONF_LANGUAGE,
    CONF_MONITOR_TYPE,
    CONF_WEATHER_STATION_ID,
    MONITOR_CONDITIONS,
    MONITOR_TMS,
    MONITOR_WEATHER,
)
from .coordinator import DigitraficDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DigiTraffic from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    monitor_type = entry.data.get(CONF_MONITOR_TYPE, MONITOR_CONDITIONS)

    if monitor_type == MONITOR_TMS:
        identifier = entry.data.get(CONF_TMS_ID)
    elif monitor_type == MONITOR_WEATHER:
        identifier = entry.data.get(CONF_WEATHER_STATION_ID)
    else:
        identifier = entry.data.get(CONF_ROAD_SECTION_ID)

    language = entry.data.get(CONF_LANGUAGE, "fi")

    if identifier is None:
        _LOGGER.error(
            "Config entry %s missing identifier for monitor type %s",
            entry.entry_id,
            monitor_type,
        )
        return False

    # Create and setup coordinator
    coordinator = DigitraficDataCoordinator(hass, identifier, monitor_type, language)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Setup entry update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
