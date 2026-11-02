"""Student Profile, Smart Page Context & Pre-Arrival Checklist Engine.

Supports both:
1. Unauthenticated / No-Account Public Users on https://insis.vse.cz/?lang=en
   (pre-arrival visa, dorms/stay, admission e-application, public course catalogue).
2. Authenticated InSIS Students (e.g. George Joseph) with opt-in GDPR-safe
   personalised study context and live InSIS page awareness.
"""

from typing import Any, Dict, List, Optional

# Base ISM Master's student profile template; adapts dynamically to any logged-in student's name
DEFAULT_ISM_PROFILE_TEMPLATE: Dict[str, Any] = {
    "programme": "Master in Information Systems Management (FIS C-ISM-MBI pres [term 5, E])",
    "faculty": "Faculty of Informatics and Statistics (FIS)",
    "study_period": "WS 2026/2027 - FIS",
    "degree_target_ects": 120,
    "earned_ects": 90,
    "current_enrolled_ects": 24,
    "remaining_ects_needed": 30,
    "remaining_ects_after_current_term": 6,
    "initial_vouchers": 144,
    "remaining_vouchers": 120,
    "used_vouchers_current_sem": 24,
    "weighted_gpa": 1.42,
    "variable_symbol": "84920194",
    "tuition_status": "Cleared (0.00 CZK outstanding)",
    "thesis_title": "Improving International Student Experience with GenAI based tool at University of Economics and Business in Prague",
    "thesis_supervisor": "Ing. Pavel Sládek, Ph.D.",
    "thesis_department": "Department of Information Technology (FIS)",
    "thesis_assignment_status": "Confirmed by supervisor; student can no longer edit the assignment",
    "thesis_submission_status": "Final thesis has not yet been entered into InSIS (3 red X editing steps pending: Insert additional info, Insert thesis PDF/appendices, Final submission)",
    "enrolled_courses": [
        "4IT445 Advanced Data Analytics (6 ECTS, Mon 09:15 RB 101)",
        "4SA421 Information Systems Management (6 ECTS, Tue 14:30 SB 204)",
        "2SE411 European Economic Integration (6 ECTS, Thu 11:00 NB 403)",
        "1PE401 Business Ethics & Governance (6 ECTS, Fri 09:15 JM 310)",
    ],
    "pending_assignments": [
        {
            "id": "4it445_m2",
            "course_code": "4IT445",
            "course_name": "Advanced Data Analytics",
            "task_title": "Milestone 2 - Machine Learning Pipeline Report",
            "due_date": "Nov 15, 2026 (23:59)",
            "urgency": "urgent",
            "days_left": "3 days left",
            "weight": "25 points",
            "submission_url": "https://insis.vse.cz/auth/student/odevzdavarna.pl?course=4IT445&lang=en",
            "button_label": "📂 Go to 4IT445 Submission Page",
        },
        {
            "id": "4sa421_cs",
            "course_code": "4SA421",
            "course_name": "Information Systems Management",
            "task_title": "Enterprise Architecture Case Study",
            "due_date": "Nov 22, 2026 (23:59)",
            "urgency": "upcoming",
            "days_left": "10 days left",
            "weight": "30 points",
            "submission_url": "https://insis.vse.cz/auth/student/odevzdavarna.pl?course=4SA421&lang=en",
            "button_label": "📂 Go to 4SA421 Submission Page",
        },
        {
            "id": "thesis_abstract",
            "course_code": "DIP-THESIS",
            "course_name": "Master's Thesis",
            "task_title": "Insert Additional Info (Abstracts & Keywords) & Upload Thesis PDF",
            "due_date": "Nov 30, 2026 (23:59)",
            "urgency": "upcoming",
            "days_left": "18 days left",
            "weight": "Thesis Requirement (§ 47b)",
            "submission_url": "https://insis.vse.cz/auth/student/zp.pl?lang=en",
            "button_label": "🎓 Go to Master's Thesis Submission Area",
        },
        {
            "id": "2se411_pb",
            "course_code": "2SE411",
            "course_name": "European Economic Integration",
            "task_title": "Policy Brief Essay",
            "due_date": "Dec 05, 2026 (23:59)",
            "urgency": "later",
            "days_left": "23 days left",
            "weight": "20 points",
            "submission_url": "https://insis.vse.cz/auth/student/odevzdavarna.pl?course=2SE411&lang=en",
            "button_label": "📂 Go to 2SE411 Submission Page",
        },
    ],
}

STUDENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "george joseph": {"name": "George Joseph", **DEFAULT_ISM_PROFILE_TEMPLATE},
}


def get_student_profile(user_name: str) -> Dict[str, Any]:
    """Return personalised study profile matching the exact logged-in user's name."""
    clean_name = (user_name or "").strip() or "Authenticated Student"
    existing = STUDENT_PROFILES.get(clean_name.lower())
    if existing:
        return dict(existing)
    profile = dict(DEFAULT_ISM_PROFILE_TEMPLATE)
    profile["name"] = clean_name
    return profile

# Screen-level descriptions for Context-Aware Co-Pilot (Idea 1)
INSIS_PAGE_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "public_home": {
        "title": "Public Information Portal (No Login Required)",
        "url": "https://insis.vse.cz/?lang=en",
        "summary": (
            "The user is currently on the PUBLIC InSIS homepage without logging in. "
            "Visible public sections on screen: "
            "1. Personal administration ('Log in to the Personal administration of InSIS', 'First log in to InSIS instructions', 'System integrators'); "
            "2. Admission procedure ('E-application form to study at VŠE', 'Pre-enrollment confirmation', 'Courses on offer', 'Application to U3V'); "
            "3. Information about VŠE ('Persons at VŠE', 'Validity verification of ID cards', 'Departments', 'Thematic search', 'Public document server'); "
            "4. Study information ('Academic year schedule', 'Study plans', 'Course catalogue', 'Electronic study materials', 'Final theses at VŠE', 'Timetables', 'Study financing'); "
            "5. Science and research ('Projects', 'Publications'); "
            "6. Jobs portal ('Registration of a company to Internship Portal'); "
            "7. About the information system ('InSIS documentation', 'Statistics of using InSIS')."
        ),
    },
    "personal_admin": {
        "title": "Personal Administration (Logged-In Home)",
        "url": "https://insis.vse.cz/auth/?lang=en",
        "summary": (
            "The logged-in student is viewing the Personal Administration dashboard. "
            "Visible module tiles: Public information portal, My College (with 'Student's portal' link), "
            "eLearning ('Tests and examinations', 'Electronic study materials'), Personal management ('Document server', 'Mail box'), "
            "eAgenda ('Contact centre', 'eSurveys', 'Electronic document verification'), and Information system set-up ('OTP authentication')."
        ),
    },
    "student_portal": {
        "title": "Student's Portal (My College)",
        "url": "https://insis.vse.cz/auth/student/studium.pl?lang=en",
        "summary": (
            "The student is viewing Student's Portal (FIS C-ISM-MBI pres [term 5, E]). "
            "Top tabs: My College, E-study record, My schoolmates, Study details, Map of my study, Course e-plans, "
            "List of topics, Coursework submissions, Plan progress check, My lectures sheet. "
            "Main study row icons: Register for examinations (pen), Registration/Enrollment, Extra-sem. courses, Final thesis (green book icon)."
        ),
    },
    "master_thesis": {
        "title": "Student's Portal » Master's Thesis",
        "url": "https://insis.vse.cz/auth/student/zp.pl?lang=en",
        "summary": (
            "The student is viewing their Master's Thesis management page. "
            "Assignment status: Confirmed by supervisor Ing. Pavel Sládek, Ph.D. "
            "Blue notice banner: 'Thesis has not been entered – Final thesis has not been entered in the information system.' "
            "Editing application icons at bottom (currently showing red X incomplete badges): "
            "1. 'Insert additional information' (EN/CZ abstracts & keywords), "
            "2. 'Insert the thesis and the appendices' (PDF/A & ZIP), "
            "3. 'Thesis submission' (irreversible lock), plus 'Insert errata (§ 47b)'."
        ),
    },
    "coursework_submissions": {
        "title": "Student's Portal » Coursework Submissions (Odevzdávárna)",
        "url": "https://insis.vse.cz/auth/student/odevzdavarna.pl?lang=en",
        "summary": (
            "The student is viewing Coursework Submissions (Odevzdávárna). "
            "Active course drop-boxes: "
            "1. 4IT445 Advanced Data Analytics: 'Milestone 2 - Machine Learning Pipeline Report' (Due: Nov 15, 2026, 23:59, max 20 MB PDF/ZIP, Status: Pending submission); "
            "2. 4SA421 Information Systems Management: 'Enterprise Architecture Case Study' (Due: Nov 22, 2026, 23:59, max 25 MB PDF, Status: Pending submission); "
            "3. 2SE411 European Economic Integration: 'Policy Brief Essay' (Due: Dec 05, 2026, 23:59, max 10 MB PDF, Status: Not yet opened); "
            "4. 1PE401 Business Ethics & Governance: 'Ethical Dilemma Presentation Slides' (Due: Dec 12, 2026, 23:59, Status: Not yet opened). "
            "On screen features: Select assignment drop-box, browse file upload, submit button, and submission protocol verification."
        ),
    },
}

# Topic cue lists for Smart Topic Check
SCREEN_DEICTIC_CUES = [
    "this page", "this screen", "what do i click", "where do i click", "click here",
    "on my screen", "what is this", "red x", "green book", "which icon", "which button",
    "where am i", "current page", "explain this page", "on this page", "locked icon",
]

PERSONAL_STUDY_CUES = [
    "who am i", "my name", "my profile", "logged in", "my account",
    "my credit", "my credits", "my voucher", "my vouchers", "my thesis", "my gpa",
    "my grade", "my grades", "my course", "my courses", "my timetable", "my schedule",
    "my variable symbol", "my tuition", "my study", "credit vouchers",
    "how many vouchers", "how many credit vouchers", "vouchers left", "vouchers remaining",
    "can i afford to fail", "if i fail", "drop a course", "do i have enough",
    "my supervisor", "am i eligible", "my balance", "left", "remaining",
    "assignment", "assignments", "homework", "task", "tasks", "submission", "submissions",
    "odevzdavarna", "odevzdani", "odevzdání", "due", "deadline", "deadlines", "pending", "to do",
    "credits left", "credits remaining", "degree progress", "how many credits",
]

EXTERNAL_LIFE_STAY_VISA_CUES = [
    "visa", "visas", "foreign police", "cizinecka", "embassy", "mvcr", "oamp", "biometric",
    "dorm", "dorms", "dormitory", "dormitories", "iskam", "koleje",
    "accommodation", "accomodation", "stay", "housing", "flat", "flats", "apartment",
    "apartments", "rent", "living", "find a place", "room", "guest", "quiet hours",
    "smoking", "insurance", "pvzp", "ehic", "doctor", "hospital", "emergency", "mental",
    "psycholog", "stress", "anxiety", "washroom", "toilet", "wc", "bathroom", "restroom",
    "menza", "canteen", "library", "tram", "metro", "litacka", "pid", "transport",
    "arrive", "arrival",
]


def build_dynamic_context_chunks(
    question: str,
    user_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Build optional context chunks based on login state, page context, and Smart Topic Check.

    Guarantees that if a student (logged in or guest) asks about visas, stay/dorms,
    campus rooms, or general life in Prague, the open InSIS screen does NOT pollute
    or hijack the answer.
    """
    if not user_context:
        return []

    q_lower = question.lower()
    logged_in = bool(user_context.get("logged_in", False))
    personalised_on = bool(user_context.get("personalised", True))
    user_name = str(user_context.get("user_name") or "Guest").strip()
    page_key = str(user_context.get("page_key") or "").strip()
    page_title = str(user_context.get("page_title") or "").strip()
    page_url = str(user_context.get("page_url") or "").strip()

    asks_external_life = any(cue in q_lower for cue in EXTERNAL_LIFE_STAY_VISA_CUES)
    asks_screen = any(cue in q_lower for cue in SCREEN_DEICTIC_CUES)
    asks_personal = any(cue in q_lower for cue in PERSONAL_STUDY_CUES)

    extra_chunks: List[Dict[str, Any]] = []

    # 1. NO-LOGIN / PUBLIC PORTAL USER
    if not logged_in:
        # Inject Public InSIS Portal context whenever the user specifically asks about the screen,
        # navigation on this page, or public admission/courses.
        # Do NOT hijack questions about vouchers, accommodation, visas, or rules.
        explicit_no_account = any(
            kw in q_lower for kw in ("no account", "without login", "without account", "without insis", "before login", "this page", "this screen")
        )
        is_academic_rule = any(kw in q_lower for kw in ("voucher", "vouchers", "credit", "credits", "ects", "grading", "exam"))

        is_authenticated_insis_task = any(
            kw in q_lower for kw in (
                "general query", "general querry", "contact centre", "contact center",
                "kontaktní", "kontaktni", "ubytovací", "ubytovaci", "benefit", "stipend",
                "scholarship", "errata", "final thesis", "master thesis", "bachelor thesis",
                "odevzdani", "potvrzeni o studiu", "confirmation of study"
            )
        )

        if asks_screen or explicit_no_account or (not asks_external_life and not is_academic_rule and not is_authenticated_insis_task):
            pub_info = INSIS_PAGE_DESCRIPTIONS["public_home"]
            extra_chunks.append({
                "id": "public_insis_context",
                "doc_id": "public_insis_portal",
                "title": "InSIS Public Portal Guide (No Login / Pre-Arrival Access)",
                "source_url": "https://insis.vse.cz/?lang=en",
                "date_saved": "2026-11-01",
                "unverified": False,
                "score": 0.99,
                "text": (
                    "User Status: Unauthenticated Public User / Prospective or Incoming Student (NOT logged into InSIS).\n"
                    f"{pub_info['summary']}\n"
                    "Key Public InSIS Links Accessible WITHOUT Login:\n"
                    "- E-application form to study at VŠE: https://insis.vse.cz/prihlaska/?lang=en (under 'Admission procedure' — create/manage admission application without a student account; Admission Office RB 527, admissions@vse.cz)\n"
                    "- Pre-enrollment confirmation: https://insis.vse.cz/navratka/?lang=en | Courses on offer: https://insis.vse.cz/kurzy/?lang=en\n"
                    "- First log in to InSIS instructions: https://insis.vse.cz/navod/?lang=en (under 'Personal administration')\n"
                    "- Course catalogue: https://insis.vse.cz/katalog/?lang=en | Study plans: https://insis.vse.cz/katalog/plany.pl?lang=en | Timetables: https://insis.vse.cz/katalog/rozvrhy.pl?lang=en | Academic year schedule: https://insis.vse.cz/harmonogram/harmonogram.pl?lang=en (all under 'Study information')\n"
                    "- Persons at VŠE: https://insis.vse.cz/lide/?lang=en | Departments: https://insis.vse.cz/pracoviste/pracoviste.pl?lang=en | Public document server: https://insis.vse.cz/dok_server/?lang=en\n"
                    "Guidance rule: Direct this user to the PUBLIC links available right on https://insis.vse.cz/?lang=en without login. "
                    "If they ask about an action that requires a student account (such as personal exam registration, grades, or thesis upload), "
                    "explain the procedure briefly AND note that they will need to sign in via 'Log in to the Personal administration of InSIS' once they have VŠE credentials."
                ),
                "is_dynamic_context": True,
            })
        return extra_chunks

    # 2. LOGGED-IN STUDENT: If asking purely about visas, dorm stay, washrooms, etc. -> DO NOT inject InSIS page clutter!
    if asks_external_life and not asks_screen and not asks_personal:
        return []

    # 3. Inject Live Page Context (Idea 1) when asking about the current screen
    if asks_screen:
        known_page = INSIS_PAGE_DESCRIPTIONS.get(page_key)
        summary_text = (
            known_page["summary"]
            if known_page
            else f"The logged-in student currently has InSIS page '{page_title}' ({page_url}) open on screen."
        )
        extra_chunks.append({
            "id": f"live_page_{page_key or 'custom'}",
            "doc_id": "insis_live_screen",
            "title": f"Current Open InSIS Screen: {page_title or (known_page['title'] if known_page else 'InSIS')}",
            "source_url": page_url or "https://insis.vse.cz/auth/?lang=en",
            "date_saved": "2026-11-01",
            "unverified": False,
            "score": 0.995,
            "text": summary_text,
            "is_dynamic_context": True,
        })

    # 4. Inject Personalised Study Profile (Idea 2) when opt-in is ON and question relates to personal academics or screen
    if personalised_on and (asks_personal or asks_screen):
        profile = get_student_profile(user_name)
        courses_str = "; ".join(profile["enrolled_courses"])
        assignments = profile.get("pending_assignments", [])
        assignments_lines = []
        for a in assignments:
            assignments_lines.append(
                f"- {a['course_code']} ({a['course_name']}): '{a['task_title']}' | "
                f"Due: {a['due_date']} ({a['days_left']}) | Weight: {a['weight']} | "
                f"Direct Link: [{a['button_label']}]({a['submission_url']})"
            )
        assignments_str = "\n".join(assignments_lines)

        extra_chunks.append({
            "id": "student_personal_profile",
            "doc_id": "insis_student_profile",
            "title": f"Personalised InSIS Study Record: {profile['name']}",
            "source_url": "https://insis.vse.cz/auth/student/studium.pl?lang=en",
            "date_saved": "2026-11-01",
            "unverified": False,
            "score": 0.995,
            "text": (
                f"Authenticated Student: {profile['name']}\n"
                f"Programme: {profile['programme']} ({profile['faculty']})\n"
                f"Active Period: {profile['study_period']}\n"
                f"Credits Earned: {profile['earned_ects']} / {profile['degree_target_ects']} ECTS "
                f"({profile['remaining_ects_needed']} ECTS needed to graduate)\n"
                f"Current Enrolled Semester Credits: {profile.get('current_enrolled_ects', 24)} ECTS (in progress this semester across 4 courses)\n"
                f"Net Remaining to Graduate After Current Semester: {profile.get('remaining_ects_after_current_term', 6)} ECTS\n"
                f"Credit Vouchers: {profile['remaining_vouchers']} remaining out of {profile['initial_vouchers']} initial Master's vouchers "
                f"({profile['used_vouchers_current_sem']} used in current semester; voucher buffer is safe)\n"
                f"Weighted GPA: {profile['weighted_gpa']} (scale 1=Excellent to 4=Fail)\n"
                f"Tuition Variable Symbol: {profile['variable_symbol']} | Tuition Status: {profile['tuition_status']}\n"
                f"Enrolled Courses: {courses_str}\n"
                f"Pending Coursework Assignments & Deadlines:\n{assignments_str}\n"
                f"Master's Thesis: '{profile['thesis_title']}' | Supervisor: {profile['thesis_supervisor']} | "
                f"Assignment: {profile['thesis_assignment_status']} | Submission: {profile['thesis_submission_status']} | "
                f"Direct Thesis Link: [🎓 Go to Master's Thesis Submission Area](https://insis.vse.cz/auth/student/zp.pl?lang=en)\n"
                f"Direct Study Record Link: [📑 View Full E-Study Record](https://insis.vse.cz/auth/student/studium.pl?lang=en)"
            ),
            "is_dynamic_context": True,
        })

    return extra_chunks


def get_onboarding_checklist(
    origin: str = "non_eu",
    housing: str = "dorm",
    stage: str = "pre_arrival",
) -> List[Dict[str, str]]:
    """Generate a tailored checklist for Idea 3 (works for both No-Login & Logged-In students)."""
    origin = origin.lower()
    housing = housing.lower()
    stage = stage.lower()

    items: List[Dict[str, str]] = []

    if stage == "pre_arrival":
        items.append({
            "task": "Submit VŠE E-Application & pay admission fee on Public InSIS",
            "prompt": "How do I submit the E-application form to study at VŠE?",
        })
        if origin == "non_eu":
            items.append({
                "task": "Book Czech Embassy visa/residence appointment & arrange pVZP insurance",
                "prompt": "What are the visa and health insurance requirements for non-EU students?",
            })
        else:
            items.append({
                "task": "Bring valid EU ID/Passport and European Health Insurance Card (EHIC)",
                "prompt": "What health insurance do EU students need in Prague?",
            })
        if housing == "dorm":
            items.append({
                "task": "Apply for VŠE Dormitory room & pay booking deposit in ISKaM",
                "prompt": "How do I apply for a VŠE dormitory room in ISKaM?",
            })
        else:
            items.append({
                "task": "Secure signed Czech lease agreement (proof of accommodation)",
                "prompt": "What should I check when renting private accommodation in Prague?",
            })
        items.append({
            "task": "Prepare nostrification (recognition of previous foreign diploma)",
            "prompt": "How does foreign diploma recognition (nostrification) work at VŠE?",
        })

    elif stage == "arrival":
        if origin == "non_eu" and housing != "dorm":
            items.append({
                "task": "URGENT (3 Working Days): Register address in person at Foreign Police!",
                "prompt": "How do I register with the Foreign Police within 3 days of arrival?",
            })
        elif housing == "dorm":
            items.append({
                "task": "Check into VŠE Dormitory (SÚZ reports Foreign Police automatically!)",
                "prompt": "Does VŠE dormitory register me with the Foreign Police automatically?",
            })
        else:
            items.append({
                "task": "EU Stay > 30 days: Optional Foreign Police registration if in private flat",
                "prompt": "Do EU students need to register with the Foreign Police?",
            })
        items.append({
            "task": "Read 'First log in to InSIS' & set up OTP two-factor authentication",
            "prompt": "How do I change my password and set up OTP authentication in InSIS?",
        })
        items.append({
            "task": "Upload ID photo in InSIS & pick up ISIC card at Room SB 01",
            "prompt": "Where is the Student Card Centre to pick up my ISIC card?",
        })
        items.append({
            "task": "Download Confirmation of Study PDF for Prague Lítačka transport pass",
            "prompt": "How do I download an electronic Confirmation of Study in InSIS?",
        })

    else:  # studies / exams / thesis
        items.append({
            "task": "Check credit vouchers & ensure >= 9 ECTS in 1st semester (20 ECTS/year)",
            "prompt": "What is the minimum 9 ECTS credit rule and how do vouchers work?",
        })
        items.append({
            "task": "Verify tuition Variable Symbol before semester payment deadline",
            "prompt": "Where do I find my Variable Symbol for tuition payment?",
        })
        items.append({
            "task": "Locate your FIS/FMV/FPH Study Coordinator office hours",
            "prompt": "Where is the study coordinator office for FIS?",
        })
        items.append({
            "task": "Confirm Final Thesis assignment & PDF/A submission steps in InSIS",
            "prompt": "Where do I upload my final Master's thesis in InSIS?",
        })

    return items
