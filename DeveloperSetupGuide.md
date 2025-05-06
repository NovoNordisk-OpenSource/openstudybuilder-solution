# OpenStudyBuilder Developer Setup

**This guide is intended for anybody looking to run a local OpenStudyBuilder environment for exploring, testing and developing. For additional information and configuration options, see the individual README files for each component.**

### Disclaimers

This guide assumes you are running `Ubuntu 20.4`.

- It is possible to us other version of Ubuntu, but that might require other configurations that are not within the scope of this guide.
- Equally this can also be run on a windows system using [WSL](https://learn.microsoft.com/en-us/windows/wsl/install), instructions for which are not within the scope of this guide.

## Table of Contents

1. [Configure Local Environment](#configure-local-environment)
2. [Set Up Local Database](#set-up-local-database)
3. [Populate Database](#populate-database)
4. [Set Up API](#set-up-api)
5. [Import Data](#import-data)
6. [Set Up Frontend](#set-up-frontend)
7. [Initialize OpenStudyBuilder after setup](#initialize-openstudybuilder-after-setup)

## Configure Local Environment

### Clone git repo

Change to the directory you wish to clone the repository to using `cd`, then run:

```console
git clone https://gitlab.com/Novo-Nordisk/nn-public/openstudybuilder/OpenStudyBuilder-Solution.git
```

### Install Docker on Ubuntu 20.4

To run Docker in Ubuntu 20.4 complete the following steps:

Update the local repository:

```console
sudo apt update
```

Install docker:

```console
sudo apt install docker.io -y
```

Add you username to the docker group:

```console
sudo usermod -aG docker $USER
```

To verify that docker is running ***exit out of the terminal window and restart it again***, then run:

```console
docker run hello-world
```

Text starting with "Hello from Docker!" should appear, it might need to download the content first.

### Install Python 3.11

The current version of OpenStudyBuilder requires Python 3.11, to install it run:

```console
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11-dev
```

It may take a few minutes to complete the installation.

---

*[Back to top](#openstudybuilder-developer-setup)*

## Set Up Local Database

This section is for utilities and scripts for managing Neo4j MDR Database.

### Check python installation and install pipenv

This project uses [*pipenv*](https://github.com/pypa/pipenv) for dependencies
management, so you must install it on your system (version 2020.8.13 or later, ubuntu apt ships an old version so use *pip* to *install pipenv*)

Check python version and install pip:

```console
python3 --version
sudo apt-get -y install python3-pip 
```

Check *pip* version and install *pipenv*:

```console
pip --version
pip3 install pipenv
```

### Setup environment variables for the database

Create `.env` file **in the root of cloned repository** (`neo4j-mdr-db`) with the following content (adjust configuration if needed):

```sh
#
# Neo4j Database
#
NEO4J_MDR_HTTP_PORT=7474
NEO4J_MDR_BOLT_PORT=7687
NEO4J_MDR_HTTPS_PORT=443
NEO4J_MDR_HOST=localhost
NEO4J_MDR_AUTH_USER=neo4j
NEO4J_MDR_AUTH_PASSWORD=changeme1234
NEO4J_MDR_DATABASE=neo4j

NEO4J_MDR_CLEAR_DATABASE=false
NEO4J_MDR_BACKUP_DATABASE=false
```

### Create docker container

Create/re-create the `neo4j_local` container (after `cd neo4j-mdr-db`):

```console
./create_neo4j_local.sh
docker start neo4j_local
```

To start or stop the neo4j database use `docker start neo4j_local` and `docker stop neo4j_local`

**Note:**
On very first run of `create_neo4j_local.sh` at the beginning of command output you may see an error message `Error: No such container: neo4j_local` which is perfectly normal at very first run and can be ignored.

**Warning:**
You may notice from there that after starting the docker container for the neo4j database, some folder of the project are not anymore owned by your user.
Then you will have to change them back before working with the neo4j_local!

#### Verify container is running

In order to verify that the neo4j_local docker is running, you can run the following:

```console
docker ps
```

You will get a docker table of running containers. Sometimes it may take a few minutes before the container is fully up and running. To check the status of the startup of the docker container use `docker logs neo4j_local`.

### Initializing the database

#### Prepare python environment

Install all dependencies by running:

```console
pipenv install
```

#### Initiate neo4j database

This step assumes you have an empty database, for other options refer to the [README file](neo4j-mdr-db/README.md) for database setup.

Initiate the database using pipenv:

```console
pipenv run init_neo4j
```

**Note:** You may have to install the following package if you get the error: invalid command 'bdist_wheel':

```console
pip3 install wheel
```

#### Verify setup is correctly done

Verify that neo4j browser/database is accessible on `http://localhost:7474` in a browser (user: `neo4j`, password: `changeme1234`)

For further details about the database setup and configuration see the [README](neo4j-mdr-db/README.md) file in the `neo4j-mdr-db` subdirectory.

---

*[Back to top](#openstudybuilder-developer-setup)*

## Populate Database

Before Studybuilder can be used, the database must be populated.
The database should have been initialized as part of the build steps above.
If not, see [Initiate neo4j database](#initiate-neo4j-database).

As part of the Clinical MDR project, this repository takes care of the import of

- the controlled terminology (CT) from CDISC.

Later on, other imports like UNII, SNOMED, etc. can be added.

### Setup python virtual environment

Change directory to `mdr-standards-import` then run:

```console
pipenv install
```

### Setup environment variables for the database import

Create `.env` file (in the root of the repository) with the following content (adjust accordingly):

```.env
#
# Neo4j Database
#
NEO4J_MDR_BOLT_PORT=7687
NEO4J_MDR_HOST=localhost
NEO4J_MDR_AUTH_USER=neo4j
NEO4J_MDR_AUTH_PASSWORD=changeme1234
NEO4J_MDR_DATABASE=neo4j

NEO4J_CDISC_IMPORT_BOLT_PORT=7687
NEO4J_CDISC_IMPORT_HOST=localhost
NEO4J_CDISC_IMPORT_AUTH_USER=neo4j
NEO4J_CDISC_IMPORT_AUTH_PASSWORD=changeme1234
NEO4J_CDISC_IMPORT_DATABASE=cdisc-ct

#
# CDISC API
# API token is needed to download from CDISC 
#
CDISC_BASE_URL="https://library.cdisc.org/api"
CDISC_AUTH_TOKEN="<<Insert secret here>>"

#
# Download folder for the CDISC JSON package files
#
CDISC_DATA_DIR="cdisc_data/packages"
```

In the line with `CDISC_AUTH_TOKEN` replace the `<<Insert secret here>>` with a token from CDISC.

- Example: `CDISC_AUTH_TOKEN="abcdef0123456789abcdef0123456789"`

This can be acquired by following the [Access to CDISC Library API using API Key Authentication](https://wiki.cdisc.org/display/LIBSUPRT/Getting+Started%3A+Access+to+CDISC+Library+API+using+API+Key+Authentication) guide on the CDISC website.

**Note:** Bolt port number might need to be changed for different customized setup, but the above could do the trick for basic setup.

### CDISC CT Data

- Download CT Packages from the CDISC REST API to the `cdisc_data` folder referenced in the `.env` file above, by running:

```console
pipenv run python -m mdr_standards_import.cdisc_ct.dev_scripts.download_json_data_from_cdisc_api 'cdisc_data'
```

#### Import CDISC data

The following command will:

- trigger the import of CDISC files into a staging database

- trigger the import from the staging database into the MDR DB

```console
pipenv run bulk_import 'TEST' ''
```

### Verify setup is complete

Open Neo4j browser in your web browser at the address: <http://localhost:7474/>, log in with username and password stated in .env file in neo4j_database repository (this should be username: neo4j, password: changeme1234 unless configuration deters from this guide).

Switch to database cdisc-ct, run command:

```console
MATCH (p:Package)-[:CONTAINS]->(c:Codelist) WHERE c.effective_date=date("2015-12-18")
WITH p.name as name, count(c) AS count
RETURN name, count
```

The output should be similar to:

```console
name                count
"SDTM CT 2015-12-18"  480
"SEND CT 2015-12-18"  92
"ADAM CT 2015-12-18"  7
```

Switch to database neo4j, run command:

```cypher
MATCH (c:CTPackage)-[:CONTAINS_CODELIST]->(cc:CTPackageCodelist) WHERE c.effective_date=date("2015-12-18")
WITH c.name as name, count(cc) AS count
RETURN name, count
```

The output should be the same as before:

```cypher
name                  count
"SDTM CT 2015-12-18"  480
"SEND CT 2015-12-18"  92
"ADAM CT 2015-12-18"  7
```

For further details about the import and populating the database see the [README](mdr-standards-import/README.md) file in the `mdr-standards-import` subdirectory.

---

*[Back to top](#openstudybuilder-developer-setup)*

## Set Up API

Clinical MDR repository to store the API linked with the neo4j database

- Python with [*FastAPI*](https://fastapi.tiangolo.com/)

### Setup Development Environment

#### Setup python virtual environment for the API

- Make sure Python 3.11 and pipenv version 20232.3.20 or later are installed, as described [here](#install-python-311) and [here] (#check-python-installation-and-install-pipenv).
- Run:

```console
pipenv install --dev
```

#### Setup environment variables for the API

Create `.env` file (in the root of the repository) with the following content:

```console
NEO4J_DSN=bolt://neo4j:changeme1234@localhost:7687
OAUTH_ENABLED=false
ALLOW_ORIGIN_REGEX='.*'
```

#### Launch Development Server

Then, launch the development server by:

```console
pipenv run uvicorn clinical_mdr_api.main:app --reload
```

#### Verify the API is running

If the setup is correctly done, the API should be available at:

<http://localhost:8000/>

And the documentation at:

<http://localhost:8000/docs/>

For further details about the API see the [README](clinical-mdr-api/README.md) file in the `clinical-mdr-api` subdirectory.

---

*[Back to top](#openstudybuilder-developer-setup)*

## Import Data

This repository is used for utilities and scripts for initializing the Neo4j MDR Database with test data.

### Prerequisites

These migration scripts populate the database via the backend. Thus they require both the Neo4j database and the clinical-mdr-api to be running.

### Setup environment variables for data import

Create `.env` file (in the root of cloned repository). Use the `.env.import` file as a template and adjust as needed.

### Install dependencies

```console
pipenv install
```

### Run full import

Run the following command to start the full import.

```console
pipenv run import_all
```

**Note:** This will take some time to run (up to ~30 minutes).

For further details and options for configuring the data import see the [README](studybuilder-import/README.md) file in the `studybuilder-import` subdirectory.

---

*[Back to top](#openstudybuilder-developer-setup)*

## Set Up Frontend

### Prerequisites for the initialization of the frontend

#### Nodejs

Nodejs 12 or above is required to run this app.
If you are using a debian based system, you can install a newer version using packages provided by Node's team:

```console
curl -sL https://deb.nodesource.com/setup_16.x | sudo bash -
sudo apt-get install -y nodejs
```

**NOTE:** Some distributions of Ubuntu might not have curl installed, to fix this just run `sudo apt install curl`.

#### Yarn

A command called yarn is already installed on Ubuntu systems, but it is not the right one.
You must install the `yarnpkg` package and use it instead as follows:

```console
sudo apt remove cmdtest
sudo apt remove yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt-get update
sudo apt-get install yarn -y
```

### Project setup and initialization

To initialize the frontend run:

```console
yarn install
```

To compile run:

```console
yarn serve
```

This compiles and hot-reloads for development purposes.

For further details and options for configurations see the [README](studybuilder/README.md) file in the `studybuilder` subdirectory.

---

*[Back to top](#openstudybuilder-developer-setup)*

## Initialize OpenStudyBuilder after setup

Once the setup and configuration of all of the above has been completed, an OpenStudyBuilder environment should be up and running on you local machine.

Henceforth to initialize the full stack of your local OpenStudyBuilder after a shutdown or reboot of your Ubuntu environment, the following steps must be completed to start up OpenStudyBuilder:

### Start the database

Change directory to `neo4j-mdr-db` and then run:

```console
./create_neo4j_local.sh
```

Wait for the docker container to complete startup. To monitor the startup progress of the docker container run:

```console
docker logs neo4j_local --follow
```

Once the status shows started use `ctrl+c` to stop monitoring.

### Start the API

Change directory to `clinical_mdr_api` and then run:

```console
pipenv run uvicorn clinical_mdr_api.main:app --reload
```

### Start the frontend

In a new terminal window change directory to `studybuilder` and then run:

```console
yarn serve
```

After this i completed your local OpenStudyBuilder should now be up and running.

---

*[Back to top](#openstudybuilder-developer-setup)*


