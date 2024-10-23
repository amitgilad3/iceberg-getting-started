# Iceberg Getting Started

Welcome to the [Iceberg](https://iceberg.apache.org/) getting started tutorial repository. 
This is a home for a set of preconfigured [Docker Compose](https://docs.docker.com/compose/) 
modules that are used to set up sandbox environments to learn and have fun with Apache Iceberg.
 
## Prerequisites

For beginners, I recommend using [Docker](https://www.docker.com/why-docker) to run your service [containers](https://www.docker.com/why-docker). I do not use the `version` tag for compose files and therefore don't provide support for [legacy compose versions](https://docs.docker.com/reference/compose-file/legacy-versions/). Make sure you have the correct Docker Compose version by having one of the following installed.


 * [Docker Desktop](https://docs.docker.com/desktop/) >= [4.1.0](https://docs.docker.com/desktop/release-notes/#410)(latest recommended)
 
 or

 * Docker Engine and Docker Compose [with compose version >= 1.27.0](https://docs.docker.com/reference/compose-file/legacy-versions/).


## Helpful Docker commands

### Start Services

`docker compose up -d`

### Remove Services

`docker compose up -d`

### Stop Services

`docker compose stop`

### Clean Services

[cleans images, containers, and networks](https://docs.docker.com/config/pruning/)

`docker system prune --all --force`

[cleans volumes](shttps://docs.docker.com/config/pruning/)

`docker volume prune --force`

### Show Service Images 

`docker images`

### Login to Container

`docker container exec -it <container_id> /bin/bash`

### Show Service Logs

`docker logs <container_id>`

### List Services

`docker container ls`

### List Service Process information

`docker compose ps`

See trademark and other [legal notices](https://www.apache.org/legal/).
