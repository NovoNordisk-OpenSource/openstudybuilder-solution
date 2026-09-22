#!/bin/bash
set -e
if [ $# -lt 3 ]; then
	cat 1>&2 <<- EOF
		Error: not enough arguments.
		Example usage, connects to the container 'database' and dumps the database 'mdrdb'
		to a file named 'filename.dump'.
		$ ./export_db_dump.sh database mdrdb filename.dump
		The dump file is placed in '/db_backup' in the neo4j container.
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

docker exec "$1" sh -c "[ -d /tmp/dump ] || mkdir /tmp/dump"

echo "- Stop database"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "STOP DATABASE \`$DBNAME\`;"

echo "- Perform dump"
docker exec "$1" /var/lib/neo4j/bin/neo4j-admin database dump --to-path=/tmp/dump/ --overwrite-destination=true "$DBNAME"

echo "- Start database"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "START DATABASE \`$DBNAME\`;"

echo "- List existing databases"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "SHOW DATABASES;"

echo "- Move and rename dump file"
docker exec "$1" mv "/tmp/dump/$DBNAME.dump" "/db_backup/$3"