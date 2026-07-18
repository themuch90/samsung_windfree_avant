"""Config flow per Samsung Windfree Avant - autenticazione OAuth2 SmartThings.
Flusso:

  1. step_user       -> mostra il redirect URI da usare in fase di
                        creazione della SmartThings API App (calcolato
                        automaticamente dall'URL esterno di HA), e
                        chiede client_id / client_secret ottenuti con
                        la SmartThings CLI
  2. step_authorize   -> mostra un link cliccabile pre-compilato che
                        apre il consenso SmartThings; l'utente autorizza
                        e incolla qui il "code" ricevuto nell'URL di
                        risposta (va copiato subito, scade in pochi
                        secondi/minuti ed è utilizzabile una sola volta)
  3. scambio code -> access_token/refresh_token e creazione della entry

Dopo la creazione, il coordinator si occupa da solo di rinnovare
access_token/refresh_token nel tempo (vedi oauth.py / coordinator.py).
"""
from __future__ import annotations

import logging
import time
from urllib.parse import urlencode

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import get_url, NoURLAvailableError
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    OAUTH_TOKEN_URL,
    OAUTH_AUTHORIZE_URL,
)

_LOGGER = logging.getLogger(__name__)

# Scope minimi necessari per leggere lo stato e mandare comandi al
# climatizzatore. Aggiungere altri scope solo se servono.
OAUTH_SCOPES = "r:devices:* x:devices:*"

# Link alla SmartThings CLI, usato nel testo dello step "user".
SMARTTHINGS_CLI_URL = "https://github.com/SmartThingsCommunity/smartthings-cli"

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
    }
)

STEP_AUTHORIZE_SCHEMA = vol.Schema(
    {
        vol.Required("code"): str,
    }
)


class SamsungWindfreeAvantConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Gestisce la configurazione dell'integrazione."""

    VERSION = 2  # OAuth2 con refresh automatico

    def __init__(self) -> None:
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._redirect_uri: str | None = None
        self._errors: dict[str, str] = {}

    def _compute_redirect_uri(self) -> str:
        """Calcola il redirect URI dall'URL esterno configurato in HA.

        Non deve rispondere realmente a nulla: il flow è manuale (l'utente
        copia il "code" dalla barra degli indirizzi), quindi basta che sia
        un URL valido, raggiungibile o meno, identico a quello che verrà
        registrato nella SmartThings API App.
        """
        try:
            base_url = get_url(
                self.hass, prefer_external=True, allow_internal=False
            )
        except NoURLAvailableError:
            # Fallback: nessun URL esterno configurato in HA, si usa
            # quello che c'è (anche interno/IP locale) pur di avere
            # qualcosa di coerente da mostrare e riutilizzare.
            base_url = get_url(self.hass)
        return f"{base_url.rstrip('/')}/callback"

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Primo step: chiede client_id e client_secret."""
        errors: dict[str, str] = {}

        if self._redirect_uri is None:
            self._redirect_uri = self._compute_redirect_uri()

        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID]
            self._client_secret = user_input[CONF_CLIENT_SECRET]
            return await self.async_step_authorize()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={
                "cli_url": SMARTTHINGS_CLI_URL,
                "redirect_uri": self._redirect_uri,
            },
        )

    async def async_step_authorize(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Secondo step: mostra il link di autorizzazione e riceve il code."""
        errors: dict[str, str] = {}

        if user_input is not None:
            code = user_input["code"].strip()
            try:
                token_data = await self._async_exchange_code(code)
            except SmartThingsAuthError as err:
                _LOGGER.error("Scambio code fallito: %s", err)
                errors["base"] = "auth_failed"
            else:
                return self.async_create_entry(
                    title="Samsung Windfree Avant",
                    data={
                        CONF_CLIENT_ID: self._client_id,
                        CONF_CLIENT_SECRET: self._client_secret,
                        CONF_ACCESS_TOKEN: token_data["access_token"],
                        CONF_REFRESH_TOKEN: token_data["refresh_token"],
                        CONF_TOKEN_EXPIRES_AT: time.time()
                        + token_data.get("expires_in", 86400),
                    },
                )

        auth_url = self._build_authorize_url()

        return self.async_show_form(
            step_id="authorize",
            data_schema=STEP_AUTHORIZE_SCHEMA,
            errors=errors,
            description_placeholders={"auth_url": auth_url},
        )

    def _build_authorize_url(self) -> str:
        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": self._redirect_uri,
            "scope": OAUTH_SCOPES,
        }
        return f"{OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    async def _async_exchange_code(self, code: str) -> dict:
        """Scambia l'authorization code per access_token + refresh_token."""
        session = async_get_clientsession(self.hass)

        # SmartThings richiede client_id/client_secret come Basic Auth
        # nell'header, NON come campi del form. Senza questo header
        # la risposta è 401 Unauthorized con corpo vuoto.
        auth = aiohttp.BasicAuth(self._client_id, self._client_secret)

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
        }

        try:
            resp = await session.post(
                OAUTH_TOKEN_URL,
                data=data,
                auth=auth,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except aiohttp.ClientError as err:
            raise SmartThingsAuthError(f"errore di rete: {err}") from err

        if resp.status != 200:
            body = await resp.text()
            raise SmartThingsAuthError(
                f"risposta {resp.status} da SmartThings: {body}"
            )

        payload = await resp.json()

        if "access_token" not in payload or "refresh_token" not in payload:
            raise SmartThingsAuthError(f"risposta inattesa: {payload}")

        return payload

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SamsungWindfreeAvantOptionsFlow(config_entry)


class SamsungWindfreeAvantOptionsFlow(config_entries.OptionsFlow):
    """Options flow, per eventuali impostazioni (es. intervallo di polling)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )


class SmartThingsAuthError(Exception):
    """Errore durante l'autenticazione OAuth2 con SmartThings."""
