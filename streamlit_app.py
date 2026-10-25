import os
from datetime import date, datetime, time
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
div[data-testid="stMetric"] {background:white;border:1px solid #e3e9f7;padding:14px;border-radius:15px;transition:transform .22s ease,box-shadow .22s ease}
div[data-testid="stMetric"]:hover {transform:translateY(-5px) rotateX(1deg);box-shadow:0 14px 28px rgba(30,55,120,.12)}
.feature-card {background:linear-gradient(145deg,#ffffff,#f3f6ff);border:1px solid #e0e8ff;border-radius:18px;padding:1.1rem;min-height:155px;box-shadow:0 5px 12px rgba(30,55,120,.04);transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease;margin-bottom:.8rem}
.feature-card:hover {transform:translateY(-6px) perspective(800px) rotateX(1.2deg);box-shadow:0 18px 32px rgba(30,55,120,.15);border-color:#8ca6f5}
.feature-card h3 {margin:.1rem 0 .55rem;color:#1b326c;font-size:1.08rem}
.feature-card p {margin:0;color:#56658d;font-size:.94rem}
.portal-hero {padding:1.5rem 1.7rem;border-radius:20px;background:linear-gradient(120deg,#172b61,#3457b8 65%,#7860cf);color:white;box-shadow:0 16px 34px rgba(38,61,140,.18)}
.portal-hero h1 {color:white;font-family:Manrope,sans-serif;font-size:2rem;margin:.1rem 0 .5rem}
.portal-hero p {color:#e4eaff;margin:0}
button[kind="secondary"] {transition:transform .18s ease,box-shadow .18s ease}
button[kind="secondary"]:hover {transform:translateY(-2px);box-shadow:0 8px 18px rgba(37,68,150,.14)}
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
# Streamlit reruns the script on most interactions. Keep the Supabase Auth
# tokens in session_state and restore them onto each newly-created client so
# PostgREST requests carry the signed-in user's JWT and RLS can identify auth.uid().
if "supabase_access_token" not in st.session_state:
    st.session_state.supabase_access_token = None
if "supabase_refresh_token" not in st.session_state:
    st.session_state.supabase_refresh_token = None

def get_profile(user_id):
    rows = result_data(sb.table("profiles").select("*").eq("id", user_id).limit(1).execute())
    return rows[0] if rows else None

def restore_supabase_session():
    """Restore the authenticated Supabase session on this script rerun."""
    if not sb or not st.session_state.supabase_access_token or not st.session_state.supabase_refresh_token:
        return
    try:
        auth_response = sb.auth.set_session(
            st.session_state.supabase_access_token,
            st.session_state.supabase_refresh_token,
        )
        session = getattr(auth_response, "session", None)
        user = getattr(auth_response, "user", None)
        if session:
            st.session_state.supabase_access_token = getattr(session, "access_token", None)
            st.session_state.supabase_refresh_token = getattr(session, "refresh_token", None)
        if user:
            st.session_state.user = user
            # Refresh the profile using the restored JWT, not the anonymous client.
            st.session_state.profile = get_profile(user.id)
    except Exception:
        # A revoked/expired session should not leave the UI claiming the user is signed in.
        st.session_state.user = None
        st.session_state.profile = None
        st.session_state.supabase_access_token = None
        st.session_state.supabase_refresh_token = None

def refresh_profile():
    if sb and st.session_state.user:
        st.session_state.profile = safe_call(lambda: get_profile(st.session_state.user.id))

# Must run after get_profile is defined and before any database operation/UI.
restore_supabase_session()

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
    st.caption("Learn Better. Grow Brighter.")
    st.caption("Classes 1–10 · CBSE · ICSE · Karnataka")
    current_role = (st.session_state.profile or {}).get("role", "") if st.session_state.user else ""
    if st.session_state.user:
        profile = st.session_state.profile or {}
        st.success(f"Signed in: {profile.get('full_name') or st.session_state.user.email}")
        st.caption(f"Role: {profile.get('role', 'profile pending')}")
        if st.button("Sign out", use_container_width=True):
            safe_call(lambda: sb.auth.sign_out())
            st.session_state.user = None
            st.session_state.profile = None
            st.session_state.supabase_access_token = None
            st.session_state.supabase_refresh_token = None
            st.rerun()
    if not st.session_state.user:
        pages = ["Home", "Admin Login", "Student / Parent Login"]
    elif current_role == "admin":
        pages = ["Admin Overview", "Students", "Batches & Classes", "Online Classes", "Attendance", "Fees & Payments", "Assignments", "Academic Reports", "Admin Settings"]
    elif current_role == "tutor":
        pages = ["Tutor Dashboard", "Batches & Classes", "Online Classes", "Attendance", "Assignments", "Academic Reports"]
    elif current_role == "student":
        pages = ["Student Portal"]
    elif current_role == "parent":
        pages = ["Parent Portal"]
    else:
        pages = ["Account Pending"]
    preferred_page = st.session_state.get("selected_portal")
    page_index = pages.index(preferred_page) if preferred_page in pages else 0
    page = st.radio("Navigation", pages, index=page_index, label_visibility="visible")

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
    st.markdown('<div class="hero"><h1>Big goals begin with small wins.</h1><p>Learn Better. Grow Brighter. One connected place for tuition, live classes, assignments and academic growth.</p></div>', unsafe_allow_html=True)
    st.write("")
    c1,c2,c3,c4 = st.columns(4)
    for col, label, value in [(c1,"Grades","1–10"),(c2,"Boards","3"),(c3,"Learning","Structured"),(c4,"Experience","Interactive")]:
        col.metric(label, value)
    st.subheader("One platform for the whole tuition journey")
    features = [
        ("🎓","Student management","Admissions, guardian details, board, grade and enrolment status.","Admin Login"),
        ("🗓️","Classes & attendance","Batch schedules, live-class links and attendance registers.","Student / Parent Login"),
        ("💳","Fee tracking","Fee plans, invoices, payment records and outstanding balances.","Admin Login"),
        ("📝","Assignments","Homework, due dates, instructions, scores and feedback.","Student / Parent Login"),
        ("📊","Academic reports","Performance by subject, attendance and progress exports.","Admin Login"),
        ("🔐","Role-based access","Separate workspaces for admin, tutor, parent and student.","Student / Parent Login")
    ]
    for start in range(0, len(features), 3):
        cols = st.columns(3)
        for col, (icon, title, desc, target) in zip(cols, features[start:start+3]):
            with col:
                st.markdown(f'<div class="feature-card"><h3>{icon} {title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
                if st.button("Explore →", key=f"explore_{title}", use_container_width=True):
                    st.session_state["selected_portal"] = target
                    st.rerun()
    st.markdown('<div class="portal-hero"><h1>Ready to learn?</h1><p>Sign in to your own workspace. Your menus and records depend on your approved account role.</p></div>', unsafe_allow_html=True)
    a,b = st.columns(2)
    if a.button("🔐 Admin & Tutor Login", type="primary", use_container_width=True):
        st.session_state["selected_portal"] = "Admin Login"
        st.rerun()
    if b.button("🎒 Student & Parent Portal", use_container_width=True):
        st.session_state["selected_portal"] = "Student / Parent Login"
        st.rerun()
    st.caption("Security: student/parent-specific records and class links must be linked to verified accounts before real student data is enabled.")

elif page in ["Admin Login", "Student / Parent Login"]:
    portal_is_admin = page == "Admin Login"
    title = "Admin & Tutor Access" if portal_is_admin else "Student & Parent Portal"
    st.markdown(f'<div class="portal-hero"><h1>{title}</h1><p>{"Manage enrolments, classes, attendance, fees and academic operations." if portal_is_admin else "Access your classes, meeting schedule, assignments and learning progress."}</p></div>', unsafe_allow_html=True)
    st.write("")
    page_header("Sign in or register", "Your permissions are determined by the role approved in your profile.")
    mode = st.segmented_control("Choose action", ["Sign in","Register"] if not portal_is_admin else ["Sign in"], default="Sign in")
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
                    auth_result = sb.auth.sign_up({"email": email.strip(), "password": password, "options": {"data": {"full_name": full_name.strip()}}})
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
                    session = getattr(auth_result, "session", None)
                    if session:
                        st.session_state.supabase_access_token = getattr(session, "access_token", None)
                        st.session_state.supabase_refresh_token = getattr(session, "refresh_token", None)
                    st.session_state.profile = get_profile(auth_result.user.id)
                    signed_role = (st.session_state.profile or {}).get("role", "")
                    if not st.session_state.profile:
                        st.warning("Authentication succeeded, but no profile exists. Ask an administrator to create/approve your profile.")
                    elif portal_is_admin and signed_role not in ["admin", "tutor"]:
                        st.session_state.user = None
                        st.session_state.profile = None
                        st.session_state.supabase_access_token = None
                        st.session_state.supabase_refresh_token = None
                        st.error("This account is not approved for Admin/Tutor access. Use the Student & Parent Portal or contact the administrator.")
                    elif not portal_is_admin and signed_role not in ["student", "parent"]:
                        st.session_state.user = None
                        st.session_state.profile = None
                        st.session_state.supabase_access_token = None
                        st.session_state.supabase_refresh_token = None
                        st.error("This account is an Admin/Tutor account. Please use Admin & Tutor Login.")
                    else:
                        st.rerun()
            except Exception as e:
                st.error("Authentication failed.")
                st.caption(str(e))
    st.caption("Security note: role assignment is administrator-controlled. Public registration must never be allowed to self-assign the admin role.")

elif page in ["Admin Overview", "Tutor Dashboard", "Student Portal", "Parent Portal", "Account Pending", "My Dashboard"]:
    if require_login():
        p = st.session_state.profile or {}
        st.subheader(f"Welcome, {p.get('full_name') or st.session_state.user.email}")
        st.write(f"**Role:** {p.get('role','pending')} · **Board:** {p.get('board') or 'Not set'} · **Grade:** {p.get('grade') or 'Not set'}")
        if role() in ["admin","tutor"]:
            st.markdown('<div class="portal-hero"><h1>Operations at a glance</h1><p>Use the cards below to manage your tuition academy.</p></div>', unsafe_allow_html=True)
            students = safe_call(lambda: list_rows("students"), [])
            batches = safe_call(lambda: list_rows("batches"), [])
            payments = safe_call(lambda: list_rows("payments"), []) if role() == "admin" else []
            assignments = safe_call(lambda: list_rows("assignments"), [])
            a,b,c,d = st.columns(4)
            a.metric("Student records",len(students))
            b.metric("Active batches",sum(1 for x in batches if x.get("status", "active") == "active"))
            c.metric("Assignments",len(assignments))
            d.metric("Payment entries",len(payments) if role() == "admin" else "Admin only")
            st.subheader("Quick actions")
            actions = [("🎓 Students","Students"),("📚 Batches & Classes","Batches & Classes"),("🎥 Online Classes","Online Classes"),("📝 Assignments","Assignments")]
            quick_cols = st.columns(4)
            for col, (label, target) in zip(quick_cols, actions):
                with col:
                    if st.button(label, key=f"quick_{target}", use_container_width=True):
                        st.session_state["quick_nav"] = target
                        st.info(f"Use the {target} page in the sidebar to continue.")
        elif role() in ["student", "parent"]:
            st.markdown('<div class="portal-hero"><h1>Your learning space</h1><p>Classes, homework and progress — in one place.</p></div>', unsafe_allow_html=True)
            st.info("Your account is signed in. To safely show personal schedules, meeting links, attendance, fees and assignments, the database must first link this login to the correct student record. That relationship is not configured yet, so private student records are intentionally not displayed.")
            st.subheader("What will appear here")
            c1,c2,c3 = st.columns(3)
            c1.markdown('<div class="feature-card"><h3>🎥 Online classes</h3><p>Meeting link, date, time, teacher and class notes.</p></div>', unsafe_allow_html=True)
            c2.markdown('<div class="feature-card"><h3>📝 Assignments</h3><p>Homework instructions, due dates and feedback.</p></div>', unsafe_allow_html=True)
            c3.markdown('<div class="feature-card"><h3>📈 Progress</h3><p>Attendance and academic progress for your linked student.</p></div>', unsafe_allow_html=True)
        else:
            st.warning("Your account role is pending administrator approval.")

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

elif page == "Online Classes":
    if require_roles("admin", "tutor"):
        page_header("Online classes & meeting schedule", "Schedule lessons and store the meeting link, platform and teacher notes.")
        st.info("This page needs the class_meetings table migration applied in Supabase before it can save meetings.")
        batches = safe_call(lambda: list_rows("batches"), [])
        try:
            existing_meetings = safe_call(lambda: list_rows("class_meetings"), [])
        except Exception:
            existing_meetings = []
        if batches:
            bmap = {f"{b.get('name')} · Class {b.get('grade')} · {b.get('subject')} · {b.get('id')}": b for b in batches}
            with st.form("meeting_form", clear_on_submit=True):
                meeting_title = st.text_input("Meeting title *", placeholder="Class 7 Mathematics — Algebra")
                batch_key = st.selectbox("Batch *", list(bmap))
                col1, col2, col3 = st.columns(3)
                meeting_date = col1.date_input("Date", date.today())
                start_time = col2.time_input("Start time", time(17, 0))
                end_time = col3.time_input("End time", time(18, 0))
                col4, col5 = st.columns(2)
                platform = col4.selectbox("Platform", ["Google Meet", "Zoom", "Microsoft Teams", "Other"])
                meeting_url = col5.text_input("Meeting URL *", placeholder="https://...")
                meeting_notes = st.text_area("Agenda / class notes")
                meeting_status = st.selectbox("Status", ["scheduled", "completed", "cancelled"])
                submitted = st.form_submit_button("Save meeting", type="primary")
            if submitted:
                if not meeting_title.strip() or not meeting_url.strip().startswith(("https://", "http://")):
                    st.error("Enter a meeting title and a valid http(s) meeting URL.")
                elif end_time <= start_time:
                    st.error("End time must be later than start time.")
                else:
                    batch = bmap[batch_key]
                    payload = {"title": meeting_title.strip(), "batch_id": batch["id"], "meeting_date": str(meeting_date),
                               "start_time": str(start_time), "end_time": str(end_time), "platform": platform,
                               "meeting_url": meeting_url.strip(), "notes": meeting_notes.strip() or None, "status": meeting_status}
                    res = safe_call(lambda: add_row("class_meetings", payload))
                    if res is not None: st.success("Meeting saved.")
            st.subheader("Upcoming and recent meetings")
            meetings = safe_call(lambda: list_rows("class_meetings"), [])
            if meetings:
                b_lookup = {str(b.get("id")): b for b in batches}
                for m in sorted(meetings, key=lambda x: (x.get("meeting_date") or "", x.get("start_time") or ""), reverse=True):
                    batch = b_lookup.get(str(m.get("batch_id")), {})
                    st.markdown(f'<div class="feature-card"><h3>🎥 {m.get("title", "Class meeting")}</h3><p><b>{m.get("meeting_date", "Date pending")}</b> · {m.get("start_time", "")}–{m.get("end_time", "")} · {m.get("platform", "Online")}</p><p>{batch.get("name", "Batch")} · Class {batch.get("grade", "?")} · {batch.get("subject", "")}</p><p>{m.get("notes") or "No notes added."}</p></div>', unsafe_allow_html=True)
                    st.link_button("Open meeting link", m.get("meeting_url", "https://example.com"), disabled=not bool(m.get("meeting_url")))
            else:
                st.caption("No meetings have been scheduled yet.")
        else:
            st.warning("Create a batch first, then schedule its online class meeting.")

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
        page_header("Admin settings","Control account roles and academy access.")
        st.warning("Role changes are managed here. Passwords are never displayed to administrators; use account recovery/reset flows. Creating Auth accounts on behalf of students requires a secure server-side invite function.")
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
