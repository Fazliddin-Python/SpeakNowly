#!/usr/bin/env bash
set -euo pipefail

DB_URL="postgresql://backender:Fazliddin.000@localhost:5432/speaknowly"

for file in fixtures/*.json; do
  table=$(basename "$file" .json)
  constraint="${table}_pkey"
  echo
  echo "→ Сеем (upsert) данные в таблицу: $table (ON CONFLICT ON CONSTRAINT $constraint)"

  # Для каждого объекта в JSON-массиве
  jq -c '.[]' "$file" | while IFS= read -r row; do
    # Получаем списки колонок и значений
    cols=$(echo "$row" | jq -r 'keys_unsorted | map(.|@sh) | join(", ")')
    vals=$(echo "$row" | jq -r '[
               to_entries[] | 
               if .value == null then
                 "NULL"
               elif (.value|type) == "string" then
                 @sh "\(.value)"
               else
                 "\(.value)"
               end
             ] | join(", ")')

    # Команда INSERT ... ON CONFLICT
    sql="
      INSERT INTO public.$table ($cols)
      VALUES ($vals)
      ON CONFLICT ON CONSTRAINT $constraint
      DO UPDATE SET
        $(echo "$cols" | sed 's/, */ = EXCLUDED./g') = EXCLUDED.$(echo "$cols" | sed 's/, */, EXCLUDED./g');
    "

    # Выполняем, но не обрываем весь скрипт, если вдруг что-то сломалось в одной строке
    if ! psql "$DB_URL" -v ON_ERROR_STOP=off -q -c "$sql" ; then
      echo "⚠️  Ошибка при вставке/обновлении в $table: пропускаем эту строку"
    fi
  done
done

echo
echo "✅ seed_fixtures.sh завершён (upsert по именованному constraint)."
