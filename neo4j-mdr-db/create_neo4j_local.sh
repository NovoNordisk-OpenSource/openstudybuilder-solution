#!/usr/bin/env bash
set -e
# Stop and remove neo4j_local if it already exists
if [ -n "$(docker ps -qa -f name=^/neo4j_local$)" ]; then
	echo "- Found container neo4j_local"
	if [ -n "$(docker ps -q -f name=^/neo4j_local$)" ]; then
		echo "- Stopping running container neo4j_local"
		docker stop neo4j_local
	fi
	echo "- Removing container neo4j_local"
	docker rm neo4j_local
fi

# Source env file
echo "- Reading environment variables from $(pwd)/.env"
source .env

# Look up working directory
WD="$(dirname "$(realpath "$0")")"
echo "- Workdir: $WD"

# Database storage directory
DATA="$WD/data"
# Plugins directory
PLUGINS="$WD/plugins"
# Import directory
IMPORT="$WD/import_files"
# Load scripts directory
SCRIPTS="$WD/load_scripts"
# Directory for database import and export
DB_BACKUP_DIR="$WD/db_backups"

# User and Group
USER_AND_GROUP="$(id -u):$(id -g)"

# Make sure direcories exist
echo "- Creating directories to mount"
[ -d "$DATA" ] || mkdir -p "$DATA"
[ -d "$PLUGINS" ] || mkdir -p "$PLUGINS"
[ -d "$IMPORT" ] || mkdir -p "$IMPORT"
[ -d "$SCRIPTS" ] || mkdir -p "$SCRIPTS"
[ -d "$DB_BACKUP_DIR" ] || mkdir -p "$DB_BACKUP_DIR"

echo "- Creating and starting container neo4j_local"
docker run -d \
    --user="$USER_AND_GROUP" \
    --name neo4j_local \
    --ulimit nofile=10000:10000 \
    -p"$NEO4J_MDR_HTTP_PORT":"$NEO4J_MDR_HTTP_PORT" -p"$NEO4J_MDR_HTTPS_PORT":"$NEO4J_MDR_HTTPS_PORT" -p"$NEO4J_MDR_BOLT_PORT":"$NEO4J_MDR_BOLT_PORT" \
    -v "$DATA":/data \
    -v "$PLUGINS":/plugins \
    -v "$IMPORT":/var/lib/neo4j/import \
    -v "$SCRIPTS":/var/lib/neo4j/load_scripts \
    -v "$DB_BACKUP_DIR":/db_backup \
    -v /etc/ssl/certs:/etc/ssl/certs \
    -e NEO4J_AUTH="$NEO4J_MDR_AUTH_USER"/"$NEO4J_MDR_AUTH_PASSWORD" \
    -e NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_apoc_export_file_enabled=true \
    -e NEO4J_apoc_trigger_enabled=true \
    -e NEO4J_server_memory_heap_max__size=4g \
    -e NEO4J_server_memory_heap_initial__size=4g \
    -e NEO4J_server_memory_pagecache_size=4g \
    -e NEO4J_dbms_memory_transaction_total_max=6g \
    -e NEO4J_dbms_max__databases=1000 \
    -e NEO4J_server_logs_gc_enabled=false \
    -e NEO4J_db_logs_query_enabled=OFF \
    -e NEO4J_server_bolt_advertised__address="$NEO4J_MDR_HOST":"$NEO4J_MDR_BOLT_PORT" \
    -e NEO4J_server_http_advertised__address="$NEO4J_MDR_HOST":"$NEO4J_MDR_HTTP_PORT" \
    -e NEO4J_server_https_advertised__address="$NEO4J_MDR_HOST":"$NEO4J_MDR_HTTPS_PORT" \
    -e NEO4J_server_bolt_listen__address=:"$NEO4J_MDR_BOLT_PORT" \
    -e NEO4J_server_http_listen__address=:"$NEO4J_MDR_HTTP_PORT" \
    -e NEO4J_server_https_listen__address=:"$NEO4J_MDR_HTTPS_PORT" \
    -e NEO4J_server_metrics_enabled=false \
    --env=NEO4J_PLUGINS='["apoc"]' \
    neo4j:5.19.0-enterprise
# If you see some 'Unable to find the transaction entry for the given change identifier' coming from
# capture_changes in data corrections please add the below configuration to the container setup above.
# This will extend the size of the stored logs so that capture_changes can find a transaction identifier.
#-e NEO4J_db_tx__log_rotation_retention__policy=keep_all \
#-e NEO4J_db_tx__log_rotation_size=256M \
#-e NEO4J_db_checkpoint_interval_time=15m \
#-e NEO4J_db_checkpoint_interval_tx=100000 \
