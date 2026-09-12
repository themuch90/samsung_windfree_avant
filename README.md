# Integrazione
*[Read this in English](README.en.md)*

**Versione:** `0.6.6`
**Domain:** `samsung_windfree_avant`

Questa integrazione custom controlla **Samsung WindFree Avant** tramite **SmartThings API**, con autenticazione **OAuth2** (access token + refresh token rinnovati automaticamente in background — nessun intervento manuale periodico richiesto).

Testato con:
- Samsung WindFree Avant S2

## Funzionalità
- Entità **Climate** con ON/OFF (OFF → `switch.off`, altre modalità → `switch.on` + `airConditionerMode`).
- Modalità HVAC supportate: auto, cool, heat, dry, fan_only.
- Entità aggiuntive:
  - **Display** (`samsungce.airConditionerLighting` → `on`/`off`)
  - **Beep** (`samsungce.airConditionerBeep` → `setBeep` on/off)
  - **Auto Cleaning** (`custom.autoCleaningMode` → `setAutoCleaningMode` on/off)
- Autenticazione **OAuth2** con refresh automatico di `access_token`/`refresh_token`: una volta configurata, non scade mai finché l'integrazione gira regolarmente.
- Icona/logo Samsung mostrati automaticamente per l'integrazione (cartella `brand/`, riconosciuta nativamente da Home Assistant 2026.3+).

## Requisiti
- **Home Assistant** 2023.6+ (consigliato 2025.x+).
- Un **URL esterno** configurato in Home Assistant (Impostazioni → Sistema → Rete → URL esterno), usato per calcolare automaticamente il redirect URI da registrare su SmartThings.
- Una **SmartThings API App** (client_id + client_secret), creata una tantum con la SmartThings CLI — vedi sotto.

## Installazione e configurazione
1. Copia il contenuto del repo in:
   ```
   config/custom_components/samsung_windfree_avant
   ```
2. Riavvia Home Assistant.
3. Vai su **Impostazioni → Dispositivi e servizi → Aggiungi Integrazione → Samsung WindFree Avant**.
4. Nel primo step, segui le istruzioni per creare l'API App (vedi sopra) e inserisci **Client ID** e **Client Secret**.
5. Nel secondo step, clicca il link di autorizzazione mostrato: si aprirà il consenso SmartThings con i campi già pre-compilati. Dopo aver autorizzato, copia il parametro `code` dalla barra degli indirizzi del browser (scade rapidamente ed è utilizzabile una sola volta) e incollalo nel form.
6. L'integrazione ottiene `access_token`/`refresh_token` e da quel momento si rinnova da sola in background — nessuna manutenzione periodica richiesta.

## Riautenticazione / Riconfigurazione
Se il `refresh_token` viene revocato o scade (es. app SmartThings disabilitata o ricreata), Home Assistant mostra automaticamente un avviso con il pulsante **Riconfigura** sull'integrazione: basta seguirlo per rifare l'autorizzazione senza dover cancellare e riaggiungere l'integrazione (i dispositivi ed eventuali automazioni restano invariati).

Lo stesso flow è disponibile in ogni momento anche manualmente da **Impostazioni → Dispositivi e servizi → Samsung WindFree Avant → ⋮ → Riconfigura**, ad esempio se hai rigenerato client_id/client_secret.

## Creare la SmartThings API App (una tantum)
1. Scarica e installa la SmartThings CLI da: https://github.com/SmartThingsCommunity/smartthings-cli (su Windows: `smartthings.msi`).
2. Apri il **Prompt dei comandi come amministratore**.
3. Esegui:
   ```
   smartthings apps:create
   ```
4. Segui le istruzioni guidate. Seleziona gli scope: `r:devices:*` e `x:devices:*`. Quando chiede il **Redirect URI**, usa esattamente quello che il config flow dell'integrazione ti mostrerà al passo 4 qui sotto (calcolato dal tuo URL esterno HA + `/callback`).
5. Al termine otterrai **Client ID** e **Client Secret** — vengono mostrati una sola volta: copiali subito.

## Debug rapido API
### Requisiti
- **SmartThings Personal Access Token (PAT)** con scope: `r:devices:*` e `x:devices:*`.
  - Accedere al portale [API](https://account.smartthings.com/tokens) con l'account del condizionatore e creare un nuovo token

Per test manuali via `curl`, serve un access token valido momentaneo (es. copiato dai log in debug, o generato temporaneamente dal portale sviluppatori SmartThings per test):
```bash
# Elenco dispositivi
curl -s -H "Authorization: Bearer $ST_TOKEN"   "https://api.smartthings.com/v1/devices" | jq .

# Stato device
curl -s -H "Authorization: Bearer $ST_TOKEN"   "https://api.smartthings.com/v1/devices/<DEVICE_ID>/status" | jq

# Comando device
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
- Documentazione API SmartThings: https://developer.smartthings.com/docs/api/public#tag/Devices
- Documentazione OAuth2 SmartThings: https://developer.smartthings.com/docs/getting-started/quickstart
- SmartThings CLI: https://github.com/SmartThingsCommunity/smartthings-cli
