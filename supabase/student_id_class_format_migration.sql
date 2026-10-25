-- JrAdemy student ID format update
-- New format: JRA-YYYY-ZZ-NNNN, where ZZ is class 01-10.
-- Example: JRA-2026-05-0001
-- Run this migration in Supabase SQL Editor AFTER student_portal_migration.sql.
-- Existing IDs are reformatted based on each student's created_at year and current stored grade.

begin;

-- Track a separate sequential number for each admission-year/class pair.
create table if not exists public.student_code_counters (
  admission_year integer not null check (admission_year between 2000 and 2999),
  class_number integer not null check (class_number between 1 and 10),
  last_number integer not null default 0 check (last_number >= 0),
  primary key (admission_year, class_number)
);

-- Generate unique IDs safely even if two student records are created concurrently.
create or replace function public.set_student_code()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_year integer;
  v_class integer;
  v_number integer;
begin
  -- Generate an ID when blank; do not change an existing ID on updates/class changes.
  if tg_op = 'INSERT' and (new.student_code is null or btrim(new.student_code) = '') then
    v_year := extract(year from current_date)::integer;
    v_class := new.grade;

    if v_class is null or v_class < 1 or v_class > 10 then
      raise exception 'Student class must be between 1 and 10 to generate a Student ID';
    end if;

    insert into public.student_code_counters (admission_year, class_number, last_number)
    values (v_year, v_class, 1)
    on conflict (admission_year, class_number)
    do update set last_number = public.student_code_counters.last_number + 1
    returning last_number into v_number;

    new.student_code := 'JRA-' || v_year::text || '-' || lpad(v_class::text, 2, '0') || '-' || lpad(v_number::text, 4, '0');
  end if;
  return new;
end;
$$;

drop trigger if exists students_set_student_code on public.students;
create trigger students_set_student_code
before insert on public.students
for each row execute function public.set_student_code();

-- Reformat existing IDs by admission year and class. Sequence restarts for each year/class.
with numbered as (
  select
    id,
    extract(year from coalesce(created_at::date, current_date))::integer as admission_year,
    grade as class_number,
    row_number() over (
      partition by extract(year from coalesce(created_at::date, current_date))::integer, grade
      order by created_at nulls first, id
    ) as class_seq
  from public.students
)
update public.students s
set student_code = 'JRA-' || n.admission_year::text || '-' || lpad(n.class_number::text, 2, '0') || '-' || lpad(n.class_seq::text, 4, '0')
from numbered n
where s.id = n.id
  and (s.student_code is null or s.student_code !~ '^JRA-[0-9]{4}-[0-9]{2}-[0-9]{4}$'
       or split_part(s.student_code, '-', 3)::integer <> n.class_number);

-- Seed counters at the highest assigned number per year/class, so future IDs don't collide.
insert into public.student_code_counters (admission_year, class_number, last_number)
select
  split_part(student_code, '-', 2)::integer,
  split_part(student_code, '-', 3)::integer,
  max(split_part(student_code, '-', 4)::integer)
from public.students
where student_code ~ '^JRA-[0-9]{4}-[0-9]{2}-[0-9]{4}$'
group by split_part(student_code, '-', 2)::integer, split_part(student_code, '-', 3)::integer
on conflict (admission_year, class_number)
do update set last_number = greatest(public.student_code_counters.last_number, excluded.last_number);

commit;
