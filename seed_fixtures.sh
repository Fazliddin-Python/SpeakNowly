#!/usr/bin/env bash
set -e

# Connection string (can be in .env or directly here)
DB_URL="postgresql://backender:Fazliddin.000@localhost:5432/speaknowly"

for file in fixtures/*.json; do
  table=$(basename "$file" .json)
  echo "→ Seeding (upsert) data into table: $table"

  # For each object in the JSON array
  jq -c '.[]' "$file" | while read -r row; do
    # Collect column names into an array
    IFS=',' read -r -a cols_array < <(echo "$row" | jq -r 'keys_unsorted | @csv' | sed 's/"//g')
    # Collect values into a CSV string, escaping quotes and converting null to NULL
    vals=$(echo "$row" | jq -r '[.[]] |
      map(
        if type=="string" then
          ("'"'"'" + gsub("'"'"'" ; "''") + "'"'"'")
        elif . == null then
          "NULL"
        else
          tostring
        end
      ) | @csv')
    vals=${vals//\"/}

    # Form the list of columns and VALUES(...)
    cols=$(IFS=, ; echo "${cols_array[*]}")
    values=$(echo "$vals")

    # Generate UPDATE part: col = EXCLUDED.col, except for the primary key id
    update_clause=$(printf ", %s = EXCLUDED.%s" "${cols_array[@]:1}" "${cols_array[@]:1}")
    update_clause=${update_clause:2}  # remove leading comma and space

    # Execute UPSERT
    psql "$DB_URL" -c \
      "INSERT INTO $table ($cols) VALUES ($values)
       ON CONFLICT (id) DO UPDATE SET $update_clause;"
  done
done

echo "✅ All fixtures applied (upsert)."