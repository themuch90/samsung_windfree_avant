# Integrazione
**Versione:** `0.6.2`   
**Domain:** `samsung_windfree_avant`

Questa integrazione custom controlla **Samsung WindFree Avant** tramite **SmartThings API (PAT)**.

Testato  con : 
- Samsung WindFree Avant S2

## Funzionalità
- Entità **Climate** con ON/OFF (OFF → `switch.off`, altre modalità → `switch.on` + `airConditionerMode`).
- Modalità HVAC supportate: auto, cool, heat, dry, fan_only.
- Entità aggiuntive:
  - **Display** (`samsungce.airConditionerLighting` → `on`/`off`)
  - **Beep** (`samsungce.airConditionerBeep` → `setBeep` on/off)
  - **Auto Cleaning** (`custom.autoCleaningMode` → `setAutoCleaningMode` on/off)


## Requisiti
- **Home Assistant** 2023.6+ (consigliato 2025.x+).
- **SmartThings Personal Access Token (PAT)**
  - Accedere al portale [API](https://account.smartthings.com/tokens) con l'account del condizionatore e creare un nuovo token

## Installazione
1. Copia il contenuto del repo in:
   ```
   config/custom_components/samsung_windfree_avant
   ```
2. Riavvia Home Assistant.
3. Vai su **Impostazioni → Dispositivi e servizi → Aggiungi Integrazione → ""**.
4. Inserisci il tuo **PAT** SmartThings.


## Debug rapido API
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
```

## Links
- Documentazione: https://developer.smartthings.com/docs/api/public#tag/Devices
- Portale API: https://account.smartthings.com/tokens

