# Stock Date Simplification — Design Spec

## Problem
`weeksUntil()` im Frontend mischt `Date.UTC()`, `getUTCFullYear`/`getUTCMonth`/`getUTCDate` und manuelles ISO-String-Parsing (`split('T')`). Das ist schwer lesbar, fehleranfällig und DST-unsicher.

## Lösung
BE liefert `expires_at` als date-only String (YYYY-MM-DD) statt ISO-Datetime. FE rechnet Differenz mit lokalen `Date`-Konstruktoren — DST-sicher, Browserzeit = immer aktuell.

## Änderungen

### Backend — `api/app/services/stock.py`
- `compute_stock_balance()`: `"expires_at"` → `g["date"]` (schon YYYY-MM-DD), `"expired"` entfernen
- `create_production()`: Parsing von `datetime.fromisoformat(...)` → `datetime.strptime(body.expires_at, "%Y-%m-%d")`

### Backend — `api/app/schemas/stock.py`
- `BatchExpiresAtUpdate.expires_at`: `datetime` → `date`

### Frontend — `web/src/views/StockView.vue`
- `Batch`-Interface: `expired`-Feld entfernen
- `startEdit()`: `batch.expires_at.split('T')[0]` → `batch.expires_at`
- `weeksUntil()`: Lokale Date-Konstruktoren statt UTC
- `fmtDate()`: Vereinfachen (optional, aktuell schon robust)

### Betroffene Dateien
- `api/app/services/stock.py` (2 Stellen)
- `api/app/schemas/stock.py` (1 Stelle)
- `api/app/routers/stock.py` (evtl. Import für `date`)
- `web/src/views/StockView.vue` (Interface, Funktionen)

### Nicht betroffen
- Kein DB-Migration nötig (SQLite speichert DateTime und Date identisch)
- `CozinhaView.vue`, `ExpedicaoView.vue` — kein `expires_at`-Zugriff
