#!/bin/bash

# Cargar variables de entorno del .env
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# Formato de fecha y hora para la carpeta.
FECHA=$(date +"%Y%m%d_%H%M%S")
DIR_BACKUP="./copias/$FECHA"

mkdir -p "$DIR_BACKUP"

echo "Guardando copia de seguridad en $DIR_BACKUP..."

# 1. Copia de seguridad de PostgreSQL (pg_dump)
docker exec albergues-postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$DIR_BACKUP/postgres.sql"

# 2. Cop seg de MongoDB (mongodump)
docker exec albergues-mongodb mongodump --username "$MONGO_USER" --password "$MONGO_PASSWORD" --authenticationDatabase admin --db "$MONGO_DB" --out /tmp/dump
docker cp albergues-mongodb:/tmp/dump/"$MONGO_DB" "$DIR_BACKUP/mongo_dump"

echo "Backup completado en $DIR_BACKUP"