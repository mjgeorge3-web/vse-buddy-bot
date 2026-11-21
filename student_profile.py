"""Student Profile & Pre-Arrival Checklist Engine.

Supports:
1. Simulated Authenticated InSIS Student Demo Profile (opt-in, GDPR-safe):
   provides synthetic ECTS progress, credit voucher balance, enrolled courses,
   pending coursework deadlines, and thesis status for prototype demonstration.
2. Interactive Onboarding Checklists for pre-arrival, arrival, and study stages.
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional


def _build_dynamic_assignments() -> List[Dict[str, str]]:
    """Generate demo coursework deadlines relative to today so dates never go stale."""
    today = date.today()
    d3 = today + timedelta(days=3)
    d10 = today + timedelta(days=10)
    d18 = today + timedelta(days=18)
    d23 = today + timedelta(days=23)
    return [
        {
            "id": "4it445_m2",
            "course_code": "4IT445",
            "course_name": "Advanced Data Analytics (Demo)",
            "task_title": "Milestone 2 - Data Pipeline Report",
            "due_date": f"{d3.strftime('%b %d, %Y')} (23:59)",
            "urgency": "urgent",
            "days_left": "3 days left",
            "weight": "25 points",
            "submission_url": "https://insis.vse.cz/auth/student/odevzdavarna.pl?course=4IT445&lang=en",
            "button_label": "📂 Go to 4IT445 Submission Page",
        },
        {
            "id": "4sa421_cs",
            "course_code": "4SA421",
            "course_name": "Information Systems Management (Demo)",
            "task_title": "Enterprise Architecture Case Study",
            "due_date": f"{d10.strftime('%b %d, %Y')} (23:59)",
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
            "due_date": f"{d18.strftime('%b %d, %Y')} (23:59)",
            "urgency": "upcoming",
            "days_left": "18 days left",
            "weight": "Thesis Requirement (§ 47b)",
            "submission_url": "https://insis.vse.cz/auth/student/zp.pl?lang=en",
            "button_label": "🎓 Go to Master's Thesis Submission Area",
        },
        {
            "id": "2se411_pb",
            "course_code": "2SE411",
            "course_name": "European Economic Integration (Demo)",
            "task_title": "Policy Brief Essay",
            "due_date": f"{d23.strftime('%b %d, %Y')} (23:59)",
            "urgency": "later",
            "days_left": "23 days left",
            "weight": "20 points",
            "submission_url": "https://insis.vse.cz/auth/student/odevzdavarna.pl?course=2SE411&lang=en",
            "button_label": "📂 Go to 2SE411 Submission Page",
        },
    ]


# Synthetic ISM Master's demo student profile template (not real InSIS SSO data)
# Voucher math: 144 initial - 90 earned - 24 currently enrolled = 30 remaining vouchers
# (6 ECTS remaining after this term + 24 buffer vouchers).
DEFAULT_ISM_PROFILE_TEMPLATE: Dict[str, Any] = {
    "programme": "Master in Information Systems Management (FIS — Demo Profile)",
    "faculty": "Faculty of Informatics and Statistics (FIS)",
    "study_period": "Current Academic Term (Demo)",
    "degree_target_ects": 120,
    "earned_ects": 90,
    "current_enrolled_ects": 24,
    "remaining_ects_needed": 30,
    "remaining_ects_after_current_term": 6,
    "initial_vouchers": 144,
    "used_vouchers_total": 114,
    "used_vouchers_current_sem": 24,
    "remaining_vouchers": 30,
    "voucher_buffer": 24,
    "weighted_gpa": 1.42,
    "variable_symbol": "00000000 (Demo VS)",
    "tuition_status": "Cleared (Demo Record)",
    "thesis_title": "Sample Master's Thesis: AI-Assisted Student Support Prototype",
    "thesis_supervisor": "Sample FIS Thesis Supervisor",
    "thesis_department": "Department of Information Technology (FIS)",
    "thesis_assignment_status": "Confirmed by supervisor (demo status)",
    "thesis_submission_status": "Pending final PDF/A upload in InSIS",
    "enrolled_courses": [
        "4IT445 Advanced Data Analytics (6 ECTS, Demo)",
        "4SA421 Information Systems Management (6 ECTS, Demo)",
        "2SE411 European Economic Integration (6 ECTS, Demo)",
        "3PE401 Business Ethics & Governance (6 ECTS, Demo)",
    ],
}

STUDENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "alex novak": {"name": "Alex Novak", **DEFAULT_ISM_PROFILE_TEMPLATE},
}


def get_student_profile(user_name: str) -> Dict[str, Any]:
    """Return synthetic demo study profile matching the logged-in demo user's name."""
    clean_name = (user_name or "").strip() or "Demo Student"
    existing = STUDENT_PROFILES.get(clean_name.lower())
    profile = dict(existing) if existing else dict(DEFAULT_ISM_PROFILE_TEMPLATE)
    profile["name"] = clean_name
    profile["pending_assignments"] = _build_dynamic_assignments()
    return profile


PERSONAL_STUDY_CUES = [
    "who am i", "my name", "my profile", "logged in", "my account",
    "my credit", "my credits", "my voucher", "my vouchers", "my thesis", "my gpa",
    "my grade", "my grades", "my course", "my courses", "my timetable", "my schedule",
    "my variable symbol", "my tuition", "my study",
    "how many vouchers do i", "how many credit vouchers do i",
    "how many vouchers i have", "how many credit vouchers i have",
    "vouchers do i have", "vouchers i have left", "vouchers remaining for me",
    "can i afford to fail", "drop a course", "do i have enough",
    "my supervisor", "am i eligible", "my balance",
    "my assignment", "my assignments", "pending assignment", "pending assignments",
    "my homework", "my task", "my tasks", "my submission", "my submissions",
    "my odevzdavarna", "my deadline", "my deadlines",
    "pending deadline", "pending deadlines", "what is due", "assignments due",
    "credits do i have left", "credits left to graduate", "my degree progress",
    "how many credits do i", "assignments do i have", "tasks do i have",
]


def build_dynamic_context_chunks(
    question: str,
    user_context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Build optional personalised study profile context chunk when opt-in is enabled.

    Does NOT guess or inject open screen descriptions, keeping responses strictly focused
    on the student's question and verified VŠE / personal study data.
    """
    if not user_context:
        return []

    q_lower = question.lower()
    logged_in = bool(user_context.get("logged_in", False))
    personalised_on = bool(user_context.get("personalised", True))
    user_name = str(user_context.get("user_name") or "Guest").strip()

    if not logged_in or not personalised_on:
        return []

    asks_personal = any(cue in q_lower for cue in PERSONAL_STUDY_CUES)
    if not asks_personal:
        return []

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

    return [{
        "id": "student_personal_profile",
        "doc_id": "insis_student_profile",
        "title": f"Personalised InSIS Study Record: {profile['name']}",
        "source_url": "https://insis.vse.cz/auth/student/studium.pl?lang=en",
        "date_saved": date.today().isoformat(),
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
            f"({profile['earned_ects']} used for earned ECTS + {profile['used_vouchers_current_sem']} used this semester = {profile['used_vouchers_total']} used; "
            f"6 needed after current term + {profile['voucher_buffer']} buffer vouchers)\n"
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
    }]


def get_onboarding_checklist(
    origin: str = "non_eu",
    housing: str = "dorm",
    stage: str = "pre_arrival",
) -> List[Dict[str, str]]:
    """Generate a stage-aware onboarding checklist for both guest and logged-in students."""
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
                "task": "Book Czech Embassy visa/residence appointment & arrange comprehensive Czech health insurance",
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
            "task": "Prepare foreign diploma assessment / recognition documents for VŠE",
            "prompt": "How does foreign diploma assessment (nostrification) work at VŠE?",
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
                "task": "EU Stay > 30 days: Mandatory Foreign Police reporting within 30 days if in private flat (Act No. 326/1999 Sb. § 93)",
                "prompt": "Do EU students need to register with the Foreign Police?",
            })
        items.append({
            "task": "Read 'First log in to InSIS' & set up OTP two-factor authentication",
            "prompt": "How do I change my password and set up OTP authentication in InSIS?",
        })
        items.append({
            "task": "Upload ID photo in InSIS & pick up ISIC card at the VŠE Student ID Card Centre (SB)",
            "prompt": "Where is the Student Card Centre to pick up my ISIC card?",
        })
        items.append({
            "task": "Download Confirmation of Study PDF for Prague Lítačka transport pass",
            "prompt": "How do I download an electronic Confirmation of Study in InSIS?",
        })

    else:  # studies / exams / thesis
        items.append({
            "task": "Check credit vouchers & ensure >= 9 ECTS in 1st semester (20 ECTS per active semester)",
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
