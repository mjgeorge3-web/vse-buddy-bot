"""InSIS Navigation & Campus Database with 50 University Policies & Floor Locations.

Provides an SQLite database (`data/insis_navigation.db`) and query engine
for guiding international students through:
1. InSIS Navigation Routes (20+ tasks with breadcrumbs and demo links)
2. 50 VŠE Policies, Rules, Regulations & Penalties
3. Complete Floor-by-Floor Campus Navigation (washrooms on each floor,
   classrooms, study coordinator offices, lecture halls, and amenities).
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from vse_data_fixtures import POLICIES_50, CAMPUS_LOCATIONS

DB_PATH = Path(__file__).resolve().parent / "data" / "insis_navigation.db"

# Schema definitions
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- 1. InSIS Modules & Navigation Routes
CREATE TABLE IF NOT EXISTS insis_modules (
    module_id TEXT PRIMARY KEY,
    title_en TEXT NOT NULL,
    title_cs TEXT NOT NULL,
    description TEXT,
    icon TEXT
);

CREATE TABLE IF NOT EXISTS insis_routes (
    task_id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL,
    title_en TEXT NOT NULL,
    title_cs TEXT NOT NULL,
    category TEXT NOT NULL,
    portal_path TEXT NOT NULL,
    official_url TEXT NOT NULL,
    demo_url TEXT NOT NULL,
    breadcrumbs TEXT NOT NULL,
    step_by_step_instructions TEXT NOT NULL,
    prerequisites TEXT,
    common_pitfalls TEXT,
    keywords TEXT NOT NULL,
    FOREIGN KEY (module_id) REFERENCES insis_modules(module_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS insis_routes_fts USING fts5(
    task_id UNINDEXED,
    title_en,
    title_cs,
    category,
    breadcrumbs,
    step_by_step_instructions,
    keywords,
    tokenize = 'porter unicode61'
);

-- 2. VŠE Policies, Rules & Regulations
CREATE TABLE IF NOT EXISTS vse_policies (
    rule_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    rule_text TEXT NOT NULL,
    official_reference TEXT NOT NULL,
    penalty_or_consequence TEXT,
    faq_triggers TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS vse_policies_fts USING fts5(
    rule_id UNINDEXED,
    category,
    title,
    summary,
    rule_text,
    official_reference,
    faq_triggers,
    tokenize = 'porter unicode61'
);

-- 3. Campus Navigation (Classrooms, Washrooms, Coordinators)
CREATE TABLE IF NOT EXISTS campus_locations (
    location_id TEXT PRIMARY KEY,
    building TEXT NOT NULL,
    floor TEXT NOT NULL,
    room_number TEXT NOT NULL,
    facility_type TEXT NOT NULL,
    name TEXT NOT NULL,
    directions_from_entrance TEXT NOT NULL,
    amenities_accessibility TEXT,
    hours_or_availability TEXT,
    keywords TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS campus_locations_fts USING fts5(
    location_id UNINDEXED,
    building,
    floor,
    room_number,
    facility_type,
    name,
    directions_from_entrance,
    keywords,
    tokenize = 'porter unicode61'
);
"""

MODULES_DATA = [
    ("portal_student", "Student's Portal / My College", "Portál studenta / Moje studium", "Core academic tasks: enrollment, exams, study plan, grades, and thesis", "🎓"),
    ("portal_public", "Public Information Portal", "Veřejný informační portál", "Public course catalogue, study plans, schedules, faculty and person search", "🌐"),
    ("portal_elearning", "eLearning & Examinations", "eLearning a zkoušky", "Course materials, e-tests, coursework dropboxes, and state exam topics", "📚"),
    ("portal_personal", "Personal Management", "Osobní management", "Internal mailbox, document server, news notifications, and calendar sync", "📬"),
    ("portal_eagenda", "eAgenda & Official Requests", "eAgenda a úřední úkony", "Contact centre, electronic document verification, and academic surveys", "📋"),
    ("portal_tech", "Technology & Adjustments", "Technologie a nastavení", "Account passwords, OTP 2-factor authentication, and student ID photos", "⚙️"),
    ("portal_finances", "Finances & Accommodation", "Finance a ubytování", "Tuition fees, bank account details, variable symbols, and ISKaM dorm link", "💳")
]

ROUTES_DATA = [
    (
        "TASK_THESIS_REGISTRATION",
        "portal_student",
        "Final Thesis Registration & Assignment Confirmation",
        "Registrace a zadání závěrečné práce",
        "Final Thesis",
        "/auth/student/diplomka.pl",
        "https://insis.vse.cz/auth/student/diplomka.pl?lang=en",
        "http://localhost:8502/auth/student/diplomka.pl",
        "Personal administration > My College > Student's portal > Final thesis (green book icon)",
        "1. Log into InSIS (https://insis.vse.cz).\n2. Click 'My College' or 'Student's portal'.\n3. In the study table, locate the 'Final thesis' column (icon with a green book) and click it.\n4. View 'Basic information about a final thesis' to check assignment status.\n5. Click 'Instructions for submission process of final thesis' to verify deadlines and supervisor confirmation.",
        "Must be enrolled in degree programme; supervisor must confirm the assignment in InSIS before submission unlocks.",
        "Assignment completeness status must show 'changes in assignment made by student have been confirmed by supervisor'. If not confirmed, submission icons remain locked.",
        "thesis registration, master thesis, bachelor thesis, assignment, diplomka, final thesis, supervisor approval, topic, zadani prace"
    ),
    (
        "TASK_THESIS_SUBMISSION",
        "portal_student",
        "Upload Final Thesis & Appendices (PDF/A)",
        "Odevzdání závěrečné práce a příloh",
        "Final Thesis",
        "/auth/student/diplomka.pl",
        "https://insis.vse.cz/auth/student/diplomka.pl?lang=en",
        "http://localhost:8502/auth/student/diplomka.pl",
        "Personal administration > My College > Student's portal > Final thesis > Editing application",
        "1. Navigate to: Student's portal > Final thesis.\n2. Under 'Editing application', click 'Insert additional information' to enter English & Czech abstracts and keywords.\n3. Click 'Insert the thesis and the appendices' (icon with paperclip).\n4. Upload the main thesis in PDF/A format (ensure fonts are embedded).\n5. Upload ZIP archive of source code, data, or supplementary models under 'Appendices'.\n6. Click 'Thesis submission' (icon with green arrow) to perform final irreversible submission.",
        "Both Czech and English abstracts and keywords must be filled. The file must comply with PDF/A standard. File size must not exceed 50 MB.",
        "Once you click 'Thesis submission', the submission is final and cannot be edited by the student. Any subsequent updates require official § 47b Errata approval.",
        "submit thesis, upload thesis, thesis pdf, odevzdani diplomky, final thesis upload, pdf/a, abstract, keywords, submission deadline"
    ),
    (
        "TASK_THESIS_ERRATA",
        "portal_student",
        "Post-Defense Thesis Errata Submission (§ 47b)",
        "Vložení errat k obhájené práci (§ 47b)",
        "Final Thesis",
        "/auth/student/diplomka.pl",
        "https://insis.vse.cz/auth/student/diplomka.pl?lang=en",
        "http://localhost:8502/auth/student/diplomka.pl",
        "Personal administration > My College > Student's portal > Final thesis > Post-defense errata",
        "1. Open Student's portal > Final thesis.\n2. Locate the 'Post-defense errata (§ 47b Higher Education Act)' section.\n3. Prepare a standalone PDF file documenting errata (corrections, typographical fixes) without altering original core findings.\n4. Upload the Errata PDF and click 'Submit Errata for Archival Review'.\n5. Retain the generated Errata Tracking Protocol number for your records.",
        "Allowed only after the formal thesis defense has taken place pursuant to Czech Act No. 111/1998 Sb. § 47b.",
        "Errata cannot rewrite the original thesis document; it is attached as an official separate corrective annex.",
        "errata, post-defense corrections, 47b, thesis errata, opravy po obhajobe, thesis error fix"
    ),
    (
        "TASK_COURSE_REGISTRATION",
        "portal_student",
        "Course Registration & Enrollment (Zápis předmětů)",
        "Registrace a zápis předmětů",
        "Enrollment",
        "/auth/student/prihlasovani.pl",
        "https://insis.vse.cz/auth/student/prihlasovani.pl?lang=en",
        "http://localhost:8502/auth/student/prihlasovani.pl",
        "Personal administration > My College > Student's portal > Registration/Enrollment",
        "1. Go to InSIS > My College > Student's portal.\n2. In the studies table row, click the icon under 'Registration/Enrollment' (fountain pen writing).\n3. Select the upcoming academic semester (e.g., WS 2026/2027 or SS 2026/2027).\n4. Choose 'Add course by code or plan' (compulsory obligatory group, elective, or language).\n5. Add courses to your registration basket.\n6. During the enrollment round (zápis), confirm your final schedule timetable slots.\n7. Check credit voucher total (do not exceed your remaining voucher balance).",
        "Enrollment occurs in strict time phases (Round 1 pre-registration, Round 2 enrollment by automated ranking, Round 3 open changes). Ensure tuition is paid.",
        "Missing the registration deadline leaves you unable to enroll in compulsory courses. Remember you must earn at least 9 ECTS in your first semester and 20 ECTS per academic year.",
        "course registration, zapis, enroll in courses, register classes, registration enrollment, add course, registration round, timetable slots"
    ),
    (
        "TASK_CREDIT_VOUCHERS",
        "portal_student",
        "Check Remaining Credit Vouchers & Study Progress",
        "Kontrola studijního plánu a poukázek (ECTS)",
        "Study Progress",
        "/auth/student/kontrola_planu.pl",
        "https://insis.vse.cz/auth/student/kontrola_planu.pl?lang=en",
        "http://localhost:8502/auth/student/kontrola_planu.pl",
        "Personal administration > My College > Student's portal > Plan progress check",
        "1. Navigate to InSIS > Student's portal.\n2. Click the 'Plan progress check' tab in the top navigation bar (or 'Progress of study' icon).\n3. Review 'Credit voucher balance': Initial allocation (144 vouchers for Master's, 216 for Bachelor's), spent vouchers, and remaining balance.\n4. Check required course categories: Compulsory (oP), Minor Specialization (sP), and Optional electives (vP).\n5. Verify that completed ECTS meet the threshold for progression to the next semester.",
        "Available at any time to active students. Shows automated calculation based on enrolled and completed courses.",
        "Failing a course consumes credit vouchers without granting credits. Running out of credit vouchers leads to study termination under VŠE Study and Examination Regulations Art. 12.",
        "credit vouchers, voucher balance, ects credits, kontrola planu, study progress, poukazky, credit limit, failed course penalty"
    ),
    (
        "TASK_EXAM_REGISTRATION",
        "portal_student",
        "Register for Examinations & Tests",
        "Přihlašování na zkoušky a testy",
        "Examinations",
        "/auth/student/prihlasovani.pl",
        "https://insis.vse.cz/auth/student/prihlasovani.pl?lang=en",
        "http://localhost:8502/auth/student/prihlasovani.pl",
        "Personal administration > My College > Student's portal > Register for examinations",
        "1. Go to InSIS > Student's portal.\n2. Click the fountain pen icon under 'Register for examinations' (or go to eLearning > Tests and examinations).\n3. Browse active course exam dates (termíny zkoušek).\n4. Review capacity, room number, examiner name, and cancellation deadline.\n5. Click 'Sign up' next to your preferred date.\n6. Confirm that the status updates to 'Registered'.",
        "Must be actively enrolled in the course and have met any semester prerequisite conditions (zápočet / continuous assessment threshold).",
        "Cancelling registration after the deadline or failing to appear without an excused medical absence results in grade '4 - Nevyhověl' (Fail) and burns an exam attempt.",
        "exam dates, register exam, exam registration, test dates, termin zkousky, sign up for exam, exam cancellation"
    ),
    (
        "TASK_TIMETABLE_VIEW",
        "portal_public",
        "Personal Timetable & Weekly Schedule (Rozvrh)",
        "Osobní rozvrh hodin",
        "Schedule",
        "/auth/katalog/rozvrhy.pl",
        "https://insis.vse.cz/auth/katalog/rozvrhy.pl?lang=en",
        "http://localhost:8502/auth/katalog/rozvrhy.pl",
        "Personal administration > My College > Student's portal > My lectures sheet (or Public information portal > Timetables)",
        "1. Log into InSIS.\n2. Go to 'Student's portal' > 'My lectures sheet' (or 'My timetable' in quick links).\n3. Select the active semester.\n4. View weekly grid: Green/blue blocks show your lecture and seminar rooms (e.g. SB M1, NB B, RB 211).\n5. Optional: Click 'Export schedule to Office 365 / Google Calendar' to generate an iCal subscription link.",
        "Shows timetable only after course enrollment slots have been confirmed.",
        "Room codes: SB = Old Building (Stará budova), NB = New Building (Nová budova), RB = Rajská budova. Check campus maps if unfamiliar.",
        "timetable, schedule, my lectures, rozvrh, class times, room number, calendar export, iCal"
    ),
    (
        "TASK_CONFIRMATION_STUDY",
        "portal_eagenda",
        "Electronic Confirmation of Study (Potvrzení o studiu)",
        "Elektronické potvrzení o studiu",
        "Certificates",
        "/auth/eagenda/potvrzeni.pl",
        "https://insis.vse.cz/auth/eagenda/potvrzeni.pl?lang=en",
        "http://localhost:8502/auth/eagenda/potvrzeni.pl",
        "Personal administration > Student's portal > Study details > Confirmation of study (or eAgenda > Electronic document verification)",
        "1. Open InSIS > Student's portal > 'Study details' tab.\n2. Click 'Print / generate confirmation of study' (or go to eAgenda > Electronic document verification).\n3. Select academic year and language (Czech or English).\n4. Click 'Generate digitally signed PDF'.\n5. The document contains an official VŠE qualified electronic seal and verification hash recognized by Czech immigration (MVČR) and transport offices (PID/Lítačka).",
        "Student must be actively enrolled for the requested semester.",
        "For Czech immigration (MVČR / OAMP), official authorities accept the qualified electronic PDF directly. Do NOT print a scanned color copy if electronic submission is required.",
        "confirmation of study, potvrzeni o studiu, proof of enrollment, study certificate, mvcr visa letter, digital seal"
    ),
    (
        "TASK_TUITION_PAYMENT",
        "portal_finances",
        "Tuition Fees, Bank Account & Variable Symbol",
        "Poplatky za studium, bankovní spojení a variabilní symbol",
        "Finances",
        "/auth/student/poplatky.pl",
        "https://insis.vse.cz/auth/student/poplatky.pl?lang=en",
        "http://localhost:8502/auth/student/poplatky.pl",
        "Personal administration > Student's portal > Study details > Tuition fees & payments",
        "1. In InSIS, navigate to 'Student's portal' > 'Study details'.\n2. Click 'Tuition fees' or 'Payments overview'.\n3. Note down the three mandatory payment parameters:\n   - Bank Account / IBAN: ČSOB account specified for your faculty\n   - Variable Symbol (VS): Your 8-digit InSIS student identification number\n   - Specific Symbol (SS): Faculty-specific fee identifier\n4. For international transfers, use SWIFT/BIC: CEKOCZPP and add VS into the payment narrative / reference field.",
        "Fee assessment is issued each semester for English-taught degree programmes according to the Dean's decree.",
        "CRITICAL: Always specify the correct Variable Symbol (your student ID). Without the Variable Symbol, the automated VŠE clearing system cannot match the payment to your student account.",
        "tuition fee, pay tuition, bank account, variable symbol, variabilni symbol, iban, swift, school fees, csob"
    ),
    (
        "TASK_CONTACT_CENTRE",
        "portal_eagenda",
        "InSIS Contact Centre & Official Helpdesk Requests",
        "Kontaktní centrum InSIS",
        "Helpdesk",
        "/auth/eagenda/kontaktni_centrum.pl",
        "https://insis.vse.cz/auth/eagenda/kontaktni_centrum.pl?lang=en",
        "http://localhost:8502/auth/eagenda/kontaktni_centrum.pl",
        "Personal administration > eAgenda > Contact centre",
        "1. Open InSIS > Personal administration.\n2. Scroll down to the 'eAgenda' tile box.\n3. Click 'Contact centre'.\n4. Select 'Submit new inquiry' and choose the category (e.g. Study Department, Course Registration Issue, InSIS IT Bug, Tuition Matters).\n5. Type your request with relevant course codes or screenshot attachments and submit.\n6. You will receive email tracking and official replies logged directly into InSIS.",
        "Available to all registered students.",
        "Use the Contact Centre for official administrative matters rather than sending informal emails to random professors. Responses have administrative tracking.",
        "contact centre, helpdesk, support ticket, kontaktni centrum, message study department, insis support, report bug"
    ),
    (
        "TASK_DORM_ISKAM",
        "portal_finances",
        "Dormitory Housing Portal (ISKaM Link) & Accommodation",
        "Ubytovací systém ISKaM a koleje",
        "Accommodation",
        "/auth/student/ubytovani.pl",
        "https://insis.vse.cz/auth/student/ubytovani.pl?lang=en",
        "http://localhost:8502/auth/student/ubytovani.pl",
        "Personal administration > Public information portal > Accommodation / ISKaM",
        "1. Log into InSIS.\n2. On the main Personal Administration dashboard, locate 'Accommodation' or 'ISKaM login'.\n3. Click the external redirect to https://iskam-web.vse.cz.\n4. Log in using your InSIS credentials (username without @vse.cz or with VŠE single sign-on).\n5. In ISKaM, view room reservations, pay dorm deposit, sign contract, and download proof of accommodation for visa purposes.",
        "Requires active InSIS credentials. Dormitory applications open during specific booking windows (June/July for autumn, November for spring).",
        "ISKaM is a separate system from InSIS, but uses the same user credentials and centralized university database.",
        "dormitory, dorms, iskam, housing, student accommodation, koleje, room reservation, jarov, rooseveltova"
    ),
    (
        "TASK_PASSWORD_OTP",
        "portal_tech",
        "Change Password & Configure OTP Two-Factor Authentication",
        "Změna hesla a nastavení OTP autentizace",
        "Security",
        "/auth/sprava/nastaveni.pl",
        "https://insis.vse.cz/auth/sprava/nastaveni.pl?lang=en",
        "http://localhost:8502/auth/sprava/nastaveni.pl",
        "Personal administration > Information system set-up > Setting of authentication using one-time passwords (OTP)",
        "1. In InSIS, navigate to 'Personal administration'.\n2. Find 'Information system set-up' or 'Adjustment of the information system'.\n3. To set up 2FA: Click 'Setting of authentication using one-time passwords (OTP)'.\n4. Scan QR code using Google Authenticator, Microsoft Authenticator, or Bitwarden.\n5. To change master password: Click 'User settings' > 'Change password'.\n6. The new password synchronizes with Eduroam Wi-Fi and Microsoft 365 within 15 minutes.",
        "Passwords must be at least 12 characters long and contain uppercase, lowercase, numbers, and special symbols.",
        "Changing your password updates InSIS, Office 365, and Eduroam. Remember to update Eduroam Wi-Fi profile on your phone/laptop after changing it.",
        "change password, otp, two factor authentication, 2fa, mfa, eduroam password, reset password, authenticator app"
    ),
    (
        "TASK_STUDY_RECORD_GRADES",
        "portal_student",
        "Electronic Study Record & Grades (Index)",
        "E-index a přehled známek",
        "Grades",
        "/auth/student/znamky.pl",
        "https://insis.vse.cz/auth/student/znamky.pl?lang=en",
        "http://localhost:8502/auth/student/znamky.pl",
        "Personal administration > My College > Student's portal > E-study record",
        "1. Go to InSIS > Student's portal.\n2. Click the 'E-study record' tab at the top.\n3. View list of courses completed and in-progress.\n4. Check recorded grades (1 - Výborně, 2 - Velmi dobře, 3 - Dobře, 4 - Nevyhověl, or Zap - Zápočet).\n5. Review Grade Point Average (weighted GPA) and cumulative ECTS earned.",
        "Grades appear as soon as the examiner records them in InSIS.",
        "Czech grading system is inverted compared to American/European GPA: 1 is the highest mark (A), 3 is the lowest passing mark (E), and 4 is fail (F).",
        "grades, study record, index, znamky, gpa, transcripts, results, failed course, credits earned"
    ),
    (
        "TASK_COURSE_CATALOGUE",
        "portal_public",
        "Course Catalogue & Syllabus Search",
        "Katalog předmětů a sylaby",
        "Catalog",
        "/auth/katalog/predmety.pl",
        "https://insis.vse.cz/auth/katalog/predmety.pl?lang=en",
        "http://localhost:8502/auth/katalog/predmety.pl",
        "Personal administration > Public information portal > Course catalogue",
        "1. Go to InSIS home > 'Public information portal'.\n2. Click 'Course catalogue'.\n3. Filter by Faculty (e.g. FIS - Faculty of Informatics and Statistics), Language (English), or Department.\n4. Click any course name or code (e.g. 4IT445, 4IZ440) to view full syllabus:\n   - Course objectives and learning outcomes\n   - ECTS credits and hours\n   - Grading criteria (points breakdown)\n   - Required textbooks and literature.",
        "Publicly accessible without logging in.",
        "Check prerequisites and corequisites in the syllabus before attempting to enroll in advanced courses.",
        "course catalogue, syllabus, course details, search course, predmety, learning outcomes, course literature, textbooks"
    ),
    (
        "TASK_STUDY_PLANS",
        "portal_public",
        "Study Plans (Studijní plány) & Degree Specialization",
        "Studijní plány a specializace",
        "Study Plans",
        "/auth/katalog/plany.pl",
        "https://insis.vse.cz/auth/katalog/plany.pl?lang=en",
        "http://localhost:8502/auth/katalog/plany.pl",
        "Personal administration > Public information portal > Study plans",
        "1. Go to InSIS > 'Public information portal' > 'Study plans'.\n2. Select your Faculty and degree type (Bachelor / Master).\n3. Find your study programme (e.g. Information Systems Management - ISM, Economics, International Business).\n4. View recommended study trajectory per semester to guarantee graduation in standard duration (4 semesters for Master's, 6 for Bachelor's).",
        "Publicly accessible.",
        "Study plans outline required courses by group (oP = compulsory, sP = specialization, vP = free elective). Ensure you complete all required group quotas.",
        "study plan, degree structure, curriculum, recommended trajectory, studijni plan, ism curriculum, specialization"
    ),
    (
        "TASK_COURSE_EVALUATION",
        "portal_student",
        "Course Evaluation by Students (Semester Feedback Survey)",
        "Studentská evaluace předmětů",
        "Surveys",
        "/auth/anketa/anketa.pl",
        "https://insis.vse.cz/auth/anketa/anketa.pl?lang=en",
        "http://localhost:8502/auth/anketa/anketa.pl",
        "Personal administration > My College > Course evaluation by students",
        "1. Open InSIS > Personal administration.\n2. In the 'My College' section, click 'Course evaluation by students'.\n3. Complete the anonymous questionnaire for each course taken in the semester.\n4. Rate course difficulty, teaching quality, and provide constructive textual comments.\n5. Submissions are strictly anonymous; teachers only see aggregated statistics after grades are recorded.",
        "Open only during the exam period and first weeks of the subsequent semester.",
        "Students who participate in course evaluations often receive earlier priority registration in subsequent enrollment rounds.",
        "course evaluation, student feedback, survey, evaluace, rate professor, course rating, anonymous feedback"
    ),
    (
        "TASK_DOCUMENT_SERVER",
        "portal_personal",
        "Document Server & Internal Regulations Repository",
        "Dokumentový server VŠE",
        "Documents",
        "/auth/dok_server/dok_server.pl",
        "https://insis.vse.cz/auth/dok_server/dok_server.pl?lang=en",
        "http://localhost:8502/auth/dok_server/dok_server.pl",
        "Personal administration > Personal management > Document server",
        "1. Log into InSIS > Personal administration.\n2. In the 'Personal management' box, click 'Document server'.\n3. Browse folders:\n   - University-wide directives & Dean's decrees\n   - Faculty forms & guidelines\n   - Master thesis templates and formal guidelines\n4. Download official PDFs directly.",
        "Accessible to all authenticated students.",
        "Check faculty-specific subfolders for exact graduation, thesis formatting, or internship guidelines.",
        "document server, templates, dean decrees, directives, download forms, dokumentovy server, university regulations"
    ),
    (
        "TASK_INTERNAL_MAIL",
        "portal_personal",
        "InSIS Internal Mailbox & Notifications",
        "Pošta v InSIS a systémová oznámení",
        "Communications",
        "/auth/posta/posta.pl",
        "https://insis.vse.cz/auth/posta/posta.pl?lang=en",
        "http://localhost:8502/auth/posta/posta.pl",
        "Personal administration > Personal management > Mail box",
        "1. Go to InSIS > Personal administration.\n2. Click 'Mail box' in the 'Personal management' section.\n3. View official administrative notices, study department alerts, and course messages.\n4. Tip: Go to User settings > Configure transfer of events to Office 365 to auto-forward notices to your @vse.cz Outlook inbox.",
        "Internal messaging system within VŠE.",
        "Do not ignore InSIS mailbox messages; formal legal notices and deadline warnings are considered officially delivered when posted here.",
        "mailbox, internal mail, messages, posta, notifications, study department email, notifications forwarding"
    ),
    (
        "TASK_ISIC_ID_PHOTO",
        "portal_tech",
        "Student ID Card (ISIC) Photo Upload & Status",
        "Změna fotografie a správa průkazu studenta",
        "Identity",
        "/auth/sprava/foto.pl",
        "https://insis.vse.cz/auth/sprava/foto.pl?lang=en",
        "http://localhost:8502/auth/sprava/foto.pl",
        "Personal administration > Adjustment of the information system > Change photo (or Identification cards in use)",
        "1. Navigate to InSIS > Personal administration.\n2. In 'Adjustment of the information system', click 'Change photo'.\n3. Upload a standard passport-format digital portrait (clear white background, neutral expression).\n4. Wait for administrative approval by the Student ID Card Office.\n5. Once approved, collect your physical ISIC card from the Card Office in the Old Building (SB).",
        "Required upon first enrollment at VŠE.",
        "Photo must be a realistic, front-facing portrait. Do not submit group photos, selfies with filters, or sunglasses.",
        "student id, isic card, upload photo, change photo, id card center, prukaz studenta, identification card"
    ),
    (
        "TASK_ELECTIONS_SURVEYS",
        "portal_eagenda",
        "eSurveys & Academic Senate Student Elections",
        "Elektronické volby a ankety",
        "Elections",
        "/auth/anketa/volby.pl",
        "https://insis.vse.cz/auth/anketa/volby.pl?lang=en",
        "http://localhost:8502/auth/anketa/volby.pl",
        "Personal administration > eAgenda > My Elections (or eSurveys)",
        "1. Log into InSIS > Personal administration.\n2. In the 'eAgenda' tile, click 'My Elections' or 'eSurveys'.\n3. View active voting ballots for Faculty and Academic Senate student chamber.\n4. Cast an encrypted, verified vote to elect student representatives.",
        "Only active during published academic election dates.",
        "International students are full voting members of the academic community and are eligible to vote and run for senate seats.",
        "elections, academic senate, vote, esurveys, volby, student chamber, student representation"
    )
]


def init_database(force_refresh: bool = False) -> sqlite3.Connection:
    """Creates the SQLite database schema and populates routes, policies, and locations."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    
    with conn:
        conn.executescript(SCHEMA_SQL)
        cur = conn.cursor()
        
        # 1. Populate InSIS modules & routes
        cur.execute("SELECT COUNT(*) FROM insis_modules;")
        if cur.fetchone()[0] == 0 or force_refresh:
            cur.execute("DELETE FROM insis_routes_fts;")
            cur.execute("DELETE FROM insis_routes;")
            cur.execute("DELETE FROM insis_modules;")
            cur.executemany(
                "INSERT INTO insis_modules (module_id, title_en, title_cs, description, icon) VALUES (?, ?, ?, ?, ?);",
                MODULES_DATA
            )
            cur.executemany(
                """INSERT INTO insis_routes (
                    task_id, module_id, title_en, title_cs, category,
                    portal_path, official_url, demo_url, breadcrumbs,
                    step_by_step_instructions, prerequisites, common_pitfalls, keywords
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                ROUTES_DATA
            )
            cur.execute("""
                INSERT INTO insis_routes_fts (task_id, title_en, title_cs, category, breadcrumbs, step_by_step_instructions, keywords)
                SELECT task_id, title_en, title_cs, category, breadcrumbs, step_by_step_instructions, keywords
                FROM insis_routes;
            """)

        # 2. Populate 50 Policies & Rules
        cur.execute("SELECT COUNT(*) FROM vse_policies;")
        if cur.fetchone()[0] < len(POLICIES_50) or force_refresh:
            cur.execute("DELETE FROM vse_policies;")
            cur.execute("DELETE FROM vse_policies_fts;")
            policy_rows = [
                (
                    p["rule_id"], p["category"], p["title"], p["summary"],
                    p["rule_text"], p["official_reference"], p.get("penalty_or_consequence", ""),
                    p["faq_triggers"]
                )
                for p in POLICIES_50
            ]
            cur.executemany(
                """INSERT INTO vse_policies (
                    rule_id, category, title, summary, rule_text,
                    official_reference, penalty_or_consequence, faq_triggers
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
                policy_rows
            )
            cur.execute("""
                INSERT INTO vse_policies_fts (
                    rule_id, category, title, summary, rule_text, official_reference, faq_triggers
                ) SELECT rule_id, category, title, summary, rule_text, official_reference, faq_triggers
                FROM vse_policies;
            """)

        # 3. Populate Campus Navigation Locations
        cur.execute("SELECT COUNT(*) FROM campus_locations;")
        if cur.fetchone()[0] < len(CAMPUS_LOCATIONS) or force_refresh:
            cur.execute("DELETE FROM campus_locations;")
            cur.execute("DELETE FROM campus_locations_fts;")
            loc_rows = [
                (
                    loc["location_id"], loc["building"], loc["floor"], loc["room_number"],
                    loc["facility_type"], loc["name"], loc["directions_from_entrance"],
                    loc.get("amenities_accessibility", ""), loc.get("hours_or_availability", ""),
                    loc["keywords"]
                )
                for loc in CAMPUS_LOCATIONS
            ]
            cur.executemany(
                """INSERT INTO campus_locations (
                    location_id, building, floor, room_number, facility_type,
                    name, directions_from_entrance, amenities_accessibility,
                    hours_or_availability, keywords
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                loc_rows
            )
            cur.execute("""
                INSERT INTO campus_locations_fts (
                    location_id, building, floor, room_number, facility_type,
                    name, directions_from_entrance, keywords
                ) SELECT location_id, building, floor, room_number, facility_type,
                         name, directions_from_entrance, keywords
                FROM campus_locations;
            """)
            
    return conn


def get_connection() -> sqlite3.Connection:
    """Returns an open connection with row_factory set to sqlite3.Row."""
    if not DB_PATH.exists():
        return init_database()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# 1. Search Functions for InSIS Routes
# ---------------------------------------------------------------------------
def search_routes(query_str: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches InSIS routes using FTS5 full-text matching with fallback to LIKE search."""
    if not query_str or not query_str.strip():
        return []
        
    clean_q = query_str.strip()
    conn = get_connection()
    cur = conn.cursor()
    tokens = re.findall(r"[a-zA-Z0-9_\u00c0-\u017f]+", clean_q)
    if not tokens:
        return []
        
    fts_match_expr = " OR ".join(f'"{t}"*' for t in tokens if len(t) > 1)
    results = []
    if fts_match_expr:
        try:
            sql_fts = """
                SELECT r.*, rank
                FROM insis_routes_fts fts
                JOIN insis_routes r ON fts.task_id = r.task_id
                WHERE insis_routes_fts MATCH ?
                ORDER BY rank
                LIMIT ?;
            """
            cur.execute(sql_fts, (fts_match_expr, limit))
            for row in cur.fetchall():
                results.append(dict(row))
        except Exception:
            results = []
            
    if len(results) < limit:
        existing_ids = {r["task_id"] for r in results}
        placeholders = " OR ".join(["r.keywords LIKE ? OR r.title_en LIKE ? OR r.breadcrumbs LIKE ?"] * len(tokens[:4]))
        params = []
        for t in tokens[:4]:
            p = f"%{t}%"
            params.extend([p, p, p])
            
        sql_like = f"SELECT r.* FROM insis_routes r WHERE ({placeholders}) LIMIT ?;"
        params.append(limit * 2)
        try:
            cur.execute(sql_like, params)
            for row in cur.fetchall():
                d = dict(row)
                if d["task_id"] not in existing_ids:
                    results.append(d)
                    existing_ids.add(d["task_id"])
                    if len(results) >= limit:
                        break
        except Exception:
            pass
            
    conn.close()
    return results[:limit]


def get_route_by_task_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an exact route by task_id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM insis_routes WHERE task_id = ? LIMIT 1;", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# 2. Search Functions for 50 Policies & Rules
# ---------------------------------------------------------------------------
def search_policies(query_str: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches 50 VŠE Policies and Rules using FTS5 and LIKE fallback."""
    if not query_str or not query_str.strip():
        return []
        
    conn = get_connection()
    cur = conn.cursor()
    tokens = re.findall(r"[a-zA-Z0-9_\u00c0-\u017f]+", query_str.strip())
    if not tokens:
        return []

    fts_match_expr = " OR ".join(f'"{t}"*' for t in tokens if len(t) > 1)
    results = []
    if fts_match_expr:
        try:
            sql_fts = """
                SELECT p.*, rank
                FROM vse_policies_fts fts
                JOIN vse_policies p ON fts.rule_id = p.rule_id
                WHERE vse_policies_fts MATCH ?
                ORDER BY rank
                LIMIT ?;
            """
            cur.execute(sql_fts, (fts_match_expr, limit))
            for row in cur.fetchall():
                results.append(dict(row))
        except Exception:
            results = []

    if len(results) < limit:
        existing_ids = {r["rule_id"] for r in results}
        placeholders = " OR ".join(["p.faq_triggers LIKE ? OR p.title LIKE ? OR p.summary LIKE ? OR p.rule_text LIKE ?"] * len(tokens[:4]))
        params = []
        for t in tokens[:4]:
            p = f"%{t}%"
            params.extend([p, p, p, p])
            
        sql_like = f"SELECT p.* FROM vse_policies p WHERE ({placeholders}) LIMIT ?;"
        params.append(limit * 2)
        try:
            cur.execute(sql_like, params)
            for row in cur.fetchall():
                d = dict(row)
                if d["rule_id"] not in existing_ids:
                    results.append(d)
                    existing_ids.add(d["rule_id"])
                    if len(results) >= limit:
                        break
        except Exception:
            pass

    conn.close()
    return results[:limit]


# ---------------------------------------------------------------------------
# 3. Search Functions for Campus Locations (Washrooms, Classrooms, Offices)
# ---------------------------------------------------------------------------
def search_campus_locations(query_str: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches Campus Locations (washrooms, classrooms, study coordinators) via FTS5 & LIKE."""
    if not query_str or not query_str.strip():
        return []
        
    conn = get_connection()
    cur = conn.cursor()
    tokens = re.findall(r"[a-zA-Z0-9_\u00c0-\u017f]+", query_str.strip())
    if not tokens:
        return []

    fts_match_expr = " OR ".join(f'"{t}"*' for t in tokens if len(t) > 1)
    results = []
    if fts_match_expr:
        try:
            sql_fts = """
                SELECT loc.*, rank
                FROM campus_locations_fts fts
                JOIN campus_locations loc ON fts.location_id = loc.location_id
                WHERE campus_locations_fts MATCH ?
                ORDER BY rank
                LIMIT ?;
            """
            cur.execute(sql_fts, (fts_match_expr, limit))
            for row in cur.fetchall():
                results.append(dict(row))
        except Exception:
            results = []

    if len(results) < limit:
        existing_ids = {r["location_id"] for r in results}
        placeholders = " OR ".join(["loc.keywords LIKE ? OR loc.name LIKE ? OR loc.room_number LIKE ? OR loc.directions_from_entrance LIKE ?"] * len(tokens[:4]))
        params = []
        for t in tokens[:4]:
            p = f"%{t}%"
            params.extend([p, p, p, p])
            
        sql_like = f"SELECT loc.* FROM campus_locations loc WHERE ({placeholders}) LIMIT ?;"
        params.append(limit * 2)
        try:
            cur.execute(sql_like, params)
            for row in cur.fetchall():
                d = dict(row)
                if d["location_id"] not in existing_ids:
                    results.append(d)
                    existing_ids.add(d["location_id"])
                    if len(results) >= limit:
                        break
        except Exception:
            pass

    conn.close()
    return results[:limit]


# ---------------------------------------------------------------------------
# 4. Card Formatters
# ---------------------------------------------------------------------------
def format_navigation_card(route: Dict[str, Any]) -> str:
    """Formats an InSIS route record into a structured Markdown block."""
    card = []
    card.append(f"### 🧭 InSIS Navigation: {route['title_en']}")
    card.append(f"**Category:** `{route['category']}` | **Path:** `{route['portal_path']}`")
    card.append(f"")
    card.append(f"**Breadcrumb Trail:**")
    card.append(f"> `{route['breadcrumbs']}`")
    card.append(f"")
    card.append(f"**Step-by-Step Instructions:**")
    for step in route['step_by_step_instructions'].split("\n"):
        if step.strip():
            card.append(f"{step}")
    card.append(f"")
    if route.get("prerequisites"):
        card.append(f"**Prerequisites:** {route['prerequisites']}")
    if route.get("common_pitfalls"):
        card.append(f"⚠️ **Important Note:** {route['common_pitfalls']}")
    card.append(f"")
    card.append(f"🔗 [Open in Official InSIS]({route['official_url']})  |  🧪 [Test in InSIS Demo Simulation]({route['demo_url']})")
    return "\n".join(card)


def format_policy_card(policy: Dict[str, Any]) -> str:
    """Formats a University Policy into an authoritative, readable Markdown block."""
    card = []
    card.append(f"### 📜 VŠE Policy [{policy['rule_id']}]: {policy['title']}")
    card.append(f"**Category:** `{policy['category']}` | **Official Ref:** `{policy['official_reference']}`")
    card.append(f"")
    card.append(f"**Core Rule Summary:**")
    card.append(f"> {policy['summary']}")
    card.append(f"")
    card.append(f"**Full Regulation:**")
    card.append(f"{policy['rule_text']}")
    card.append(f"")
    if policy.get("penalty_or_consequence"):
        card.append(f"⚠️ **Sanction / Non-Compliance Consequence:**")
        card.append(f"{policy['penalty_or_consequence']}")
    return "\n".join(card)


def format_location_card(location: Dict[str, Any]) -> str:
    """Formats a Campus Location into a clear, turn-by-turn navigation guide."""
    card = []
    card.append(f"### 📍 Campus Navigation: {location['name']}")
    card.append(f"**Building:** `{location['building']}` | **Floor:** `{location['floor']}` | **Room:** `{location['room_number']}`")
    card.append(f"")
    card.append(f"**Walking Directions from Main Entrance:**")
    card.append(f"> {location['directions_from_entrance']}")
    card.append(f"")
    if location.get("amenities_accessibility"):
        card.append(f"**Amenities & Accessibility:** {location['amenities_accessibility']}")
    if location.get("hours_or_availability"):
        card.append(f"**Hours / Availability:** {location['hours_or_availability']}")
    return "\n".join(card)


# ---------------------------------------------------------------------------
# 5. Unified Intelligent Search
# ---------------------------------------------------------------------------
def unified_search(query_str: str, limit: int = 3) -> Dict[str, Any]:
    """Smart dispatcher searching across InSIS routes, policies, and campus locations."""
    q_lower = query_str.lower()
    
    # Campus cues
    campus_cues = ["where is", "how do i get to", "toilet", "washroom", "wc", "restroom", "bathroom",
                   "floor", "room", "hall", "aula", "sb", "nb", "rb", "menza", "canteen", "library",
                   "coordinator", "office hours", "atm", "gym", "sports", "helpdesk", "ciks"]
    # Policy cues
    policy_cues = ["policy", "rule", "regulation", "penalty", "fail", "plagiarism", "cheat",
                   "attending", "absence", "doctor", "retake", "guest", "dorm rules", "smoking",
                   "insurance", "police", "foreign police", "merit", "scholarship", "voucher",
                   "minimum credits", "9 ects", "20 ects", "termination", "expulsion"]
                   
    is_campus = any(c in q_lower for c in campus_cues)
    is_policy = any(p in q_lower for p in policy_cues)
    
    locations = search_campus_locations(query_str, limit=limit) if is_campus or not is_policy else []
    policies = search_policies(query_str, limit=limit) if is_policy or not is_campus else []
    routes = search_routes(query_str, limit=limit)

    return {
        "query": query_str,
        "campus_locations": locations,
        "policies": policies,
        "insis_routes": routes
    }


if __name__ == "__main__":
    print("[InSIS & Campus DB] Initializing complete database with 50 policies and locations...")
    init_database()
    print(f"[InSIS & Campus DB] Database ready at: {DB_PATH}")
    
    test_queries = [
        "washroom 1st floor",
        "where is the study coordinator for fis",
        "what happens if i fail an exam 3 times",
        "overnight guest dorm rules",
        "where is room RB 211"
    ]
    for q in test_queries:
        print(f"\n==================== QUERY: '{q}' ====================")
        res = unified_search(q, limit=1)
        if res["campus_locations"]:
            print(format_location_card(res["campus_locations"][0]))
        elif res["policies"]:
            print(format_policy_card(res["policies"][0]))
        elif res["insis_routes"]:
            print(format_navigation_card(res["insis_routes"][0]))
        else:
            print("No immediate entity found.")
