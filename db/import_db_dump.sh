#!/bin/bash
set -e
if [ $# -lt 3 ]; then
	cat 1>&2 <<- EOF
		Error: not enough arguments.
		Example usage, connects to the container 'database' and imports the data dump in 'filename.backup' into the database 'mdrdb'.
		$ ./import_db_backup.sh database mdrdb filename.backup
		This script assumes that the file 'filename.backup' exists in the directory
		'/db_backup' in the neo4j container.
		A local directory should be mounted at that path.
	EOF
	exit 2
fi

if [ -z "$NEO4J_MDR_AUTH_USER" ] || [ -z "$NEO4J_MDR_AUTH_PASSWORD" ] || [ -z "$NEO4J_MDR_BOLT_PORT" ]; then
	echo "Missing one or several environment variables for db connection, needed: NEO4J_MDR_AUTH_USER, NEO4J_MDR_AUTH_PASSWORD, NEO4J_MDR_BOLT_PORT"
	exit 2
fi

echo "- Checking for database alias"
DBNAME=$(docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "SHOW ALIASES FOR DATABASE YIELD * WHERE name=\"$2\" RETURN database" | tail -n 1 | tr -d '"')
if [ -z "$DBNAME" ]
then
	DBNAME="$2"
else
	echo "$2 is an alias for database $DBNAME"
fi

echo "- Checking that database $DBNAME exists"
DBLISTING=$(docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "SHOW DATABASE \`$DBNAME\` YIELD *")
if [ -z "$DBLISTING" ]
then
	echo "Error, database $DBNAME does not exist"
	exit 1
fi

echo "- Link to dump file"
docker exec "$1" sh -c "[ -d /tmp/load ] || mkdir /tmp/load"
docker exec "$1" ln -sf "/db_backup/$3" "/tmp/load/$DBNAME.dump"

echo "- Stop database"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "STOP DATABASE \`$DBNAME\`;"
echo "- Restore backup"
docker exec "$1" /var/lib/neo4j/bin/neo4j-admin database load --from-path="/tmp/load/" --overwrite-destination=true "$DBNAME"
echo "- Create database if not already existing"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "CREATE DATABASE \`$DBNAME\` IF NOT EXISTS;"
echo "- Start database"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "START DATABASE \`$DBNAME\`;"
echo "- List existing databases"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "SHOW DATABASES;"
