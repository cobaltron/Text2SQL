import psycopg2

conn = psycopg2.connect(
    dbname="mydb",
    user="postgres",
    password="test",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
print(cursor.fetchall())

import json

cursor.execute(""" SELECT
    c.table_name,
    c.column_name,
    c.data_type,
    pgd.description AS column_description,
    CASE
        WHEN kcu.column_name IS NOT NULL THEN TRUE
        ELSE FALSE
    END AS is_primary_key,
    fk.foreign_table_name,
    fk.foreign_column_name
FROM
    information_schema.columns c
LEFT JOIN
    pg_catalog.pg_statio_all_tables st
    ON c.table_schema = st.schemaname
    AND c.table_name = st.relname
LEFT JOIN
    pg_catalog.pg_description pgd
    ON pgd.objoid = st.relid
    AND pgd.objsubid = c.ordinal_position
LEFT JOIN
    information_schema.key_column_usage kcu
    ON c.table_name = kcu.table_name
    AND c.column_name = kcu.column_name
    AND c.table_schema = kcu.table_schema
LEFT JOIN
    information_schema.table_constraints tc
    ON kcu.constraint_name = tc.constraint_name
    AND tc.constraint_type = 'PRIMARY KEY'
LEFT JOIN (
    SELECT
        tc2.table_name, kcu2.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM
        information_schema.table_constraints AS tc2
        JOIN information_schema.key_column_usage AS kcu2
          ON tc2.constraint_name = kcu2.constraint_name
          AND tc2.table_schema = kcu2.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc2.constraint_name
          AND ccu.table_schema = tc2.table_schema
    WHERE tc2.constraint_type = 'FOREIGN KEY'
) fk
    ON c.table_name = fk.table_name 
    AND c.column_name = fk.column_name
WHERE
    c.table_schema = 'public'
ORDER BY
    c.table_name,
    c.ordinal_position;

 """)
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
schema = [dict(zip(columns, row)) for row in rows]

print(json.dumps(schema, indent=2))

with open('schema.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, ensure_ascii=False, indent=4)

