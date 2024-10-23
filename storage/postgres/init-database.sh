#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

    -- create hive admin and database
    CREATE USER hiveadmin;
    ALTER USER hiveadmin PASSWORD 'password';

    CREATE DATABASE metastore_db;
    GRANT ALL PRIVILEGES ON DATABASE metastore_db TO hiveadmin;

    -- create iceberg admin and database
    CREATE USER icebergadmin;
    ALTER USER icebergadmin PASSWORD 'password';

    CREATE DATABASE iceberg;
    GRANT ALL PRIVILEGES ON DATABASE iceberg TO icebergadmin;

EOSQL

