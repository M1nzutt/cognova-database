--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6 (Debian 18.6-1.pgdg12+2)
-- Dumped by pg_dump version 18.6 (Debian 18.6-1.pgdg12+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.users (id, name, email, password_hash, degree_program, semester, academic_goal, created_at, updated_at) VALUES (36, 'Lucia Torres Demo', 'demo.software@example.com', NULL, 'Ingeniería de Software (demostración ficticia)', 5, NULL, '2026-11-16 03:25:41.476709+00', '2026-11-16 03:25:41.552504+00');


--
-- Data for Name: academic_conversations; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: academic_messages; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: subjects; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.subjects (id, user_id, name, status, difficulty, color_base, color_shade, active_slot, created_at, updated_at) VALUES (25, 36, 'Req. de Software', 'active', 'hard', 'blue', 200, 1, '2026-11-16 03:25:41.626326+00', '2026-11-16 03:25:41.626326+00');
INSERT INTO public.subjects (id, user_id, name, status, difficulty, color_base, color_shade, active_slot, created_at, updated_at) VALUES (26, 36, 'Arquitectura SW', 'active', 'hard', 'violet', 200, 2, '2026-11-16 03:25:41.661949+00', '2026-11-16 03:25:41.661949+00');
INSERT INTO public.subjects (id, user_id, name, status, difficulty, color_base, color_shade, active_slot, created_at, updated_at) VALUES (27, 36, 'Bases de Datos', 'active', 'medium', 'pink', 200, 3, '2026-11-16 03:25:41.701879+00', '2026-11-16 03:25:41.701879+00');
INSERT INTO public.subjects (id, user_id, name, status, difficulty, color_base, color_shade, active_slot, created_at, updated_at) VALUES (28, 36, 'Calidad y Pruebas', 'active', 'medium', 'rose', 200, 4, '2026-11-16 03:25:41.746676+00', '2026-11-16 03:25:41.746676+00');
INSERT INTO public.subjects (id, user_id, name, status, difficulty, color_base, color_shade, active_slot, created_at, updated_at) VALUES (29, 36, 'Gestión Ágil', 'active', 'easy', 'orange', 200, 5, '2026-11-16 03:25:41.776656+00', '2026-11-16 03:25:41.776656+00');


--
-- Data for Name: activities; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE public.activities DISABLE TRIGGER activity_prepare;
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (28, 36, 27, 'S1 Modelo de entidades', '2026-10-14 18:00:00+00', '2026-10-14 18:00:00+00', 0, 'high', 'completed', 90, 'TurnoClaro demo v1; semana 1. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:41.967236+00', '2026-11-16 03:25:41.9843+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (29, 36, 28, 'S1 Plan de calidad', '2026-10-15 18:00:00+00', '2026-10-15 18:00:00+00', 0, 'low', 'completed', 45, 'TurnoClaro demo v1; semana 1. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.024945+00', '2026-11-16 03:25:42.042046+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (30, 36, 29, 'S1 Backlog inicial', '2026-10-16 18:00:00+00', '2026-10-16 18:00:00+00', 0, 'medium', 'completed', 60, 'TurnoClaro demo v1; semana 1. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.068759+00', '2026-11-16 03:25:42.086029+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (26, 36, 25, 'S1 Entrevistas', '2026-10-12 18:00:00+00', '2026-10-12 18:00:00+00', 0, 'low', 'completed', 45, 'TurnoClaro demo v1; semana 1. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:41.829079+00', '2026-11-16 03:25:41.858926+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (27, 36, 26, 'S1 Contexto del sistema', '2026-10-13 18:00:00+00', '2026-10-13 18:00:00+00', 0, 'medium', 'completed', 60, 'TurnoClaro demo v1; semana 1. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:41.905+00', '2026-11-16 03:25:41.92289+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (31, 36, 25, 'S2 Historias de usuario', '2026-10-19 18:00:00+00', '2026-10-19 18:00:00+00', 0, 'medium', 'completed', 45, 'TurnoClaro demo v1; semana 2. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.137207+00', '2026-11-16 03:25:42.155058+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (32, 36, 26, 'S2 Diagramas de componentes', '2026-10-20 18:00:00+00', '2026-10-20 18:00:00+00', 0, 'high', 'completed', 60, 'TurnoClaro demo v1; semana 2. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.199691+00', '2026-11-16 03:25:42.231772+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (33, 36, 27, 'S2 Normalización', '2026-10-21 18:00:00+00', '2026-10-21 18:00:00+00', 0, 'low', 'completed', 90, 'TurnoClaro demo v1; semana 2. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.2742+00', '2026-11-16 03:25:42.309338+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (34, 36, 28, 'S2 Casos de prueba', '2026-10-22 18:00:00+00', '2026-10-22 18:00:00+00', 0, 'medium', 'completed', 45, 'TurnoClaro demo v1; semana 2. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.336189+00', '2026-11-16 03:25:42.353378+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (35, 36, 29, 'S2 Estimación de historias', '2026-10-23 18:00:00+00', '2026-10-23 18:00:00+00', 0, 'high', 'completed', 60, 'TurnoClaro demo v1; semana 2. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.382694+00', '2026-11-16 03:25:42.400415+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (36, 36, 25, 'S3 Criterios de aceptación', '2026-10-29 18:00:00+00', '2026-10-26 18:00:00+00', 1, 'high', 'pending', 45, 'TurnoClaro demo v1; semana 3. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.427013+00', '2026-11-16 03:25:42.472529+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (37, 36, 26, 'S3 Contrato REST', '2026-10-27 18:00:00+00', '2026-10-27 18:00:00+00', 0, 'low', 'pending', 60, 'TurnoClaro demo v1; semana 3. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.500762+00', '2026-11-16 03:25:42.500762+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (38, 36, 27, 'S3 Consultas de reservas', '2026-10-28 18:00:00+00', '2026-10-28 18:00:00+00', 0, 'medium', 'pending', 90, 'TurnoClaro demo v1; semana 3. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.528408+00', '2026-11-16 03:25:42.528408+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (39, 36, 28, 'S3 Pruebas unitarias', '2026-10-29 18:00:00+00', '2026-10-29 18:00:00+00', 0, 'high', 'pending', 45, 'TurnoClaro demo v1; semana 3. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.556387+00', '2026-11-16 03:25:42.556387+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (40, 36, 29, 'S3 Revisión del sprint', '2026-10-30 18:00:00+00', '2026-10-30 18:00:00+00', 0, 'low', 'pending', 60, 'TurnoClaro demo v1; semana 3. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.583576+00', '2026-11-16 03:25:42.583576+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (41, 36, 25, 'S4 Prototipo de reservas', '2026-11-02 18:00:00+00', '2026-11-02 18:00:00+00', 0, 'low', 'in_progress', 45, 'TurnoClaro demo v1; semana 4. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.609646+00', '2026-11-16 03:25:42.626596+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (47, 36, 26, 'S5 Revisión de seguridad', '2026-11-10 18:00:00+00', '2026-11-10 18:00:00+00', 0, 'high', 'pending', 60, 'TurnoClaro demo v1; semana 5. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.043029+00', '2026-11-16 03:25:43.043029+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (42, 36, 26, 'S4 Diseño de servicios', '2026-11-03 18:00:00+00', '2026-11-03 18:00:00+00', 0, 'high', 'in_progress', 60, 'TurnoClaro demo v1; semana 4. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.676341+00', '2026-11-16 03:25:42.739076+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (51, 36, 25, 'S6 Entrega de requisitos', '2026-11-16 18:00:00+00', '2026-11-16 18:00:00+00', 0, 'high', 'pending', 45, 'TurnoClaro demo v1; semana 6. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.228658+00', '2026-11-16 03:25:43.228658+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (43, 36, 27, 'S4 Índices y rendimiento', '2026-11-07 18:00:00+00', '2026-11-04 18:00:00+00', 1, 'high', 'in_progress', 90, 'TurnoClaro demo v1; semana 4. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.766061+00', '2026-11-16 03:25:42.838353+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (44, 36, 28, 'S4 Pruebas de integración', '2026-11-05 18:00:00+00', '2026-11-05 18:00:00+00', 0, 'low', 'in_progress', 45, 'TurnoClaro demo v1; semana 4. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.864805+00', '2026-11-16 03:25:42.900992+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (45, 36, 29, 'S4 Ajuste de prioridades', '2026-11-06 18:00:00+00', '2026-11-06 18:00:00+00', 0, 'medium', 'in_progress', 60, 'TurnoClaro demo v1; semana 4. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:42.940959+00', '2026-11-16 03:25:42.958486+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (46, 36, 25, 'S5 Validación del alcance', '2026-11-09 18:00:00+00', '2026-11-09 18:00:00+00', 0, 'medium', 'pending', 45, 'TurnoClaro demo v1; semana 5. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.004919+00', '2026-11-16 03:25:43.004919+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (52, 36, 26, 'S6 Integración de módulos', '2026-11-17 18:00:00+00', '2026-11-17 18:00:00+00', 0, 'low', 'pending', 60, 'TurnoClaro demo v1; semana 6. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.259258+00', '2026-11-16 03:25:43.259258+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (48, 36, 27, 'S5 Transacciones', '2026-11-11 18:00:00+00', '2026-11-11 18:00:00+00', 0, 'low', 'pending', 90, 'TurnoClaro demo v1; semana 5. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.070958+00', '2026-11-16 03:25:43.070958+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (54, 36, 28, 'S6 Informe de calidad', '2026-11-19 18:00:00+00', '2026-11-19 18:00:00+00', 0, 'high', 'pending', 45, 'TurnoClaro demo v1; semana 6. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.32886+00', '2026-11-16 03:25:43.32886+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (49, 36, 28, 'S5 Regresión de reservas', '2026-11-15 18:00:00+00', '2026-11-12 18:00:00+00', 1, 'medium', 'pending', 45, 'TurnoClaro demo v1; semana 5. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.109649+00', '2026-11-16 03:25:43.128719+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (50, 36, 29, 'S5 Retrospectiva', '2026-11-13 18:00:00+00', '2026-11-13 18:00:00+00', 0, 'high', 'pending', 60, 'TurnoClaro demo v1; semana 5. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.159789+00', '2026-11-16 03:25:43.159789+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (55, 36, 29, 'S6 Preparación de entrega', '2026-11-20 18:00:00+00', '2026-11-20 18:00:00+00', 0, 'low', 'pending', 60, 'TurnoClaro demo v1; semana 6. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.392354+00', '2026-11-16 03:25:43.392354+00');
INSERT INTO public.activities (id, user_id, subject_id, title, deadline, original_deadline, deadline_revision, priority, status, estimated_duration, notes, created_at, updated_at) VALUES (53, 36, 27, 'S6 Entrega de persistencia', '2026-11-18 18:00:00+00', '2026-11-18 18:00:00+00', 0, 'medium', 'pending', 90, 'TurnoClaro demo v1; semana 6. Planificación ficticia; cambios y ejecución registrados con fecha real al preparar o utilizar la cuenta.', '2026-11-16 03:25:43.290018+00', '2026-11-16 03:25:43.290018+00');
ALTER TABLE public.activities ENABLE TRIGGER activity_prepare;


--
-- Data for Name: activity_deadline_events; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.activity_deadline_events (activity_id, revision, previous_deadline, new_deadline, event_type, occurred_at) VALUES (36, 1, '2026-10-26 18:00:00+00', '2026-10-29 18:00:00+00', 'postponed', '2026-11-16 03:25:42.472529+00');
INSERT INTO public.activity_deadline_events (activity_id, revision, previous_deadline, new_deadline, event_type, occurred_at) VALUES (43, 1, '2026-11-04 18:00:00+00', '2026-11-07 18:00:00+00', 'postponed', '2026-11-16 03:25:42.838353+00');
INSERT INTO public.activity_deadline_events (activity_id, revision, previous_deadline, new_deadline, event_type, occurred_at) VALUES (49, 1, '2026-11-12 18:00:00+00', '2026-11-15 18:00:00+00', 'postponed', '2026-11-16 03:25:43.128719+00');


--
-- Data for Name: auth_sessions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: questionnaire_responses; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.questionnaire_responses (user_id, revision, questionnaire_version, answers, recorded_at) VALUES (36, 1, 1, '{"q1": "organize_time", "q2": "one_two_days", "q3": "night", "q4": "over_two_hours", "q5": "always", "q6": ["too_many_activities"], "q7": ["no_method"], "q8": "most_urgent", "q9": "partially", "q10": ["consistency"]}', '2026-11-16 03:25:41.588755+00');


--
-- Data for Name: rate_limit_buckets; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: study_plans; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_plans (id, user_id, name, objective, start_at, end_at, status, source, created_at, updated_at, ai_proposal_snapshot) VALUES (24, 36, 'TurnoClaro · Fundamentos', 'TurnoClaro: sistema ficticio de reservas. Las fechas pasadas son planificación; ejecución y decisiones conservan la fecha real.', '2026-10-10 00:00:00+00', '2026-11-25 23:00:00+00', 'completed', 'manual', '2026-11-16 03:25:44.789696+00', '2026-11-16 03:25:44.891504+00', NULL);
INSERT INTO public.study_plans (id, user_id, name, objective, start_at, end_at, status, source, created_at, updated_at, ai_proposal_snapshot) VALUES (25, 36, 'TurnoClaro · Ruta revisada', 'TurnoClaro: sistema ficticio de reservas. Las fechas pasadas son planificación; ejecución y decisiones conservan la fecha real.', '2026-10-10 00:00:00+00', '2026-11-25 23:00:00+00', 'active', 'manual', '2026-11-16 03:25:44.944371+00', '2026-11-16 03:25:45.061255+00', NULL);
INSERT INTO public.study_plans (id, user_id, name, objective, start_at, end_at, status, source, created_at, updated_at, ai_proposal_snapshot) VALUES (26, 36, 'TurnoClaro · Propuesta elegida', 'Optimizar el rendimiento en las materias activas y mantener la consistencia en el estudio diario.', '2026-10-10 00:00:00+00', '2026-11-25 23:00:00+00', 'active', 'ai', '2026-11-17 02:15:12.760952+00', '2026-11-17 02:15:12.918181+00', '{"plan": {"name": "Propuesta de Plan Académico", "end_date": "2026-11-25T23:00:00Z", "objective": "Optimizar el rendimiento en las materias activas y mantener la consistencia en el estudio diario.", "start_date": "2026-10-10T00:00:00Z", "session_ids": [53, 54, 55, 56, 57, 59], "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 52, 53, 54, 55]}, "model": "gemini-3.5-flash-lite", "explanation": "Plan estructurado para equilibrar la carga de actividades pendientes y mejorar la consistencia según el análisis de sesiones previas.", "generated_at": "2026-11-17T02:15:12.757034Z", "schema_version": 1, "reasoning_summary": "Se priorizan materias activas y se establecen metas acordes a las actividades pendientes y sesiones registradas.", "proposed_challenges": [{"title": "Completar Requisitos", "end_date": "2026-11-16T18:00:00Z", "evidence": ["subject:25", "activity:51", "session:53"], "objective": "Finalizar la entrega de requisitos de software.", "target_id": null, "session_id": 53, "start_date": "2026-10-11T00:00:00Z", "subject_id": 25, "activity_id": 51, "explanation": "Reto enfocado en la materia de Req. de Software dada su dificultad y actividad pendiente.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "Completar la actividad S6 Entrega de requisitos."}]}');
INSERT INTO public.study_plans (id, user_id, name, objective, start_at, end_at, status, source, created_at, updated_at, ai_proposal_snapshot) VALUES (31, 36, 'TurnoClaro · Ruta de estudio adaptada', 'Consolidar el progreso en las materias activas y mantener la consistencia en el tiempo de estudio diario.', '2026-10-10 00:00:00+00', '2026-11-25 23:00:00+00', 'draft', 'ai', '2026-11-18 18:42:05.279519+00', '2026-11-18 18:42:05.279519+00', '{"plan": {"name": "TurnoClaro · Ruta de estudio adaptada", "end_date": "2026-11-25T23:00:00Z", "objective": "Consolidar el progreso en las materias activas y mantener la consistencia en el tiempo de estudio diario.", "start_date": "2026-10-10T00:00:00Z", "session_ids": [53, 59], "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 53]}, "model": "gemini-3.5-flash-lite", "explanation": "Propuesta basada en el análisis de sesiones de estudio y actividades pendientes para mejorar la consistencia y completar las entregas.", "generated_at": "2026-11-18T18:42:05.276841Z", "schema_version": 1, "reasoning_summary": "Se seleccionaron actividades clave con sesiones asociadas para fomentar la consistencia en el estudio y cumplir con las fechas límite.", "proposed_challenges": [{"title": "Completar entrega de requisitos", "end_date": "2026-11-16T18:00:00Z", "evidence": ["subject:25", "activity:51", "session:53"], "objective": "Finalizar la actividad de requisitos de software con éxito.", "target_id": null, "session_id": 53, "start_date": "2026-11-16T09:00:00Z", "subject_id": 25, "activity_id": 51, "explanation": "Es necesario completar la actividad pendiente para mantener el ritmo académico.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "Completar la actividad de requisitos de software"}, {"title": "Entrega de persistencia", "end_date": "2026-11-18T18:00:00Z", "evidence": ["subject:27", "activity:53", "session:59"], "objective": "Asegurar la entrega de la persistencia en bases de datos.", "target_id": null, "session_id": 59, "start_date": "2026-11-17T14:00:00Z", "subject_id": 27, "activity_id": 53, "explanation": "Se requiere culminar la actividad vinculada para asegurar el dominio de bases de datos.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "Finalizar la actividad de persistencia"}]}');
INSERT INTO public.study_plans (id, user_id, name, objective, start_at, end_at, status, source, created_at, updated_at, ai_proposal_snapshot) VALUES (32, 36, 'TurnoClaro · Propuesta de Optimización', 'Mejorar la constancia en el estudio y completar las actividades pendientes en las materias activas.', '2026-10-10 00:00:00+00', '2026-11-25 23:00:00+00', 'draft', 'ai', '2026-11-18 18:42:13.13463+00', '2026-11-18 18:42:13.13463+00', '{"plan": {"name": "TurnoClaro · Propuesta de Optimización", "end_date": "2026-11-25T23:00:00Z", "objective": "Mejorar la constancia en el estudio y completar las actividades pendientes en las materias activas.", "start_date": "2026-10-10T00:00:00Z", "session_ids": [53, 54, 56, 57, 59], "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 52, 53, 54, 55]}, "model": "gemini-3.5-flash-lite", "explanation": "Esta propuesta busca mitigar las dificultades reportadas en la consistencia de estudio y la acumulación de actividades pendientes mediante retos específicos vinculados a las materias activas y sus sesiones correspondientes.", "generated_at": "2026-11-18T18:42:13.133089Z", "schema_version": 1, "reasoning_summary": "Se han seleccionado materias activas clave junto con actividades y sesiones recientes que presentaron un resultado parcial o cancelado, con el fin de proponer desafíos orientados a mejorar la consistencia y la finalización de tareas.", "proposed_challenges": [{"title": "Completar entrega de requisitos", "end_date": "2026-11-16T18:00:00Z", "evidence": ["subject:25", "activity:51", "session:53"], "objective": "Finalizar la actividad de requisitos de software con éxito.", "target_id": null, "session_id": 53, "start_date": "2026-10-10T00:00:00Z", "subject_id": 25, "activity_id": 51, "explanation": "Se requiere concluir la actividad pendiente para mantener el flujo de entrega.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "La actividad debe quedar en estado completado."}, {"title": "Integración de módulos SW", "end_date": "2026-11-17T18:00:00Z", "evidence": ["subject:26", "activity:52", "session:54"], "objective": "Avanzar en la integración de módulos de arquitectura.", "target_id": null, "session_id": 54, "start_date": "2026-10-10T00:00:00Z", "subject_id": 26, "activity_id": 52, "explanation": "Es necesario superar las sesiones parciales registradas en esta materia.", "target_type": "session_completion", "target_value": {"lifecycle": "finished"}, "measurable_condition": "La sesión vinculada debe finalizar correctamente."}, {"title": "Entrega de persistencia BD", "end_date": "2026-11-18T18:00:00Z", "evidence": ["subject:27", "activity:53", "session:59"], "objective": "Completar la persistencia en bases de datos.", "target_id": null, "session_id": 59, "start_date": "2026-10-10T00:00:00Z", "subject_id": 27, "activity_id": 53, "explanation": "Se observaron sesiones canceladas o parciales que requieren refuerzo.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "La actividad de persistencia debe estar completada."}, {"title": "Informe de calidad", "end_date": "2026-11-19T18:00:00Z", "evidence": ["subject:28", "activity:54", "session:56"], "objective": "Finalizar el reporte de calidad y pruebas.", "target_id": null, "session_id": 56, "start_date": "2026-10-10T00:00:00Z", "subject_id": 28, "activity_id": 54, "explanation": "Ayuda a mitigar los problemas de consistencia en el estudio.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "El informe de calidad debe marcarse como completado."}, {"title": "Preparación de entrega ágil", "end_date": "2026-11-20T18:00:00Z", "evidence": ["subject:29", "activity:55", "session:57"], "objective": "Concluir la preparación de la entrega en gestión ágil.", "target_id": null, "session_id": 57, "start_date": "2026-10-10T00:00:00Z", "subject_id": 29, "activity_id": 55, "explanation": "Permite mantener el ritmo adecuado frente al volumen de actividades.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "La actividad de preparación debe registrar estado completado."}]}');
INSERT INTO public.study_plans (id, user_id, name, objective, start_at, end_at, status, source, created_at, updated_at, ai_proposal_snapshot) VALUES (71, 36, 'Plan de Refuerzo Académico', 'Consolidar las entregas pendientes y mejorar la consistencia en el estudio diario de las materias activas.', '2026-10-10 00:00:00+00', '2026-11-25 23:00:00+00', 'active', 'ai', '2026-11-19 03:27:43.349825+00', '2026-11-19 03:27:57.596144+00', '{"plan": {"name": "Plan de Refuerzo Académico", "end_date": "2026-11-25T23:00:00Z", "objective": "Consolidar las entregas pendientes y mejorar la consistencia en el estudio diario de las materias activas.", "start_date": "2026-10-10T00:00:00Z", "session_ids": [53, 54, 56, 57, 59], "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 52, 53, 54, 55]}, "model": "gemini-3.5-flash-lite", "explanation": "Se propone una ruta centrada en completar actividades clave y mantener el hábito de estudio diario para mitigar la acumulación de tareas.", "generated_at": "2026-11-19T03:27:43.347096Z", "schema_version": 1, "reasoning_summary": "El plan se basa en el análisis de las materias activas con mayor carga pendiente y en la necesidad de mejorar la consistencia según los datos de sesiones anteriores.", "proposed_challenges": [{"title": "Desafío Requisitos", "end_date": "2026-11-16T18:00:00Z", "evidence": ["subject:25", "activity:51", "session:53"], "objective": "Completar la actividad de requisitos de software", "target_id": null, "session_id": 53, "start_date": "2026-11-16T09:00:00Z", "subject_id": 25, "activity_id": 51, "explanation": "Es necesario asegurar la entrega a tiempo de la actividad para mantener el progreso en la materia de alta dificultad.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "La actividad debe marcarse como completada."}, {"title": "Desafío Arquitectura", "end_date": "2026-11-17T18:00:00Z", "evidence": ["subject:26", "activity:52", "session:54"], "objective": "Finalizar la sesión de integración de módulos", "target_id": null, "session_id": 54, "start_date": "2026-11-16T10:00:00Z", "subject_id": 26, "activity_id": 52, "explanation": "Se requiere mantener la consistencia en las sesiones de arquitectura de software.", "target_type": "session_completion", "target_value": {"lifecycle": "finished"}, "measurable_condition": "La sesión debe finalizarse con éxito."}, {"title": "Desafío Bases de Datos", "end_date": "2026-11-18T18:00:00Z", "evidence": ["subject:27", "activity:53", "session:59"], "objective": "Completar la entrega de persistencia", "target_id": null, "session_id": 59, "start_date": "2026-11-17T14:00:00Z", "subject_id": 27, "activity_id": 53, "explanation": "La consistencia y el avance en bases de datos son prioritarios para evitar retrasos.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "La actividad debe quedar completada."}]}');


--
-- Data for Name: study_plan_subjects; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 24, 25);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 24, 26);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 24, 27);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 24, 28);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 24, 29);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 25, 25);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 25, 26);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 25, 27);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 25, 28);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 25, 29);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 26, 25);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 26, 26);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 26, 27);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 26, 28);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 26, 29);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 31, 25);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 31, 26);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 31, 27);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 31, 28);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 31, 29);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 32, 25);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 32, 26);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 32, 27);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 32, 28);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 32, 29);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 71, 25);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 71, 26);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 71, 27);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 71, 28);
INSERT INTO public.study_plan_subjects (user_id, plan_id, subject_id) VALUES (36, 71, 29);


--
-- Data for Name: study_plan_activities; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 25, 26);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 26, 27);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 27, 28);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 28, 29);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 29, 30);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 25, 31);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 26, 32);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 27, 33);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 28, 34);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 24, 29, 35);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 25, 26);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 26, 27);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 27, 28);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 28, 29);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 29, 30);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 25, 31);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 26, 32);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 27, 33);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 28, 34);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 29, 35);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 25, 36);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 26, 37);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 27, 38);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 28, 39);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 29, 40);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 25, 41);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 26, 42);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 27, 43);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 28, 44);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 29, 45);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 25, 46);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 26, 47);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 27, 48);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 28, 49);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 29, 50);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 25, 51);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 26, 52);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 27, 53);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 28, 54);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 25, 29, 55);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 26, 25, 51);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 26, 26, 52);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 26, 27, 53);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 26, 28, 54);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 26, 29, 55);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 31, 25, 51);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 31, 27, 53);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 32, 25, 51);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 32, 26, 52);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 32, 27, 53);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 32, 28, 54);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 32, 29, 55);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 71, 25, 51);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 71, 26, 52);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 71, 27, 53);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 71, 28, 54);
INSERT INTO public.study_plan_activities (user_id, plan_id, subject_id, activity_id) VALUES (36, 71, 29, 55);


--
-- Data for Name: study_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (41, 36, 28, 44, '2026-11-04 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.200876+00', '2026-11-16 03:25:44.200876+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (42, 36, 29, 45, '2026-11-05 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.251605+00', '2026-11-16 03:25:44.251605+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (43, 36, 25, 46, '2026-11-08 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.281301+00', '2026-11-16 03:25:44.281301+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (44, 36, 26, 47, '2026-11-09 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.309786+00', '2026-11-16 03:25:44.309786+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (45, 36, 27, 48, '2026-11-10 15:00:00+00', 75, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.337313+00', '2026-11-16 03:25:44.337313+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (46, 36, 28, 49, '2026-11-11 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.365382+00', '2026-11-16 03:25:44.365382+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (47, 36, 29, 50, '2026-11-12 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.403469+00', '2026-11-16 03:25:44.403469+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (48, 36, 25, 51, '2026-11-15 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.431003+00', '2026-11-16 03:25:44.431003+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (49, 36, 26, 52, '2026-11-16 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.458692+00', '2026-11-16 03:25:44.458692+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (50, 36, 27, 53, '2026-11-17 15:00:00+00', 75, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.486353+00', '2026-11-16 03:25:44.486353+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (51, 36, 28, 54, '2026-11-18 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.515203+00', '2026-11-16 03:25:44.515203+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (52, 36, 29, 55, '2026-11-19 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.543575+00', '2026-11-16 03:25:44.543575+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (23, 36, 25, 26, '2026-10-11 15:00:00+00', 45, 'finished', 'postponed', NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.420081+00', '2026-11-16 03:25:43.459623+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (24, 36, 26, 27, '2026-10-12 15:00:00+00', 60, 'finished', 'cancelled', NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.505643+00', '2026-11-16 03:25:43.535225+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (25, 36, 27, 28, '2026-10-13 15:00:00+00', 75, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.58287+00', '2026-11-16 03:25:43.58287+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (26, 36, 28, 29, '2026-10-14 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.629291+00', '2026-11-16 03:25:43.629291+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (27, 36, 29, 30, '2026-10-15 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.658659+00', '2026-11-16 03:25:43.658659+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (28, 36, 25, 31, '2026-10-18 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.722986+00', '2026-11-16 03:25:43.722986+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (29, 36, 26, 32, '2026-10-19 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.770657+00', '2026-11-16 03:25:43.770657+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (30, 36, 27, 33, '2026-10-20 15:00:00+00', 75, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.798188+00', '2026-11-16 03:25:43.798188+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (31, 36, 28, 34, '2026-10-21 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.824988+00', '2026-11-16 03:25:43.824988+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (32, 36, 29, 35, '2026-10-22 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.875516+00', '2026-11-16 03:25:43.875516+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (33, 36, 25, 36, '2026-10-25 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.902988+00', '2026-11-16 03:25:43.902988+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (34, 36, 26, 37, '2026-10-26 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.951327+00', '2026-11-16 03:25:43.951327+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (35, 36, 27, 38, '2026-10-27 15:00:00+00', 75, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:43.998637+00', '2026-11-16 03:25:43.998637+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (36, 36, 28, 39, '2026-10-28 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.045688+00', '2026-11-16 03:25:44.045688+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (37, 36, 29, 40, '2026-10-29 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.074901+00', '2026-11-16 03:25:44.074901+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (38, 36, 25, 41, '2026-11-01 15:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.102475+00', '2026-11-16 03:25:44.102475+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (39, 36, 26, 42, '2026-11-02 15:00:00+00', 60, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.140544+00', '2026-11-16 03:25:44.140544+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (40, 36, 27, 43, '2026-11-03 15:00:00+00', 75, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.170831+00', '2026-11-16 03:25:44.170831+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (58, 36, 26, 52, '2026-11-22 16:00:00+00', 45, 'planned', NULL, NULL, NULL, 0.000000, NULL, NULL, '2026-11-16 03:25:44.743533+00', '2026-11-16 03:25:44.743533+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (54, 36, 26, 52, '2026-11-16 10:00:00+00', 10, 'finished', 'partial', '2026-11-16 03:35:56.094418+00', '2026-11-16 03:36:56.26683+00', 60.140789, 'interrupted', NULL, '2026-11-16 03:25:44.620126+00', '2026-11-16 03:36:56.269461+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (53, 36, 25, 51, '2026-11-16 09:00:00+00', 10, 'finished', 'completed', '2026-11-16 03:25:55.825315+00', '2026-11-16 03:35:56.057632+00', 600.232317, 'finished_early', NULL, '2026-11-16 03:25:44.572458+00', '2026-11-16 03:35:56.063653+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (59, 36, 27, 53, '2026-11-17 14:00:00+00', 10, 'finished', 'partial', '2026-11-16 16:18:15.240048+00', '2026-11-16 16:19:15.364661+00', 60.124613, 'interrupted', NULL, '2026-11-16 16:17:58.858879+00', '2026-11-16 16:19:15.371209+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (55, 36, 27, 53, '2026-11-16 11:00:00+00', 10, 'finished', 'cancelled', '2026-11-16 03:36:56.294012+00', '2026-11-16 16:17:58.716584+00', 45662.422572, 'other', 'Interrupción técnica durante la preparación de la demo. El temporizador permaneció abierto; no representa estudio efectivo.', '2026-11-16 03:25:44.648949+00', '2026-11-16 16:17:58.755324+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (56, 36, 28, 54, '2026-11-16 12:00:00+00', 10, 'finished', 'partial', '2026-11-16 16:19:15.453167+00', '2026-11-16 16:20:15.578209+00', 60.125042, 'interrupted', NULL, '2026-11-16 03:25:44.677443+00', '2026-11-16 16:20:15.58008+00');
INSERT INTO public.study_sessions (id, user_id, subject_id, activity_id, planned_start_at, planned_duration, execution_state, status, start_at, end_at, actual_duration, context, other_text, created_at, updated_at) VALUES (57, 36, 29, 55, '2026-11-16 13:00:00+00', 10, 'finished', 'partial', '2026-11-16 16:20:15.637207+00', '2026-11-16 16:21:15.749816+00', 60.112609, 'interrupted', NULL, '2026-11-16 03:25:44.705002+00', '2026-11-16 16:21:15.751614+00');


--
-- Data for Name: study_plan_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 25, 23);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 24);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 27, 25);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 28, 26);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 29, 27);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 25, 28);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 29);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 27, 30);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 28, 31);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 29, 32);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 25, 33);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 34);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 27, 35);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 28, 36);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 29, 37);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 25, 38);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 39);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 27, 40);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 28, 41);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 29, 42);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 25, 43);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 44);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 27, 45);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 28, 46);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 29, 47);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 25, 48);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 49);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 27, 50);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 28, 51);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 29, 52);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 25, 53);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 54);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 27, 55);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 28, 56);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 29, 57);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 25, 26, 58);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 26, 25, 53);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 26, 26, 54);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 26, 27, 55);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 26, 28, 56);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 26, 29, 57);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 26, 27, 59);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 31, 25, 53);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 31, 27, 59);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 32, 25, 53);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 32, 26, 54);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 32, 28, 56);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 32, 29, 57);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 32, 27, 59);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 71, 25, 53);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 71, 26, 54);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 71, 28, 56);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 71, 29, 57);
INSERT INTO public.study_plan_sessions (user_id, plan_id, subject_id, study_session_id) VALUES (36, 71, 27, 59);


--
-- Data for Name: study_challenges; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (22, 36, 25, 25, 26, NULL, 'Entrevistas revisadas', 'Revisar la entrega TurnoClaro vinculada y su resultado.', 'activity_completion', '{"status": "completed"}', NULL, '2026-11-22 22:00:00+00', 'completed', 'manual', '{"origin": "manual_demo", "evidence": "Actividad del semestre ficticio TurnoClaro."}', '2026-11-16 03:25:45.095642+00', '2026-11-16 03:25:45.158166+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (23, 36, 25, 27, 33, NULL, 'Normalización comprobada', 'Revisar la entrega TurnoClaro vinculada y su resultado.', 'activity_completion', '{"status": "completed"}', NULL, '2026-11-22 22:00:00+00', 'completed', 'manual', '{"origin": "manual_demo", "evidence": "Actividad del semestre ficticio TurnoClaro."}', '2026-11-16 03:25:45.184513+00', '2026-11-16 03:25:45.224118+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (24, 36, 25, 28, 39, NULL, 'Pruebas pospuestas', 'Revisar la entrega TurnoClaro vinculada y su resultado.', 'activity_completion', '{"status": "completed"}', NULL, '2026-11-22 22:00:00+00', 'failed', 'manual', '{"origin": "manual_demo", "evidence": "Actividad del semestre ficticio TurnoClaro."}', '2026-11-16 03:25:45.270499+00', '2026-11-16 03:25:45.312843+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (25, 36, 25, 26, 42, NULL, 'Contrato en revisión', 'Revisar la entrega TurnoClaro vinculada y su resultado.', 'activity_completion', '{"status": "completed"}', NULL, '2026-11-22 22:00:00+00', 'in_progress', 'manual', '{"origin": "manual_demo", "evidence": "Actividad del semestre ficticio TurnoClaro."}', '2026-11-16 03:25:45.341035+00', '2026-11-16 03:25:45.380486+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (26, 36, 25, 25, 41, NULL, 'Validar prototipo', 'Revisar la entrega TurnoClaro vinculada y su resultado.', 'activity_completion', '{"status": "completed"}', NULL, '2026-11-22 22:00:00+00', 'pending', 'manual', '{"origin": "manual_demo", "evidence": "Actividad del semestre ficticio TurnoClaro.", "depends_on_activity_ids": [36]}', '2026-11-16 03:25:45.407096+00', '2026-11-16 03:25:45.407096+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (27, 36, 25, 29, 55, NULL, 'Preparar sustentación', 'Revisar la entrega TurnoClaro vinculada y su resultado.', 'activity_completion', '{"status": "completed"}', NULL, '2026-11-22 22:00:00+00', 'pending', 'manual', '{"origin": "manual_demo", "evidence": "Actividad del semestre ficticio TurnoClaro."}', '2026-11-16 03:25:45.441417+00', '2026-11-16 03:25:45.441417+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (28, 36, 26, 25, 51, 53, 'Completar Requisitos', 'Finalizar la entrega de requisitos de software.', 'activity_completion', '{"status": "completed"}', '2026-10-11 00:00:00+00', '2026-11-16 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Req. de Software: estado active; dificultad hard.", "Actividad S6 Entrega de requisitos: estado pending; prioridad high; fecha límite 2026-11-16T18:00:00+00:00.", "Sesión 53: 10 minutos planificados, 10.00387195 minutos contabilizados como estudio; resultado completed, 0 pausas."], "explanation": "Reto enfocado en la materia de Req. de Software dada su dificultad y actividad pendiente.", "measurable_condition": "Completar la actividad S6 Entrega de requisitos."}', '2026-11-17 02:15:12.760952+00', '2026-11-17 02:15:12.760952+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (32, 36, 31, 25, 51, 53, 'Completar entrega de requisitos', 'Finalizar la actividad de requisitos de software con éxito.', 'activity_completion', '{"status": "completed"}', '2026-11-16 09:00:00+00', '2026-11-16 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Req. de Software: estado active; dificultad hard.", "Actividad S6 Entrega de requisitos: estado pending; prioridad high; fecha límite 2026-11-16T18:00:00+00:00.", "Sesión 53: 10 minutos planificados, 10.00387195 minutos contabilizados como estudio; resultado completed, 0 pausas."], "explanation": "Es necesario completar la actividad pendiente para mantener el ritmo académico.", "measurable_condition": "Completar la actividad de requisitos de software"}', '2026-11-18 18:42:05.279519+00', '2026-11-18 18:42:05.279519+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (33, 36, 31, 27, 53, 59, 'Entrega de persistencia', 'Asegurar la entrega de la persistencia en bases de datos.', 'activity_completion', '{"status": "completed"}', '2026-11-17 14:00:00+00', '2026-11-18 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Bases de Datos: estado active; dificultad medium.", "Actividad S6 Entrega de persistencia: estado pending; prioridad medium; fecha límite 2026-11-18T18:00:00+00:00.", "Sesión 59: 10 minutos planificados, 1.0020768833333333 minutos contabilizados como estudio; resultado partial, 0 pausas."], "explanation": "Se requiere culminar la actividad vinculada para asegurar el dominio de bases de datos.", "measurable_condition": "Finalizar la actividad de persistencia"}', '2026-11-18 18:42:05.279519+00', '2026-11-18 18:42:05.279519+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (34, 36, 32, 25, 51, 53, 'Completar entrega de requisitos', 'Finalizar la actividad de requisitos de software con éxito.', 'activity_completion', '{"status": "completed"}', '2026-10-10 00:00:00+00', '2026-11-16 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Req. de Software: estado active; dificultad hard.", "Actividad S6 Entrega de requisitos: estado pending; prioridad high; fecha límite 2026-11-16T18:00:00+00:00.", "Sesión 53: 10 minutos planificados, 10.00387195 minutos contabilizados como estudio; resultado completed, 0 pausas."], "explanation": "Se requiere concluir la actividad pendiente para mantener el flujo de entrega.", "measurable_condition": "La actividad debe quedar en estado completado."}', '2026-11-18 18:42:13.13463+00', '2026-11-18 18:42:13.13463+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (35, 36, 32, 26, 52, 54, 'Integración de módulos SW', 'Avanzar en la integración de módulos de arquitectura.', 'session_completion', '{"lifecycle": "finished"}', '2026-10-10 00:00:00+00', '2026-11-17 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Arquitectura SW: estado active; dificultad hard.", "Actividad S6 Integración de módulos: estado pending; prioridad low; fecha límite 2026-11-17T18:00:00+00:00.", "Sesión 54: 10 minutos planificados, 1.0023464833333333 minutos contabilizados como estudio; resultado partial, 1 pausas."], "explanation": "Es necesario superar las sesiones parciales registradas en esta materia.", "measurable_condition": "La sesión vinculada debe finalizar correctamente."}', '2026-11-18 18:42:13.13463+00', '2026-11-18 18:42:13.13463+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (36, 36, 32, 27, 53, 59, 'Entrega de persistencia BD', 'Completar la persistencia en bases de datos.', 'activity_completion', '{"status": "completed"}', '2026-10-10 00:00:00+00', '2026-11-18 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Bases de Datos: estado active; dificultad medium.", "Actividad S6 Entrega de persistencia: estado pending; prioridad medium; fecha límite 2026-11-18T18:00:00+00:00.", "Sesión 59: 10 minutos planificados, 1.0020768833333333 minutos contabilizados como estudio; resultado partial, 0 pausas."], "explanation": "Se observaron sesiones canceladas o parciales que requieren refuerzo.", "measurable_condition": "La actividad de persistencia debe estar completada."}', '2026-11-18 18:42:13.13463+00', '2026-11-18 18:42:13.13463+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (37, 36, 32, 28, 54, 56, 'Informe de calidad', 'Finalizar el reporte de calidad y pruebas.', 'activity_completion', '{"status": "completed"}', '2026-10-10 00:00:00+00', '2026-11-19 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Calidad y Pruebas: estado active; dificultad medium.", "Actividad S6 Informe de calidad: estado pending; prioridad high; fecha límite 2026-11-19T18:00:00+00:00.", "Sesión 56: 10 minutos planificados, 1.0020840333333334 minutos contabilizados como estudio; resultado partial, 0 pausas."], "explanation": "Ayuda a mitigar los problemas de consistencia en el estudio.", "measurable_condition": "El informe de calidad debe marcarse como completado."}', '2026-11-18 18:42:13.13463+00', '2026-11-18 18:42:13.13463+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (38, 36, 32, 29, 55, 57, 'Preparación de entrega ágil', 'Concluir la preparación de la entrega en gestión ágil.', 'activity_completion', '{"status": "completed"}', '2026-10-10 00:00:00+00', '2026-11-20 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Gestión Ágil: estado active; dificultad easy.", "Actividad S6 Preparación de entrega: estado pending; prioridad low; fecha límite 2026-11-20T18:00:00+00:00.", "Sesión 57: 10 minutos planificados, 1.0018768166666667 minutos contabilizados como estudio; resultado partial, 0 pausas."], "explanation": "Permite mantener el ritmo adecuado frente al volumen de actividades.", "measurable_condition": "La actividad de preparación debe registrar estado completado."}', '2026-11-18 18:42:13.13463+00', '2026-11-18 18:42:13.13463+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (73, 36, 71, 25, 51, 53, 'Desafío Requisitos', 'Completar la actividad de requisitos de software', 'activity_completion', '{"status": "completed"}', '2026-11-16 09:00:00+00', '2026-11-16 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Req. de Software: estado active; dificultad hard.", "Actividad S6 Entrega de requisitos: estado pending; prioridad high; fecha límite 2026-11-16T18:00:00+00:00.", "Sesión 53: 10 minutos planificados, 10.00387195 minutos contabilizados como estudio; resultado completed, 0 pausas."], "explanation": "Es necesario asegurar la entrega a tiempo de la actividad para mantener el progreso en la materia de alta dificultad.", "measurable_condition": "La actividad debe marcarse como completada."}', '2026-11-19 03:27:43.349825+00', '2026-11-19 03:27:43.349825+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (74, 36, 71, 26, 52, 54, 'Desafío Arquitectura', 'Finalizar la sesión de integración de módulos', 'session_completion', '{"lifecycle": "finished"}', '2026-11-16 10:00:00+00', '2026-11-17 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Arquitectura SW: estado active; dificultad hard.", "Actividad S6 Integración de módulos: estado pending; prioridad low; fecha límite 2026-11-17T18:00:00+00:00.", "Sesión 54: 10 minutos planificados, 1.0023464833333333 minutos contabilizados como estudio; resultado partial, 1 pausas."], "explanation": "Se requiere mantener la consistencia en las sesiones de arquitectura de software.", "measurable_condition": "La sesión debe finalizarse con éxito."}', '2026-11-19 03:27:43.349825+00', '2026-11-19 03:27:43.349825+00');
INSERT INTO public.study_challenges (id, user_id, plan_id, subject_id, activity_id, study_session_id, title, description, target_type, target_value, start_at, deadline, status, source, generation_criteria, created_at, updated_at) VALUES (75, 36, 71, 27, 53, 59, 'Desafío Bases de Datos', 'Completar la entrega de persistencia', 'activity_completion', '{"status": "completed"}', '2026-11-17 14:00:00+00', '2026-11-18 18:00:00+00', 'pending', 'ai', '{"evidence": ["Materia Bases de Datos: estado active; dificultad medium.", "Actividad S6 Entrega de persistencia: estado pending; prioridad medium; fecha límite 2026-11-18T18:00:00+00:00.", "Sesión 59: 10 minutos planificados, 1.0020768833333333 minutos contabilizados como estudio; resultado partial, 0 pausas."], "explanation": "La consistencia y el avance en bases de datos son prioritarios para evitar retrasos.", "measurable_condition": "La actividad debe quedar completada."}', '2026-11-19 03:27:43.349825+00', '2026-11-19 03:27:43.349825+00');


--
-- Data for Name: study_plan_decisions; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_plan_decisions (id, user_id, plan_id, action, field_path, proposed_value, chosen_value, created_at) VALUES (9, 36, 25, 'edited', 'name', '"TurnoClaro · Ruta del semestre"', '"TurnoClaro · Ruta revisada"', '2026-11-16 03:25:45.015103+00');
INSERT INTO public.study_plan_decisions (id, user_id, plan_id, action, field_path, proposed_value, chosen_value, created_at) VALUES (10, 36, 26, 'edited', 'name', '"Propuesta de Plan Académico"', '"TurnoClaro · Propuesta elegida"', '2026-11-17 02:15:12.870972+00');
INSERT INTO public.study_plan_decisions (id, user_id, plan_id, action, field_path, proposed_value, chosen_value, created_at) VALUES (11, 36, 26, 'accepted', NULL, '{"plan": {"name": "Propuesta de Plan Académico", "end_date": "2026-11-25T23:00:00Z", "objective": "Optimizar el rendimiento en las materias activas y mantener la consistencia en el estudio diario.", "start_date": "2026-10-10T00:00:00Z", "session_ids": [53, 54, 55, 56, 57, 59], "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 52, 53, 54, 55]}, "model": "gemini-3.5-flash-lite", "explanation": "Plan estructurado para equilibrar la carga de actividades pendientes y mejorar la consistencia según el análisis de sesiones previas.", "generated_at": "2026-11-17T02:15:12.757034Z", "schema_version": 1, "reasoning_summary": "Se priorizan materias activas y se establecen metas acordes a las actividades pendientes y sesiones registradas.", "proposed_challenges": [{"title": "Completar Requisitos", "end_date": "2026-11-16T18:00:00Z", "evidence": ["subject:25", "activity:51", "session:53"], "objective": "Finalizar la entrega de requisitos de software.", "target_id": null, "session_id": 53, "start_date": "2026-10-11T00:00:00Z", "subject_id": 25, "activity_id": 51, "explanation": "Reto enfocado en la materia de Req. de Software dada su dificultad y actividad pendiente.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "Completar la actividad S6 Entrega de requisitos."}]}', '{"name": "TurnoClaro · Propuesta elegida", "end_at": "2026-11-25T23:00:00+00:00", "start_at": "2026-10-10T00:00:00+00:00", "objective": "Optimizar el rendimiento en las materias activas y mantener la consistencia en el estudio diario.", "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 52, 53, 54, 55], "study_session_ids": [53, 54, 55, 56, 57, 59]}', '2026-11-17 02:15:12.914615+00');
INSERT INTO public.study_plan_decisions (id, user_id, plan_id, action, field_path, proposed_value, chosen_value, created_at) VALUES (12, 36, 71, 'accepted', NULL, '{"plan": {"name": "Plan de Refuerzo Académico", "end_date": "2026-11-25T23:00:00Z", "objective": "Consolidar las entregas pendientes y mejorar la consistencia en el estudio diario de las materias activas.", "start_date": "2026-10-10T00:00:00Z", "session_ids": [53, 54, 56, 57, 59], "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 52, 53, 54, 55]}, "model": "gemini-3.5-flash-lite", "explanation": "Se propone una ruta centrada en completar actividades clave y mantener el hábito de estudio diario para mitigar la acumulación de tareas.", "generated_at": "2026-11-19T03:27:43.347096Z", "schema_version": 1, "reasoning_summary": "El plan se basa en el análisis de las materias activas con mayor carga pendiente y en la necesidad de mejorar la consistencia según los datos de sesiones anteriores.", "proposed_challenges": [{"title": "Desafío Requisitos", "end_date": "2026-11-16T18:00:00Z", "evidence": ["subject:25", "activity:51", "session:53"], "objective": "Completar la actividad de requisitos de software", "target_id": null, "session_id": 53, "start_date": "2026-11-16T09:00:00Z", "subject_id": 25, "activity_id": 51, "explanation": "Es necesario asegurar la entrega a tiempo de la actividad para mantener el progreso en la materia de alta dificultad.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "La actividad debe marcarse como completada."}, {"title": "Desafío Arquitectura", "end_date": "2026-11-17T18:00:00Z", "evidence": ["subject:26", "activity:52", "session:54"], "objective": "Finalizar la sesión de integración de módulos", "target_id": null, "session_id": 54, "start_date": "2026-11-16T10:00:00Z", "subject_id": 26, "activity_id": 52, "explanation": "Se requiere mantener la consistencia en las sesiones de arquitectura de software.", "target_type": "session_completion", "target_value": {"lifecycle": "finished"}, "measurable_condition": "La sesión debe finalizarse con éxito."}, {"title": "Desafío Bases de Datos", "end_date": "2026-11-18T18:00:00Z", "evidence": ["subject:27", "activity:53", "session:59"], "objective": "Completar la entrega de persistencia", "target_id": null, "session_id": 59, "start_date": "2026-11-17T14:00:00Z", "subject_id": 27, "activity_id": 53, "explanation": "La consistencia y el avance en bases de datos son prioritarios para evitar retrasos.", "target_type": "activity_completion", "target_value": {"status": "completed"}, "measurable_condition": "La actividad debe quedar completada."}]}', '{"name": "Plan de Refuerzo Académico", "end_at": "2026-11-25T23:00:00+00:00", "start_at": "2026-10-10T00:00:00+00:00", "objective": "Consolidar las entregas pendientes y mejorar la consistencia en el estudio diario de las materias activas.", "subject_ids": [25, 26, 27, 28, 29], "activity_ids": [51, 52, 53, 54, 55], "study_session_ids": [53, 54, 56, 57, 59]}', '2026-11-19 03:27:57.590509+00');


--
-- Data for Name: study_session_intervals; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.study_session_intervals (id, session_id, started_at, ended_at, created_at, updated_at) VALUES (37, 53, '2026-11-16 03:25:55.825315+00', '2026-11-16 03:35:56.057632+00', '2026-11-16 03:25:55.827507+00', '2026-11-16 03:35:56.060141+00');
INSERT INTO public.study_session_intervals (id, session_id, started_at, ended_at, created_at, updated_at) VALUES (38, 54, '2026-11-16 03:35:56.094418+00', '2026-11-16 03:36:56.21874+00', '2026-11-16 03:35:56.097517+00', '2026-11-16 03:36:56.219717+00');
INSERT INTO public.study_session_intervals (id, session_id, started_at, ended_at, created_at, updated_at) VALUES (39, 54, '2026-11-16 03:36:56.250363+00', '2026-11-16 03:36:56.26683+00', '2026-11-16 03:36:56.252373+00', '2026-11-16 03:36:56.267884+00');
INSERT INTO public.study_session_intervals (id, session_id, started_at, ended_at, created_at, updated_at) VALUES (40, 55, '2026-11-16 03:36:56.294012+00', '2026-11-16 16:17:58.716584+00', '2026-11-16 03:36:56.29486+00', '2026-11-16 16:17:58.742681+00');
INSERT INTO public.study_session_intervals (id, session_id, started_at, ended_at, created_at, updated_at) VALUES (41, 59, '2026-11-16 16:18:15.240048+00', '2026-11-16 16:19:15.364661+00', '2026-11-16 16:18:15.246271+00', '2026-11-16 16:19:15.366284+00');
INSERT INTO public.study_session_intervals (id, session_id, started_at, ended_at, created_at, updated_at) VALUES (42, 56, '2026-11-16 16:19:15.453167+00', '2026-11-16 16:20:15.578209+00', '2026-11-16 16:19:15.455071+00', '2026-11-16 16:20:15.57862+00');
INSERT INTO public.study_session_intervals (id, session_id, started_at, ended_at, created_at, updated_at) VALUES (43, 57, '2026-11-16 16:20:15.637207+00', '2026-11-16 16:21:15.749816+00', '2026-11-16 16:20:15.638316+00', '2026-11-16 16:21:15.750238+00');


--
-- Data for Name: user_academic_goal_legacy; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Name: academic_conversations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.academic_conversations_id_seq', 1, false);


--
-- Name: academic_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.academic_messages_id_seq', 1, false);


--
-- Name: activities_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.activities_id_seq', 55, true);


--
-- Name: study_challenges_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.study_challenges_id_seq', 75, true);


--
-- Name: study_plan_decisions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.study_plan_decisions_id_seq', 12, true);


--
-- Name: study_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.study_plans_id_seq', 71, true);


--
-- Name: study_session_intervals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.study_session_intervals_id_seq', 43, true);


--
-- Name: study_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.study_sessions_id_seq', 59, true);


--
-- Name: subjects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.subjects_id_seq', 29, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 36, true);


--
-- PostgreSQL database dump complete
--
