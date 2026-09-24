ARG NGINX_IMAGE=nginx:alpine
ARG NODE_IMAGE=node:lts-alpine

## Build stage
FROM $NODE_IMAGE AS build-stage

WORKDIR /app

RUN apk add --no-cache git

## Install Node packages
COPY ./package.json ./package-lock.json ./
RUN npm ci

## Version information
ARG BUILD_NUMBER
ARG BUILD_BRANCH
ARG BUILD_COMMIT
ENV BUILD_NUMBER="$BUILD_NUMBER" \
    BUILD_BRANCH="$BUILD_BRANCH" \
    BUILD_COMMIT="$BUILD_COMMIT"

# Build the app
COPY ./ .
RUN npm run update-config /app/build.json
RUN npm run docs:build

## Production stage
FROM $NGINX_IMAGE AS production-stage

COPY --from=build-stage /app/docs/.vitepress/dist /usr/share/nginx/html
COPY --from=build-stage /app/build.json /usr/share/nginx/html
COPY --from=build-stage /app/sbom.md /usr/share/nginx/html
COPY --from=build-stage /app/LICENSE.md /usr/share/nginx/html/license.md
COPY ./nginx/default.conf /etc/nginx/conf.d/

ARG PORT=5006
ENV PORT=$PORT
EXPOSE $PORT

## Runs healthcheck on the application root
## checks every `interval` seconds, fails if `timeout`,
## unhealthy status is reached if `retries` number of consecutive failures,
## but failures does not count within `start-period` seconds of start.
HEALTHCHECK --start-period=10s --timeout=2s --interval=10s --retries=2 CMD \
    curl --fail --silent --show-error --max-time 1 \
    "http://localhost:$PORT/" \
    > /dev/null || exit 1
