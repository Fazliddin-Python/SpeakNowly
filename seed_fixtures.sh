#!/usr/bin/env bash
set -e

DB_URL="postgresql://backender:Fazliddin.000@localhost:5432/speaknowly"

for file in fixtures/*.json; do
  table=$(basename "$file" .json)
  echo "→ Сеем (upsert) данные в таблицу: $table"

  jq -c '.[]' "$file" | while read -r row; do
    # колонки
    readarray -td, cols_array < <(echo "$row" | jq -r 'keys_unsorted | @csv' | sed 's/"//g,' )
    unset 'cols_array[-1]' # убрать пустой элемент из readarray

    # значения
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

    cols=$(IFS=, ; echo "${cols_array[*]}")
    update_clause=$(printf ", %s = EXCLUDED.%s" "${cols_array[@]:1}" "${cols_array[@]:1}")
    update_clause=${update_clause:2}

    psql "$DB_URL" -c \
      "INSERT INTO $table ($cols) VALUES ($vals)
       ON CONFLICT (id) DO UPDATE SET $update_clause;"
  done
done

echo "✅ Все fixtures применены (upsert)."
