-- JrAdemy admin cleanup tools.
-- Prerequisites: schema.sql, online_classes_migration.sql, and student_portal_migration.sql
-- have been applied successfully. This migration does not delete Auth users or profiles.

create table if not exists public.admin_cleanup_audit (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  actor_id uuid,
  action text not null,
  scope text not null,
  details jsonb not null default '{}'::jsonb
);

alter table public.admin_cleanup_audit enable row level security;
drop policy if exists admin_cleanup_audit_admin_read on public.admin_cleanup_audit;
create policy admin_cleanup_audit_admin_read on public.admin_cleanup_audit
for select to authenticated using (public.current_role() = 'admin');

create or replace function public.admin_clear_student_activity(target_student_ids uuid[])
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_attendance integer := 0;
  v_payments integer := 0;
  v_fees integer := 0;
  v_scores integer := 0;
  v_submissions integer := 0;
  v_enrollments integer := 0;
  v_ids uuid[];
  v_details jsonb;
begin
  if auth.uid() is null or public.current_role() <> 'admin' then
    raise exception 'Admin role required';
  end if;
  if target_student_ids is null or cardinality(target_student_ids) = 0 then
    raise exception 'Select at least one student';
  end if;
  select array_agg(distinct s.id) into v_ids
  from public.students s where s.id = any(target_student_ids);
  if v_ids is null or cardinality(v_ids) = 0 then
    raise exception 'No matching student records found';
  end if;

  delete from public.attendance where student_id = any(v_ids);
  get diagnostics v_attendance = row_count;

  delete from public.payments p using public.fee_records f
  where p.fee_record_id = f.id and f.student_id = any(v_ids);
  get diagnostics v_payments = row_count;

  delete from public.fee_records where student_id = any(v_ids);
  get diagnostics v_fees = row_count;

  delete from public.assessment_scores where student_id = any(v_ids);
  get diagnostics v_scores = row_count;

  delete from public.assignment_submissions where student_id = any(v_ids);
  get diagnostics v_submissions = row_count;

  delete from public.batch_enrollments where student_id = any(v_ids);
  get diagnostics v_enrollments = row_count;

  v_details := jsonb_build_object(
    'student_ids', to_jsonb(v_ids), 'students_preserved', cardinality(v_ids),
    'attendance_deleted', v_attendance, 'payments_deleted', v_payments,
    'fee_records_deleted', v_fees, 'assessment_scores_deleted', v_scores,
    'assignment_submissions_deleted', v_submissions, 'batch_enrollments_deleted', v_enrollments
  );
  insert into public.admin_cleanup_audit(actor_id, action, scope, details)
  values (auth.uid(), 'clear_student_activity', 'selected_students', v_details);
  return v_details;
end;
$$;

create or replace function public.admin_delete_students(target_student_ids uuid[])
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_ids uuid[];
  v_deleted integer := 0;
  v_details jsonb;
begin
  if auth.uid() is null or public.current_role() <> 'admin' then
    raise exception 'Admin role required';
  end if;
  if target_student_ids is null or cardinality(target_student_ids) = 0 then
    raise exception 'Select at least one student';
  end if;
  select array_agg(distinct s.id) into v_ids
  from public.students s where s.id = any(target_student_ids);
  if v_ids is null or cardinality(v_ids) = 0 then
    raise exception 'No matching student records found';
  end if;
  delete from public.students where id = any(v_ids);
  get diagnostics v_deleted = row_count;
  v_details := jsonb_build_object('requested_ids', to_jsonb(v_ids), 'students_deleted', v_deleted,
    'note', 'Related records with ON DELETE CASCADE were removed by the database. Auth users/profiles were not deleted.');
  insert into public.admin_cleanup_audit(actor_id, action, scope, details)
  values (auth.uid(), 'delete_students', 'selected_students', v_details);
  return v_details;
end;
$$;

create or replace function public.admin_reset_academy_data()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  n_payments integer := 0;
  n_fees integer := 0;
  n_attendance integer := 0;
  n_scores integer := 0;
  n_submissions integer := 0;
  n_enrollments integer := 0;
  n_meetings integer := 0;
  n_assignments integer := 0;
  n_students integer := 0;
  n_batches integer := 0;
  v_details jsonb;
begin
  if auth.uid() is null or public.current_role() <> 'admin' then
    raise exception 'Admin role required';
  end if;

  delete from public.payments;
  get diagnostics n_payments = row_count;
  delete from public.fee_records;
  get diagnostics n_fees = row_count;
  delete from public.attendance;
  get diagnostics n_attendance = row_count;
  delete from public.assessment_scores;
  get diagnostics n_scores = row_count;
  delete from public.assignment_submissions;
  get diagnostics n_submissions = row_count;
  delete from public.batch_enrollments;
  get diagnostics n_enrollments = row_count;
  delete from public.class_meetings;
  get diagnostics n_meetings = row_count;
  delete from public.assignments;
  get diagnostics n_assignments = row_count;
  delete from public.students;
  get diagnostics n_students = row_count;
  delete from public.batches;
  get diagnostics n_batches = row_count;

  v_details := jsonb_build_object(
    'payments_deleted', n_payments, 'fee_records_deleted', n_fees,
    'attendance_deleted', n_attendance, 'assessment_scores_deleted', n_scores,
    'assignment_submissions_deleted', n_submissions, 'batch_enrollments_deleted', n_enrollments,
    'class_meetings_deleted', n_meetings, 'assignments_deleted', n_assignments,
    'students_deleted', n_students, 'batches_deleted', n_batches,
    'profiles_preserved', true, 'auth_users_preserved', true, 'schema_preserved', true
  );
  insert into public.admin_cleanup_audit(actor_id, action, scope, details)
  values (auth.uid(), 'reset_academy_data', 'all_operational_data', v_details);
  return v_details;
end;
$$;

revoke all on function public.admin_clear_student_activity(uuid[]) from public, anon;
revoke all on function public.admin_delete_students(uuid[]) from public, anon;
revoke all on function public.admin_reset_academy_data() from public, anon;
grant execute on function public.admin_clear_student_activity(uuid[]) to authenticated;
grant execute on function public.admin_delete_students(uuid[]) to authenticated;
grant execute on function public.admin_reset_academy_data() to authenticated;
grant select on public.admin_cleanup_audit to authenticated;
