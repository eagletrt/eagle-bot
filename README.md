# T.E.C.S.

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

1.  **Core (`main.py`)**: This is the application's entry point. It manages the bot's lifecycle, initializes clients for external APIs, and registers command and mention handlers based on the configuration.
2.  **Command Handlers (`/commands`)**: Each file in this directory implements the logic for a specific command (e.g., `/odg`, `/inlab`). This approach keeps the code organized and easy to extend.
3.  **Modules (`/modules`)**: Contains clients and wrappers for interacting with external services and the local database.
    - `nocodb.py`: Client for NocoDB APIs.
    - `api_client.py`: Client for E-Agle's internal APIs.
    - `database.py`: Manager for the local database (SQLite with Pony ORM).
    - `quiz.py`: Logic for quiz management.
    - `scheduler.py`: For running scheduled tasks.
4.  **Persistent Data (`/data`)**: A directory mounted as a Docker volume to store the SQLite database, log files, and configuration.
5.  **Configuration (`config.ini`)**: A central configuration file that allows enabling or disabling features (feature flags) and customizing bot settings without modifying the code.

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
├── Dockerfile        # Instructions to build the Docker image
├── config.ini.example # Example configuration file
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

3.  **Configure the bot:**
    Create a copy of the `config.ini.example` file, rename it to `config.ini`, and move it to the `data/` folder. Modify the values inside according to your needs.

4.  **Export the required environment variables:**
    API keys and tokens should not be placed in the configuration file but exported as environment variables for security.

    ```bash
    export TELEGRAM_BOT_TOKEN="your_token"
    export NOCO_API_KEY="your_api_key"
    export SHLINK_API_KEY="your_api_key"
    export CONFIG_PATH="data/config.ini"
    ```

5.  **Start the bot:**
    ```bash
    python main.py
    ```

### Docker

The recommended way to run the bot in production is via Docker, to ensure an isolated environment and simplified management.

1.  **Create the configuration file:**
    Create the `data` folder if it doesn't exist, then create the `data/config.ini` file from `config.ini.example` and customize it.

2.  **Create a `.env` file:**
    Create a `.env` file in the project root for environment variables. Docker Compose will automatically use it to populate them in the container.

    ```env
    TELEGRAM_BOT_TOKEN=...
    NOCO_API_KEY=...
    SHLINK_API_KEY=...
    CONFIG_PATH=...
    ```

3.  **Start the container:**
    ```bash
    docker compose up --build -d
    ```

## Configuration

The bot's configuration is managed through the `data/config.ini` file, which allows you to customize the bot's behavior without modifying the source code.

### Environment Variables

The following environment variables are **mandatory** for authentication with external services:

| Variable             | Description                                  |
| -------------------- | -------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | Authentication token for the Telegram bot.   |
| `NOCO_API_KEY`       | API key for authentication with NocoDB.      |
| `SHLINK_API_KEY`     | API key for authentication with Shlink.      |

### `config.ini` File

This file is divided into sections:

- **`[Settings]`**: Contains general settings like API URLs, log levels, and quiz areas.
- **`[Paths]`**: Defines the paths for log files and the database.
- **`[Features]`**: Allows you to enable or disable bot features (e.g., `ODGCommand`, `FSQuiz`). Setting a value to `false` will prevent the corresponding command or feature from being loaded.

## Usage

### Available Commands

| Command     | Description                                             | Example                             |
| ----------- | ------------------------------------------------------- | ----------------------------------- |
| `/start`    | Shows a welcome message.                                | `/start`                            |
| `/odg`      | Manages the Agenda (ODG).                               | `/odg`, `/odg <task>`, `/odg reset` |
| `/tags`     | Shows available tags (areas, projects, etc.).           | `/tags`                             |
| `/inlab`    | Shows who is currently in the lab.                      | `/inlab`                            |
| `/ore`      | Shows the monthly hours for each member.                | `/ore`                              |
| `/quiz`     | Starts or manages a quiz.                               | `/quiz <id>`                        |
| `/quizzes`  | Lists all available quizzes.                            | `/quizzes`                          |
| `/question` | Sends a random question from a specific area.           | `/question <area>`                  |
| `/answer`   | Allows answering an open-ended question.                | `/answer <text>`                    |
| `/qr`       | Generates a QR code from the provided text.             | `/qr https://example.com`           |
| `/events`   | Shows upcoming events.                                  | `/events`                           |
| `/id`       | Shows the current chat ID and your user ID.             | `/id`                               |

### Mentions

You can mention a tag (previously configured in NocoDB) to notify all associated members.

- **Syntax**: `@<tag_name>`
- **Example**: `@sw` will mention all members of the "Software" group.
- **Special Mentions**:
  - `@inlab`: Mentions all users currently in the lab.

## Technical Details

### Logging

The logging system is configurable via the `config.ini` file:

- **`ConsoleLogLevel`**: Sets the log level for console output (e.g., `INFO`, `DEBUG`). Console logs are colored for better readability.
- **`FileLogLevel`**: Sets the log level for saving to a file (e.g., `WARNING`, `ERROR`).
- **`LogFilePath`**: Specifies the path to the log file (e.g., `data/bot.log`).

### Database

- The bot uses an **SQLite** database (`/data/eagletrtbot.db`) for persisting data related to the agenda and quizzes.
- Interaction with the database is handled via **Pony ORM**, which abstracts SQL queries and simplifies entity management.
- The database file is created automatically on the first run.
