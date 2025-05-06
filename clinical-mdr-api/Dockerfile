# Set the build target (either "dev" or "prod") with a default of "dev"
ARG TARGET=dev
ARG PYTHON_IMAGE=python:3.13.0-slim

# Start with a slim default Python 3.13.0 base image, creating a shared base stage
FROM $PYTHON_IMAGE AS common-stage

# Update package lists, upgrade installed packages and install required system packages
RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get -y install curl git libpango-1.0-0 libpangoft2-1.0-0 \
    && pip install --upgrade pip pipenv wheel \
    && apt-get clean && rm -rf /var/lib/apt/lists && rm -rf ~/.cache

# Define a non-root user ID and name
ARG UID=1000
ARG USER=appuser
ENV USER=$USER
# Create the non-root user with the specified UID and home directory
RUN useradd --home-dir /home/"$USER" --user-group --create-home --uid "$UID" "$USER"

# Set the working directory to /app for the project files
WORKDIR /app

# Copy all files from the build context (current directory) into the container's /app directory
COPY ./ ./

# Begin the production stage
FROM common-stage AS prod-stage

# Remove test directories and byte-code compile application
RUN echo "Compile prod-stage" 1>&2 \
    rm -r clinical_mdr_api/tests consumer_api/tests \
    && python -m compileall -f -j 0 .

USER $USER
# Install only production dependencies with Pipenv
RUN echo "Building prod-stage" 1>&2 \
    && pipenv sync \
    && rm -rf ~/.cache

# Begin the development stage
FROM common-stage AS dev-stage
USER $USER
# Install all dependencies with Pipenv
RUN echo "Building dev-stage" 1>&2 && pipenv sync --dev && rm -rf ~/.cache

# Select either the production or development stage to build the final image based on TARGET
FROM ${TARGET}-stage AS final-stage

# Set environment variables for the Uvicorn server configuration and health check path
ENV UVICORN_APP="clinical_mdr_api.main:app" \
    UVICORN_HOST="0.0.0.0" \
    UVICORN_PORT="8000" \
    UVICORN_ROOT_PATH="/" \
    HEALTHCHECK_PATH="system/healthcheck"

# Build metadata for version tracking
ARG BUILD_NUMBER
ARG BUILD_BRANCH
ARG BUILD_COMMIT
ENV BUILD_NUMBER="$BUILD_NUMBER" \
    BUILD_BRANCH="$BUILD_BRANCH" \
    BUILD_COMMIT="$BUILD_COMMIT"

# Expose port 8000 for the Uvicorn application
EXPOSE $UVICORN_PORT

# Define a health check to verify that the application is responding at the health check endpoint
HEALTHCHECK --start-period=60s --timeout=3s --interval=10s --retries=2 CMD \
    curl --fail --silent --show-error --max-time 2 \
    "http://localhost:$UVICORN_PORT/$HEALTHCHECK_PATH" > /dev/null || exit 1

# Run the application using Uvicorn
CMD ["pipenv", "run", "uvicorn"]
