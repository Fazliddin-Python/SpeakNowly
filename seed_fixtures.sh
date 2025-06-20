#!/usr/bin/env bash
set -euo pipefail

DB_URL="postgresql://backender:Fazliddin.000@localhost:5432/speaknowly"

for file in fixtures/*.json; do
    table=$(basename "$file" .json)
    echo "→ Seeding (upsert) data into table: $table"

    jq -c '.[]' "$file" | while read -r row; do
        # 1) Get list of columns
        readarray -t cols_array < <(echo "$row" | jq -r 'keys_unsorted[]')

        # 2) Make string "col1, col2, col3"
        cols=$(IFS=, ; echo "${cols_array[*]}")

        # 3) Build VALUES, escaping string literals and replacing null with NULL
        vals=$(echo "$row" | jq -r '[.[]] |
            map(
                if . == null then
                    "NULL"
                elif type=="string" then
                    "'"'"'" + (gsub("'"'"'" ; "''")) + "'"'"'"
                else
                    tostring
                end
            ) | join(", ")')
        
        # 4) Build ON CONFLICT part, skipping id
        update_parts=()
        for col in "${cols_array[@]}"; do
            if [[ "$col" != "id" ]]; then
                update_parts+=("$col = EXCLUDED.$col")
            fi
        done
        update_clause=$(IFS=, ; echo "${update_parts[*]}")

        # 5) Build final SQL and execute
        sql="
            INSERT INTO public.$table ($cols)
            VALUES ($vals)
            ON CONFLICT (id) DO UPDATE
            SET $update_clause;
        "
        psql "$DB_URL" -c "$sql"
    done
done

echo "✅ All fixtures applied (upsert)."
