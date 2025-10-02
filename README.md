# T.E.C.S. - 3.0

**eagle-bot** is a Telegram bot designed for the EagleTRT team. It integrates task management, interaction with a NocoDB database, and internal API queries to monitor lab presence and time spent.

## Main features

- **ODG (Agenda) management:** Add, remove, reset, and view a shared task list per chat/thread.
- **NocoDB integration:** Retrieve tags (areas, workgroups, projects, roles) and members associated with tags via the REST API.
- **Eagle API interaction:** Display people currently in the lab and the hours each member has spent.
- **Reply to mentions:** Mentioning a tag (e.g. `@sw`) the bot replies with the list of associated members.
- **Detailed logging:** Logs to file and console, with colored log levels.

## Main file structure

- [`main.py`](main.py):  
  Bot entrypoint. Handles configuration, startup, registering command and mention handlers, and initializing clients for NocoDB and the Eagle API.

- [`modules/nocodb.py`](modules/nocodb.py):  
  Lightweight wrapper for the NocoDB REST API. Allows fetching tags, members associated with a tag, and mapping Telegram usernames ↔ team emails.

- [`modules/api_client.py`](modules/api_client.py):  
  Client for the Eagle API (endpoints `/lab/ore` and `/lab/inlab`). Allows obtaining the list of people in the lab and presence hours.

- [`modules/database.py`](modules/database.py):  
  ORM module (Pony ORM) for local management of tasks (Task) and ODG lists, persisted to SQLite (`/data/eagletrtbot.db`).

- [`docker-compose.yml`](docker-compose.yml) & [`Dockerfile`](Dockerfile):  
  Enable running the bot in Docker with persistent data and configuration via environment variables.

- [`requirements.txt`](requirements.txt):  
  List of required Python dependencies: `python-telegram-bot`, `requests`, `pony`.

## Required environment variables

- `TELEGRAM_BOT_TOKEN`: Telegram bot token.
- `NOCO_URL`: Base URL of the NocoDB instance.
- `NOCO_API_KEY`: API key for NocoDB authentication.
- `EAGLE_API_URL`: Base URL of the Eagle API.

## Quick start (for local development)

1. **Configure environment variables:**  
   Set the required variables (see above).

2. **Install dependencies:**  
   Run `pip install -r requirements.txt` to install Python dependencies.

3. **Start the bot:**  
   Run `python main.py` to start the bot.

## Running with Docker

1. **Configure environment variables:**  
   Update `docker-compose.yml` with the required variables.

2. **Build and run the container:**  
   Run `docker-compose up --build -d` to build and start the container in the background.

## Logs

- Logs are saved to `/data/bot.log` with level WARNING and above.
- INFO and above are shown in the console with colored output.

## ODG Database

- The SQLite database `/data/eagletrtbot.db` is created automatically on first run.
- It contains the `Task` and `OdgList` tables for managing tasks.

## Usage examples

- **Add a task to the ODG:**

  ```
  /odg <task>
  ```

- **Remove a task from the ODG:**

  ```
  /odg <task_number>
  ```

- **Reset the ODG:**

  ```
  /odg reset
  ```

- **Show the ODG:**

  ```
  /odg
  ```

- **Show available tags:**

  ```
  /tags
  ```

- **Show members of an area/workgroup/project/role/inlab:**

  ```
  @sw @rt @cr @tl @inlab
  ```

- **Show people currently in the lab:**

  ```
  /inlab
  ```

- **Show monthly lab presence hours:**
  ```
  /ore
  ```
