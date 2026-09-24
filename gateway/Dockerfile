ARG NGINX_IMAGE=nginx:alpine
FROM $NGINX_IMAGE

COPY ./default.conf /etc/nginx/conf.d/default.conf

ARG BUILD_NUMBER
ARG BUILD_BRANCH
ARG BUILD_COMMIT
ENV BUILD_NUMBER="$BUILD_NUMBER" \
    BUILD_BRANCH="$BUILD_BRANCH" \
    BUILD_COMMIT="$BUILD_COMMIT"

EXPOSE 80

HEALTHCHECK --start-period=10s --timeout=2s --interval=10s --retries=2 CMD \
    wget --quiet --spider --timeout=1 "http://localhost:80/" || exit 1
