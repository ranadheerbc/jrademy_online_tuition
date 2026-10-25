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
        pages = ["Admin Overview", "Students", "Batches & Classes", "Online Classes", "Attendance", "Fees & Payments", "Assignments", "Academic Reports", "Admin Settings", "Database Cleanup"]
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

def render_student_portal():
    """Render only the student/guardian records allowed by Supabase RLS."""
    user_id = str(st.session_state.user.id)
    profile = st.session_state.profile or {}
    st.markdown('<div class="portal-hero"><h1>Your learning space</h1><p>Classes, homework, results, attendance and fee status — in one place.</p></div>', unsafe_allow_html=True)
    linked = safe_call(lambda: result_data(sb.table("students").select("id,student_code,student_name,grade,board,status,linked_profile_id,guardian_profile_id").or_(f"linked_profile_id.eq.{user_id},guardian_profile_id.eq.{user_id}").execute()), [])
    if not linked:
        st.warning("Your login is active, but an administrator has not linked it to a student record yet. Ask the academy administrator to open Admin Settings → Student account mapping.")
        st.caption("Once mapped, this page will show your personal classes, assignments, academic results, attendance and fee balance.")
        return

    # Parents can be linked to multiple children; students are normally linked to one record.
    chosen_label = {f"{x.get('student_code') or 'Student'} · {x.get('student_name')} · Class {x.get('grade')} · {x.get('board')}": x for x in linked}
    if len(chosen_label) > 1:
        selected_label = st.selectbox("Choose student", list(chosen_label), key="portal_student_select")
        student = chosen_label[selected_label]
    else:
        student = linked[0]
    student_id = student["id"]
    st.markdown(f"### {student.get('student_name','Student')}  ")
    st.caption(f"Student ID: **{student.get('student_code') or 'Pending ID'}** · Class: **{student.get('grade') or '—'}** · Board: **{student.get('board') or '—'}** · Status: **{student.get('status') or '—'}**")

    meetings, assignments, attendance, fees, scores, enrollments = [], [], [], [], [], []
    meetings = safe_call(lambda: result_data(sb.table("class_meetings").select("id,title,batch_id,meeting_date,start_time,end_time,platform,meeting_url,notes,status").gte("meeting_date", str(date.today())).order("meeting_date").execute()), [])
    # RLS restricts meetings to enrolled batches, so no cross-student links are exposed.
    assignments = safe_call(lambda: result_data(sb.table("assignments").select("id,title,grade,board,subject,due_date,instructions,status,batch_id").eq("status","published").eq("grade",student["grade"]).eq("board",student["board"]).order("due_date").execute()), [])
    attendance = safe_call(lambda: result_data(sb.table("attendance").select("attendance_date,status,batch_id").eq("student_id",student_id).order("attendance_date",desc=True).execute()), [])
    fees = safe_call(lambda: result_data(sb.table("fee_records").select("id,amount_due,due_date,fee_period,status,notes").eq("student_id",student_id).order("due_date",desc=True).execute()), [])
    scores = safe_call(lambda: result_data(sb.table("assessment_scores").select("subject,score,max_score,feedback,assessed_at,assignment_id").eq("student_id",student_id).order("assessed_at",desc=True).execute()), [])
    enrollments = safe_call(lambda: result_data(sb.table("batch_enrollments").select("batch_id,status").eq("student_id",student_id).eq("status","active").execute()), [])
    batch_ids = {str(x.get("batch_id")) for x in enrollments}
    meetings = [m for m in meetings if str(m.get("batch_id")) in batch_ids]
    assignments = [a for a in assignments if not a.get("batch_id") or str(a.get("batch_id")) in batch_ids]

    fee_ids = [str(f["id"]) for f in fees]
    payments = []
    if fee_ids:
        payments = safe_call(lambda: result_data(sb.table("payments").select("fee_record_id,amount,paid_on,method,reference").in_("fee_record_id", fee_ids).order("paid_on",desc=True).execute()), [])
    paid_by_fee = {}
    for payment in payments:
        key = str(payment.get("fee_record_id"))
        paid_by_fee[key] = paid_by_fee.get(key, 0.0) + float(payment.get("amount") or 0)
    total_fee = sum(float(f.get("amount_due") or 0) for f in fees)
    total_paid = sum(paid_by_fee.values())
    total_due = max(0.0, total_fee - total_paid)
    present = sum(1 for x in attendance if x.get("status") in ("present", "late"))
    attendance_rate = (present / len(attendance) * 100) if attendance else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Upcoming classes", len(meetings))
    c2.metric("Assignments", len(assignments))
    c3.metric("Attendance", f"{attendance_rate:.0f}%" if attendance else "—")
    c4.metric("Fee balance", f"₹{total_due:,.2f}")

    tab_classes, tab_assignments, tab_results, tab_attendance, tab_fees = st.tabs(["🎥 Online classes", "📝 Assignments", "📊 Results", "📅 Attendance", "💳 Fees & payments"])
    with tab_classes:
        st.subheader("Your online class schedule")
        if meetings:
            for m in meetings:
                st.markdown(f'<div class="feature-card"><h3>🎥 {m.get("title") or "Online class"}</h3><p><b>{m.get("meeting_date")}</b> · {m.get("start_time","")}–{m.get("end_time","")} · {m.get("platform") or "Online"}</p><p>{m.get("notes") or "No class notes provided yet."}</p></div>', unsafe_allow_html=True)
                st.link_button("Join online class ↗", m.get("meeting_url") or "", disabled=not bool(m.get("meeting_url")), key=f"join_{m.get('id')}")
        else:
            st.info("No upcoming online classes are scheduled for your enrolled batches yet.")
    with tab_assignments:
        st.subheader("Homework and assignments")
        submissions = safe_call(lambda: result_data(sb.table("assignment_submissions").select("id,assignment_id,answer_text,submitted_at,status,tutor_feedback").eq("student_id",student_id).execute()), [])
        sub_by_assignment = {str(x.get("assignment_id")):x for x in submissions}
        if not assignments:
            st.info("No published assignments match your class and board right now.")
        for assignment in assignments:
            sub = sub_by_assignment.get(str(assignment["id"]), {})
            with st.expander(f"{assignment.get('subject')} · {assignment.get('title')} · Due {assignment.get('due_date')}", expanded=False):
                st.write(assignment.get("instructions") or "No additional instructions.")
                if sub:
                    st.success(f"Submission status: {sub.get('status','submitted')} · {str(sub.get('submitted_at',''))[:10]}")
                    if sub.get("tutor_feedback"): st.info(f"Tutor feedback: {sub['tutor_feedback']}")
                else:
                    st.caption("Not submitted yet")
                with st.form(f"submit_assignment_{assignment['id']}"):
                    answer = st.text_area("Your answer / submission notes", value=sub.get("answer_text") or "", key=f"answer_{assignment['id']}")
                    submit = st.form_submit_button("Submit assignment" if not sub else "Update submission")
                if submit:
                    payload = {"assignment_id":assignment["id"],"student_id":student_id,"answer_text":answer.strip(),"status":"submitted","submitted_at":datetime.now().astimezone().isoformat()}
                    result = safe_call(lambda: sb.table("assignment_submissions").upsert(payload,on_conflict="assignment_id,student_id").execute())
                    if result is not None:
                        st.success("Assignment submitted.")
                        st.rerun()
    with tab_results:
        st.subheader("Academic results")
        if scores:
            score_df = pd.DataFrame([{ "Subject":x.get("subject"), "Score":x.get("score"), "Out of":x.get("max_score"), "Percentage":round(float(x.get("score") or 0)/float(x.get("max_score") or 1)*100,1), "Date":str(x.get("assessed_at") or "")[:10], "Feedback":x.get("feedback") or "—"} for x in scores])
            st.dataframe(score_df, use_container_width=True, hide_index=True)
        else:
            st.info("No assessment results have been published yet.")
    with tab_attendance:
        st.subheader("Attendance history")
        if attendance:
            att_df = pd.DataFrame([{ "Date":x.get("attendance_date"), "Status":str(x.get("status","")).title()} for x in attendance])
            st.dataframe(att_df, use_container_width=True, hide_index=True)
        else: st.info("No attendance entries are available yet.")
    with tab_fees:
        st.subheader("Fee status")
        a,b,c = st.columns(3); a.metric("Total fees",f"₹{total_fee:,.2f}"); b.metric("Paid",f"₹{total_paid:,.2f}"); c.metric("Balance due",f"₹{total_due:,.2f}")
        if fees:
            fee_rows = []
            for f in fees:
                amount = float(f.get("amount_due") or 0); paid = paid_by_fee.get(str(f["id"]),0.0)
                fee_rows.append({"Fee period":f.get("fee_period") or "—", "Fee amount":amount, "Paid":paid, "Balance":max(0,amount-paid), "Due date":f.get("due_date"), "Status":"Paid" if amount-paid <= 0 else ("Partially paid" if paid > 0 else f.get("status","Due").replace("_"," ").title())})
            st.dataframe(pd.DataFrame(fee_rows), use_container_width=True, hide_index=True)
        else: st.info("No fee records are available yet.")
        if payments:
            st.caption("Recorded payments")
            st.dataframe(pd.DataFrame([{ "Date":p.get("paid_on"),"Amount":f"₹{float(p.get('amount') or 0):,.2f}","Method":p.get("method"),"Reference":p.get("reference") or "—"} for p in payments]), use_container_width=True, hide_index=True)

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
            render_student_portal()
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
        if rows:
            friendly = pd.DataFrame([{ "Student ID":x.get("student_code") or "Pending ID", "Student name":x.get("student_name"), "Class":x.get("grade"), "Board":x.get("board"), "Guardian":x.get("guardian_name"), "Guardian email":x.get("guardian_email"), "Phone":x.get("guardian_phone"), "Status":x.get("status"), "Account linked":bool(x.get("linked_profile_id"))} for x in rows])
            st.dataframe(friendly, use_container_width=True, hide_index=True)
            st.download_button("Export students CSV", friendly.to_csv(index=False), "jrademy_students.csv", "text/csv")
        else:
            st.info("No student records yet.")

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
        if rows:
            st.dataframe(pd.DataFrame([{ "Batch":x.get("name"), "Class":x.get("grade"), "Board":x.get("board"), "Subject":x.get("subject"), "Schedule":x.get("schedule_text"), "Start date":x.get("start_date"), "Status":x.get("status")} for x in rows]), use_container_width=True, hide_index=True)
            students_for_enrol = safe_call(lambda: list_rows("students"), [])
            if students_for_enrol:
                st.subheader("Enroll student into a batch")
                student_map = {f"{x.get('student_code') or 'Pending ID'} · {x.get('student_name')} · Class {x.get('grade')}":x for x in students_for_enrol}
                batch_map = {f"{x.get('name')} · Class {x.get('grade')} · {x.get('subject')}":x for x in rows}
                with st.form("batch_enrollment_form"):
                    student_label = st.selectbox("Student", list(student_map))
                    batch_label = st.selectbox("Batch", list(batch_map))
                    enroll_status = st.selectbox("Enrollment status", ["active","paused","completed"])
                    enroll_submit = st.form_submit_button("Save enrollment")
                if enroll_submit:
                    student_obj, batch_obj = student_map[student_label], batch_map[batch_label]
                    enroll_res = safe_call(lambda: sb.table("batch_enrollments").upsert({"student_id":student_obj["id"],"batch_id":batch_obj["id"],"status":enroll_status},on_conflict="student_id,batch_id").execute())
                    if enroll_res is not None: st.success("Student batch enrollment saved.")
        else:
            st.info("Create a batch before enrolling students.")

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
            bmap = {f"{b.get('name')} · Class {b.get('grade')} · {b.get('subject')}": b for b in batches}
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
            student_map = {f"{x.get('student_code') or 'Pending ID'} · {x.get('student_name')} · Class {x.get('grade')}":x for x in students}
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
            smap = {f"{s.get('student_code') or 'Pending ID'} · {s['student_name']} · Class {s['grade']}":s for s in students}
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
            fmap = {f"{f.get('fee_period') or 'Fee'} · ₹{f.get('amount_due')} · Due {f.get('due_date')}":f for f in fees}
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
        page_header("Admin settings","Control account roles, academy access and automatic student-to-batch matching.")
        st.subheader("Auto-assign students")
        st.caption("Rules are saved in Supabase. Automatic matching uses grade, board, subject preferences, batch capacity and schedule-text conflict checks. Because existing schedules are free text, schedule conflict detection is conservative; use consistent schedule text and review suggestions before enabling auto-enrollment.")
        settings_rows = safe_call(lambda: result_data(sb.table("auto_assignment_settings").select("*").eq("id", 1).limit(1).execute()), [])
        current_settings = settings_rows[0] if settings_rows else {}
        with st.form("auto_assignment_settings_form"):
            auto_enabled = st.toggle("Enable automatic batch suggestions", value=bool(current_settings.get("enabled", True)))
            auto_enroll = st.toggle("Automatically enroll when exactly one eligible batch matches", value=bool(current_settings.get("auto_enroll_single_match", False)))
            require_approval = st.toggle("Require admin approval before enrollment", value=bool(current_settings.get("require_approval", True)))
            match_board = st.checkbox("Match school board", value=bool(current_settings.get("match_board", True)))
            match_grade = st.checkbox("Match class/grade", value=bool(current_settings.get("match_grade", True)))
            match_subject = st.checkbox("Match subject", value=bool(current_settings.get("match_subject", True)))
            check_capacity = st.checkbox("Respect batch capacity", value=bool(current_settings.get("check_capacity", True)))
            check_schedule = st.checkbox("Check for schedule conflicts", value=bool(current_settings.get("check_schedule_conflicts", True)))
            default_capacity = st.number_input("Default batch capacity", min_value=1, max_value=500, value=int(current_settings.get("default_capacity", 20)))
            save_auto_settings = st.form_submit_button("Save auto-assignment settings", type="primary")
        if save_auto_settings:
            settings_payload = {"id":1,"enabled":auto_enabled,"auto_enroll_single_match":auto_enroll,"require_approval":require_approval,"match_board":match_board,"match_grade":match_grade,"match_subject":match_subject,"check_capacity":check_capacity,"check_schedule_conflicts":check_schedule,"default_capacity":int(default_capacity),"updated_by":st.session_state.user.id,"updated_at":datetime.now().isoformat()}
            save_result = safe_call(lambda: sb.table("auto_assignment_settings").upsert(settings_payload, on_conflict="id").execute())
            if save_result is not None:
                st.success("Auto-assignment settings saved.")
                st.rerun()
        st.markdown("---")
        st.subheader("Match students to eligible batches")
        st.caption("Preview matching first. The app only enrolls when the configured rules allow it; manual enrollment remains available under Batches & Classes.")
        students_auto = safe_call(lambda: list_rows("students"), [])
        batches_auto = safe_call(lambda: list_rows("batches"), [])
        enrollments_auto = safe_call(lambda: list_rows("batch_enrollments"), [])
        if students_auto and batches_auto and current_settings.get("enabled", True):
            student_labels_auto = {f"{x.get('student_code') or x.get('id','')[:8]} · {x.get('student_name')} · Class {x.get('grade')} · {x.get('board')}":x for x in students_auto}
            with st.form("auto_assign_preview_form"):
                student_label_auto = st.selectbox("Student to match", list(student_labels_auto))
                preview_submit = st.form_submit_button("Find matching batches")
            if preview_submit:
                st.session_state["auto_assign_target_id"] = student_labels_auto[student_label_auto]["id"]
            target_id = st.session_state.get("auto_assign_target_id")
            target_student = next((x for x in students_auto if x.get("id") == target_id), None)
            if target_student:
                enrolled_batch_ids = {str(x.get("batch_id")) for x in enrollments_auto if str(x.get("student_id")) == str(target_id) and x.get("status", "active") == "active"}
                eligible, rejected = [], []
                for batch in batches_auto:
                    if batch.get("status", "active") != "active" or str(batch.get("id")) in enrolled_batch_ids:
                        continue
                    reasons=[]
                    if current_settings.get("match_grade", True) and batch.get("grade") != target_student.get("grade"): reasons.append("grade mismatch")
                    if current_settings.get("match_board", True) and batch.get("board") != target_student.get("board"): reasons.append("board mismatch")
                    # Subject match is only meaningful when a student's preferred_subjects field exists.
                    prefs = target_student.get("preferred_subjects") or []
                    if isinstance(prefs, str): prefs=[x.strip().lower() for x in prefs.split(",") if x.strip()]
                    if current_settings.get("match_subject", True) and prefs and str(batch.get("subject","")).lower() not in [str(x).lower() for x in prefs]: reasons.append("subject mismatch")
                    active_count = sum(1 for e in enrollments_auto if str(e.get("batch_id")) == str(batch.get("id")) and e.get("status", "active") == "active")
                    cap = int(batch.get("capacity") or current_settings.get("default_capacity",20))
                    if current_settings.get("check_capacity", True) and active_count >= cap: reasons.append("batch full")
                    if current_settings.get("check_schedule_conflicts", True):
                        target_schedule = str(batch.get("schedule_text") or "").strip().lower()
                        existing_schedules = [str(b.get("schedule_text") or "").strip().lower() for b in batches_auto if str(b.get("id")) in enrolled_batch_ids]
                        if target_schedule and any(target_schedule == x for x in existing_schedules if x): reasons.append("same schedule text as an existing enrollment")
                    if reasons: rejected.append({"Batch":batch.get("name"),"Subject":batch.get("subject"),"Schedule":batch.get("schedule_text"),"Reason":", ".join(reasons)})
                    else: eligible.append(batch)
                if eligible:
                    st.success(f"{len(eligible)} eligible batch(es) found for {target_student.get('student_name')}.")
                    st.dataframe(pd.DataFrame([{"Batch":b.get("name"),"Class":b.get("grade"),"Board":b.get("board"),"Subject":b.get("subject"),"Schedule":b.get("schedule_text") or "Not set","Capacity":b.get("capacity") or current_settings.get("default_capacity",20)} for b in eligible]),use_container_width=True,hide_index=True)
                    if current_settings.get("auto_enroll_single_match",False) and not current_settings.get("require_approval",True) and len(eligible)==1:
                        if st.button("Confirm automatic enrollment",type="primary"):
                            er=safe_call(lambda: sb.table("batch_enrollments").upsert({"student_id":target_id,"batch_id":eligible[0]["id"],"status":"active"},on_conflict="student_id,batch_id").execute())
                            if er is not None: st.success(f"Enrolled in {eligible[0].get('name')}."); st.rerun()
                    else:
                        batch_choice=st.selectbox("Choose a batch to enroll",[f"{b.get('name')} · {b.get('subject')} · {b.get('schedule_text') or 'Schedule not set'}" for b in eligible],key="auto_assign_choice")
                        chosen=eligible[[f"{b.get('name')} · {b.get('subject')} · {b.get('schedule_text') or 'Schedule not set'}" for b in eligible].index(batch_choice)]
                        if st.button("Enroll selected student",type="primary"):
                            er=safe_call(lambda: sb.table("batch_enrollments").upsert({"student_id":target_id,"batch_id":chosen["id"],"status":"active"},on_conflict="student_id,batch_id").execute())
                            if er is not None: st.success(f"Enrolled in {chosen.get('name')}."); st.rerun()
                else: st.warning("No eligible batches matched. Review the matching rules, capacity and schedule.")
                if rejected:
                    with st.expander("Batches excluded by matching rules"):
                        st.dataframe(pd.DataFrame(rejected),use_container_width=True,hide_index=True)
        elif not students_auto or not batches_auto:
            st.info("Create at least one student and one batch to use auto-assignment.")
        st.warning("Role changes are managed here. Passwords are never displayed to administrators; use account recovery/reset flows. Creating Auth accounts on behalf of students requires a secure server-side invite function.")
        st.markdown("""
        **Bootstrap the first administrator**
        1. Register your own account through Sign in / Register.
        2. In Supabase, open Authentication → Users and copy your user UUID.
        3. In SQL Editor, insert or update your `profiles` row with `role = 'admin'`.
        4. Sign out and back in to refresh the profile.
        """)
        st.subheader("Student account mapping")
        st.caption("Create the student record first, let the student/parent register or be invited securely, then link the existing profile here. Passwords are never visible in the admin portal.")
        students_for_link = safe_call(lambda: list_rows("students"), [])
        profiles = safe_call(lambda: list_rows("profiles"), [])
        if students_for_link and profiles:
            student_map = {f"{x.get('student_code') or 'Pending ID'} · {x.get('student_name')} · Class {x.get('grade')}":x for x in students_for_link}
            student_profiles = [x for x in profiles if x.get("role") == "student"]
            parent_profiles = [x for x in profiles if x.get("role") == "parent"]
            with st.form("student_account_mapping_form"):
                selected_student_label = st.selectbox("Student record", list(student_map))
                student_profile_map = {f"{x.get('full_name') or 'Unnamed'} · {x.get('email') or 'No email'}":x for x in student_profiles}
                parent_profile_map = {"No parent login linked":None, **{f"{x.get('full_name') or 'Unnamed'} · {x.get('email') or 'No email'}":x for x in parent_profiles}}
                selected_student_profile = st.selectbox("Student login profile", ["No student login linked"] + list(student_profile_map))
                selected_parent_profile = st.selectbox("Parent / guardian login (optional)", list(parent_profile_map))
                mapping_submit = st.form_submit_button("Save student account mapping", type="primary")
            if mapping_submit:
                target_student = student_map[selected_student_label]
                student_profile = student_profile_map.get(selected_student_profile)
                parent_profile = parent_profile_map.get(selected_parent_profile)
                update_values = {"linked_profile_id": student_profile.get("id") if student_profile else None,
                                 "guardian_profile_id": parent_profile.get("id") if parent_profile else None}
                mapping_result = safe_call(lambda: sb.table("students").update(update_values).eq("id", target_student["id"]).execute())
                if mapping_result is not None:
                    st.success("Student and parent mapping saved. Ask the user to sign out and sign in again.")
                    st.rerun()
        elif not students_for_link:
            st.info("Add a student record first, then map an account to it.")
        elif not profiles:
            st.info("No registered profiles found yet. Have the student/parent register, then refresh this page.")
        st.subheader("Profiles")
        if profiles:
            st.dataframe(pd.DataFrame([{ "Name":x.get("full_name") or "—", "Email":x.get("email") or "—", "Role":x.get("role"), "Board":x.get("board") or "—", "Class":x.get("grade") or "—", "Created":str(x.get("created_at") or "")[:10]} for x in profiles]), use_container_width=True, hide_index=True)
        if profiles:
            pmap = {f"{p.get('full_name') or 'Unnamed'} · {p.get('email') or 'No email'}":p for p in profiles}
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


elif page == "Database Cleanup":
    if require_roles("admin"):
        page_header("Database cleanup & data maintenance", "Admin-only tools to export backups, reset selected student records, delete selected students, or clear operational data.")
        st.error("DESTRUCTIVE ACTIONS: take and verify backups first. These actions cannot be undone from this screen.")
        st.info("This tool never deletes Supabase Auth users, admin profiles, database tables, schema, or project settings. Full cleanup removes academy operational records only.")

        # Export current data before allowing destructive actions. RLS remains enforced by Supabase.
        st.subheader("1. Export backups before cleanup")
        export_tables = [
            ("students", "students_backup.csv"),
            ("batches", "batches_backup.csv"),
            ("attendance", "attendance_backup.csv"),
            ("fee_records", "fee_records_backup.csv"),
            ("payments", "payments_backup.csv"),
            ("assignments", "assignments_backup.csv"),
            ("assessment_scores", "assessment_scores_backup.csv"),
            ("batch_enrollments", "batch_enrollments_backup.csv"),
            ("class_meetings", "class_meetings_backup.csv"),
            ("assignment_submissions", "assignment_submissions_backup.csv"),
        ]
        export_cols = st.columns(3)
        for idx, (table_name, filename) in enumerate(export_tables):
            with export_cols[idx % 3]:
                if st.button(f"Prepare {table_name} backup", key=f"cleanup_export_{table_name}", use_container_width=True):
                    rows = safe_call(lambda t=table_name: result_data(sb.table(t).select("*").limit(5000).execute()), None)
                    if rows is not None:
                        df = table_df(rows)
                        if df.empty:
                            st.warning(f"No rows found in {table_name}, or the table is not available yet.")
                        else:
                            st.download_button(f"Download {table_name} CSV", df.to_csv(index=False).encode("utf-8"), filename, "text/csv", key=f"cleanup_download_{table_name}")

        st.divider()
        st.subheader("2. Reset or delete selected students")
        students_cleanup = safe_call(lambda: list_rows("students", limit=5000), [])
        if not students_cleanup:
            st.info("No student records are available to manage.")
        else:
            student_labels = {
                f"{x.get('student_code') or 'NO-ID'} · {x.get('student_name')} · Class {x.get('grade')} · {x.get('board')} · {x.get('status')}": x
                for x in students_cleanup
            }
            selected_labels = st.multiselect("Select student(s)", list(student_labels), key="cleanup_students_selected")
            cleanup_action = st.radio(
                "Choose action",
                ["Clear academic/fee activity (keep student record)", "Delete student record and linked activity"],
                key="cleanup_student_action",
            )
            st.caption("Clear keeps the student name, student ID and account mapping, but removes attendance, fee records/payments, scores, submissions and batch enrollments. Delete removes the student record too. Shared batches, meetings and assignments are not deleted by a selected-student action.")
            confirmation_text = "CLEAR SELECTED STUDENTS" if cleanup_action.startswith("Clear") else "DELETE SELECTED STUDENTS"
            typed_confirmation = st.text_input(f"Type exactly: {confirmation_text}", key="cleanup_selected_confirmation")
            if st.button("Run selected-student action", type="primary", disabled=not selected_labels, key="cleanup_selected_run"):
                if typed_confirmation.strip() != confirmation_text:
                    st.error("Confirmation text does not match. No data was changed.")
                else:
                    ids = [str(student_labels[label]["id"]) for label in selected_labels]
                    rpc_name = "admin_clear_student_activity" if cleanup_action.startswith("Clear") else "admin_delete_students"
                    response = safe_call(lambda: sb.rpc(rpc_name, {"target_student_ids": ids}).execute(), None)
                    if response is not None:
                        st.success(f"Request completed: {cleanup_action.lower()} for {len(ids)} selected student(s). Review the cleanup audit log in Supabase.")
                        st.session_state.pop("cleanup_students_selected", None)
                        st.rerun()

        st.divider()
        st.subheader("3. Full operational database reset")
        st.warning("This removes all students, batches, batch enrollments, class meetings, attendance, assignments, assignment submissions, assessment scores, fee records and payments. It preserves profiles/Auth accounts and the database schema. Do not use this for routine maintenance.")
        full_confirm = st.text_input('Type exactly: RESET ALL ACADEMY DATA', key="cleanup_full_confirmation")
        full_ack = st.checkbox("I have exported and checked backups, and understand this deletes all academy operational records.", key="cleanup_full_ack")
        if st.button("Reset all academy data", type="primary", disabled=not full_ack, key="cleanup_full_run"):
            if full_confirm.strip() != "RESET ALL ACADEMY DATA":
                st.error("Confirmation text does not match. No data was changed.")
            else:
                response = safe_call(lambda: sb.rpc("admin_reset_academy_data", {}).execute(), None)
                if response is not None:
                    st.success("Full operational reset completed. Admin/tutor/student/parent login profiles and database structure were preserved.")
                    st.rerun()

        st.divider()
        st.subheader("4. Audit history")
        st.caption("Destructive actions are recorded by database functions in `admin_cleanup_audit`. If the table is not yet available, apply the cleanup migration before using these controls.")
        audit_rows = safe_call(lambda: result_data(sb.table("admin_cleanup_audit").select("created_at,actor_id,action,scope,details").order("created_at", desc=True).limit(100).execute()), None)
        if audit_rows is not None:
            if audit_rows:
                st.dataframe(table_df(audit_rows), use_container_width=True, hide_index=True)
            else:
                st.caption("No cleanup actions recorded yet.")

st.divider()
st.caption("© 2026 JrAdemy Online Tuition · Classes 1–10 · CBSE · ICSE · Karnataka State Board")
