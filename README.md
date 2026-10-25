# JrAdemy Online Tuition — Supabase Edition

Tuition management starter for Classes 1–10, supporting CBSE, ICSE and Karnataka State Board.

## Included
- Supabase email/password authentication
- Profiles and role-based UI for admin, tutor, parent and student
- Student enrolment records
- Batch and class scheduling records
- Attendance register
- Fee records and manually recorded payments
- Assignment management
- Academic report exports
- SQL schema with row-level security policies
- Streamlit Cloud secrets example

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run streamlit_app.py
```
Replace placeholder values in `.streamlit/secrets.toml` with your Supabase project URL and publishable/anon key. Never commit the actual secrets file.

## Set up Supabase
1. Create a project at https://supabase.com/dashboard.
2. Open SQL Editor and run `supabase/schema.sql`.
3. Open Project Settings / API (or Connect) and copy the project URL and publishable/anon key.
4. In Authentication settings, configure email confirmation and allowed redirect URLs.
5. Register your own account in the app.
6. Find the user's UUID under Authentication → Users. In SQL Editor, promote the first administrator:
```sql
update public.profiles
set role = 'admin', full_name = 'Academy Administrator'
where id = 'YOUR-AUTH-USER-UUID';
```
7. Sign out and sign back in. The Admin Settings page can then assign approved roles.

## Deploy to GitHub + Streamlit Community Cloud
1. Create a private GitHub repository named `jrademy-online-tuition` (recommended while configuring).
2. Upload all files while preserving `supabase/schema.sql` and `.streamlit/config.toml`. Do not upload `.streamlit/secrets.toml`.
3. Visit https://share.streamlit.io, sign in with GitHub, select Create app, choose the repository and branch, and set `streamlit_app.py` as the entrypoint.
4. Open app settings → Secrets and add:
```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"
```
5. Deploy, then test with separate admin and non-admin accounts.

Official deployment guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy

## Security and production readiness
This is an implementation starter and needs a security review before real student records are entered.
- Admin/tutor screens are role-gated in the UI and database staff policies are enforced through RLS. The current schema intentionally does not yet expose student/parent self-service records because student-to-auth-user linkage has not been modeled.
- A profile created by the auth trigger defaults to `student`; role changes must be approved by an admin.
- RLS must be tested with non-admin accounts. Never place the Supabase service-role key in Streamlit or browser code.
- Add student/profile and guardian/profile relationship tables before enabling parent/student views. Implement row-specific RLS policies so a parent sees only their linked child and a student only their own records.
- Streamlit's built-in sign-in form is a prototype for email/password auth. Production should include secure session/token refresh, account recovery, rate limiting and login abuse protections.
- Fee entries are manual tracking only. No online payment processing is included.
- CSV exports contain personal information; limit access and use only for authorized purposes.
- Before launch, implement guardian consent, privacy notice, retention/deletion policy, backups, audit logs and incident handling. Review applicable Indian privacy and child-data requirements.
- Do not use real children’s data in testing. Use fictional sample records until access controls have been tested.


## Important status
- This is a starter project; syntax and package configuration should be tested in your deployment environment.
- Parent/student access to individual student records is not enabled until secure account-to-student relationships and row-level security policies are implemented.
- Fees are tracked manually; no payment gateway is integrated.
- Use fictional data while testing. Review child-data privacy, consent, access controls and backups before launch.
