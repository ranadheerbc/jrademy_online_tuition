-- JrAdemy Online Tuition schema for Supabase PostgreSQL.
-- Run in Supabase SQL Editor. Review the RLS policies before production.
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique,
  full_name text,
  role text not null default 'student' check (role in ('admin','tutor','parent','student')),
  board text check (board in ('CBSE','ICSE','Karnataka State Board')),
  grade int check (grade between 1 and 10),
  created_at timestamptz not null default now()
);

create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  student_name text not null,
  grade int not null check (grade between 1 and 10),
  board text not null check (board in ('CBSE','ICSE','Karnataka State Board')),
  guardian_name text not null,
  guardian_email text,
  guardian_phone text,
  status text not null default 'active' check (status in ('active','trial','paused','completed')),
  created_at timestamptz not null default now()
);

create table if not exists public.batches (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  grade int not null check (grade between 1 and 10),
  board text not null check (board in ('CBSE','ICSE','Karnataka State Board')),
  subject text not null,
  schedule_text text,
  tutor_email text,
  start_date date,
  status text not null default 'active',
  created_at timestamptz not null default now()
);

create table if not exists public.attendance (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  batch_id uuid not null references public.batches(id) on delete cascade,
  attendance_date date not null default current_date,
  status text not null check (status in ('present','absent','late','excused')),
  notes text,
  created_at timestamptz not null default now(),
  unique(student_id, batch_id, attendance_date)
);

create table if not exists public.fee_records (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  amount_due numeric(12,2) not null check (amount_due >= 0),
  due_date date not null,
  fee_period text,
  status text not null default 'due' check (status in ('due','partially_paid','paid','waived')),
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  fee_record_id uuid not null references public.fee_records(id) on delete cascade,
  amount numeric(12,2) not null check (amount > 0),
  paid_on date not null default current_date,
  method text not null,
  reference text,
  created_at timestamptz not null default now()
);

create table if not exists public.assignments (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  grade int not null check (grade between 1 and 10),
  board text not null check (board in ('CBSE','ICSE','Karnataka State Board')),
  subject text not null,
  due_date date not null,
  instructions text,
  status text not null default 'draft',
  created_at timestamptz not null default now()
);

create table if not exists public.assessment_scores (
  id uuid primary key default gen_random_uuid(),
  student_id uuid references public.students(id) on delete cascade,
  assignment_id uuid references public.assignments(id) on delete set null,
  subject text not null,
  score numeric(7,2) not null check (score >= 0),
  max_score numeric(7,2) not null check (max_score > 0),
  feedback text,
  assessed_at timestamptz not null default now(),
  check (score <= max_score)
);

-- Create a profile row after each new Auth registration.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
begin
  insert into public.profiles (id, email, full_name, role)
  values (new.id, new.email, coalesce(new.raw_user_meta_data ->> 'full_name',''), 'student')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

create or replace function public.current_role()
returns text
language sql stable security definer
set search_path = ''
as $$
  select role from public.profiles where id = auth.uid()
$$;

alter table public.profiles enable row level security;
alter table public.students enable row level security;
alter table public.batches enable row level security;
alter table public.attendance enable row level security;
alter table public.fee_records enable row level security;
alter table public.payments enable row level security;
alter table public.assignments enable row level security;
alter table public.assessment_scores enable row level security;

-- Profiles: users can read their own profile; admins can read/update all.
drop policy if exists "profiles_select_own_or_admin" on public.profiles;
create policy "profiles_select_own_or_admin" on public.profiles
for select to authenticated using (id = auth.uid() or public.current_role() = 'admin');
drop policy if exists "profiles_update_admin" on public.profiles;
create policy "profiles_update_admin" on public.profiles
for update to authenticated using (public.current_role() = 'admin') with check (public.current_role() = 'admin');

-- Admin/tutor access for operational records. Parent/student self-service linkage is a later step:
-- add a student_id/profile_id relationship before granting row-specific access to minors.
do $$
declare t text;
begin
  foreach t in array array['students','batches','attendance','assignments','assessment_scores'] loop
    execute format('drop policy if exists %I on public.%I', t || '_staff_all', t);
    execute format('create policy %I on public.%I for all to authenticated using (public.current_role() in (''admin'',''tutor'')) with check (public.current_role() in (''admin'',''tutor''))', t || '_staff_all', t);
  end loop;
  foreach t in array array['fee_records','payments'] loop
    execute format('drop policy if exists %I on public.%I', t || '_admin_all', t);
    execute format('create policy %I on public.%I for all to authenticated using (public.current_role() = ''admin'') with check (public.current_role() = ''admin'')', t || '_admin_all', t);
  end loop;
end $$;

-- No anonymous access policies are created. Do not use the service-role key in Streamlit.
-- Before launch: add explicit parent/student linkage, least-privilege policies, audit logs,
-- backups, retention rules, and a privacy notice/guardian-consent workflow.
