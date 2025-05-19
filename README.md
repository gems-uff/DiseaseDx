# DiseaseDx: Disease Diagnosis

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.44.1-brightgreen?style=flat-square&logo=streamlit)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=flat-square&logo=mysql)
![SQLite](https://img.shields.io/badge/SQLite-3.0-lightblue?style=flat-square&logo=sqlite)

DiseaseDx is a disease diagnosis system developed as part of my final project in Computer Science.

---

## Table of Contents
1. [About the Project](#about-the-project)
2. [Setting Up the Local Environment](#setting-up-the-local-environment)
3. [Running the Project](#running-the-project)
4. [Configuring VS Code Debugging](#configuring-vs-code-debugging)
5. [Diagrams](#diagrams)
6. [Technologies Used](#technologies-used)

---

## About the Project

DiseaseDx is a system designed to assist in diagnosing diseases by evaluating symptoms and test results using an evaluation tree. It leverages SQLAlchemy for database interactions and Streamlit for front-end with caching and performance optimization.

---

## Setting Up the Local Environment

Follow these steps to set up the project locally:

### Prerequisites
- Python 3.13
- `pipenv` for dependency management
- If running on Windows it also needs `protobuf==5.27.0`

### Installation

```bash
# Check if pipenv is installed
$ pip show pipenv

# Install pipenv if not installed
$ pip install pipenv

# Install dependencies from Pipfile
$ pipenv install
```

---

## Running the Project

You can run the project in three ways:

1. **Using a MySQL Database**:
   - Create a MySQL database called `diseasedx_test`.
   - Set the environment variables `MYSQL_USER` and `MYSQL_PASS` with your MySQL credentials.

2. **Using a SQLite Database in Memory**:
   - Modify the connection string in `db_config.py` to use SQLite in-memory mode.

3. **Using a Local SQLite Database**:
   - Modify the connection string in `db_config.py` to use a local SQLite database (e.g., `sqlite:///mylocaldb.db`).
   - Install the [SQLite extension](https://marketplace.visualstudio.com/items?itemName=alexcvzz.vscode-sqlite) for VS Code to interact with the database.

> **Tip**: For the local SQLite database, after running the project and creating `mylocaldb.db`, you can open it in VS Code:
> - Press `CTRL + SHIFT + P`, type `SQLite: Open Database`, and select `mylocaldb.db`.
> - A blade will open in the bottom-left corner where you can interact with the database.

---

## Configuring VS Code Debugging

To debug the project in VS Code, you can use the following `launch.json` configuration:

```jsonc
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Python:Streamlit",
            "type": "debugpy",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "main.py"
            ],
            "console": "integratedTerminal",
            "justMyCode": false,
            "cwd": "${workspaceFolder}/src"
        }
    ]
}
```

### Steps to Configure:
1. Open the `.vscode` folder in your project directory.
2. Create or edit the `launch.json` file with the above configuration.
3. To debug the Streamlit app:
   - Open the Debug panel in VS Code (`CTRL + SHIFT + D`).
   - Select the `Python:Streamlit` configuration.
   - Click the green "Start Debugging" button.

---

## Diagrams

### Class Diagram
![class_diagram](./diagrams/tcc_class_diagram.png)

### Object Diagram
![object_diagram](./diagrams/tcc_object_diagram.png)

---

## Technologies Used

- **Python**: Core programming language for the project.
- **SQLAlchemy**: ORM for database interactions.
- **Streamlit**: Used as front-end for caching and performance optimization.
- **MySQL**: Primary database for production.
- **SQLite**: Alternative database for local development and testing.

---

Feel free to contribute or reach out with any questions!