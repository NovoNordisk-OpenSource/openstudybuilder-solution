ARG NGINX_IMAGE=nginx:alpine

FROM $NGINX_IMAGE

## Upgrade the CA bundle at build time instead of trusting the base image to be current (CVE-2026-111943).
## Name both packages: ca-certificates alone rewrites the bundle file but leaves ca-certificates-bundle at the old version.
RUN apk upgrade --no-cache ca-certificates ca-certificates-bundle

COPY ./results/allure-report /public_html
COPY ./nginx/default.conf /etc/nginx/conf.d/
COPY ./nginx/redirect.html /public_html/

ARG PORT=5007
EXPOSE $PORT

## Runs healthcheck on the application root
## checks every `interval` seconds, fails if `timeout`,
## unhealthy status is reached if `retries` number of consecutive failures,
## but failures does not count within `start-period` seconds of start.
HEALTHCHECK --start-period=10s --timeout=2s --interval=10s --retries=2 CMD \
    curl --fail --silent --show-error --max-time 1 \
    "http://localhost:$PORT/" \
    > /dev/null || exit 1
