ARG PYTHON_IMAGE=python:3.13.0-slim

FROM $PYTHON_IMAGE

## Create non-root user (arg has to be exported to env for later build stages)
ARG UID=1000
ARG USER=appuser
ENV USER="$USER"
RUN useradd --home-dir /home/"$USER" --user-group --create-home --uid "$UID" "$USER"

## Commands below run relative to this working directory
ARG WORKDIR=/app
WORKDIR $WORKDIR

## Copy Pipfiles into the working directory
COPY ./Pipfile* ./

# Update package lists, upgrade installed packages and install required system packages
# and create virtual environment according to Pipfile.lock into user's home as root
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get -y install curl \
    && pip install --upgrade pip pipenv wheel \
    && apt-get clean && rm -rf /var/lib/apt/lists \
    && HOME=/home/"$USER" pipenv sync \
    # clean-up
    && rm -rf ~/.cache

## Copy the rest of the application owned by root
COPY ./ ./

## Run as non-root user
USER $USER
