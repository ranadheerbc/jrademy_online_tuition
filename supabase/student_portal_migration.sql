-- JrAdemy student mapping and student-facing portal data.
-- Run AFTER schema.sql and online_classes_migration.sql.
-- Review the policies and test with separate admin, student and parent accounts before production.

create extension if not exists pgcrypto;

-- Human-friendly student ID. UUIDs remain internal database keys and should not be shown as student IDs.
create sequence if not exists public.student_code_seq start 1001;
alter table public.students add column if not exists student_code text;
alter table public.students add column if not exists linked_profile_id uuid references public.profiles(id) on delete set null;
alter table public.students add column if not exists guardian_profile_id uuid references public.profiles(id) on delete set null;

update public.students
set student_code = 'JRA-' || to_char(coalesce(created_at::date, current_date), 'YYYY') || '-' || lpad(nextval('public.student_code_seq')::text, 5, '0')
where student_code is null;

create unique index if not exists students_student_code_uq on public.students(student_code);
create unique index if not exists students_linked_profile_uq on public.students(linked_profile_id) where linked_profile_id is not null;
create index if not exists students_guardian_profile_idx on public.students(guardian_profile_id) where guardian_profile_id is not null;

create or replace function public.set_student_code()
returns trigger language plpgsql set search_path = '' as $$
begin
  if new.student_code is null or btrim(new.student_code) = '' then
    new.student_code := 'JRA-' || to_char(current_date, 'YYYY') || '-' || lpad(nextval('public.student_code_seq')::text, 5, '0');
  end if;
  return new;
end;
$$;
drop trigger if exists students_set_student_code on public.students;
create trigger students_set_student_code before insert on public.students
for each row execute function public.set_student_code();

create table if not exists public.batch_enrollments (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students(id) on delete cascade,
  batch_id uuid not null references public.batches(id) on delete cascade,
  enrolled_at timestamptz not null default now(),
  status text not null default 'active' check (status in ('active','paused','completed')),
  unique(student_id, batch_id)
);
create index if not exists batch_enrollments_batch_idx on public.batch_enrollments(batch_id);

alter table public.assignments add column if not exists batch_id uuid references public.batches(id) on delete set null;

create table if not exists public.assignment_submissions (
  id uuid primary key default gen_random_uuid(),
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  student_id uuid not null references public.students(id) on delete cascade,
  answer_text text,
  submitted_at timestamptz not null default now(),
  status text not null default 'submitted' check (status in ('submitted','late','reviewed','resubmit')),
  tutor_feedback text,
  unique(assignment_id, student_id)
);
create index if not exists assignment_submissions_student_idx on public.assignment_submissions(student_id, submitted_at desc);

-- Security-definer helpers avoid recursive RLS checks against public.students.
create or replace function public.is_linked_student(target_student_id uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.students s
    where s.id = target_student_id
      and (s.linked_profile_id = auth.uid() or s.guardian_profile_id = auth.uid())
  );
$$;
create or replace function public.is_enrolled_in_batch(target_batch_id uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.batch_enrollments e
    join public.students s on s.id = e.student_id
    where e.batch_id = target_batch_id and e.status = 'active'
      and (s.linked_profile_id = auth.uid() or s.guardian_profile_id = auth.uid())
  );
$$;
grant execute on function public.is_linked_student(uuid) to authenticated;
grant execute on function public.is_enrolled_in_batch(uuid) to authenticated;

alter table public.students enable row level security;
alter table public.batch_enrollments enable row level security;
alter table public.class_meetings enable row level security;
alter table public.assignments enable row level security;
alter table public.assignment_submissions enable row level security;
alter table public.assessment_scores enable row level security;
alter table public.attendance enable row level security;
alter table public.fee_records enable row level security;
alter table public.payments enable row level security;

-- Students: staff manage; linked student/guardian may read only their own record.
drop policy if exists students_staff_all on public.students;
create policy students_staff_all on public.students for all to authenticated
using (public.current_role() in ('admin','tutor')) with check (public.current_role() in ('admin','tutor'));
drop policy if exists students_linked_read on public.students;
create policy students_linked_read on public.students for select to authenticated
using (linked_profile_id = auth.uid() or guardian_profile_id = auth.uid());

-- Batch enrollment: staff manage; linked users see only their own enrollments.
drop policy if exists batch_enrollments_staff_all on public.batch_enrollments;
create policy batch_enrollments_staff_all on public.batch_enrollments for all to authenticated
using (public.current_role() in ('admin','tutor')) with check (public.current_role() in ('admin','tutor'));
drop policy if exists batch_enrollments_linked_read on public.batch_enrollments;
create policy batch_enrollments_linked_read on public.batch_enrollments for select to authenticated
using (public.is_linked_student(student_id));

-- Meetings: staff manage; students/parents can read scheduled or completed meetings for enrolled batches.
drop policy if exists class_meetings_staff_all on public.class_meetings;
create policy class_meetings_staff_all on public.class_meetings for all to authenticated
using (public.current_role() in ('admin','tutor')) with check (public.current_role() in ('admin','tutor'));
drop policy if exists class_meetings_enrolled_read on public.class_meetings;
create policy class_meetings_enrolled_read on public.class_meetings for select to authenticated
using (public.is_enrolled_in_batch(batch_id) and status <> 'cancelled');

-- Assignments: staff manage; students see published assignments matching their board/grade and, when set, batch enrollment.
drop policy if exists assignments_staff_all on public.assignments;
create policy assignments_staff_all on public.assignments for all to authenticated
using (public.current_role() in ('admin','tutor')) with check (public.current_role() in ('admin','tutor'));
drop policy if exists assignments_linked_read on public.assignments;
create policy assignments_linked_read on public.assignments for select to authenticated
using (
  status = 'published' and exists (
    select 1 from public.students s
    where (s.linked_profile_id = auth.uid() or s.guardian_profile_id = auth.uid())
      and s.grade = assignments.grade and s.board = assignments.board
      and (assignments.batch_id is null or public.is_enrolled_in_batch(assignments.batch_id))
  )
);

-- Submissions: linked users can submit/read their own work; staff can review all submissions.
drop policy if exists assignment_submissions_staff_all on public.assignment_submissions;
create policy assignment_submissions_staff_all on public.assignment_submissions for all to authenticated
using (public.current_role() in ('admin','tutor')) with check (public.current_role() in ('admin','tutor'));
drop policy if exists assignment_submissions_linked_read on public.assignment_submissions;
create policy assignment_submissions_linked_read on public.assignment_submissions for select to authenticated
using (public.is_linked_student(student_id));
drop policy if exists assignment_submissions_linked_insert on public.assignment_submissions;
create policy assignment_submissions_linked_insert on public.assignment_submissions for insert to authenticated
with check (public.is_linked_student(student_id) and exists (select 1 from public.assignments a where a.id = assignment_id and a.status = 'published'));
drop policy if exists assignment_submissions_linked_update on public.assignment_submissions;
create policy assignment_submissions_linked_update on public.assignment_submissions for update to authenticated
using (public.is_linked_student(student_id) and status in ('submitted','late','resubmit'))
with check (public.is_linked_student(student_id) and status in ('submitted','late','resubmit'));

-- Assessment scores: staff manage; student/guardian can see linked learner's results.
drop policy if exists assessment_scores_staff_all on public.assessment_scores;
create policy assessment_scores_staff_all on public.assessment_scores for all to authenticated
using (public.current_role() in ('admin','tutor')) with check (public.current_role() in ('admin','tutor'));
drop policy if exists assessment_scores_linked_read on public.assessment_scores;
create policy assessment_scores_linked_read on public.assessment_scores for select to authenticated
using (student_id is not null and public.is_linked_student(student_id));

-- Attendance: staff manage; linked student/guardian can read their own attendance.
drop policy if exists attendance_staff_all on public.attendance;
create policy attendance_staff_all on public.attendance for all to authenticated
using (public.current_role() in ('admin','tutor')) with check (public.current_role() in ('admin','tutor'));
drop policy if exists attendance_linked_read on public.attendance;
create policy attendance_linked_read on public.attendance for select to authenticated
using (public.is_linked_student(student_id));

-- Fees/payments: admin manage; linked student/guardian can read only linked fee/payment records.
drop policy if exists fee_records_admin_all on public.fee_records;
create policy fee_records_admin_all on public.fee_records for all to authenticated
using (public.current_role() = 'admin') with check (public.current_role() = 'admin');
drop policy if exists fee_records_linked_read on public.fee_records;
create policy fee_records_linked_read on public.fee_records for select to authenticated
using (public.is_linked_student(student_id));
drop policy if exists payments_admin_all on public.payments;
create policy payments_admin_all on public.payments for all to authenticated
using (public.current_role() = 'admin') with check (public.current_role() = 'admin');
drop policy if exists payments_linked_read on public.payments;
create policy payments_linked_read on public.payments for select to authenticated
using (exists (select 1 from public.fee_records f where f.id = fee_record_id and public.is_linked_student(f.student_id)));

-- Profiles: a user can read their own profile, admins already have the base policy.
-- This migration intentionally does not grant client-side Auth account creation or password visibility.
