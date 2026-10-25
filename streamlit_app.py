import os
from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="JrAdemy Online Tuition", page_icon="🎓", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;700;800&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif}
.stApp {background:#f7f9ff}
.hero {padding:2rem;border-radius:22px;background:linear-gradient(120deg,#172b61,#3457b8 70%,#7860cf);color:white}
.hero h1 {font-family:Manrope,sans-serif;font-size:2.35rem;font-weight:800;margin:.2rem 0}
.hero p {color:#e4eaff;font-size:1.05rem}
div[data-testid="stMetric"] {background:white;border:1px solid #e3e9f7;padding:14px;border-radius:15px}
</style>
""", unsafe_allow_html=True)

BOARDS = ["CBSE", "ICSE", "Karnataka State Board"]
GRADES = list(range(1, 11))
ROLES = ["admin", "tutor", "parent", "student"]

def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def result_data(response):
    return getattr(response, "data", None) or []

def safe_call(fn, fallback=None):
    try:
        return fn()
    except Exception as e:
        st.error("The database request failed. Check your Supabase schema, access policies and secrets.")
        with st.expander("Technical details"):
            st.code(str(e))
        return fallback

def page_header(title, subtitle):
    st.title(title)
    st.caption(subtitle)

def table_df(rows):
    return pd.DataFrame(rows) if rows else pd.DataFrame()

sb = get_supabase()
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None

def get_profile(user_id):
    rows = result_data(sb.table("profiles").select("*").eq("id", user_id).limit(1).execute())
    return rows[0] if rows else None

def refresh_profile():
    if sb and st.session_state.user:
        st.session_state.profile = safe_call(lambda: get_profile(st.session_state.user.id))

if sb is None:
    st.markdown('<div class="hero"><h1>JrAdemy Online Tuition</h1><p>Learn Better. Grow Brighter.</p></div>', unsafe_allow_html=True)
    st.error("Supabase is not configured yet.")
    st.markdown("""
    **To connect the database**
    1. Create a Supabase project.
    2. Run `supabase/schema.sql` in Supabase SQL Editor.
    3. Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to `.streamlit/secrets.toml` locally or Streamlit Cloud Secrets.
    4. Restart the app.
    """)
    st.stop()

with st.sidebar:
    st.markdown("## 🎓 JrAdemy")
    st.caption("Classes 1–10 · CBSE · ICSE · Karnataka")
    if st.session_state.user:
        profile = st.session_state.profile or {}
        st.success(f"Signed in: {profile.get('full_name') or st.session_state.user.email}")
        st.caption(f"Role: {profile.get('role', 'profile pending')}")
        if st.button("Sign out", use_container_width=True):
            safe_call(lambda: sb.auth.sign_out())
            st.session_state.user = None
            st.session_state.profile = None
            st.rerun()
    page = st.radio("Navigation", [
        "Home", "Sign in / Register", "My Dashboard", "Students",
        "Batches & Classes", "Attendance", "Fees & Payments",
        "Assignments", "Academic Reports", "Admin Settings"
    ])

def require_login():
    if not st.session_state.user:
        st.info("Please sign in to access this workspace.")
        return False
    return True

def role():
    return (st.session_state.profile or {}).get("role", "")

def require_roles(*roles):
    if not require_login():
        return False
    if role() not in roles:
        st.error("Your account does not have permission to access this section.")
        return False
    return True

def add_row(table, row):
    return sb.table(table).insert(row).execute()

def list_rows(table, limit=500):
    return result_data(sb.table(table).select("*").order("created_at", desc=True).limit(limit).execute())

def update_row(table, row_id, values):
    return sb.table(table).update(values).eq("id", row_id).execute()

if page == "Home":
    st.markdown('<div class="hero"><h1>Big goals begin with small wins.</h1><p>One connected place for tuition admissions, batches, attendance, fee tracking and academic growth.</p></div>', unsafe_allow_html=True)
    st.write("")
    c1,c2,c3,c4 = st.columns(4)
    for col, label, value in [(c1,"Grades","1–10"),(c2,"Boards","3"),(c3,"Learning","Structured"),(c4,"Records","Cloud-backed")]:
        col.metric(label, value)
    st.subheader("One platform for the whole tuition journey")
    cols = st.columns(3)
    features = [
        ("🎓","Student management","Admissions, guardian details, board, grade and enrolment status."),
        ("🗓️","Classes & attendance","Batch schedules, attendance registers and class notes."),
        ("💳","Fee tracking","Fee plans, invoices, payment records and outstanding balances."),
        ("📝","Assignments","Create assignments, set due dates and record scores."),
        ("📊","Academic reports","Performance by subject, quiz scores and progress exports."),
        ("🔐","Role-based access","Separate workspaces for admin, tutor, parent and student.")
    ]
    for col,(icon,title,desc) in zip([cols[0],cols[1],cols[2],cols[0],cols[1],cols[2]],features):
        with col:
            st.markdown(f"### {icon} {title}\n{desc}")
    st.info("This app uses Supabase for persistence. Configure database schema and authentication before inviting real families.")

elif page == "Sign in / Register":
    page_header("Account access","Use an email and password. New accounts need an approved role in the profiles table.")
    mode = st.segmented_control("Choose action", ["Sign in","Register"], default="Sign in")
    with st.form("auth_form"):
        email = st.text_input("Email address")
        password = st.text_input("Password", type="password", help="Use a strong, unique password.")
        full_name = st.text_input("Full name (registration only)") if mode == "Register" else ""
        submitted = st.form_submit_button(mode, type="primary")
    if submitted:
        if not email.strip() or len(password) < 8:
            st.error("Enter an email and a password of at least 8 characters.")
        else:
            try:
                if mode == "Register":
                    auth_result = sb.auth.sign_up({"email": email.strip(), "password": password})
                    user = getattr(auth_result, "user", None)
                    if user:
                        st.success("Registration submitted. Confirm your email if Supabase email confirmation is enabled.")
                        if full_name.strip():
                            st.info("After registration, the profile row may need to be completed by an administrator.")
                    else:
                        st.error("Registration did not return a user. Check Supabase Auth settings.")
                else:
                    auth_result = sb.auth.sign_in_with_password({"email": email.strip(), "password": password})
                    st.session_state.user = auth_result.user
                    st.session_state.profile = get_profile(auth_result.user.id)
                    if not st.session_state.profile:
                        st.warning("Authentication succeeded, but no profile exists. Ask an administrator to create/approve your profile.")
                    st.rerun()
            except Exception as e:
                st.error("Authentication failed.")
                st.caption(str(e))
    st.caption("Security note: role assignment is administrator-controlled. Public registration must never be allowed to self-assign the admin role.")

elif page == "My Dashboard":
    if require_login():
        p = st.session_state.profile or {}
        st.subheader(f"Welcome, {p.get('full_name') or st.session_state.user.email}")
        st.write(f"**Role:** {p.get('role','pending')} · **Board:** {p.get('board') or 'Not set'} · **Grade:** {p.get('grade') or 'Not set'}")
        if role() in ["admin","tutor"]:
            students = safe_call(lambda: list_rows("students"), [])
            batches = safe_call(lambda: list_rows("batches"), [])
            payments = safe_call(lambda: list_rows("payments"), [])
            a,b,c = st.columns(3)
            a.metric("Student records",len(students))
            b.metric("Batches",len(batches))
            c.metric("Payment entries",len(payments))
        else:
            st.info("Your dashboard will show classes, assignments, attendance and progress linked to your approved account.")

elif page == "Students":
    if require_roles("admin","tutor"):
        page_header("Student management","Create and review enrolment records.")
        with st.expander("Add student", expanded=True):
            with st.form("student_form", clear_on_submit=True):
                a,b = st.columns(2)
                with a:
                    student_name = st.text_input("Student full name *")
                    grade = st.selectbox("Class", GRADES)
                    board = st.selectbox("Board", BOARDS)
                with b:
                    guardian_name = st.text_input("Parent / guardian name *")
                    guardian_email = st.text_input("Parent / guardian email")
                    phone = st.text_input("Guardian phone")
                status = st.selectbox("Enrolment status", ["active","trial","paused","completed"])
                submitted = st.form_submit_button("Save student", type="primary")
            if submitted:
                if not student_name.strip() or not guardian_name.strip():
                    st.error("Student and guardian names are required.")
                else:
                    payload = {"student_name":student_name.strip(),"grade":grade,"board":board,
                               "guardian_name":guardian_name.strip(),"guardian_email":guardian_email.strip() or None,
                               "guardian_phone":phone.strip() or None,"status":status}
                    res = safe_call(lambda: add_row("students",payload))
                    if res is not None: st.success("Student saved.")
        rows = safe_call(lambda: list_rows("students"), [])
        st.dataframe(table_df(rows), use_container_width=True, hide_index=True)
        if rows:
            st.download_button("Export students CSV", table_df(rows).to_csv(index=False), "jrademy_students.csv", "text/csv")

elif page == "Batches & Classes":
    if require_roles("admin","tutor"):
        page_header("Batches & classes","Manage tuition groups and lesson schedules.")
        with st.form("batch_form", clear_on_submit=True):
            name = st.text_input("Batch name *")
            a,b,c = st.columns(3)
            grade = a.selectbox("Class", GRADES)
            board = b.selectbox("Board", BOARDS)
            subject = c.selectbox("Subject", ["Mathematics","Science","English","Social Studies","Computer Science"])
            d,e = st.columns(2)
            schedule = d.text_input("Schedule", placeholder="Mon/Wed/Fri · 5:00 PM")
            tutor_email = e.text_input("Tutor email (optional)")
            start_date = st.date_input("Start date", date.today())
            submitted = st.form_submit_button("Create batch", type="primary")
        if submitted:
            if not name.strip(): st.error("Batch name is required.")
            else:
                res = safe_call(lambda: add_row("batches",{"name":name.strip(),"grade":grade,"board":board,"subject":subject,
                                                           "schedule_text":schedule,"tutor_email":tutor_email.strip() or None,
                                                           "start_date":str(start_date),"status":"active"}))
                if res is not None: st.success("Batch created.")
        rows = safe_call(lambda: list_rows("batches"), [])
        st.dataframe(table_df(rows), use_container_width=True, hide_index=True)

elif page == "Attendance":
    if require_roles("admin","tutor"):
        page_header("Attendance register","Record attendance for a date and batch.")
        students = safe_call(lambda: list_rows("students"), [])
        batches = safe_call(lambda: list_rows("batches"), [])
        if not students or not batches:
            st.info("Add at least one student and one batch first.")
        else:
            student_map = {f"{x.get('student_name')} · Class {x.get('grade')} · {x.get('id')}":x for x in students}
            batch_map = {f"{x.get('name')} · {x.get('id')}":x for x in batches}
            with st.form("attendance_form"):
                selected_student = st.selectbox("Student", list(student_map))
                selected_batch = st.selectbox("Batch", list(batch_map))
                attendance_date = st.date_input("Date", date.today())
                status = st.selectbox("Status", ["present","absent","late","excused"])
                notes = st.text_input("Notes (optional)")
                submitted = st.form_submit_button("Save attendance", type="primary")
            if submitted:
                st_res = safe_call(lambda: add_row("attendance",{"student_id":student_map[selected_student]["id"],
                    "batch_id":batch_map[selected_batch]["id"],"attendance_date":str(attendance_date),
                    "status":status,"notes":notes.strip() or None}))
                if st_res is not None: st.success("Attendance saved.")
        rows = safe_call(lambda: list_rows("attendance"), [])
        st.dataframe(table_df(rows), use_container_width=True, hide_index=True)

elif page == "Fees & Payments":
    if require_roles("admin"):
        page_header("Fees & payments","Track fee obligations and manually recorded payments. This does not process online payments.")
        students = safe_call(lambda: list_rows("students"), [])
        if students:
            smap = {f"{s['student_name']} · Class {s['grade']} · {s['id']}":s for s in students}
            with st.form("fee_form"):
                student_key = st.selectbox("Student", list(smap))
                amount_due = st.number_input("Fee amount (INR)", min_value=0.0, step=100.0)
                due_date = st.date_input("Due date", date.today())
                period = st.text_input("Fee period", placeholder="October 2026")
                status = st.selectbox("Status", ["due","partially_paid","paid","waived"])
                notes = st.text_input("Notes")
                submitted = st.form_submit_button("Create fee record", type="primary")
            if submitted:
                resp = safe_call(lambda: add_row("fee_records",{"student_id":smap[student_key]["id"],"amount_due":amount_due,
                    "due_date":str(due_date),"fee_period":period.strip() or None,"status":status,"notes":notes.strip() or None}))
                if resp is not None: st.success("Fee record created.")
        st.subheader("Record a payment")
        fees = safe_call(lambda: list_rows("fee_records"), [])
        if fees:
            fmap = {f"{f.get('fee_period') or 'Fee'} · ₹{f.get('amount_due')} · {f.get('id')}":f for f in fees}
            with st.form("payment_form"):
                fee_key = st.selectbox("Fee record", list(fmap))
                amount = st.number_input("Amount received (INR)", min_value=1.0, step=100.0)
                paid_on = st.date_input("Payment date", date.today())
                method = st.selectbox("Method", ["UPI","Bank transfer","Cash","Card","Other"])
                reference = st.text_input("Transaction reference (optional)")
                submitted = st.form_submit_button("Record payment")
            if submitted:
                res = safe_call(lambda: add_row("payments",{"fee_record_id":fmap[fee_key]["id"],"amount":amount,"paid_on":str(paid_on),
                    "method":method,"reference":reference.strip() or None}))
                if res is not None: st.success("Payment record saved. Reconcile manually with the fee balance.")
        st.subheader("Fee records")
        st.dataframe(table_df(safe_call(lambda: list_rows("fee_records"), [])), use_container_width=True, hide_index=True)
        st.subheader("Payments")
        st.dataframe(table_df(safe_call(lambda: list_rows("payments"), [])), use_container_width=True, hide_index=True)
        st.caption("Do not store card numbers, UPI PINs or payment credentials. Integrate a payment gateway with server-side webhook verification for online collection.")

elif page == "Assignments":
    if require_roles("admin","tutor"):
        page_header("Assignments","Create assignments and review submissions.")
        with st.form("assignment_form"):
            title = st.text_input("Title *")
            grade = st.selectbox("Class", GRADES)
            board = st.selectbox("Board", BOARDS)
            subject = st.selectbox("Subject", ["Mathematics","Science","English","Social Studies","Computer Science"])
            due = st.date_input("Due date", date.today())
            instructions = st.text_area("Instructions")
            submitted = st.form_submit_button("Create assignment", type="primary")
        if submitted:
            if not title.strip(): st.error("Title is required.")
            else:
                res = safe_call(lambda: add_row("assignments",{"title":title.strip(),"grade":grade,"board":board,"subject":subject,
                    "due_date":str(due),"instructions":instructions.strip() or None,"status":"published"}))
                if res is not None: st.success("Assignment created.")
        rows = safe_call(lambda: list_rows("assignments"), [])
        st.dataframe(table_df(rows), use_container_width=True, hide_index=True)

elif page == "Academic Reports":
    if require_roles("admin","tutor"):
        page_header("Academic reports","Export records and review performance data.")
        scores = safe_call(lambda: list_rows("assessment_scores"), [])
        attendance = safe_call(lambda: list_rows("attendance"), [])
        fees = safe_call(lambda: list_rows("fee_records"), [])
        c1,c2,c3 = st.columns(3)
        c1.metric("Assessment records",len(scores))
        c2.metric("Attendance entries",len(attendance))
        c3.metric("Fee records",len(fees))
        st.subheader("Assessment scores")
        st.dataframe(table_df(scores), use_container_width=True, hide_index=True)
        if scores: st.download_button("Export scores CSV",table_df(scores).to_csv(index=False),"jrademy_scores.csv","text/csv")
        st.subheader("Attendance")
        st.dataframe(table_df(attendance), use_container_width=True, hide_index=True)
        if attendance: st.download_button("Export attendance CSV",table_df(attendance).to_csv(index=False),"jrademy_attendance.csv","text/csv")

elif page == "Admin Settings":
    if require_roles("admin"):
        page_header("Admin settings","Approve roles and manage access.")
        st.warning("Use Supabase's dashboard to assign the first admin role securely. Never let public users choose their own role.")
        st.markdown("""
        **Bootstrap the first administrator**
        1. Register your own account through Sign in / Register.
        2. In Supabase, open Authentication → Users and copy your user UUID.
        3. In SQL Editor, insert or update your `profiles` row with `role = 'admin'`.
        4. Sign out and back in to refresh the profile.
        """)
        st.subheader("Profiles")
        profiles = safe_call(lambda: list_rows("profiles"), [])
        st.dataframe(table_df(profiles), use_container_width=True, hide_index=True)
        if profiles:
            pmap = {f"{p.get('full_name') or p.get('email') or p['id']} · {p['id']}":p for p in profiles}
            with st.form("role_form"):
                key = st.selectbox("Profile",list(pmap))
                new_role = st.selectbox("New role",ROLES)
                board = st.selectbox("Board (optional)",["",*BOARDS])
                grade = st.selectbox("Grade (optional)",["",*GRADES])
                submitted = st.form_submit_button("Update profile")
            if submitted:
                vals = {"role":new_role,"board":board or None,"grade":grade or None}
                res = safe_call(lambda: update_row("profiles",pmap[key]["id"],vals))
                if res is not None: st.success("Profile updated. User may need to sign in again.")
        st.caption("Database row-level security policies are the actual security boundary. Review schema.sql before launch.")

st.divider()
st.caption("© 2026 JrAdemy Online Tuition · Classes 1–10 · CBSE · ICSE · Karnataka State Board")
