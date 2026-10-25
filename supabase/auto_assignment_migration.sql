-- JrAdemy auto-assignment settings and batch capacity.
-- Apply only after schema.sql and the other required migrations.
alter table public.batches add column if not exists capacity integer not null default 20 check (capacity > 0);

create table if not exists public.auto_assignment_settings (
  id integer primary key check (id = 1),
  enabled boolean not null default true,
  auto_enroll_single_match boolean not null default false,
  require_approval boolean not null default true,
  match_board boolean not null default true,
  match_grade boolean not null default true,
  match_subject boolean not null default true,
  check_capacity boolean not null default true,
  check_schedule_conflicts boolean not null default true,
  default_capacity integer not null default 20 check (default_capacity > 0),
  updated_by uuid references auth.users(id) on delete set null,
  updated_at timestamptz not null default now()
);

alter table public.auto_assignment_settings enable row level security;
drop policy if exists "Admins manage auto assignment settings" on public.auto_assignment_settings;
create policy "Admins manage auto assignment settings"
on public.auto_assignment_settings
for all to authenticated
using (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'))
with check (exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin'));

insert into public.auto_assignment_settings (id)
values (1)
on conflict (id) do nothing;
