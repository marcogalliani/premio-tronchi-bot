# Premio tronchi

Bot Telegram per aggiornare e mostrare la classifica dei "tronchi", cioe' gli attaccanti di Serie A che prendono voto (senza bonus/malus) minore o uguale a 5 al fantacalcio.

## Funzionalita'

- inizializzazione classifica fino alla giornata corrente (processando tutte le giornate disponibili)
- aggiornamento incrementale alle nuove giornate
- visualizzazione classifica aggiornata

## Regole classifica

Per ogni file voti trovato su Fantacalcio:

- vengono considerati solo i giocatori con ruolo attaccante (`A`, `ATT`, `ATTACCANTE`)
- viene usato il voto puro (colonna `Voto`, senza bonus)
- se voto <= 5, il giocatore riceve `+1`

La classifica totale e' la somma dei `+1` su tutte le giornate elaborate.

## Fonte dati

Pagina usata per i voti:

- https://www.fantacalcio.it/voti-fantacalcio-serie-a

Il bot cerca i link di download voti presenti nella pagina (`.xlsx` o endpoint API). Se trova l'endpoint API (`/api/v1/Excel/votes/<stagione>/<giornata>`), genera automaticamente tutte le giornate da `1` a quella corrente e processa solo quelle non ancora elaborate.

Nota: Fantacalcio puo' proteggere il download con autenticazione. In quel caso va configurata la variabile `FANTACALCIO_COOKIE`.

## Stack tecnico

- Python 3.10+
- `python-telegram-bot`
- `pandas` + `openpyxl`
- `requests` + `beautifulsoup4`
- SQLite locale (`premio_tronchi.db`)

## Setup

1. Crea e attiva un virtual environment.
2. Installa il progetto:

```bash
pip install -e .
```

3. Crea `.env` partendo da `.env.example`.
4. Inserisci il token Telegram.

Variabili ambiente:

- `TELEGRAM_BOT_TOKEN` (obbligatoria)
- `FANTACALCIO_VOTI_PAGE_URL` (opzionale, default: pagina ufficiale)
- `DATABASE_PATH` (opzionale, default: `premio_tronchi.db`)
- `FANTACALCIO_COOKIE` (opzionale ma spesso necessaria per scaricare i voti da utente loggato)

## Avvio

```bash
premio-tronchi
```

Oppure:

```bash
python -m premio_tronchi
```

## Comandi Telegram

- `/start`: mostra i comandi disponibili
- `/aggiorna`: scarica e processa tutte le giornate non ancora elaborate
- `/classifica`: mostra la classifica tronchi

## Persistenza

Nel database SQLite vengono salvati:

- classifica (`ranking`)
- sorgenti gia' elaborate (`processed_sources`)

## Deploy su Render

Il progetto include la configurazione Blueprint in [render.yaml](render.yaml).

### 1. Pubblica il repository

Esegui push del progetto su GitHub/GitLab.

### 2. Crea il servizio su Render

1. Apri Render e seleziona New + -> Blueprint.
2. Collega il repository.
3. Render rilevera' automaticamente [render.yaml](render.yaml) e creera' un worker chiamato `premio-tronchi-bot`.

### 3. Configura variabili ambiente

Nel pannello Render del servizio imposta:

- `TELEGRAM_BOT_TOKEN` (obbligatoria)
- `FANTACALCIO_COOKIE` (consigliata/necessaria per download voti autenticato)

Le variabili seguenti sono gia' preimpostate dal Blueprint, ma puoi modificarle:

- `FANTACALCIO_VOTI_PAGE_URL`
- `DATABASE_PATH`

### 4. Deploy e verifica

1. Avvia il deploy.
2. Controlla i log: deve comparire il worker in esecuzione senza errori.
3. Su Telegram testa `/start`, `/aggiorna`, `/classifica`.

Nota: sul piano free il servizio puo' subire limitazioni di risorse o stop. Per massima affidabilita' 24/7 valuta un piano paid.