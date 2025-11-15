"""Config flow for Digitraffic Road Conditions integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .client import DigitraficClient
from .const import DOMAIN, CONF_ROAD_SECTION, CONF_ROAD_SECTION_ID

_LOGGER = logging.getLogger(__name__)


class DigitraficRoadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Digitraffic Road Conditions."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step - enter road section ID or title."""
        errors = {}
        
        # If user submitted input
        if user_input is not None:
            section_input = user_input.get("section_input", "").strip()
            
            if not section_input:
                errors["base"] = "empty_search"
            else:
                _LOGGER.debug("Road section input: %s", section_input)
                
                # Use the input as-is for the section ID (will be used to fetch conditions)
                # The input can be like "Tie 4: Kemintie 4.421" from the Fintraffic map
                section_id = section_input.replace(" ", "_").replace(":", "").replace(".", "_")
                section_name = section_input
                
                # Check if already configured
                await self.async_set_unique_id(section_id)
                self._abort_if_unique_id_configured()
                
                _LOGGER.debug("Creating config entry for section: %s", section_name)
                
                return self.async_create_entry(
                    title=section_name,
                    data={
                        CONF_ROAD_SECTION_ID: section_input,
                        CONF_ROAD_SECTION: section_name,
                    },
                )
        
        # Show input form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("section_input", description={"suggested_value": "Tie 4: Kemintie 4.421"}): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "example": "Tie 4: Kemintie 4.421"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this integration."""
        return DigitraficRoadOptionsFlow(config_entry)


class DigitraficRoadOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Digitraffic Road Conditions."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
