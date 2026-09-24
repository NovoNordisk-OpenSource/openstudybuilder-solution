ARG NGINX_IMAGE=nginx:alpine
ARG NODE_IMAGE=node:lts-alpine

## Build stage
FROM $NODE_IMAGE as build-stage

WORKDIR /app

## Install Node packages
COPY ./package*.json ./package-lock.json ./
RUN npm ci

## Build the app
COPY ./ .
RUN npm run build

## Select which nginx config template to ship as the default one.
##   gateway (default) - an upstream gateway does the path-based routing,
##                       so this container only serves the static SPA.
##   standalone        - this container reverse-proxies to the sibling
##                       api/doc/neodash services itself. The compose files
##                       pass this explicitly for local/full-stack runs.
## Fails the build on an unknown value rather than shipping a config-less image.
ARG NGINX_CONF=gateway
RUN test -r "/app/config/nginx/$NGINX_CONF.conf.template" \
    || { echo "Unknown NGINX_CONF '$NGINX_CONF' (expected: standalone, gateway)" >&2; exit 1; } \
    && cp "/app/config/nginx/$NGINX_CONF.conf.template" /app/config/nginx/default.conf.template \
    && rm -f /app/config/nginx/standalone.conf.template /app/config/nginx/gateway.conf.template

## If pipeline built a default.conf, then the template needs to be deleted to avoid overwriting.
RUN test ! -r /app/config/nginx/default.conf || rm -f /app/config/nginx/default.conf.template*

## Production stage
FROM $NGINX_IMAGE as prod-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY --from=build-stage /app/sbom.md /usr/share/nginx/html
COPY --from=build-stage /app/LICENSE.md /usr/share/nginx/html/license.md
COPY --from=build-stage /app/config/nginx/default.conf* /etc/nginx/conf.d
COPY --from=build-stage /app/config/nginx/default.conf.template* /etc/nginx/templates/
COPY config/nginx/sb-config.sh /docker-entrypoint.d/
COPY --from=build-stage /app/config/config.json /opt/
COPY scripts/update-config.awk /opt/

ARG PORT=5005
EXPOSE $PORT

## Version information
ARG BUILD_NUMBER
ARG BUILD_BRANCH
ARG BUILD_COMMIT
ENV BUILD_NUMBER="$BUILD_NUMBER" \
    BUILD_BRANCH="$BUILD_BRANCH" \
    BUILD_COMMIT="$BUILD_COMMIT"

## Environment variable defaults (for interpolating config.json)
ENV SB_UPDATE_CONFIG_AWK=/opt/update-config.awk \
    SB_CONFIG_TEMPLATE=/opt/config.json \
    SB_CONFIG_JSON=/usr/share/nginx/html/config.json \
    PORT=$PORT \
    API_HOST=api \
    API_PATH=/api/ \
    API_PORT=5003 \
    CONSUMER_API_HOST=consumerapi \
    CONSUMER_API_PATH=/consumer-api/ \
    CONSUMER_API_PORT=5008 \
    EXTENSIONS_API_HOST=extensionsapi \
    EXTENSIONS_API_PATH=/extensions-api/ \
    EXTENSIONS_API_PORT=5009 \
    DOC_HOST=documentation \
    DOC_PATH=/doc/ \
    DOC_PORT=5006 \
    NEODASH_HOST=neodash \
    NEODASH_PATH=/neodash/ \
    NEODASH_PORT=5007

## Runs healthcheck on the application root
## checks every `interval` seconds, fails if `timeout`,
## unhealthy status is reached if `retries` number of consecutive failures,
## but failures does not count within `start-period` seconds of start.
HEALTHCHECK --start-period=10s --timeout=2s --interval=10s --retries=2 CMD \
    curl --fail --silent --show-error --max-time 1 \
    "http://localhost:$PORT/" \
    > /dev/null || exit 1
