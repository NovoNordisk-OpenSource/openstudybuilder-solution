#!/bin/sh
# Nginx docker-entrypoint.d startup script to overwrite config.json of StudyBuilder
# with values from environment variables on container startup before starting Nginx.
# Must be put into folder /docker-entrypoint.d/ with .sh suffix and exec permission.

SB_UPDATE_CONFIG_AWK="${SB_UPDATE_CONFIG_AWK:-/opt/update-config.awk}"
SB_CONFIG_TEMPLATE="${SB_CONFIG_TEMPLATE:-/opt/config.json}"
SB_CONFIG_JSON="${SB_CONFIG_JSON:-/usr/share/nginx/html/config.json}"

# a bit of plumbing required to achieve some buffering if the template and target is the same file
cat "$SB_CONFIG_TEMPLATE" | "$SB_UPDATE_CONFIG_AWK" | tee "$SB_CONFIG_JSON" > /dev/null
