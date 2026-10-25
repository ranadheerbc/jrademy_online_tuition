-- JrAdemy Online Classes migration.
-- Run in Supabase SQL Editor after the base schema is installed.
-- Meeting links are initially staff-only. Do not expose links to all students
-- until student-to-batch enrollment relationships and row-specific RLS are added.

create table if not exists public.class_meetings (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  batch_id uuid not null references public.batches(id) on delete cascade,
  meeting_date date not null,
  start_time time not null,
  end_time time not null,
  platform text not null default 'Google Meet',
  meeting_url text not null,
  notes text,
  status text not null default 'scheduled'
    check (status in ('scheduled','completed','cancelled')),
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  constraint class_meetings_valid_time check (end_time > start_time)
);

alter table public.class_meetings enable row level security;

drop policy if exists class_meetings_staff_all on public.class_meetings;
create policy class_meetings_staff_all
on public.class_meetings
for all to authenticated
using (public.current_role() in ('admin','tutor'))
with check (public.current_role() in ('admin','tutor'));

create index if not exists class_meetings_batch_date_idx
on public.class_meetings(batch_id, meeting_date, start_time);
