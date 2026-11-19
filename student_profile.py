"""Student Profile & Pre-Arrival Checklist Engine.

Supports:
1. Authenticated InSIS Students (e.g. George Joseph) with opt-in GDPR-safe
   personalised study context (ECTS progress, credit vouchers, enrolled courses,
   pending coursework deadlines, and thesis status).
2. Interactive Onboarding Checklists for pre-arrival, arrival, and study stages.
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
    "thesis_submission_status": "Pending final PDF/A upload in InSIS",
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
    }]


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
