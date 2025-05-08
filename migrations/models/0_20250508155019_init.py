from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "features" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT
);
COMMENT ON COLUMN "features"."name" IS 'Feature Name';
COMMENT ON COLUMN "features"."description" IS 'Description';
CREATE TABLE IF NOT EXISTS "listenings" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT NOT NULL
);
COMMENT ON COLUMN "listenings"."title" IS 'Title of the listening test';
COMMENT ON COLUMN "listenings"."description" IS 'Description of the listening test';
CREATE TABLE IF NOT EXISTS "listening_parts" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "part_number" SMALLINT NOT NULL,
    "audio_file" VARCHAR(255) NOT NULL,
    "listening_id" INT NOT NULL REFERENCES "listenings" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "listening_parts"."part_number" IS 'Part number of the test';
COMMENT ON COLUMN "listening_parts"."audio_file" IS 'Audio file path';
COMMENT ON COLUMN "listening_parts"."listening_id" IS 'Related listening test';
CREATE TABLE IF NOT EXISTS "listening_sections" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "section_number" INT NOT NULL,
    "start_index" INT NOT NULL,
    "end_index" INT NOT NULL,
    "question_type" VARCHAR(19) NOT NULL,
    "question_text" TEXT,
    "options" JSONB,
    "part_id" INT NOT NULL REFERENCES "listening_parts" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "listening_sections"."section_number" IS 'Section number within the part';
COMMENT ON COLUMN "listening_sections"."start_index" IS 'Start index of the section';
COMMENT ON COLUMN "listening_sections"."end_index" IS 'End index of the section';
COMMENT ON COLUMN "listening_sections"."question_type" IS 'Type of questions in the section';
COMMENT ON COLUMN "listening_sections"."question_text" IS 'Question text for the section';
COMMENT ON COLUMN "listening_sections"."options" IS 'Options for the questions in the section';
COMMENT ON COLUMN "listening_sections"."part_id" IS 'Related listening part';
CREATE TABLE IF NOT EXISTS "listening_questions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "index" INT NOT NULL,
    "options" JSONB,
    "correct_answer" JSONB NOT NULL,
    "section_id" INT NOT NULL REFERENCES "listening_sections" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "listening_questions"."index" IS 'Index of the question within the section';
COMMENT ON COLUMN "listening_questions"."options" IS 'Options for the question';
COMMENT ON COLUMN "listening_questions"."correct_answer" IS 'Correct answer for the question';
COMMENT ON COLUMN "listening_questions"."section_id" IS 'Related section';
CREATE TABLE IF NOT EXISTS "reading_passages" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "level" VARCHAR(50) NOT NULL,
    "number" INT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "text" TEXT NOT NULL,
    "skills" JSONB NOT NULL
);
COMMENT ON COLUMN "reading_passages"."level" IS 'Difficulty level of the passage';
COMMENT ON COLUMN "reading_passages"."number" IS 'Number of the passage';
COMMENT ON COLUMN "reading_passages"."title" IS 'Title of the passage';
COMMENT ON COLUMN "reading_passages"."text" IS 'Text content of the passage';
COMMENT ON COLUMN "reading_passages"."skills" IS 'Skills associated with the passage';
CREATE TABLE IF NOT EXISTS "reading_questions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "type" VARCHAR(50) NOT NULL,
    "score" INT NOT NULL,
    "correct_answer" TEXT NOT NULL,
    "passage_id" INT NOT NULL REFERENCES "reading_passages" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "reading_questions"."text" IS 'Text of the question';
COMMENT ON COLUMN "reading_questions"."type" IS 'Type of the question';
COMMENT ON COLUMN "reading_questions"."score" IS 'Score for the question';
COMMENT ON COLUMN "reading_questions"."correct_answer" IS 'Correct answer for the question';
COMMENT ON COLUMN "reading_questions"."passage_id" IS 'Related passage';
CREATE TABLE IF NOT EXISTS "tariff_categories" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL,
    "name_uz" VARCHAR(255),
    "name_ru" VARCHAR(255),
    "name_en" VARCHAR(255),
    "sale" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True
);
COMMENT ON COLUMN "tariff_categories"."name" IS 'Name';
COMMENT ON COLUMN "tariff_categories"."name_uz" IS 'Name (Uzbek)';
COMMENT ON COLUMN "tariff_categories"."name_ru" IS 'Name (Russian)';
COMMENT ON COLUMN "tariff_categories"."name_en" IS 'Name (English)';
COMMENT ON COLUMN "tariff_categories"."sale" IS 'Sale';
COMMENT ON COLUMN "tariff_categories"."is_active" IS 'Active';
CREATE TABLE IF NOT EXISTS "tariffs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL,
    "old_price" INT,
    "price" INT NOT NULL,
    "price_in_stars" INT NOT NULL DEFAULT 0,
    "description" TEXT NOT NULL,
    "description_uz" TEXT,
    "description_ru" TEXT,
    "description_en" TEXT,
    "tokens" INT NOT NULL,
    "duration" INT NOT NULL DEFAULT 30,
    "is_active" BOOL NOT NULL DEFAULT True,
    "is_default" BOOL NOT NULL DEFAULT False,
    "category_id" INT REFERENCES "tariff_categories" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "tariffs"."name" IS 'Name';
COMMENT ON COLUMN "tariffs"."old_price" IS 'Old Price';
COMMENT ON COLUMN "tariffs"."price" IS 'Price';
COMMENT ON COLUMN "tariffs"."price_in_stars" IS 'Price in Stars';
COMMENT ON COLUMN "tariffs"."description" IS 'Description';
COMMENT ON COLUMN "tariffs"."description_uz" IS 'Description (Uzbek)';
COMMENT ON COLUMN "tariffs"."description_ru" IS 'Description (Russian)';
COMMENT ON COLUMN "tariffs"."description_en" IS 'Description (English)';
COMMENT ON COLUMN "tariffs"."tokens" IS 'Tokens';
COMMENT ON COLUMN "tariffs"."duration" IS 'Duration';
COMMENT ON COLUMN "tariffs"."is_active" IS 'Active';
COMMENT ON COLUMN "tariffs"."is_default" IS 'Default';
COMMENT ON COLUMN "tariffs"."category_id" IS 'Category';
CREATE TABLE IF NOT EXISTS "sales" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "percent" INT NOT NULL DEFAULT 0,
    "start_date" DATE NOT NULL,
    "start_time" TIMETZ NOT NULL,
    "end_date" DATE NOT NULL,
    "end_time" TIMETZ NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "tariff_id" INT NOT NULL REFERENCES "tariffs" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "sales"."percent" IS 'Percent';
COMMENT ON COLUMN "sales"."start_date" IS 'Start Date';
COMMENT ON COLUMN "sales"."start_time" IS 'Start Time';
COMMENT ON COLUMN "sales"."end_date" IS 'End Date';
COMMENT ON COLUMN "sales"."end_time" IS 'End Time';
COMMENT ON COLUMN "sales"."is_active" IS 'Active';
COMMENT ON COLUMN "sales"."tariff_id" IS 'Tariff';
CREATE TABLE IF NOT EXISTS "tariff_features" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_included" BOOL NOT NULL DEFAULT True,
    "feature_id" INT NOT NULL REFERENCES "features" ("id") ON DELETE CASCADE,
    "tariff_id" INT NOT NULL REFERENCES "tariffs" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "tariff_features"."is_included" IS 'Is Included';
COMMENT ON COLUMN "tariff_features"."feature_id" IS 'Feature';
COMMENT ON COLUMN "tariff_features"."tariff_id" IS 'Tariff';
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "telegram_id" BIGINT UNIQUE,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "first_name" VARCHAR(255),
    "last_name" VARCHAR(255),
    "age" INT,
    "photo" VARCHAR(255),
    "password" VARCHAR(128) NOT NULL,
    "tokens" INT DEFAULT 0,
    "is_verified" BOOL NOT NULL DEFAULT False,
    "is_active" BOOL NOT NULL DEFAULT True,
    "is_staff" BOOL NOT NULL DEFAULT False,
    "is_superuser" BOOL NOT NULL DEFAULT False,
    "last_login" TIMESTAMPTZ,
    "tariff_id" INT REFERENCES "tariffs" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "users"."telegram_id" IS 'Telegram ID';
COMMENT ON COLUMN "users"."email" IS 'Email Address';
COMMENT ON COLUMN "users"."first_name" IS 'First Name';
COMMENT ON COLUMN "users"."last_name" IS 'Last Name';
COMMENT ON COLUMN "users"."age" IS 'Age';
COMMENT ON COLUMN "users"."photo" IS 'Photo';
COMMENT ON COLUMN "users"."password" IS 'Password';
COMMENT ON COLUMN "users"."tokens" IS 'Tokens';
COMMENT ON COLUMN "users"."is_verified" IS 'Verified';
COMMENT ON COLUMN "users"."is_active" IS 'Active';
COMMENT ON COLUMN "users"."is_staff" IS 'Staff';
COMMENT ON COLUMN "users"."is_superuser" IS 'Superuser';
COMMENT ON COLUMN "users"."last_login" IS 'Last Login';
COMMENT ON COLUMN "users"."tariff_id" IS 'Tariff';
CREATE TABLE IF NOT EXISTS "comments" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "rate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "status" VARCHAR(8) NOT NULL DEFAULT 'active',
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "comments"."text" IS 'Comment text';
COMMENT ON COLUMN "comments"."rate" IS 'Rating';
COMMENT ON COLUMN "comments"."status" IS 'Status';
COMMENT ON COLUMN "comments"."user_id" IS 'User';
CREATE TABLE IF NOT EXISTS "messages" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "type" VARCHAR(9) NOT NULL DEFAULT 'site',
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "content" TEXT NOT NULL,
    "user_id" INT REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "messages"."type" IS 'Type';
COMMENT ON COLUMN "messages"."title" IS 'Title';
COMMENT ON COLUMN "messages"."description" IS 'Description';
COMMENT ON COLUMN "messages"."content" IS 'Content';
COMMENT ON COLUMN "messages"."user_id" IS 'User';
CREATE TABLE IF NOT EXISTS "payments" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "uuid" UUID NOT NULL,
    "amount" INT NOT NULL,
    "start_date" TIMESTAMPTZ NOT NULL,
    "end_date" TIMESTAMPTZ NOT NULL,
    "tariff_id" INT NOT NULL REFERENCES "tariffs" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "payments"."uuid" IS 'UUID';
COMMENT ON COLUMN "payments"."amount" IS 'Amount';
COMMENT ON COLUMN "payments"."start_date" IS 'Start Date';
COMMENT ON COLUMN "payments"."end_date" IS 'End Date';
COMMENT ON COLUMN "payments"."tariff_id" IS 'Tariff';
COMMENT ON COLUMN "payments"."user_id" IS 'User';
CREATE TABLE IF NOT EXISTS "read_statuses" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "read_at" TIMESTAMPTZ,
    "message_id" INT NOT NULL REFERENCES "messages" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "read_statuses"."read_at" IS 'Read at';
COMMENT ON COLUMN "read_statuses"."message_id" IS 'Message';
COMMENT ON COLUMN "read_statuses"."user_id" IS 'User';
CREATE TABLE IF NOT EXISTS "readings" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(9) NOT NULL DEFAULT 'pending',
    "start_time" TIMESTAMPTZ NOT NULL,
    "end_time" TIMESTAMPTZ,
    "score" DECIMAL(3,1) NOT NULL,
    "duration" INT NOT NULL DEFAULT 60,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "readings"."status" IS 'Status of the test';
COMMENT ON COLUMN "readings"."start_time" IS 'Start time of the test';
COMMENT ON COLUMN "readings"."end_time" IS 'End time of the test';
COMMENT ON COLUMN "readings"."score" IS 'Score of the test';
COMMENT ON COLUMN "readings"."duration" IS 'Duration in minutes';
COMMENT ON COLUMN "readings"."user_id" IS 'Related user';
CREATE TABLE IF NOT EXISTS "reading_analyses" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "correct_answers" INT NOT NULL DEFAULT 0,
    "overall_score" DECIMAL(5,2) NOT NULL,
    "timing" TIMETZ NOT NULL,
    "feedback" TEXT NOT NULL,
    "passage_id" INT NOT NULL REFERENCES "reading_passages" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "reading_analyses"."correct_answers" IS 'Number of correct answers';
COMMENT ON COLUMN "reading_analyses"."overall_score" IS 'Overall score';
COMMENT ON COLUMN "reading_analyses"."timing" IS 'Time taken for the test';
COMMENT ON COLUMN "reading_analyses"."feedback" IS 'Feedback for the user';
COMMENT ON COLUMN "reading_analyses"."passage_id" IS 'Related reading passage';
COMMENT ON COLUMN "reading_analyses"."user_id" IS 'User who took the test';
CREATE TABLE IF NOT EXISTS "speaking" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(9) DEFAULT 'started',
    "start_time" TIMESTAMPTZ,
    "end_time" TIMESTAMPTZ,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "speaking"."status" IS 'Status';
COMMENT ON COLUMN "speaking"."start_time" IS 'Start time of the test';
COMMENT ON COLUMN "speaking"."end_time" IS 'End time of the test';
COMMENT ON COLUMN "speaking"."user_id" IS 'User taking the test';
CREATE TABLE IF NOT EXISTS "speaking_analyses" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "feedback" TEXT,
    "overall_band_score" DECIMAL(3,1),
    "fluency_and_coherence_score" DECIMAL(3,1),
    "fluency_and_coherence_feedback" TEXT,
    "lexical_resource_score" DECIMAL(3,1),
    "lexical_resource_feedback" TEXT,
    "grammatical_range_and_accuracy_score" DECIMAL(3,1),
    "grammatical_range_and_accuracy_feedback" TEXT,
    "pronunciation_score" DECIMAL(3,1),
    "pronunciation_feedback" TEXT,
    "duration" BIGINT,
    "speaking_id" INT NOT NULL UNIQUE REFERENCES "speaking" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "speaking_analyses"."feedback" IS 'Feedback for the user';
COMMENT ON COLUMN "speaking_analyses"."overall_band_score" IS 'Overall band score';
COMMENT ON COLUMN "speaking_analyses"."fluency_and_coherence_score" IS 'Fluency and coherence score';
COMMENT ON COLUMN "speaking_analyses"."fluency_and_coherence_feedback" IS 'Feedback on fluency and coherence';
COMMENT ON COLUMN "speaking_analyses"."lexical_resource_score" IS 'Lexical resource score';
COMMENT ON COLUMN "speaking_analyses"."lexical_resource_feedback" IS 'Feedback on lexical resource';
COMMENT ON COLUMN "speaking_analyses"."grammatical_range_and_accuracy_score" IS 'Grammatical range and accuracy score';
COMMENT ON COLUMN "speaking_analyses"."grammatical_range_and_accuracy_feedback" IS 'Feedback on grammatical range and accuracy';
COMMENT ON COLUMN "speaking_analyses"."pronunciation_score" IS 'Pronunciation score';
COMMENT ON COLUMN "speaking_analyses"."pronunciation_feedback" IS 'Feedback on pronunciation';
COMMENT ON COLUMN "speaking_analyses"."duration" IS 'Duration of the speaking test';
COMMENT ON COLUMN "speaking_analyses"."speaking_id" IS 'Analysis of the speaking test';
CREATE TABLE IF NOT EXISTS "speaking_questions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "part" VARCHAR(6),
    "title" TEXT,
    "content" TEXT NOT NULL,
    "speaking_id" INT NOT NULL REFERENCES "speaking" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "speaking_questions"."part" IS 'Part of the speaking test';
COMMENT ON COLUMN "speaking_questions"."title" IS 'Title of the question';
COMMENT ON COLUMN "speaking_questions"."content" IS 'Content of the question';
COMMENT ON COLUMN "speaking_questions"."speaking_id" IS 'Related speaking test';
CREATE TABLE IF NOT EXISTS "speaking_answers" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "text_answer" TEXT,
    "audio_answer" VARCHAR(255),
    "question_id" INT NOT NULL UNIQUE REFERENCES "speaking_questions" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "speaking_answers"."text_answer" IS 'Text answer to the question';
COMMENT ON COLUMN "speaking_answers"."audio_answer" IS 'Audio answer to the question';
COMMENT ON COLUMN "speaking_answers"."question_id" IS 'Related question';
CREATE TABLE IF NOT EXISTS "token_transactions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "transaction_type" VARCHAR(16) NOT NULL,
    "amount" INT NOT NULL,
    "balance_after_transaction" INT NOT NULL,
    "description" TEXT,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "token_transactions"."transaction_type" IS 'Transaction Type';
COMMENT ON COLUMN "token_transactions"."amount" IS 'Amount';
COMMENT ON COLUMN "token_transactions"."balance_after_transaction" IS 'Balance After Transaction';
COMMENT ON COLUMN "token_transactions"."description" IS 'Description';
COMMENT ON COLUMN "token_transactions"."user_id" IS 'User';
CREATE TABLE IF NOT EXISTS "user_activity_logs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "action" VARCHAR(255) NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "user_activity_logs"."action" IS 'Action performed by the user';
COMMENT ON COLUMN "user_activity_logs"."timestamp" IS 'Timestamp of the action';
COMMENT ON COLUMN "user_activity_logs"."user_id" IS 'User';
CREATE TABLE IF NOT EXISTS "user_listening_sessions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(9) DEFAULT 'started',
    "start_time" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "end_time" TIMESTAMPTZ,
    "exam_id" INT NOT NULL REFERENCES "listenings" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "user_listening_sessions"."status" IS 'Status of the user''s listening session';
COMMENT ON COLUMN "user_listening_sessions"."start_time" IS 'Start time of the session';
COMMENT ON COLUMN "user_listening_sessions"."end_time" IS 'End time of the session';
COMMENT ON COLUMN "user_listening_sessions"."exam_id" IS 'Related listening exam';
COMMENT ON COLUMN "user_listening_sessions"."user_id" IS 'Related user';
CREATE TABLE IF NOT EXISTS "listening_analyses" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "correct_answers" INT NOT NULL DEFAULT 0,
    "overall_score" DECIMAL(3,1) NOT NULL,
    "timing" BIGINT NOT NULL,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "session_id" INT NOT NULL UNIQUE REFERENCES "user_listening_sessions" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "listening_analyses"."correct_answers" IS 'Number of correct answers';
COMMENT ON COLUMN "listening_analyses"."overall_score" IS 'Overall score';
COMMENT ON COLUMN "listening_analyses"."timing" IS 'Time taken for the test';
COMMENT ON COLUMN "listening_analyses"."user_id" IS 'User who took the test';
COMMENT ON COLUMN "listening_analyses"."session_id" IS 'Related listening session';
CREATE TABLE IF NOT EXISTS "user_responses" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_answer" JSONB NOT NULL,
    "is_correct" BOOL NOT NULL DEFAULT False,
    "score" INT NOT NULL DEFAULT 0,
    "question_id" INT NOT NULL REFERENCES "listening_questions" ("id") ON DELETE CASCADE,
    "session_id" INT NOT NULL REFERENCES "user_listening_sessions" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "user_responses"."user_answer" IS 'User''s answer to the question';
COMMENT ON COLUMN "user_responses"."is_correct" IS 'Whether the user''s answer is correct';
COMMENT ON COLUMN "user_responses"."score" IS 'Score for the response';
COMMENT ON COLUMN "user_responses"."question_id" IS 'Related question';
COMMENT ON COLUMN "user_responses"."session_id" IS 'Related session';
COMMENT ON COLUMN "user_responses"."user_id" IS 'User who provided the response';
CREATE TABLE IF NOT EXISTS "reading_variants" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "is_correct" BOOL NOT NULL DEFAULT False,
    "question_id" INT NOT NULL REFERENCES "reading_questions" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "reading_variants"."text" IS 'Text of the variant';
COMMENT ON COLUMN "reading_variants"."is_correct" IS 'Whether the variant is correct';
COMMENT ON COLUMN "reading_variants"."question_id" IS 'Related question';
CREATE TABLE IF NOT EXISTS "reading_answers" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(12) NOT NULL DEFAULT 'not_answered',
    "text" TEXT NOT NULL,
    "explanation" TEXT,
    "is_correct" BOOL NOT NULL DEFAULT False,
    "correct_answer" TEXT,
    "question_id" INT NOT NULL REFERENCES "reading_questions" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "variant_id" INT REFERENCES "reading_variants" ("id") ON DELETE SET NULL
);
COMMENT ON COLUMN "reading_answers"."status" IS 'Status of the answer';
COMMENT ON COLUMN "reading_answers"."text" IS 'Answer text';
COMMENT ON COLUMN "reading_answers"."explanation" IS 'Explanation for the answer';
COMMENT ON COLUMN "reading_answers"."is_correct" IS 'Whether the answer is correct';
COMMENT ON COLUMN "reading_answers"."correct_answer" IS 'Correct answer text';
COMMENT ON COLUMN "reading_answers"."question_id" IS 'Related question';
COMMENT ON COLUMN "reading_answers"."user_id" IS 'Related user';
COMMENT ON COLUMN "reading_answers"."variant_id" IS 'Selected variant';
CREATE TABLE IF NOT EXISTS "verification_codes" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "email" VARCHAR(255),
    "verification_type" VARCHAR(15) NOT NULL,
    "code" INT,
    "is_used" BOOL NOT NULL DEFAULT False,
    "is_expired" BOOL NOT NULL DEFAULT False,
    "user_id" INT REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "verification_codes"."created_at" IS 'Created at';
COMMENT ON COLUMN "verification_codes"."email" IS 'Email';
COMMENT ON COLUMN "verification_codes"."verification_type" IS 'Verification Type';
COMMENT ON COLUMN "verification_codes"."code" IS 'Code';
COMMENT ON COLUMN "verification_codes"."is_used" IS 'Used';
COMMENT ON COLUMN "verification_codes"."is_expired" IS 'Expired';
COMMENT ON COLUMN "verification_codes"."user_id" IS 'User';
CREATE TABLE IF NOT EXISTS "writings" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(15) DEFAULT 'started',
    "start_time" TIMESTAMPTZ,
    "end_time" TIMESTAMPTZ,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "writings"."status" IS 'Status of the test';
COMMENT ON COLUMN "writings"."start_time" IS 'Start time of the test';
COMMENT ON COLUMN "writings"."end_time" IS 'End time of the test';
COMMENT ON COLUMN "writings"."user_id" IS 'Related user';
CREATE TABLE IF NOT EXISTS "writing_analyses" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "task_achievement_feedback" TEXT NOT NULL,
    "task_achievement_score" DECIMAL(3,1) NOT NULL,
    "lexical_resource_feedback" TEXT NOT NULL,
    "lexical_resource_score" DECIMAL(3,1) NOT NULL,
    "coherence_and_cohesion_feedback" TEXT NOT NULL,
    "coherence_and_cohesion_score" DECIMAL(3,1) NOT NULL,
    "grammatical_range_and_accuracy_feedback" TEXT NOT NULL,
    "grammatical_range_and_accuracy_score" DECIMAL(3,1) NOT NULL,
    "word_count_feedback" TEXT NOT NULL,
    "word_count_score" DECIMAL(3,1) NOT NULL,
    "timing_feedback" TEXT NOT NULL,
    "timing_time" BIGINT,
    "overall_band_score" DECIMAL(3,1) NOT NULL,
    "total_feedback" TEXT NOT NULL,
    "writing_id" INT NOT NULL UNIQUE REFERENCES "writings" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "writing_analyses"."task_achievement_feedback" IS 'Feedback on task achievement';
COMMENT ON COLUMN "writing_analyses"."task_achievement_score" IS 'Score for task achievement';
COMMENT ON COLUMN "writing_analyses"."lexical_resource_feedback" IS 'Feedback on lexical resource';
COMMENT ON COLUMN "writing_analyses"."lexical_resource_score" IS 'Score for lexical resource';
COMMENT ON COLUMN "writing_analyses"."coherence_and_cohesion_feedback" IS 'Feedback on coherence and cohesion';
COMMENT ON COLUMN "writing_analyses"."coherence_and_cohesion_score" IS 'Score for coherence and cohesion';
COMMENT ON COLUMN "writing_analyses"."grammatical_range_and_accuracy_feedback" IS 'Feedback on grammar';
COMMENT ON COLUMN "writing_analyses"."grammatical_range_and_accuracy_score" IS 'Score for grammar';
COMMENT ON COLUMN "writing_analyses"."word_count_feedback" IS 'Feedback on word count';
COMMENT ON COLUMN "writing_analyses"."word_count_score" IS 'Score for word count';
COMMENT ON COLUMN "writing_analyses"."timing_feedback" IS 'Feedback on timing';
COMMENT ON COLUMN "writing_analyses"."timing_time" IS 'Time taken for the test';
COMMENT ON COLUMN "writing_analyses"."overall_band_score" IS 'Overall band score';
COMMENT ON COLUMN "writing_analyses"."total_feedback" IS 'Overall feedback';
COMMENT ON COLUMN "writing_analyses"."writing_id" IS 'Related writing test';
CREATE TABLE IF NOT EXISTS "writing_part1" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "content" TEXT NOT NULL,
    "diagram" VARCHAR(255),
    "diagram_data" JSONB,
    "answer" TEXT,
    "writing_id" INT NOT NULL UNIQUE REFERENCES "writings" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "writing_part1"."content" IS 'Content of the test';
COMMENT ON COLUMN "writing_part1"."diagram" IS 'Diagram file path';
COMMENT ON COLUMN "writing_part1"."diagram_data" IS 'Data for the diagram';
COMMENT ON COLUMN "writing_part1"."answer" IS 'User''s answer';
COMMENT ON COLUMN "writing_part1"."writing_id" IS 'Related writing test part 1';
CREATE TABLE IF NOT EXISTS "writing_part2" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "content" TEXT NOT NULL,
    "answer" TEXT,
    "writing_id" INT NOT NULL UNIQUE REFERENCES "writings" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "writing_part2"."content" IS 'Content of the test';
COMMENT ON COLUMN "writing_part2"."answer" IS 'User''s answer';
COMMENT ON COLUMN "writing_part2"."writing_id" IS 'Related writing test part 2';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "readings_reading_passages" (
    "readings_id" INT NOT NULL REFERENCES "readings" ("id") ON DELETE CASCADE,
    "passage_id" INT NOT NULL REFERENCES "reading_passages" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "readings_reading_passages" IS 'Related passages';
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_readings_re_reading_5778fd" ON "readings_reading_passages" ("readings_id", "passage_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
