# JrAdemy student portal update

This update adds human-readable student IDs, admin mapping of existing student/parent login profiles to student records, batch enrollment management, and student-facing pages for enrolled online classes, published assignments, assignment submissions, assessment results, attendance, and fee/payment balances.

## Files
- `streamlit_app.py`: updated Streamlit UI.
- `supabase/student_portal_migration.sql`: adds student/profile links, human-readable student IDs, batch enrollments, assignment submissions, and row-level policies.
- Existing `supabase/schema.sql` is retained unchanged.
- Existing `supabase/online_classes_migration.sql` is retained.

## Apply safely
1. Ensure the base `schema.sql` and `online_classes_migration.sql` have already been run successfully.
2. Back up the Supabase database before applying changes.
3. Run `supabase/student_portal_migration.sql` in Supabase SQL Editor.
4. Replace `streamlit_app.py` in the GitHub repository and push to `main`.
5. Sign in as admin, open **Students** and create/update student records. Open **Admin Settings → Student account mapping** to link existing registered student and parent profiles. Open **Batches & Classes** and enroll each student into the relevant batch.
6. Publish assignments and schedule meetings for the relevant batch. Student/parent users must sign out and sign back in after linking.

## Security notes
- This does not allow admins to view existing passwords. Use Supabase Auth invite/reset flows for password setup and recovery.
- This does not create new Auth accounts from the browser. Secure account provisioning should be implemented using a Supabase Edge Function or trusted backend with a server-side service-role key; never place that key in Streamlit secrets used by the client-facing app.
- Apply to a staging project first and test with distinct admin, tutor, student and parent accounts. Review RLS policies, backups, consent, retention and local child-data privacy obligations before production use.
- Fee balances are calculated from manually recorded payment rows; no payment gateway is integrated.
