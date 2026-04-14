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
- Docker
- Kubernetes

## Setup locale

1. Crea e attiva un virtual environment.
2. Installa il progetto:

```bash
pip install -e .
```

3. Crea `.env` partendo da `.env.example`.
4. Inserisci il token Telegram e, se necessario, il cookie Fantacalcio.

Variabili ambiente:

- `TELEGRAM_BOT_TOKEN` (obbligatoria)
- `FANTACALCIO_VOTI_PAGE_URL` (opzionale, default: pagina ufficiale)
- `DATABASE_PATH` (opzionale, default: `premio_tronchi.db`)
- `FANTACALCIO_COOKIE` (opzionale ma spesso necessaria per scaricare i voti da utente loggato)

## Avvio locale

```bash
python -m premio_tronchi
```

## Docker

Build dell'immagine:

```bash
docker build -t docker.io/your-dockerhub-username/premio-tronchi:latest .
```

Login e push su Docker Hub:

```bash
docker login
docker push docker.io/your-dockerhub-username/premio-tronchi:latest
```

Avvio con Docker Compose:

```bash
docker compose up --build
```

Il compose monta un volume persistente e usa `DATABASE_PATH=/data/premio_tronchi.db`.

## Deploy su Oracle Always Free (consigliato)

Per un bot Telegram in polling, Oracle Always Free VM e' una scelta piu' stabile del Kubernetes free tier.

### 1) Crea una VM Always Free

- Usa un'immagine Ubuntu 22.04 o 24.04.
- Mantieni aperta solo la porta 22 (SSH). Nessuna porta HTTP e' necessaria per il bot in polling.

### 2) Installa Docker e Compose sulla VM

Connettiti in SSH e lancia:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
	"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
	$(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
	sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

### 3) Prepara i file applicazione

Sulla VM:

```bash
mkdir -p ~/premio-tronchi
cd ~/premio-tronchi
curl -L -o docker-compose.yml https://raw.githubusercontent.com/<OWNER>/<REPO>/<BRANCH>/deploy/oracle/docker-compose.oracle.yml
curl -L -o .env https://raw.githubusercontent.com/<OWNER>/<REPO>/<BRANCH>/.env.example
```

Poi modifica `.env` con i valori reali di `TELEGRAM_BOT_TOKEN` e `FANTACALCIO_COOKIE`.

### 4) Avvia il bot

```bash
docker compose pull
docker compose up -d
docker compose ps
docker compose logs -f
```

### 5) Aggiornamenti futuri

Quando pubblichi una nuova immagine su Docker Hub:

```bash
docker compose pull
docker compose up -d
```

### 6) Persistenza dati

La classifica e lo storico giornate restano persistenti nel volume Docker `premio-tronchi-data`.

## Kubernetes

I manifesti sono in [k8s/](k8s/).

### Prerequisiti

- una registry Docker dove pubblicare l'immagine
- un cluster Kubernetes con storage class disponibile

### Flusso rapido

1. Costruisci e pubblica l'immagine Docker.
2. Crea il Secret con `kubectl` oppure usa [k8s/secret.example.yaml](k8s/secret.example.yaml) come template per il tuo manifest reale.
3. Aggiorna l'immagine in [k8s/deployment.yaml](k8s/deployment.yaml).
4. Applica il bundle con:

```bash
kubectl apply -k k8s/
```

Esempio rapido per il Secret:

```bash
kubectl create secret generic premio-tronchi-secret \
	--from-literal=TELEGRAM_BOT_TOKEN=... \
	--from-literal=FANTACALCIO_COOKIE=...
```

### Note Kubernetes

- Il bot gira in polling.
- Mantieni `replicas: 1` per evitare polling duplicato.
- La classifica e' persistita nel PVC montato su `/data`.

Nota hosting: usare Kubernetes non e' obbligatorio per questo bot. Su free tier, una VM Always Free con Docker Compose e' in genere piu' semplice e stabile.

## Comandi Telegram

- `/start`: mostra i comandi disponibili
- `/aggiorna`: scarica e processa tutte le giornate non ancora elaborate
- `/classifica`: mostra la classifica tronchi

## Persistenza

Nel database SQLite vengono salvati:

- classifica (`ranking`)
- sorgenti gia' elaborate (`processed_sources`)
