#!/bin/bash
set -e
if [ $# -lt 2 ]; then
	cat 1>&2 <<- EOF
		Error: not enough arguments
		Example usage, connects to the container 'database' and exports the database 'mdrdb' to a file
		named as the database name with the current date and time appended, "mdrdb-yyyy-MM-ddTHH-mm-ss.backup"
		$ ./export_db_backup.sh database mdrdb
		The backup file is placed in '/db_backup' in the neo4j container.
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

echo "- List existing databases"
docker exec "$1" /var/lib/neo4j/bin/cypher-shell -d system -u "$NEO4J_MDR_AUTH_USER" -p "$NEO4J_MDR_AUTH_PASSWORD" -a "neo4j://localhost:$NEO4J_MDR_BOLT_PORT" "SHOW DATABASES;"

echo "- Perform backup"
docker exec "$1" /var/lib/neo4j/bin/neo4j-admin database backup --to-path=/db_backup/ --type=FULL "$DBNAME"