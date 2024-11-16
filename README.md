# DiseaseDx: Disease Diagnosis
Developed for my final project in Computer Science

---

## Setting up local environment

```bash
# Check for pipenv
$ pip show pipenv

# Install pipenv if not installed
$ pip install pipenv

# Install dependencies from Pipfile
$ pipenv install
```

You can run the `joined_inheritance.py` locally in 3 ways:
- Creating a MySQL database called `diseasedx_test` and saving the user and pass on `MYSQL_USER` and `MYSQL_PASS`
- Creating a `SQLite db in memory`
- Creating a `local SQLite db`

> For the `local SQLite db` it's interesting to install the extension `SQLite` as it let's you open the tables and queries on `VS Code`
>
> After running the code and creating the `mylocaldb.db` you can press `CTRL + SHIFT + P`, type `SQLite: Open Database`, hit enter and then select the `mylocaldb.db`
>
> It will open a blade on the bottom left corner where you can interact with the db

---

## Class Diagram

![class_diagram](./diagrams/tcc_class_diagram.png)

## Object Diagram

![object_diagram](./diagrams/tcc_object_diagram.png)