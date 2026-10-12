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

## Copy dependency metadata into the working directory
COPY ./pyproject.toml ./uv.lock ./

# Update package lists, upgrade installed packages and install required system packages
# and create virtual environment according to uv.lock as root
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get -y install curl \
    && pip install --upgrade pip uv wheel \
    && apt-get clean && rm -rf /var/lib/apt/lists \
    && HOME=/home/"$USER" uv sync --locked --no-dev \
    # clean-up
    && rm -rf ~/.cache

## Copy the rest of the application owned by root
COPY ./ ./

## Run as non-root user
USER $USER
