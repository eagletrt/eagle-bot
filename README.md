# T.E.C.S. - 3.0

**eagle-bot** è un bot Telegram progettato per il team E-Agle TRT, che integra funzionalità di gestione attività, interazione con database NocoDB, e interrogazione di API interne per monitorare la presenza in laboratorio e le ore di permanenza.

## Funzionalità principali

- **Gestione ODG (Ordine del Giorno):** aggiunta, rimozione, reset e visualizzazione di una lista di attività condivisa per chat/thread.
- **Integrazione con NocoDB:** recupero di tag (aree, gruppi di lavoro, progetti, ruoli) e membri associati tramite API REST.
- **Interazione con API Eagle:** visualizzazione delle persone attualmente in laboratorio e delle ore trascorse da ciascun membro.
- **Risposta a menzioni:** menzionando un tag (es. `@mt`) il bot risponde con la lista dei membri associati.
- **Log dettagliato:** log su file e console, con colorazione dei livelli di log.

## Struttura dei file principali

- [`main.py`](main.py):  
  Entrypoint del bot. Gestisce la configurazione, l'avvio, la registrazione degli handler dei comandi e delle menzioni, e l'inizializzazione dei client per NocoDB e E-Agle API.

- [`modules/nocodb.py`](modules/nocodb.py):  
  Wrapper leggero per l'API REST di NocoDB. Permette di recuperare tag, membri associati a tag, e di mappare username Telegram ↔ email di team.

- [`modules/api_client.py`](modules/api_client.py):  
  Client per le API di E-Agle (endpoints `/lab/ore` e `/lab/inlab`). Permette di ottenere la lista delle persone in laboratorio e le ore di presenza.

- [`modules/database.py`](modules/database.py):  
  Modulo ORM (Pony ORM) per la gestione locale delle attività (Task) e delle liste ODG, persistite su SQLite (`data/eagletrtbot.db`).

- [`docker-compose.yml`](docker-compose.yml) & [`Dockerfile`](Dockerfile):  
  Permettono l’esecuzione del bot in ambiente Docker, con persistenza dei dati e configurazione tramite variabili d’ambiente.

- [`requirements.txt`](requirements.txt):  
  Elenco delle dipendenze Python necessarie: `python-telegram-bot`, `requests`, `pony`.

## Variabili d’ambiente richieste

- `TELEGRAM_BOT_TOKEN`: token del bot Telegram.
- `NOCO_URL`: URL base dell’istanza NocoDB.
- `NOCO_API_KEY`: API key per autenticazione NocoDB.
- `EAGLE_API_URL`: URL base delle API E-Agle.

## Avvio rapido (per sviluppo locale)

1. **Configurazione variabili d’ambiente:**  
   Impostare le variabili richieste (vedi sopra).

2. **Installazione dipendenze:**  
   Eseguire `pip install -r requirements.txt` per installare le dipendenze Python.

3. **Avvio del bot:**  
   Eseguire `python main.py` per avviare il bot.

## Avvio con Docker

1. **Configurazione variabili d’ambiente:**  
   Aggiornare il file `docker-compose.yml` con le variabili richieste.

2. **Costruzione ed esecuzione del container:**
    Eseguire `docker-compose up --build -d` per costruire ed avviare il container in background.

## Log

- I log vengono salvati in `data/bot.log` con livello WARNING e superiori.
- I log di livello INFO e superiori vengono mostrati in console con colorazione.

## Database ODG

- Il database SQLite `data/eagletrtbot.db` viene creato automaticamente alla prima esecuzione.
- Contiene le tabelle `Task` e `OdgList` per la gestione delle attività.

## Esempi di utilizzo

- **Aggiungere una task all'ODG:**

  ```
  /odg <task>
  ```

- **Rimuovere una task dall'ODG:**

  ```
  /odg remove <numero_task>
  ```

- **Resettare l'ODG:**

  ```
  /odg reset
  ```

- **Visualizzare l'ODG:**

  ```
  /odg
  ```

- **Visualizzare i tag disponibili:**

  ```
  /tags
  ```

- **Visualizzare membri di un'area/workgroup/progetto/ruolo/inlab:**

  ```
  @sw @rt @cr @tl @inlab
  ```

- **Visualizzare persone in laboratorio:**

  ```
  /inlab
  ```

- **Visualizzare ore di presenza in lab del mese:**
  ```
  /ore
  ```
