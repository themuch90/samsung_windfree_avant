# Integration
*[Leggi questo in italiano](README.md)*

**Version:** `0.6.6`
**Domain:** `samsung_windfree_avant`

This custom integration controls a **Samsung WindFree Avant** unit through the **SmartThings API**, with **OAuth2** authentication (access token + refresh token renewed automatically in the background — no periodic manual action required).

Tested with:
- Samsung WindFree Avant S2

## Features
- **Climate** entity with ON/OFF (OFF → `switch.off`, other modes → `switch.on` + `airConditionerMode`).
- Supported HVAC modes: auto, cool, heat, dry, fan_only.
- Additional entities:
  - **Display** (`samsungce.airConditionerLighting` → `on`/`off`)
  - **Beep** (`samsungce.airConditionerBeep` → `setBeep` on/off)
  - **Auto Cleaning** (`custom.autoCleaningMode` → `setAutoCleaningMode` on/off)
- **OAuth2** authentication with automatic `access_token`/`refresh_token` renewal: once set up, it never expires as long as the integration keeps running.
- Samsung icon/logo shown automatically for the integration (`brand/` folder, natively recognized by Home Assistant 2026.3+).

## Requirements
- **Home Assistant** 2023.6+ (2025.x+ recommended).
- An **external URL** configured in Home Assistant (Settings → System → Network → External URL), used to automatically compute the redirect URI to register with SmartThings.
- A **SmartThings API App** (client_id + client_secret), created once using the SmartThings CLI — see below.

## Installation and setup
1. Copy the repo contents into:
   ```
   config/custom_components/samsung_windfree_avant
   ```
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add Integration → Samsung WindFree Avant**.
4. In the first step, follow the instructions to create the API App (see below) and enter **Client ID** and **Client Secret**.
5. In the second step, click the authorization link shown: it will open the SmartThings consent screen with the fields already pre-filled. After authorizing, copy the `code` parameter from the browser's address bar (it expires quickly and can only be used once) and paste it into the form.
6. The integration obtains `access_token`/`refresh_token` and from then on renews them by itself in the background — no periodic maintenance required.

## Re-authentication / Reconfiguration
If the `refresh_token` is revoked or expires (e.g. the SmartThings app was disabled or recreated), Home Assistant automatically shows a notification with a **Reconfigure** button on the integration: just follow it to redo the authorization without having to remove and re-add the integration (devices and any automations stay unchanged).

The same flow is also available manually at any time from **Settings → Devices & services → Samsung WindFree Avant → ⋮ → Reconfigure**, for example if you regenerated the client_id/client_secret.

## Creating the SmartThings API App (one-time)
1. Download and install the SmartThings CLI from: https://github.com/SmartThingsCommunity/smartthings-cli (on Windows: `smartthings.msi`).
2. Open **Command Prompt as Administrator**.
3. Run:
   ```
   smartthings apps:create
   ```
4. Follow the guided prompts. Select the scopes: `r:devices:*` and `x:devices:*`. When asked for the **Redirect URI**, use exactly the one the integration's config flow will show you at step 4 above (computed from your HA external URL + `/callback`).
5. At the end you'll get the **Client ID** and **Client Secret** — they are shown only once: copy them right away.

## Quick API debugging
### Requirements
- A **SmartThings Personal Access Token (PAT)** with scopes: `r:devices:*` and `x:devices:*`.
  - Sign in to the [API portal](https://account.smartthings.com/tokens) with the air conditioner's account and create a new token.

For manual tests via `curl`, you need a temporary valid access token (e.g. copied from debug logs, or generated temporarily from the SmartThings developer portal for testing):
```bash
# List devices
curl -s -H "Authorization: Bearer $ST_TOKEN"   "https://api.smartthings.com/v1/devices" | jq .

# Device status
curl -s -H "Authorization: Bearer $ST_TOKEN"   "https://api.smartthings.com/v1/devices/<DEVICE_ID>/status" | jq

# Device command
curl -sX POST "https://api.smartthings.com/v1/devices/<DEVICE_ID>/commands"   -H "Authorization: Bearer $ST_TOKEN"   -H "Content-Type: application/json"   -d '{
    "commands": [
      {
        "component": "main",
        "capability": "switch",
        "command": "off"
      }
    ]
  }'
```

## Links
- SmartThings API documentation: https://developer.smartthings.com/docs/api/public#tag/Devices
- SmartThings OAuth2 documentation: https://developer.smartthings.com/docs/getting-started/quickstart
- SmartThings CLI: https://github.com/SmartThingsCommunity/smartthings-cli
