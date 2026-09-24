# syntax=docker/dockerfile:1
# Requires BuildKit for `RUN --mount=type=secret` and named build contexts.
ARG NEO4J_IMAGE=neo4j:enterprise
ARG PYTHON_IMAGE=python:3.14-slim

# Optional external sponsor dataset.
#
# The build context is the repository root, so nothing outside it —
# such as /custom_sponsor_data — is reachable by a plain COPY.
# A *named build context* solves this: the caller passes
# `--build-context sponsordata=<path>` (buildx `build-contexts:` in the
# workflow) pointing anywhere on the caller's filesystem, and it is
# consumed below via `COPY --from=sponsordata`.
#
# When the caller supplies that flag, the named context replaces this
# stage entirely and the stage body is never evaluated. When the caller
# omits it, this empty `scratch` stage is used and the build falls back
# to the in-repo datafiles. This is why the stage must be `scratch` and
# empty rather than a copy of some default: it has to be detectably
# empty when unused.
FROM scratch AS sponsordata

# Optional external CDISC package set, by the same mechanism as
# `sponsordata` above: the caller passes
# `--build-context cdiscdata=<path>` pointing at a replacement for the
# CDISC packages directory (the one CDISC_DATA_DIR addresses, holding
# cdisc_ct/ and cdisc_data_models/). Empty `scratch` when unused, in
# which case the build keeps the in-repo package set.
FROM scratch AS cdiscdata

# --- Build stage ----
FROM $PYTHON_IMAGE AS build-stage

ARG NEO4J_DOWNLOAD_URL=https://dist.neo4j.org/neo4j-enterprise
ARG NEO4J_DOWNLOAD_FILEEXTENSION=unix.tar.gz

# Optional extra CA certificate for environments with TLS interception (e.g. Zscaler).
# Pass the path (relative to build context) via --build-arg EXTRA_CA_CERT=<file>.
# Dockerfile COPY cannot be made conditional, so when EXTRA_CA_CERT is unset we fall back to
# copying SECURITY.md as a harmless placeholder — it exists at the root of the repository
# (which is the build context). The following RUN skips the install and deletes
# the placeholder again.
#
# The placeholder must be a file that rarely changes, and specifically NOT this Dockerfile:
# this COPY sits ahead of the Neo4j download, the pipenv syncs and the import, so whatever it
# copies is a cache key for all of them. Pointing it at this file would mean every edit here
# invalidates the entire build.
ARG EXTRA_CA_CERT
COPY ${EXTRA_CA_CERT:-SECURITY.md} /tmp/extra-ca-cert
RUN if [ -n "${EXTRA_CA_CERT}" ]; then \
        cp /tmp/extra-ca-cert /usr/local/share/ca-certificates/extra-ca.crt \
        && update-ca-certificates ; \
    fi \
    && rm -f /tmp/extra-ca-cert
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

## Install required system packages, for clinical-mdr-api as well
RUN apt-get update \
    && apt-get -y install \
    ca-certificates-java \
    gpg \
    git \
    curl \
    wget \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libffi-dev \
    zlib1g-dev \
    libxml2-dev \
    libxslt-dev \
    build-essential \
    jq \
    gcc \
    net-tools \
    && pip install --upgrade pip pipenv wheel \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor | tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null \
    && echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list \
    && apt-get update \
    && apt-get -y install temurin-25-jdk \
    && apt-get clean && rm -rf /var/lib/apt/lists && rm -rf ~/.cache

WORKDIR /neo4j

ARG NEO4J_server_memory_heap_initial__size="3G"
ARG NEO4J_server_memory_heap_max__size="3G"
ARG NEO4J_server_memory_pagecache_size="2G"

ARG reportDate="2024-01-05 14:54:32 +0100"

# CDISC_DATA_DIR is resolved relative to /build/import_standards (the WORKDIR when
# cdisc_staging.py runs). In this repository the package data lives under
# src/container_booting/packages/{cdisc_ct,cdisc_data_models}, so the parent
# directory is src/container_booting. CDISC_JSON_DIR / CDISC_DATA_DIR below append
# /packages/cdisc_ct etc. to this value.
ARG CDISC_DATA_DIR="src/container_booting"
ARG SPONSOR_DATASET_DIR="import_sponsor_data/datafiles"

# NEO4J_MDR_AUTH_PASSWORD is intentionally NOT declared as an ARG — it is supplied
# as a BuildKit secret to the single RUN step that needs it, so it never lands in
# image layers, history, or build cache.

# Environment variables for database
ENV NEO4J_MDR_BOLT_PORT=7687 \
    NEO4J_MDR_HTTP_PORT=7474 \
    NEO4J_MDR_HTTPS_PORT=7473 \
    NEO4J_MDR_HOST=localhost \
    NEO4J_MDR_AUTH_USER=neo4j \
    NEO4J_MDR_DATABASE=mdrdb \
    NEO4J_MDR_DATABASE_DBNAME=mdrdockerdb \
    NEO4J_CDISC_IMPORT_BOLT_PORT=7687 \
    NEO4J_CDISC_IMPORT_HOST=localhost \
    NEO4J_CDISC_IMPORT_AUTH_USER=neo4j \
    NEO4J_CDISC_IMPORT_DATABASE=cdisc-import \
    SPONSOR_DATASET_DIR=$SPONSOR_DATASET_DIR \
    CDISC_DATA_DIR=$CDISC_DATA_DIR/packages \
    CDISC_JSON_DIR=$CDISC_DATA_DIR/packages/cdisc_ct \
    CDISC_XLS_DIR=CDISC_xls \
    NEO4J_ACCEPT_LICENSE_AGREEMENT=yes

# Install Neo4j from tarball
RUN export NEO4J_VERSION=$(curl "https://dist.neo4j.org/versions/v2/neo4j-versions.json" | jq -r '."dist-tags" .latest') \
    && curl --fail --location --output neo4j.tar.gz --silent --show-error "$NEO4J_DOWNLOAD_URL-$NEO4J_VERSION-$NEO4J_DOWNLOAD_FILEEXTENSION" \
    && tar --extract --gzip --file neo4j.tar.gz --strip-components=1 \
    && rm neo4j.tar.gz \
    && mv labs/apoc*core.jar plugins/ \
    && neo4j_conf=/neo4j/conf/neo4j.conf \
    && echo "server.memory.heap.initial_size=$NEO4J_server_memory_heap_initial__size" >> $neo4j_conf \
    && echo "server.memory.heap.max_size=$NEO4J_server_memory_heap_max__size" >> $neo4j_conf \
    && echo "server.memory.pagecache.size=$NEO4J_server_memory_pagecache_size" >> $neo4j_conf \
    && echo 'dbms.security.procedures.unrestricted=algo.*,apoc.*' >> $neo4j_conf

WORKDIR /build

# Copy Pipfiles
COPY ./db/Pipfile* db/
COPY ./import_standards/Pipfile* import_standards/

# Install dependencies for db and import_standards
RUN cd db && pipenv sync \
    && cd ../import_standards && pipenv sync \
    && rm -rf ~/.cache
    
# Copy program files for db and import_standards
COPY ./db db
COPY ./import_standards import_standards

# Stage the external CDISC package set from the `cdiscdata` named
# context, then replace the in-repo one if anything arrived. Same
# staging-then-swap shape as the sponsor dataset below, and for the same
# reason: `COPY ./import_standards import_standards` above has already
# populated the packages directory, so a merge would leave the in-repo
# packages behind. Empty when no named context was supplied.
#
# The target is ${CDISC_DATA_DIR} — the directory holding cdisc_ct/ and
# cdisc_data_models/ — so a replacement set must be rooted at that same
# level. CDISC_XLS_DIR and cdisc_data/extra/ are addressed separately
# and are NOT touched here.
COPY --from=cdiscdata / /cdisc_incoming/
RUN if [ -n "$(find /cdisc_incoming -mindepth 1 -print -quit 2>/dev/null)" ]; then \
        echo "Replacing CDISC packages with external set ($(find /cdisc_incoming -type f | wc -l) files)" ; \
        rm -rf "import_standards/${CDISC_DATA_DIR}" ; \
        mkdir -p "import_standards/${CDISC_DATA_DIR}" ; \
        cp -a /cdisc_incoming/. "import_standards/${CDISC_DATA_DIR}/" ; \
    else \
        echo "No external CDISC set supplied; keeping in-repo packages ($(find "import_standards/${CDISC_DATA_DIR}" -type f | wc -l) files)" ; \
    fi \
    && rm -rf /cdisc_incoming

# Copy environment file for import_standards
COPY ./import_sponsor_data/.env.import import_standards/.env

# Install dependencies for import_sponsor_data and api
COPY ./import_sponsor_data/Pipfile* import_sponsor_data/
COPY ./api/Pipfile* api/
RUN cd import_sponsor_data && pipenv sync \
    && cd ../api && pipenv sync \
    && rm -rf ~/.cache

# Copy program files for import_sponsor_data and api
COPY ./import_sponsor_data import_sponsor_data
COPY ./api api

# Copy special migration-data if required for import
COPY ./${SPONSOR_DATASET_DIR} import_sponsor_data/datafiles

# Stage the external sponsor dataset from the `sponsordata` named context
# (see the stage definition at the top of this file). It lands in a
# scratch location first so the RUN below can tell "no named context was
# supplied" (empty directory) from "an external set arrived", and report
# the file count either way. When no named context was supplied the
# stage is empty and this produces an empty directory.
COPY --from=sponsordata / /sponsor_incoming/

# Overlay the external sponsor dataset on top of the in-repo one.
#
# This is a merge, not a replacement: datafiles/ is left in place and
# the incoming files are copied over it. Files present in both are
# overwritten by the external set; files only the in-repo set has
# survive untouched.
#
# That matters because the importers read ~124 distinct paths out of
# datafiles/ (see import_sponsor_data/.env.import), while an external
# set is typically a partial override of a handful of them. Overlaying
# means a partial set is fine — every path the external set omits still
# resolves to the in-repo file.
#
# An empty /sponsor_incoming means no named context was passed, so the
# in-repo datafiles are kept as-is.
RUN if [ -n "$(find /sponsor_incoming -mindepth 1 -print -quit 2>/dev/null)" ]; then \
        echo "Overlaying external sponsor dataset onto in-repo datafiles ($(find /sponsor_incoming -type f | wc -l) files incoming)" ; \
        mkdir -p import_sponsor_data/datafiles ; \
        cp -a /sponsor_incoming/. import_sponsor_data/datafiles/ ; \
        echo "Sponsor datafiles after overlay: $(find import_sponsor_data/datafiles -type f | wc -l) files" ; \
    else \
        echo "No external sponsor dataset supplied; keeping in-repo datafiles ($(find import_sponsor_data/datafiles -type f | wc -l) files)" ; \
    fi \
    && rm -rf /sponsor_incoming

# Environment variables for api
# NEO4J_DSN is intentionally NOT set here — it embeds the password and would be
# captured in image config. It is exported per-RUN from the BuildKit secret instead.
ENV NEO4J_DATABASE=mdrdb \
    OAUTH_ENABLED=false \
    ALLOW_ORIGIN_REGEX=".*" \
    TRACING_ENABLED="false" \
    LOG_LEVEL="WARN"

# Set up environments for import_sponsor_data
COPY ./import_sponsor_data/.env.import import_sponsor_data/.env

# Start Neo4j then run init and import.
# The password is mounted as a BuildKit secret at /run/secrets/neo4j_mdr_auth_password
# and only lives in shell variables for the duration of this RUN — it never lands in
# image layers, history, or the build cache. NEO4J_USERNAME/NEO4J_PASSWORD are exported
# so cypher-shell picks them up without the password appearing on its command line
# (which would otherwise be echoed by `set -x` further down).
RUN --mount=type=secret,id=neo4j_mdr_auth_password \
    if [ ! -s /run/secrets/neo4j_mdr_auth_password ]; then \
        echo "ERROR: neo4j_mdr_auth_password secret is missing or empty. Pass it with --secret id=neo4j_mdr_auth_password,env=NEO4J_MDR_AUTH_PASSWORD (or src=<file>)." >&2 ; \
        exit 1 ; \
    fi \
    && export NEO4J_MDR_AUTH_PASSWORD="$(cat /run/secrets/neo4j_mdr_auth_password)" \
    && export NEO4J_CDISC_IMPORT_AUTH_PASSWORD="$NEO4J_MDR_AUTH_PASSWORD" \
    && export NEO4J_DSN="bolt://${NEO4J_MDR_AUTH_USER}:${NEO4J_MDR_AUTH_PASSWORD}@localhost:7687/mdrdb" \
    && export NEO4J_USERNAME="$NEO4J_MDR_AUTH_USER" \
    && export NEO4J_PASSWORD="$NEO4J_MDR_AUTH_PASSWORD" \
    && /neo4j/bin/neo4j-admin dbms set-initial-password "$NEO4J_MDR_AUTH_PASSWORD" \
    # start neo4j server — background only `neo4j console` itself. In POSIX sh,
    # `A && B & C` puts the whole preceding `A && B` chain into a subshell that
    # runs in the background, which would drop the exported NEO4J_* vars from
    # the parent shell before `pipenv run init_neo4j` runs. Using
    # `{ /neo4j/bin/neo4j console & neo4j_pid=$!; }` keeps the `&&` chain in
    # the parent shell and only backgrounds the neo4j process itself.
    && { /neo4j/bin/neo4j console & neo4j_pid=$!; } \
    && trap "kill -TERM $neo4j_pid" EXIT \
    # wait until 7474/tcp is open
    && while ! netstat -tna | grep 'LISTEN\>' | grep -q '7474\>'; do sleep 2; done \
    && set -x \
    # init database
    && cd db && pipenv run init_neo4j \
    # import neodash reports
    && mkdir -p neodash_reports/import && FILES="neodash/neodash_reports/*.json" \
    && for f in $FILES; do echo "Processing $f file..."; filename=`basename $f` ; \
    title=`jq -r .title $f`; uuid=`jq -r .uuid $f`; version=`jq -r .version $f`; echo "$title" "$uuid" "$version"; \
    jq -n --slurpfile content $f --arg title "$title" --arg uuid "$uuid" --arg version "$version" --arg date "$reportDate" '. += {"content": $content, "title": $title, "uuid": $uuid, "version": $version, "date": $date, "user": "OpenStudyBuilder@gmail.com"}' > neodash_reports/import/$filename; \
    done \
    && python -m pipenv run import_reports neodash_reports/import \
    && cd ../import_standards \
    && pipenv run import_cdisc_ct_into_cdisc_db \
    && pipenv run import_ct_from_cdisc_db_into_mdr \
    && pipenv run bulk_import_data_models TESTUSER "" \
    # update CT package stats
    && cd ../db && pipenv run update_ct_stats \
    # start API
    && { cd ../api && pipenv run uvicorn --host 127.0.0.1 --port 8000 --log-level info clinical_mdr_api.main:app & api_pid=$! ;} \
    # wait until 8000/tcp is open
    && while ! netstat -tna | grep 'LISTEN\>' | grep -q '8000\>'; do sleep 2; done \
    && set -x \
    # imports
    && sleep 10 && cd ../import_sponsor_data && pipenv run import_all && pipenv run import_dummydata && pipenv run import_feature_flags \
    # stop the api
    && sleep 10 && kill -INT $api_pid && wait $api_pid \
    # get database name
    # cypher-shell reads NEO4J_USERNAME/NEO4J_PASSWORD from the env exported above, so the password
    # is not passed via -p (which would be expanded into build logs by the active `set -x`).
    && dbName=$(/neo4j/bin/cypher-shell -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "SHOW ALIASES FOR DATABASE YIELD * WHERE name=\"$NEO4J_MDR_DATABASE\" RETURN database;" | tail -n 1 | tr -d '"') && echo $dbName \
    # run backup of database
    && mkdir -p /neo4j/data/backup/ \
    && sleep 10 && /neo4j/bin/neo4j-admin database backup --to-path=/neo4j/data/backup/ --type=FULL $dbName --compress=false \
    && sleep 10 && find /neo4j/data/backup/ -type f -name '*.backup' -exec sh -c 'x="{}"; mv "$x" "/neo4j/data/backup/mdrdockerdb.backup"' \; \
    # stop neo4j server gently, but first wait a little for recent transactions to finish
    && sleep 10 && /neo4j/bin/neo4j stop && sleep 10 \
    # run consistency-check on mdrdb
    && sleep 10 && /neo4j/bin/neo4j-admin database check $dbName \
    && trap EXIT
    
# --- Prod stage ----
# Copy database directory from build-stage to the official neo4j docker image
FROM $NEO4J_IMAGE AS production-stage

ARG UID=1000
ARG USER=neo4j
ARG GROUP=neo4j

# See build-stage for the full explanation of the SECURITY.md fallback.
# ARGs don't cross stages, so re-declare here.
ARG EXTRA_CA_CERT
COPY ${EXTRA_CA_CERT:-SECURITY.md} /tmp/extra-ca-cert
RUN if [ -n "${EXTRA_CA_CERT}" ]; then \
        cp /tmp/extra-ca-cert /usr/local/share/ca-certificates/extra-ca.crt \
        && update-ca-certificates ; \
    fi \
    && rm -f /tmp/extra-ca-cert

# Match id of neo4j user with the current user on the host for correct premissions of db dumps mounted folder
ARG UID=1000
RUN [ "x$UID" = "x1000" ] || { \
    echo "Changing uid & gid of neo4j user to $UID" \
    && usermod --uid "$UID" "neo4j" \
    && groupmod --gid "$UID" "neo4j" \
    ;}

# Install APOC plugin
RUN export NEO4J_VERSION=$(wget "https://dist.neo4j.org/versions/v2/neo4j-versions.json"  -qO - | jq -r '."dist-tags" .latest') \
    && wget --quiet --timeout 60 --tries 2 --output-document /var/lib/neo4j/plugins/apoc.jar \
    https://github.com/neo4j/apoc/releases/download/$NEO4J_VERSION/apoc-$NEO4J_VERSION-core.jar

# Copy database backup from build stage
COPY --from=build-stage --chown=$USER:$GROUP /neo4j/data/backup /data/backup

# Set up default environment variables
# NEO4J_AUTH is intentionally NOT set here — it must be supplied at runtime
# (e.g. via compose env interpolation or NEO4J_AUTH_FILE pointing at a Docker secret)
# and must match the password baked into the seeded backup at build time.
ENV NEO4J_apoc_trigger_enabled="true" \
    NEO4J_apoc_import_file_enabled="true" \
    NEO4J_apoc_export_file_enabled="true" \
    NEO4J_dbms_security_procedures_unrestricted="apoc.*" \
    NEO4J_dbms_databases_seed__from__uri__providers="FileSeedProvider" \
    NEO4J_apoc_initializer_system_1="CREATE DATABASE mdrdb OPTIONS {existingData: 'use', seedURI:'file:///data/backup/mdrdockerdb.backup'} WAIT 60 SECONDS"

# Volume attachment point: if an empty volume is mounted, it gets populated with the pre-built database from the image
VOLUME /data

# run as non root user
USER $USER

HEALTHCHECK --start-period=60s --timeout=3s --interval=10s --retries=3 \
    CMD wget --quiet --spider --timeout 2 --tries 1 "http://localhost:7474/" || exit 1

