# JrAdemy Admin Database Cleanup

This update adds an admin-only **Database Cleanup** page with:

- CSV export buttons for operational tables (up to 5,000 rows per table per export).
- Clear academic/fee activity for selected students while retaining their student record and account mapping.
- Delete selected student records and their dependent data (subject to database foreign-key cascade rules).
- Full operational reset that removes student, batch, meeting, attendance, assignment, assessment and fee/payment data.
- Database-side role checks and an audit log for destructive actions.

## Important scope and safety

- The full reset preserves Supabase Auth users, `profiles`, the database schema and project settings. It does **not** delete login accounts or administrator profiles.
- Export CSVs are not a full database backup. Use Supabase's supported backup/export process before production cleanup.
- Apply this migration only after `schema.sql`, `online_classes_migration.sql`, and `student_portal_migration.sql` are successfully applied:
  `supabase/admin_cleanup_migration.sql`
- Test first in a separate staging Supabase project with test records. Confirm RLS and foreign-key cascade behavior before production use.
- Cleanup RPC functions are `SECURITY DEFINER` and explicitly require `public.current_role() = 'admin'`. Do not remove these checks or grant execution to `anon`.
- The app uses the publishable/anon key and the signed-in user's JWT; never put a Supabase service-role key in Streamlit secrets or GitHub.
- This UI provides CSV exports only up to 5,000 rows per table. Use a proper database backup for complete recovery.
