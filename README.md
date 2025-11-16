# T.E.C.S. - 3.2

**Eagle-Bot** is a multi-function Telegram bot designed for the E-Agle TRT team. It simplifies task management, interaction with external databases, and monitoring of lab attendance, acting as a digital assistant for the team.

## Table of Contents

- [Main Features](#main-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation and Startup](#installation-and-startup)
  - [Local Development](#local-development)
  - [Docker](#docker)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Available Commands](#available-commands)
  - [Mentions](#mentions)
- [Technical Details](#technical-details)
  - [Logging](#logging)
  - [Database](#database)

---

## Main Features

- **Agenda Management (ODG)**: Add, remove, view, and reset a shared task list for each chat or thread.
- **NocoDB Integration**: Retrieve information about members, areas, workgroups, and projects via REST API.
- **Interaction with E-Agle API**: Monitor who is present in the lab and view the monthly hours of each member.
- **Mention Notifications**: By mentioning a tag (e.g., `@sw`), the bot responds with the list of associated members, facilitating communication.
- **Quiz Management**: Create and manage interactive quizzes for team training and engagement.
- **QR Code Generation**: Create QR codes from any text or URL.
- **Detailed Logging**: Records operations to files and console with colored log levels for easy debugging.

## Architecture

The bot is built on a modular architecture that separates responsibilities into distinct components:

1.  **Core (`main.py`)**: This is the application's entry point. It manages the bot's lifecycle, initializes clients for external APIs, and registers command and mention handlers.
2.  **Command Handlers (`/commands`)**: Each file in this directory implements the logic for a specific command (e.g., `/odg`, `/inlab`). This approach keeps the code organized and easy to extend.
3.  **Modules (`/modules`)**: Contains clients and wrappers for interacting with external services and the local database.
    - `nocodb.py`: Client for NocoDB APIs.
    - `api_client.py`: Client for E-Agle's internal APIs.
    - `database.py`: Manager for the local database (SQLite with Pony ORM).
    - `quiz.py`: Logic for quiz management.
    - `scheduler.py`: For executing scheduled tasks.
4.  **Persistent Data (`/data`)**: A directory mounted as a Docker volume to store the SQLite database and log files.

## Project Structure

```
.
├── commands/         # Bot command handlers
│   ├── odg.py
│   ├── inlab.py
│   └── ...
├── data/             # Persistent data (database, logs)
├── modules/          # Reusable modules (API clients, DB)
│   ├── nocodb.py
│   ├── api_client.py
│   ├── database.py
│   └── ...
├── main.py           # Application entrypoint
├── requirements.txt  # Python dependencies
├── Dockerfile        # Instructions for building the Docker image
└── README.md         # This documentation
```

## Prerequisites

- Python 3.9+
- Docker and Docker Compose (for running in a container)
- Access to NocoDB and E-Agle APIs

## Installation and Startup

### Local Development

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/eagletrt/eagle-bot.git
    cd eagle-bot
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv myenv
    source myenv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**
    Create a `.env` file in the project root or export the required variables (see [Configuration](#configuration)).

4.  **Start the bot:**
    ```bash
    python main.py
    ```

### Docker

The recommended way to run the bot in production is via Docker, to ensure an isolated environment and simplified management.

1.  **Configure environment variables:**
    Create a `.env` file in the project root. Docker Compose will automatically use it to populate environment variables in the container.

    ```env
    TELEGRAM_BOT_TOKEN=...
    NOCO_API_KEY=...
    SHLINK_API_KEY=...
    ```

2.  **Build and start the container:**
    ```bash
    docker compose up --build -d
    ```

## Configuration

### Environment Variables

The following environment variables are required for the bot to function correctly:

| Variable             | Description                               |
| -------------------- | ----------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | Authentication token for the Telegram bot. |
| `NOCO_API_KEY`       | API key for authentication with NocoDB.   |
| `SHLINK_API_KEY`     | API key for authentication with Shlink.   |

## Usage

### Available Commands

| Command    | Description                                      | Example                             |
| ---------- | ------------------------------------------------ | ----------------------------------- |
| `/start`   | Shows a welcome message.                         | `/start`                            |
| `/odg`     | Manages the Agenda (ODG).                        | `/odg`, `/odg <task>`, `/odg reset` |
| `/tags`    | Shows available tags (areas, projects, etc.).    | `/tags`                             |
| `/inlab`   | Shows who is currently in the lab.               | `/inlab`                            |
| `/ore`     | Shows the monthly hours for each member.         | `/ore`                              |
| `/quiz`    | Starts or manages a quiz.                        | `/quiz <id>`                        |
| `/quizzes` | Lists all available quizzes.                     | `/quizzes`                          |
| `/qr`      | Generates a QR code from the provided text.      | `/qr https://example.com`           |
| `/events`  | Shows upcoming events.                           | `/events`                           |

### Mentions

You can mention a tag (previously configured in NocoDB) to notify all associated members.

- **Syntax**: `@<tag_name>`
- **Example**: `@sw` will mention all members of the "Software" group.
- **Special Mentions**:
  - `@inlab`: Mentions all users currently in the lab.

## Technical Details

### Logging

- Logs of level `INFO` and higher are printed to the console with colored output.
- Logs of level `WARNING` and higher are saved to the `/data/bot.log` file inside the container.

### Database

- The bot uses an **SQLite** database (`/data/eagletrtbot.db`) for persisting data related to the agenda and quizzes.
- Interaction with the database is managed via **Pony ORM**, which abstracts SQL queries and simplifies entity management.
- The database file is created automatically on the first run.
