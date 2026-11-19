-- DANGER: run only in a disposable database named cognova_seed_scratch,
-- restored from a private backup. Never run against a source/production database.
BEGIN;

DO $$
DECLARE
    demo_id integer;
BEGIN
    IF current_database() <> 'cognova_seed_scratch' THEN
        RAISE EXCEPTION 'refusing_to_sanitize_non_scratch_database';
    END IF;
    IF NOT (SELECT rolsuper FROM pg_roles WHERE rolname = current_user) THEN
        RAISE EXCEPTION 'scratch_sanitization_requires_superuser';
    END IF;
    SELECT id INTO demo_id
    FROM public.users
    WHERE email = 'demo.software@example.com'
      AND name = 'Lucia Torres Demo';
    IF demo_id IS NULL THEN
        RAISE EXCEPTION 'expected_fictional_demo_account_missing';
    END IF;
END
$$;

SET LOCAL session_replication_role = replica;

DELETE FROM public.academic_messages;
DELETE FROM public.academic_conversations;
DELETE FROM public.auth_sessions;
DELETE FROM public.rate_limit_buckets;
DELETE FROM public.activity_deadline_events
WHERE activity_id NOT IN (
    SELECT id FROM public.activities
    WHERE user_id = (SELECT id FROM public.users
                     WHERE email = 'demo.software@example.com')
);
DELETE FROM public.study_challenges
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.study_plan_decisions
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.study_plan_sessions
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.study_plan_activities
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.study_plan_subjects
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.study_session_intervals i
USING public.study_sessions s
WHERE i.session_id = s.id
  AND s.user_id <> (SELECT id FROM public.users
                    WHERE email = 'demo.software@example.com');
DELETE FROM public.study_sessions
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.activities
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.subjects
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.study_plans
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.questionnaire_responses
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.user_academic_goal_legacy
WHERE user_id <> (SELECT id FROM public.users
                  WHERE email = 'demo.software@example.com');
DELETE FROM public.users
WHERE id <> (SELECT id FROM public.users
             WHERE email = 'demo.software@example.com');

ALTER TABLE public.users ALTER COLUMN password_hash DROP NOT NULL;
UPDATE public.users SET password_hash = NULL
WHERE email = 'demo.software@example.com';

DO $$
DECLARE
    demo_id integer;
    table_name text;
    has_foreign_owner_rows boolean;
BEGIN
    SELECT id INTO demo_id
    FROM public.users
    WHERE email = 'demo.software@example.com';
    IF (SELECT count(*) FROM public.users) <> 1
       OR EXISTS (SELECT 1 FROM public.users WHERE password_hash IS NOT NULL) THEN
        RAISE EXCEPTION 'unexpected_non_demo_data';
    END IF;
    FOREACH table_name IN ARRAY ARRAY[
        'subjects', 'activities', 'study_sessions', 'study_plans',
        'study_plan_subjects', 'study_plan_activities', 'study_plan_sessions',
        'study_challenges', 'study_plan_decisions', 'questionnaire_responses',
        'user_academic_goal_legacy'
    ] LOOP
        EXECUTE format(
            'SELECT EXISTS (SELECT 1 FROM public.%I WHERE user_id <> $1)',
            table_name
        ) INTO has_foreign_owner_rows USING demo_id;
        IF has_foreign_owner_rows THEN
            RAISE EXCEPTION 'unexpected_non_demo_data';
        END IF;
    END LOOP;
    IF EXISTS (SELECT 1 FROM public.auth_sessions)
       OR EXISTS (SELECT 1 FROM public.academic_conversations)
       OR EXISTS (SELECT 1 FROM public.academic_messages)
       OR EXISTS (SELECT 1 FROM public.rate_limit_buckets)
       OR EXISTS (
           SELECT 1 FROM public.activity_deadline_events e
           JOIN public.activities a ON a.id = e.activity_id
           WHERE a.user_id <> demo_id
       )
       OR EXISTS (
           SELECT 1 FROM public.study_session_intervals i
           JOIN public.study_sessions s ON s.id = i.session_id
           WHERE s.user_id <> demo_id
       ) THEN
        RAISE EXCEPTION 'unexpected_non_demo_data';
    END IF;
END
$$;

-- Reset every serial sequence from allowlisted rows; pg_dump must not reveal
-- sequence positions left by accounts removed from this disposable copy.
SELECT pg_catalog.setval(
    'public.users_id_seq',
    COALESCE((SELECT max(id) FROM public.users), 1),
    EXISTS (SELECT 1 FROM public.users)
);
SELECT pg_catalog.setval(
    'public.subjects_id_seq',
    COALESCE((SELECT max(id) FROM public.subjects), 1),
    EXISTS (SELECT 1 FROM public.subjects)
);
SELECT pg_catalog.setval(
    'public.activities_id_seq',
    COALESCE((SELECT max(id) FROM public.activities), 1),
    EXISTS (SELECT 1 FROM public.activities)
);
SELECT pg_catalog.setval(
    'public.study_sessions_id_seq',
    COALESCE((SELECT max(id) FROM public.study_sessions), 1),
    EXISTS (SELECT 1 FROM public.study_sessions)
);
SELECT pg_catalog.setval(
    'public.study_session_intervals_id_seq',
    COALESCE((SELECT max(id) FROM public.study_session_intervals), 1),
    EXISTS (SELECT 1 FROM public.study_session_intervals)
);
SELECT pg_catalog.setval(
    'public.study_plans_id_seq',
    COALESCE((SELECT max(id) FROM public.study_plans), 1),
    EXISTS (SELECT 1 FROM public.study_plans)
);
SELECT pg_catalog.setval(
    'public.study_plan_decisions_id_seq',
    COALESCE((SELECT max(id) FROM public.study_plan_decisions), 1),
    EXISTS (SELECT 1 FROM public.study_plan_decisions)
);
SELECT pg_catalog.setval(
    'public.study_challenges_id_seq',
    COALESCE((SELECT max(id) FROM public.study_challenges), 1),
    EXISTS (SELECT 1 FROM public.study_challenges)
);
SELECT pg_catalog.setval('public.academic_conversations_id_seq', 1, false);
SELECT pg_catalog.setval('public.academic_messages_id_seq', 1, false);

SET LOCAL session_replication_role = origin;
COMMIT;
