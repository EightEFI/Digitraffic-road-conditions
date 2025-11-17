"""Config flow for DigiTraffic integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector
import logging

from .client import DigitraficClient
from .const import (
    DOMAIN,
    CONF_ROAD_SECTION,
    CONF_ROAD_SECTION_ID,
    CONF_LANGUAGE,
    CONF_MONITOR_TYPE,
    CONF_TMS_ID,
    CONF_WEATHER_STATION_ID,
    MONITOR_CONDITIONS,
    MONITOR_TMS,
    MONITOR_WEATHER,
)

_LOGGER = logging.getLogger(__name__)


class DigitraficRoadConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DigiTraffic."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Initial step: go directly to monitor type selection."""
        # Use Home Assistant's language setting
        self.language = self.hass.config.language or "en"
        return await self.async_step_monitor_type(user_input)

    async def async_step_monitor_type(self, user_input=None):
        """Ask whether to monitor driving conditions or a TMS/LAM station."""

        if user_input is not None and CONF_MONITOR_TYPE in user_input:
            self.monitor_type = user_input.get(CONF_MONITOR_TYPE)
            if self.monitor_type == MONITOR_TMS:
                return await self.async_step_tms()
            if self.monitor_type == MONITOR_WEATHER:
                return await self.async_step_weather()
            return await self.async_step_section()

        return self.async_show_form(
            step_id="monitor_type",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MONITOR_TYPE,
                        default=MONITOR_CONDITIONS,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[MONITOR_CONDITIONS, MONITOR_TMS, MONITOR_WEATHER],
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="monitor_type_selector",
                        )
                    ),
                }
            ),
        )

    async def async_step_section(self, user_input=None):
        """Handle the step - enter road section ID or title."""
        errors = {}

        # If user submitted input
        if user_input is not None:
            section_input = user_input.get(CONF_ROAD_SECTION, "").strip()

            if not section_input:
                errors["base"] = "empty_search"
            else:
                _LOGGER.debug("Road section input: %s", section_input)

                # Resolve candidates using the client (may return 0, 1 or many)
                session = async_get_clientsession(self.hass)
                client = DigitraficClient(session)
                try:
                    candidates = await client.resolve_section_candidates(section_input, max_candidates=12)
                except Exception as err:
                    _LOGGER.exception("Candidate resolution failed: %s", err)
                    candidates = []

                if not candidates:
                    errors["base"] = "no_matches"
                elif len(candidates) == 1:
                    # Single candidate -> create entry directly
                    props = candidates[0]
                    chosen_id = props.get("id")
                    section_name = props.get("description") or props.get("name") or section_input

                    # Default monitor type to conditions if not set
                    monitor_type = getattr(self, "monitor_type", MONITOR_CONDITIONS)

                    unique_id = f"{monitor_type}_{chosen_id}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    data = {
                        CONF_MONITOR_TYPE: monitor_type,
                        CONF_LANGUAGE: getattr(self, "language", "en"),
                    }

                    if monitor_type == MONITOR_CONDITIONS:
                        data.update({
                            CONF_ROAD_SECTION_ID: chosen_id,
                            CONF_ROAD_SECTION: section_name,
                        })
                    else:
                        data.update({CONF_TMS_ID: chosen_id, CONF_ROAD_SECTION: section_name})

                    return self.async_create_entry(title=section_name, data=data)
                else:
                    # Multiple candidates -> present a pick step (dropdown)
                    # Store candidates temporarily and move to pick step
                    self._candidates = candidates
                    self._raw_input = section_input
                    return await self.async_step_pick()

        # Show input form
        return self.async_show_form(
            step_id="section",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ROAD_SECTION): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "example": "Tie 4: Kemintie 4.421"
            },
        )

    async def async_step_pick(self, user_input=None):
        """Allow the user to pick one of the candidate metadata entries.

        Expects `self._candidates` to be populated by `async_step_section`.
        """
        if not hasattr(self, "_candidates") or not self._candidates:
            return await self.async_step_section()

        errors = {}

        if user_input is not None and "pick" in user_input:
            pick_id = user_input.get("pick")
            # Find selected props
            props = next((p for p in self._candidates if p.get("id") == pick_id), None)
            if not props:
                errors["base"] = "invalid_selection"
            else:
                chosen_id = props.get("id")
                section_name = props.get("description") or props.get("name") or pick_id
                monitor_type = getattr(self, "monitor_type", MONITOR_CONDITIONS)

                unique_id = f"{monitor_type}_{chosen_id}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                data = {
                    CONF_MONITOR_TYPE: monitor_type,
                    CONF_LANGUAGE: getattr(self, "language", "en"),
                }
                if monitor_type == MONITOR_CONDITIONS:
                    data.update({CONF_ROAD_SECTION_ID: chosen_id, CONF_ROAD_SECTION: section_name})
                else:
                    data.update({CONF_TMS_ID: chosen_id, CONF_ROAD_SECTION: section_name})

                return self.async_create_entry(title=section_name, data=data)

        # Build choices mapping id -> label
        choices = {}
        for p in self._candidates:
            rid = p.get("id")
            desc = p.get("description") or p.get("name") or ""
            rn = p.get("roadNumber")
            rs = p.get("roadSectionNumber")
            label = f"{rid} — {desc} (road={rn}, section={rs})"
            choices[rid] = label

        schema = vol.Schema({vol.Required("pick"): vol.In(choices)})
        return self.async_show_form(step_id="pick", data_schema=schema, errors=errors)

    async def async_step_tms(self, user_input=None):
        """Handle the TMS input step for monitor type TMS.

        This step searches the Digitraffic TMS stations list by the user's input
        (matching `names.fi`, `names.sv`, `names.en`, and `properties.name`).
        If multiple matches are found, present a dropdown for the user to pick.
        """
        errors = {}

        session = async_get_clientsession(self.hass)
        client = DigitraficClient(session)

        # If user submitted input
        if user_input is not None:
            tms_input = user_input.get(CONF_TMS_ID, "").strip()
            if not tms_input:
                errors["base"] = "empty_search"
            else:
                try:
                    candidates = await client.async_search_tms_stations(tms_input, max_results=12)
                except Exception as err:
                    _LOGGER.exception("TMS search failed: %s", err)
                    candidates = []

                if not candidates:
                    errors["base"] = "no_matches"
                elif len(candidates) == 1:
                    props = candidates[0]
                    chosen_id = props.get("id")
                    section_name = props.get("names", {}).get("fi") or props.get("name") or str(chosen_id)

                    monitor_type = MONITOR_TMS
                    unique_id = f"{monitor_type}_{chosen_id}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    data = {
                        CONF_MONITOR_TYPE: monitor_type,
                        CONF_LANGUAGE: getattr(self, "language", "en"),
                    }
                    data.update({CONF_TMS_ID: chosen_id, CONF_ROAD_SECTION: section_name})

                    return self.async_create_entry(title=section_name, data=data)
                else:
                    # multiple matches - present pick step for TMS
                    self._tms_candidates = candidates
                    self._tms_raw = tms_input
                    return await self.async_step_tms_pick()

        return self.async_show_form(
            step_id="tms",
            data_schema=vol.Schema({vol.Required(CONF_TMS_ID): str}),
            errors=errors,
        )

    async def async_step_tms_pick(self, user_input=None):
        """Allow the user to pick one of the TMS station candidates."""
        if not hasattr(self, "_tms_candidates") or not self._tms_candidates:
            return await self.async_step_tms()

        errors = {}
        if user_input is not None and "pick" in user_input:
            pick_id = user_input.get("pick")
            props = next((p for p in self._tms_candidates if str(p.get("id")) == str(pick_id)), None)
            if not props:
                errors["base"] = "invalid_selection"
            else:
                chosen_id = props.get("id")
                section_name = props.get("names", {}).get("fi") or props.get("name") or str(chosen_id)
                monitor_type = MONITOR_TMS

                unique_id = f"{monitor_type}_{chosen_id}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                data = {
                    CONF_MONITOR_TYPE: monitor_type,
                    CONF_LANGUAGE: getattr(self, "language", "en"),
                }
                data.update({CONF_TMS_ID: chosen_id, CONF_ROAD_SECTION: section_name})

                return self.async_create_entry(title=section_name, data=data)

        choices = {}
        for p in self._tms_candidates:
            rid = p.get("id")
            names = p.get("names", {})
            label = f"{rid} — {names.get('fi') or names.get('en') or p.get('name') or ''}"
            choices[str(rid)] = label

        schema = vol.Schema({vol.Required("pick"): vol.In(choices)})
        return self.async_show_form(step_id="tms_pick", data_schema=schema, errors=errors)

    async def async_step_weather(self, user_input=None):
        """Handle the weather station input step."""
        errors = {}

        session = async_get_clientsession(self.hass)
        client = DigitraficClient(session)

        if user_input is not None:
            station_input = user_input.get(CONF_WEATHER_STATION_ID, "").strip()
            if not station_input:
                errors["base"] = "empty_search"
            else:
                try:
                    candidates = await client.async_search_weather_stations(station_input, max_results=12)
                except Exception as err:
                    _LOGGER.exception("Weather station search failed: %s", err)
                    candidates = []

                if not candidates:
                    errors["base"] = "no_matches"
                elif len(candidates) == 1:
                    props = candidates[0]
                    chosen_id = props.get("id")
                    name_raw = props.get("name") or str(chosen_id)
                    station_name = name_raw.replace("_", " ")

                    monitor_type = MONITOR_WEATHER
                    unique_id = f"{monitor_type}_{chosen_id}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    data = {
                        CONF_MONITOR_TYPE: monitor_type,
                        CONF_LANGUAGE: getattr(self, "language", "en"),
                        CONF_WEATHER_STATION_ID: chosen_id,
                        CONF_ROAD_SECTION: station_name,
                    }

                    return self.async_create_entry(title=station_name, data=data)
                else:
                    self._weather_candidates = candidates
                    self._weather_raw = station_input
                    return await self.async_step_weather_pick()

        return self.async_show_form(
            step_id="weather",
            data_schema=vol.Schema({vol.Required(CONF_WEATHER_STATION_ID): str}),
            errors=errors,
        )

    async def async_step_weather_pick(self, user_input=None):
        """Allow the user to pick one of the weather station candidates."""
        if not hasattr(self, "_weather_candidates") or not self._weather_candidates:
            return await self.async_step_weather()

        errors = {}
        if user_input is not None and "pick" in user_input:
            pick_id = user_input.get("pick")
            props = next((p for p in self._weather_candidates if str(p.get("id")) == str(pick_id)), None)
            if not props:
                errors["base"] = "invalid_selection"
            else:
                chosen_id = props.get("id")
                name_raw = props.get("name") or str(chosen_id)
                station_name = name_raw.replace("_", " ")

                monitor_type = MONITOR_WEATHER
                unique_id = f"{monitor_type}_{chosen_id}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                data = {
                    CONF_MONITOR_TYPE: monitor_type,
                    CONF_LANGUAGE: getattr(self, "language", "en"),
                    CONF_WEATHER_STATION_ID: chosen_id,
                    CONF_ROAD_SECTION: station_name,
                }

                return self.async_create_entry(title=station_name, data=data)

        choices = {}
        for props in self._weather_candidates:
            sid = props.get("id")
            name_raw = props.get("name") or ""
            label = f"{sid} — {name_raw.replace('_', ' ')}"
            choices[str(sid)] = label

        schema = vol.Schema({vol.Required("pick"): vol.In(choices)})
        return self.async_show_form(step_id="weather_pick", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this integration."""
        return DigitraficRoadOptionsFlow(config_entry)


class DigitraficRoadOptionsFlow(config_entries.OptionsFlow):
    """Handle options for DigiTraffic."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
