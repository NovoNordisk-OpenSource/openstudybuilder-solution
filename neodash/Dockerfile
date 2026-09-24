ARG NGINX_IMAGE=nginx:alpine
ARG NODE_IMAGE=node:lts-alpine
# build stage
FROM $NODE_IMAGE AS build-stage

RUN yarn global add typescript jest

# Run update
RUN apk add --no-cache git
# Pull and copy source code
RUN git clone https://github.com/neo4j-labs/neodash.git && cp -vr /neodash/. /.

COPY style.config.json public/
COPY style.css public/
COPY open_study_builder_logo.png public/
COPY ApplicationConfig.ts src/config/
COPY DashboardHeaderLogo.tsx src/dashboard/header/
COPY webpack.config.js /.

RUN yarn install

RUN yarn run build-minimal

# production stage
FROM $NGINX_IMAGE AS neodash
RUN apk upgrade

ENV NGINX_PORT=5005

COPY --from=build-stage /dist /usr/share/nginx/html
COPY --from=build-stage /conf/default.conf.template /etc/nginx/templates/
COPY --from=build-stage /scripts/config-entrypoint.sh /docker-entrypoint.d/config-entrypoint.sh
COPY --from=build-stage /scripts/message-entrypoint.sh /docker-entrypoint.d/message-entrypoint.sh

RUN chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    chown -R nginx:nginx /etc/nginx/templates && \
    chown -R nginx:nginx /docker-entrypoint.d/config-entrypoint.sh && \
    chmod +x /docker-entrypoint.d/config-entrypoint.sh  && \
    chmod +x /docker-entrypoint.d/message-entrypoint.sh
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid
RUN chown -R nginx:nginx /usr/share/nginx/html/

## Launch webserver as non-root user.
USER nginx

EXPOSE $NGINX_PORT

HEALTHCHECK cmd curl --fail "http://localhost:$NGINX_PORT" || exit 1
LABEL version="2.4.8"
