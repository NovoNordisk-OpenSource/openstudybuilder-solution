# Introduction 
This repository is used for utilities and scripts for managing Neo4j MDR Database.

# Neo4j Database Getting Started 
For local development we recommend running with [docker](https://docs.docker.com/engine/install/).

Please follow the **Install Docker Engine** guide based on your operating system, i.e. for Ubuntu, please follow [this](https://docs.docker.com/engine/install/ubuntu/).

**Warning:** Verify that your user is in the docker group before starting working with the docker system.

**Note:** For windows users run the shell scripts using WSL/WSL2 - or alternatively boot up a neo4j desktop DB and connect to that.

---

# Python Getting Started

This project uses https://github.com/pypa/pipenv for dependencies
management, so you must install it on your system (version 2020.8.13 or later, ubuntu apt ships and old version so use pip to install pipenv)

```
$ python3 --version
$ pip --version
$ pip install pipenv
```
---

# Build and Test
## Initial setup - Install Docker
### Clone repository

Clone the Neo4j repository on your local instance

---
### Setup environment variables
Create `.env` file (in the root of cloned repository) with a following content (adjust accordingly):
```
NEO4J_MDR_HTTP_PORT=5074
NEO4J_MDR_BOLT_PORT=5078
NEO4J_MDR_HTTPS_PORT=443
NEO4J_MDR_HOST=localhost
NEO4J_MDR_AUTH_USER=neo4j
NEO4J_MDR_AUTH_PASSWORD=test1234
NEO4J_MDR_DATABASE=neo4j
NEO4J_MDR_CLEAR_DATABASE=false
NEO4J_MDR_BACKUP_DATABASE=false
```
**Note:**
If you run neo4j desktop, the defaults ports are
```
NEO4J_MDR_HTTP_PORT=7474
NEO4J_MDR_BOLT_PORT=7687
```
---
### Create container
Create/re-create and start the `neo4j_local`container with (after `cd neo4j-mdr-db`)

```sh
$ ./create_neo4j_local.sh
```

The `create_neo4j_local.sh` script uses variables from the `.env` file.

**Note:** After creating the database container, it can be started and stopped with `docker start neo4j_local` and `docker stop neo4j_local`.

**Note:**
On very first run of `create_neo4j_local.sh` at the beginning of command output you may see an error message `Error: No such container: neo4j_local` which is perfectly normal at very first run.

**Warning:**
You may notice from there that after starting the docker container for the neo4j database, some folder of the project are not anymore owned by your user.
Then you will have to change them back before working with the neo4j_local!

---
### Verify container is running
In order to verify that the neo4j_local docker is running, you can run the following:
```sh
$ docker ps
```
You will get a docker table of running container

### Reading container logs
The standard output from the container can be read with the logs command:
```sh
$ docker logs neo4j_local
```

The log can be followed by adding the `--follow` flag:
```sh
$ docker logs neo4j_local --follow
```
Stop following with ctrl-C.

Other log files are stored inside the container and can be read like this (assuming the container is running):
```sh
$ docker exec neo4j_local cat /var/lib/neo4j/logs/debug.log | less
```
See the neo4j documentation for what log files are available.

---
### Folders mounted in the docker container

The `create_neo4j_local.sh` script creates and mounts several directories in the container.

- `import_files`: Files placed here become available for loading with Cypher queries such as:

  ```LOAD CSV WITH HEADERS FROM 'file:///my_file.csv'```

- `load_scripts`. Place .cypher files here to make them available for running with `cypher-shell`:

   ```docker exec neo4j_local bin/cypher-shell --file load_scripts/my_script.cypher --database neo4j --user neo4j --password test1234 --fail-at-end```.

- `db_import` and `db_export`: Used to export and import databases backups. 

## Initial setup - After installation of Docker
---
### Activate pipenv

Activate pipenv by running:

```
$ pipenv install
```

### Initiate neo4j database

#### Keeping or clearing existing data
The initialization script uses two environment varaibles to determine how to handle any
existing database:
```
NEO4J_MDR_CLEAR_DATABASE=false
NEO4J_MDR_BACKUP_DATABASE=false
```

If `NEO4J_MDR_CLEAR_DATABASE` is set to `false`, then the database is left as is.
If it's set to `true`, it clears the database.
When clearing, the existing database can be kept as a backup.
To do this, set `NEO4J_MDR_BACKUP_DATABASE` to `true`.
Then the existing database will be kept under a different name.

This desired database name is given by the `NEO4J_MDR_DATABASE` environment variable. 
This name will be created as an alias that points at the actual database.
This is done in order to work around the limitation that a database in neo4j cannot be renamed.
Using aliases makes it possible to keep a backup copy of the database when clearing.
The actual database name can be controlled via the `NEO4J_MDR_DATABASE_DBNAME` environment variable. 
```
NEO4J_MDR_DATABASE_DBNAME=some-name
```
If this variable is set to a value that does not start with "auto", it will be used as the database name.
Note that the name must follow the neo4j
[database naming rules](https://neo4j.com/docs/cypher-manual/current/databases/#administration-databases-create-database),
meaning that the name must start with a letter and can only contain letters, numbers, dots and dashes.
Underscores and other special characters are not allowed.
If the variable is not set, or set to something starting with "auto", the database name will be generated
by appending the current date and time to the value of `NEO4J_MDR_DATABASE`,
for example "mydbname-2022.08.15-12.25"

#### Running initialization

Initiate the database using pipenv:

```
$ pipenv run init_neo4j
```


**Note:** You may have to install the following package if you get the error: invalid command 'bdist_wheel':
```
$ pip3 install wheel
```

---
### Verify setup is correctly done

Verify that neo4j browser/database is accessible on `http://localhost:5074` (user: `neo4j`, password: `test1234`)

---

# Populate the database
Before Studybuilder can be used, the database must be populated.
The database should have been initialized as part of the build steps above.
If not, see [Initiate neo4j database](#initiate-neo4j-database). 

Populating the database consists of two steps that must be performed in order:

1. CDISC

   This imports all CDISC terms.
   Follow the instructions in the `mdr-standards-import` repository.
   The import is performed by directly accessing the Neo4j database,
   and the StudyBuilder backend is not required. 

2. Sponsor library

   This creates all needed codelists in the sponsor library. 
   It also includes a set of mockup data to create example projects, studies etc.
   Follow the instructions in the `studybuilder-import` repository.
   This step performs the import by calling the StudyBuilder api,
   and thus the backend must be running.
   See the instructions in the `clinical-mdr-api` repository.

---

# Exporting a database backup

The script `export_db_backup.sh` can be used to back the contents of a database.

For example, this connects to the container `neo4j_local` and exports the database `neo4j` to the file `./db_backups/neo4j-{timestamp}.backup`.
```sh
$ export $(grep -v '^#' .env | xargs)
$ ./export_db_backup.sh neo4j_local neo4j
```


# Importing a database backup

The script `import_backup_db.sh` can be used to import a backup into a database.

For example, this connects to the container `neo4j_local` and imports the file `./db_backups/neo4j-{timestamp}.backup` into the database `neo4j`.
```sh
$ export $(grep -v '^#' .env | xargs)
$ ./import_db_backup.sh neo4j_local neo4j neo4j-{timestamp}.backup
```
This replaces any existing content in the database `neo4j` with the data stored in the file `./db_backups/neo4j-{timestamp}.backup`.

---

# Exporting a database as Cypher statements

The script `export_to_cypher.py` can be used to back up the contents of a database.
Compared to the `export_db_backup.sh` script, this method can export from any database
that can be accessed via bolt.
The downside is that it takes considerably longer to run.

A read-only account is sufficient.

It connects to the database specified by the same environment variables as the init script:
```
NEO4J_MDR_DATABASE
NEO4J_MDR_HOST
NEO4J_MDR_BOLT_PORT
NEO4J_MDR_AUTH_USER
NEO4J_MDR_AUTH_PASSWORD
```

Run it with pipenv:
```
$ pipenv run export_to_cypher
```

This dumps all the data in the database as Cyper statements.
The filename is set to `dump_{NEO4J_MDR_DATABASE}.cypher`.

# Importing a database from Cypher statements

The script `import_from_cypher.py` can be used to import a file with Cypher statements.
Compared to the `import_db_backup.sh` script, this method can import into any database
that can be accessed via bolt.
The downside is that it takes considerably longer to run.

An account with write access and database management privileges is required.

It connects to the database specified by the same environment variables as the init script:
```
NEO4J_MDR_DATABASE
NEO4J_MDR_HOST
NEO4J_MDR_BOLT_PORT
NEO4J_MDR_AUTH_USER
NEO4J_MDR_AUTH_PASSWORD
```


Run it with pipenv, specifying the filename to read from:
```
$ pipenv run import_from_cypher dump_example.cypher
```

The database is created if it doesn't already exist.
If it does exist, it should be empty to avoid any errors due to conflicts.

# Import NeoDash reports
The script `import_reports` can be used to import pre-built NeoDash reports into the Neo4j database. That way, anyone connecting to the database using NeoDash will see a list of available reports to browse.

It connects to the database specified by the same environment variables as the init script:
```
NEO4J_MDR_DATABASE
NEO4J_MDR_HOST
NEO4J_MDR_BOLT_PORT
NEO4J_MDR_AUTH_USER
NEO4J_MDR_AUTH_PASSWORD
```
Run it with pipenv, specifying the directory where the reports JSON files are stored:
```
$ pipenv run import_reports "neodash_reports"
```

## How to Connect to NeoDash  

NeoDash can be accessed in two ways:  
1. Directly from the **Neo4j Browser**.  
2. Through the standalone site: [http://neodash.graphapp.io/](http://neodash.graphapp.io/).  

### Connecting to the Standalone Site  
To connect via the standalone site, follow these steps:  

1. **Ensure you are using HTTP, not HTTPS.** NeoDash requires an HTTP connection, so make sure the URL starts with `http://` instead of `https://`.  
2. Once on the NeoDash site, enter the following database connection details:  
   - **Host:** `NEO4J_MDR_HOST`  
   - **Bolt Port:** `NEO4J_MDR_BOLT_PORT`  
   - **Database Name:** `NEO4J_MDR_DATABASE`  
   - **Password:** `NEO4J_MDR_AUTH_PASSWORD`  
3. Click **Connect** to log in.  

### Accessing or Creating Dashboards  
- If you have already imported NeoDash reports in the previous step, you will see the existing dashboards.  
- To create a new dashboard, click **New Dashboard** and start building your reports.  

# Update CT stats
The script `update_ct_stats` loops through all CT packages to update the counters of added, modified and removed terms and codelists.
This is intended to be run periodically to keep these counters up to date.

The script reuses a fair bit of code from the API.
A future improvement could be to build this update functionality directy into the API.


