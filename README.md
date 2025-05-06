[[_TOC_]]


# Status quo of the OpenStudyBuilder

The OpenStudyBuilder solution introduces a new approach for working with studies that once fully implemented will drive end-to-end consistency and more efficient processes - all the way from protocol development and CRF design - to creation of datasets, analysis, reporting, submission to health authorities and public disclosure of study information.

OpenStudyBuilder is the first MVP of the solution covering the foundational capabilities for the front-end application, the data standards and study definition repository as well as the initial integrations.

OpenStudyBuilder is the open source version of the internal StudyBuilder solution at Novo Nordisk. Not all titles or logos in the application are yet changed to be 'OpenStudyBuilder' - when the term 'StudyBuilder' is used, it is therefore a synonym for 'OpenStudyBuilder'. This will be changed in coming updates.


# Introduction

StudyBuilder consists of a few main components, that are all included as subdirectories in this repository.

- neo4j-mdr-db: Configuration files and initialization scripts for the Neo4j database.
- mdr-standards-import: Scripts for populating the database with clinical standards.
- clinical-mdr-api: The Python/FastAPI backend.
- studybuilder-import: Python scripts for populating the database with sponsor standards and codelists.
- studybuilder: The Vue.js frontend.
- documentation-portal: Project documentation.

Each directory contains a more detailed ReadMe for that component.


# System Requirements

A Docker environment with at least 6GB of memory allocated is required.

The solution is tested on Ubuntu and Windows (WSL 2).
For alternative platforms, please refer to [Platform architecture notes](platform-architecture-notes).

The Docker environment can be either Docker Desktop or Docker Engine 
(community version), with Compose V2 integrated as a CLI plugin. 

OpenStudyBuilder has been tested on the following Docker environments:

- Windows 11 (WSL 2)
- Ubuntu 20.04 Focal - Docker Engine community version 23.0.1 

To see versions of the installed Docker engine, run: `docker version`

To check if the Docker Compose V2 is also included, run: `docker compose version`

Windows installation link: [Windows installation](https://docs.docker.com/desktop/install/windows-install/)

Ubuntu installation link: [Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/)

To test your local docker installation run the following command
in a non administrator or root shell: `docker run hello-world`

If this is not working see this link for Ubuntu rootless configuration:
[Docker Rootless](https://docs.docker.com/engine/security/rootless/)

For low-end systems, the database container may fail for low-on-memory 
reasons. In that case, update the following values in `compose.yaml`
```
        NEO4J_server_memory_heap_initial__size: "1G"
        NEO4J_server_memory_heap_max__size: "1G"
        NEO4J_server_memory_pagecache_size: "500M"
```

Mind that this will choke the performance of the Neo4j database,
which leads to increased building time of the database component,
up to a few hours.

On Windows installations the WSL engine can take up all system resources.
It is recommended to configure limits. Create a `.wslconfig` file in the user directory, typically `C:\Users\username\`.
Put the following content in the `.wslconfig` file, and change `memory` to a suitable value for the given system. Half the physical RAM is a good starting point.
```
[wsl2]
processors=2
memory=6GB
```
See [Advanced settings configuration in WSL](https://docs.microsoft.com/en-us/windows/wsl/wsl-config)
for all available options.

Also on Windows installations where GIT for Windows is used to clone the repository, errors with correct line endings in the WSL engine can occure.  

to avoid this use either of these commands before the cloning of repository.

`git config --global core.autocrlf input`

`git config --global core.autocrlf false`

See [Configuring Git to handle line endings](https://docs.github.com/en/get-started/getting-started-with-git/configuring-git-to-handle-line-endings?platform=windows) and [Resolving Git line ending issues in Docker containers](https://gist.github.com/jonlabelle/70a87e6871a1138ac3031f5e8e39f294)
for more information.

## Known Issues with Dockerfiles on ARM64 Architecture

There have been reports of issues when running the Dockerfiles on ARM64 architecture. Recent updates have resolved these problems on several ARM64 machines. If you encounter any other issues, please refer to the following link for more information and to report the inconvenience: [GitLab Issues](https://gitlab.com/Novo-Nordisk/nn-public/openstudybuilder/OpenStudyBuilder-Solution/-/issues).


# Using the preview environment

Your folder structure should look like this:
```
─ OpenStudyBuilder-Solution
  ├─ clinical-mdr-api
  ├─ studybuilder-import
  ├─ documentationfiles
  ├─ documentation-portal
  ├─ frontendfiles
  ├─ mdr-standards-import
  ├─ neo4j-mdr-db
  └─ studybuilder
```

The Docker Compose configuration is `compose.yaml` for the preview 
environment and building containers in pipelines.

The following services are part of this Docker Compose environment.

- _database_ (A Neo4j graph database container including initial data)
- _api_ (A FastAPI container hosting the clinical-mdr-api backend application)
- _frontend_ (A Nginx container hosting Vue.js StudyBuilder UI application)
- _documentation_ (A Nginx container hosting Vue.js Study Builder documentation portal)


## Building the Docker images

The Docker container images has to be built before the first use,
and rebuilt on each subsequent release:

```shell
docker compose build
```

Building the Docker images may take 30 minutes or more to complete, 
especially for the database image.


## Starting the services

To start up the services for a local evaluation environment, use:

```shell
docker compose up
```

If you add the `-d` option to the command, it will bring up the services to 
run in the background, detached from the terminal.

To validate that the environment is running, inspect the output of this command:

```shell
docker compose ps
```

The output should look like this:

```
NAME                          IMAGE                       COMMAND                  SERVICE             CREATED            STATUS                   PORTS
OpenStudyBuilder-Solution-api-1             build-tools-api             "/bin/sh -c 'pipenv …"   api                 4 minutes ago      Up 3 minutes (healthy)   5003/tcp
OpenStudyBuilder-Solution-database-1        build-tools-database        "tini -g -- /startup…"   database            4 minutes ago      Up 4 minutes (healthy)   7473/tcp, 127.0.0.1:5001->7474/tcp, 127.0.0.1:5002->7687/tcp
OpenStudyBuilder-Solution-documentation-1   build-tools-documentation   "/docker-entrypoint.…"   documentation       4 minutes ago      Up 4 minutes (healthy)   80/tcp, 5006/tcp
OpenStudyBuilder-Solution-frontend-1        build-tools-frontend        "/docker-entrypoint.…"   frontend            4 minutes ago      Up 3 minutes (healthy)   80/tcp, 127.0.0.1:5005->5005/tcp
```


## Accessing the application

- StudyBuilder main application: <http://localhost:5005/>

- StudyBuilder documentation: <http://localhost:5005/doc/>

  It can also be accessed from main web application from the ? sign in top right corner.

- StudyBuilder API (backend application): <http://localhost:5005/api/docs>

- Neo4j database web client: <http://localhost:5001/browser/>

  The default username is `neo4j` and the default password is `changeme1234`


## Stopping the services

This command will stop the docker containers, but keep the contents of the 
database for the next start.

```shell
docker compose down --remove-orphans
```


## Updating to a new release

When checking out a new release, the Docker images has to be rebuilt.
Usually the database schema gets changed between releases, so
**the old database has to be destroyed**.
A new database will be initialized when starting the  _database_ service
from the recently rebuilt Docker image.
(The OpenStudyBuilder release does not come with a database migration tool.)

```shell
docker compose build --no-cache  # rebuilds the docker images
docker compose down --remove-orphans --volumes # DESTROYS THE DATABASE volume 
docker compose up -d  # the database service re-creates the database volume on the first start 
```

## Cleaning up the Docker environment

To clean up the entire Docker environment use the following commands:

**Will delete volumes and cache NOT restricted for the OpenStudyBuilder components.**

```shell
docker compose down --remove-orphans --volumes
docker rmi $(docker images --filter=reference="*_database" -q) -f
docker rmi $(docker images --filter=reference="*_api" -q) -f
docker rmi $(docker images --filter=reference="*_ui" -q) -f
docker rmi $(docker images --filter=reference="*_docs" -q) -f
docker rmi $(docker images --filter=reference="*_sonarqube" -q) -f
docker volume prune # (Will delete all volumes not used, only needed if -v was not used on docker-compose down command)
docker builder prune --all # (Will clean all docker cache files)
```


