# Chill Data Summit 2024 NY workshop

## Requirements

 * Docker + Compose
 * Curl
 * jq (optional) 


```
┌───────────┐                  ┌───────────┐               ┌───────┐
│           │                  │           │               │       │
│   Trino   │ ───────────────► │ Lakekeeper├─────────────► │       │
│    SQL    │                  │  Iceberg  │               │  DB   │
│           │                  │  Catalog  │               │       │
└─────┬─────┘                  └─────┬─────┘               │       │
      │                              │                     └───────┘
      │                              │                              
      │                              │                              
      │                        ┌─────▼─────┐                        
      │                        │           │                        
      └───────────────────────►│  Object   │                        
                               │  Storage  │                        
                               │           │                        
                               └───────────┘                        
```

Start services using Docker Compose:
 * Trino (SQL engine)
 * Lakekeeper (Iceberg Catalog)
 * Postgres (Catalog Concurrency Broker)
 * Minio (S3 Object Storage)


```
docker compose up -d && docker compose rm -f
```

Create an `iceberg` catalog using the management api from the Lakekeeper catalog.

```
curl -X POST -v \
     -H "Content-Type: application/json" \
     http://localhost:8181/management/v1/warehouse \
     -d \
'{
  "warehouse-name": "iceberg-warehouse",
  "project-id": "00000000-0000-0000-0000-000000000000",
  "storage-profile": {
    "type": "s3",
    "bucket": "databucks",
    "endpoint": "http://s3gateway:9000/",
    "region": "local-1",
    "path-style-access": true,
    "flavor": "minio",
    "sts-enabled": true,
    "sts_role_arn": null,
    "assume-role-arn": null
  },
  "storage-credential": {
    "type": "s3",
    "credential-type": "access-key",
    "aws-access-key-id": "storage",
    "aws-secret-access-key": "storage123"
  }
}'
```

Verify the warehouse is created.

```
curl -X GET -v \
     -H "Content-Type: application/json" \
     http://localhost:8181/management/v1/warehouse?project-id=00000000-0000-0000-0000-000000000000
```

Go take a moment to log into the [object storage UI](http://localhost:9000) and check the structure under the main bucket used. Then log into the Trino CLI.

```
docker container exec -it iceberg-getting-started-trino-coordinator-1 trino
```

Create hive` and `iceberg` catalogs using the Hive Metastore and Lakekeeper. We will use the Hive data to migrate data in the Hive format to Iceberg.

```
CREATE CATALOG hive USING hive
WITH (
  "hive.metastore.uri" = 'thrift://hive-metastore:9083',
  "hive.non-managed-table-writes-enabled" = 'true',
  "fs.native-s3.enabled" = 'true',
  "s3.region"= 'local-1',
  "s3.path-style-access" = 'true',
  "s3.endpoint" = 'http://s3gateway:9000',
  "s3.aws-access-key" = 'storage',
  "s3.aws-secret-key" = 'storage123'
);

CREATE CATALOG iceberg USING iceberg
WITH (
  "iceberg.catalog.type" = 'rest',
  "iceberg.rest-catalog.uri" = 'http://lakekeeper:8181/catalog',
  "iceberg.rest-catalog.warehouse" = 'iceberg-warehouse',
  "fs.native-s3.enabled" = 'true',
  "s3.region"= 'local-1',
  "s3.path-style-access" = 'true',
  "s3.endpoint" = 'http://s3gateway:9000',
  "s3.aws-access-key" = 'storage',
  "s3.aws-secret-key" = 'storage123'
);

````

Create schemas in both `hive` and `iceberg` catalogs.

```
CREATE SCHEMA hive.pokemon
WITH (location = 's3a://databucks/pokemon/');
```

> NOTE: we use `s3a` protocol when specifying the location since Trino utilizes the Hadoop `org.apache.hadoop.fs.s3a.S3AFileSystem` class. The Iceberg catalog will use the `s3` protocol, based on the Iceberg class used by Trino and Lakekeeper.

```
CREATE SCHEMA iceberg.pokemon
WITH (location = 's3://databucks/pokemon/');
```

Copy the csv pokemon pokedex data to s3.

```
docker run --rm -it \
  -e AWS_ACCESS_KEY_ID=storage \
  -e AWS_SECRET_ACCESS_KEY=storage123 \
  --network compose_network \
  -v $PWD/data/pokemon_pokedex.csv:/tmp/pokemon_pokedex.csv \
  amazon/aws-cli --region local-1 \
  --endpoint-url http://s3gateway:9000/ \
  s3 cp /tmp/pokemon_pokedex.csv s3://databucks/pokemon/pokedex_csv/ 
```

Create the pokedex table from the csv file in Hive.

```
CREATE TABLE hive.pokemon.pokedex_csv(
  "Number" VARCHAR,
  "Name" VARCHAR,
  "Type 1" VARCHAR,
  "Type 2" VARCHAR,
  "Abilities" VARCHAR,
  "HP" VARCHAR,
  "Att" VARCHAR,
  "Def" VARCHAR,
  "Spa" VARCHAR,
  "Spd" VARCHAR,
  "Spe" VARCHAR,
  "BST" VARCHAR,
  "Mean" VARCHAR,
  "Standard Deviation" VARCHAR,
  "Generation" VARCHAR,
  "Experience type" VARCHAR,
  "Experience to level 100" VARCHAR,
  "Final Evolution" VARCHAR,
  "Catch Rate" VARCHAR,
  "Legendary" VARCHAR,
  "Mega Evolution" VARCHAR,
  "Alolan Form" VARCHAR,
  "Galarian Form" VARCHAR,
  "Against Normal" VARCHAR,
  "Against Fire" VARCHAR,
  "Against Water" VARCHAR,
  "Against Electric" VARCHAR,
  "Against Grass" VARCHAR,
  "Against Ice" VARCHAR,
  "Against Fighting" VARCHAR,
  "Against Poison" VARCHAR,
  "Against Ground" VARCHAR,
  "Against Flying" VARCHAR,
  "Against Psychic" VARCHAR,
  "Against Bug" VARCHAR,
  "Against Rock" VARCHAR,
  "Against Ghost" VARCHAR,
  "Against Dragon" VARCHAR,
  "Against Dark" VARCHAR,
  "Against Steel" VARCHAR,
  "Against Fairy" VARCHAR,
  "Height" VARCHAR,
  "Weight" VARCHAR,
  "BMI" VARCHAR
)
WITH (
  format = 'CSV',
  external_location = 's3a://databucks/pokemon/pokedex_csv',
  skip_header_line_count=1
);
```

Now convert the CSV data to Parquet and proper Hive data types along with partitioning and clustering for read efficiency.

```
CREATE TABLE hive.pokemon.pokedex 
WITH (
  format = 'PARQUET',
  partitioned_by = ARRAY['type1'],
  bucketed_by = ARRAY['type2'],
  bucket_count = 2,
  external_location = 's3a://databucks/pokemon/pokedex'
) AS
SELECT
  CAST(number AS INTEGER) AS number,
  name,
  "Type 1" AS type1,
  "Type 2" AS type2,
  CAST(json_parse(replace(replace(Abilities, '''s', 's'), '''', '"')) AS ARRAY(VARCHAR)) AS abilities,
  CAST(hp AS INTEGER) AS hp,
  CAST(att AS INTEGER) AS att,
  CAST(def AS INTEGER) AS def,
  CAST(spa AS INTEGER) AS spa,
  CAST(spd AS INTEGER) AS spd,
  CAST(spe AS INTEGER) AS spe,
  CAST(bst AS INTEGER) AS bst,
  CAST(mean AS DOUBLE) AS mean,
  CAST("Standard Deviation" AS DOUBLE) AS std_dev,
  CAST(generation AS DOUBLE) AS generation,
  "Experience type" AS experience_type,
  CAST("Experience to level 100" AS BIGINT) AS experience_to_lvl_100,
  CAST(CAST("Final Evolution" AS DOUBLE) AS BOOLEAN) AS final_evolution,
  CAST("Catch Rate" AS INTEGER) AS catch_rate,
  CAST(CAST("Legendary" AS DOUBLE) AS BOOLEAN) AS legendary,
  CAST(CAST("Mega Evolution" AS DOUBLE) AS BOOLEAN) AS mega_evolution,
  CAST(CAST("Alolan Form" AS DOUBLE) AS BOOLEAN) AS alolan_form,
  CAST(CAST("Galarian Form" AS DOUBLE) AS BOOLEAN) AS galarian_form,
  CAST("Against Normal" AS DOUBLE) AS against_normal,
  CAST("Against Fire" AS DOUBLE) AS against_fire,
  CAST("Against Water" AS DOUBLE) AS against_water,
  CAST("Against Electric" AS DOUBLE) AS against_electric,
  CAST("Against Grass" AS DOUBLE) AS against_grass,
  CAST("Against Ice" AS DOUBLE) AS against_ice,
  CAST("Against Fighting" AS DOUBLE) AS against_fighting,
  CAST("Against Poison" AS DOUBLE) AS against_poison,
  CAST("Against Ground" AS DOUBLE) AS against_ground,
  CAST("Against Flying" AS DOUBLE) AS against_flying,
  CAST("Against Psychic" AS DOUBLE) AS against_psychic,
  CAST("Against Bug" AS DOUBLE) AS against_bug,
  CAST("Against Rock" AS DOUBLE) AS against_rock,
  CAST("Against Ghost" AS DOUBLE) AS against_ghost,
  CAST("Against Dragon" AS DOUBLE) AS against_dragon,
  CAST("Against Dark" AS DOUBLE) AS against_dark,
  CAST("Against Steel" AS DOUBLE) AS against_steel,
  CAST("Against Fairy" AS DOUBLE) AS against_fairy,
  CAST("Height" AS DOUBLE) AS height,
  CAST("Weight" AS DOUBLE) AS weight,
  CAST("BMI" AS DOUBLE) AS bmi
FROM hive.pokemon.pokedex_csv;
```
Let's just take a look at the data. 

```
SELECT * FROM hive.pokemon.pokedex LIMIT 50;
```

Since Hive and Iceberg share the same data storage location, they should both be able to access that data right?

```
SELECT * FROM iceberg.pokemon.pokedex LIMIT 50;
```

Let's migrate the `hive.pokemon.pokedex` table to `iceberg.pokemon.pokedex` catalog.

```
CALL iceberg.system.register_table(
  schema_name => 'pokemon', 
  table_name => 'pokedex', 
  table_location => 's3://databucks/pokemon/pokedex'
);
```

docker run --rm -it \
  -e AWS_ACCESS_KEY_ID=storage \
  -e AWS_SECRET_ACCESS_KEY=storage123 \
  --network compose_network \
  amazon/aws-cli s3api help
  
