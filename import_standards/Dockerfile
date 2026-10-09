ARG PYTHON_IMAGE=python:3.14-slim

FROM $PYTHON_IMAGE

## Create non-root user (arg has to be exported to env for later build stages)
ARG UID=1000
ARG USER=appuser
ENV USER="$USER"
RUN useradd --home-dir /home/"$USER" --user-group --create-home --uid "$UID" "$USER"

## Commands below run relative to this working directory
ARG WORKDIR=/app
WORKDIR $WORKDIR

## Copy uv project files into the working directory
COPY ./pyproject.toml ./uv.lock ./

# Update package lists, upgrade installed packages and install required system packages
# and create virtual environment according to uv.lock into user's home as root
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get -y install curl \
    && pip install --upgrade pip wheel \
    && pip install uv \
    && apt-get clean && rm -rf /var/lib/apt/lists \
    && HOME=/home/"$USER" uv sync \
    # clean-up
    && rm -rf ~/.cache

## Copy the rest of the application owned by root
COPY ./ ./

## Run as non-root user
USER $USER
