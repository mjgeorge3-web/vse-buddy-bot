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
        "/auth/student/zp.pl",
        "https://insis.vse.cz/auth/student/zp.pl?lang=en",
        "http://localhost:8502/auth/student/zp.pl",
        "Personal administration > Student's portal > Final thesis > Display and download files",
        "1. Log into InSIS and open **My College** → **Student's portal**.\n2. In your study row, click the **Final thesis** icon (green book, `/auth/student/zp.pl`) or browse **List of topics** (`/auth/student/temata_zp.pl`).\n3. Check **Basic information about a final thesis** to verify your supervisor and assignment status.\n4. Under **Display and download files**, open **Instructions for submission process of final thesis** to confirm faculty deadlines.",
        "Must be enrolled in degree programme; supervisor must confirm the assignment in InSIS before submission unlocks.",
        "Assignment completeness status must show 'confirmed by supervisor' before the 3 submission editing steps unlock.",
        "thesis registration, master thesis, bachelor thesis, assignment, diplomka, final thesis, supervisor approval, topic, zadani prace, display and download files, instructions for submission process of final thesis"
    ),
    (
        "TASK_THESIS_SUBMISSION",
        "portal_student",
        "Upload Final Thesis & Appendices (PDF/A)",
        "Odevzdání závěrečné práce a příloh",
        "Final Thesis",
        "/auth/student/zp.pl",
        "https://insis.vse.cz/auth/student/zp.pl?lang=en",
        "http://localhost:8502/auth/student/zp.pl",
        "Personal administration > Student's portal > Final thesis > Editing application > Thesis submission",
        "1. Open **My College** → **Student's portal** → **Final thesis** (`/auth/student/zp.pl`).\n2. Under **Editing application**, click **Insert additional information** to enter both English and Czech abstracts and keywords.\n3. Click **Insert the thesis and the appendices** to upload the full thesis in **PDF/A** format (plus optional ZIP data/code under Appendices).\n4. Click **Thesis submission** (green arrow) to lock your final electronic submission and trigger the Theses.cz originality check.",
        "Both Czech and English abstracts and keywords must be filled. The file must comply with PDF/A standard (max 50 MB).",
        "Once you click 'Thesis submission', the file is permanently locked. Any post-defense corrections must be uploaded separately via § 47b Errata.",
        "submit thesis, thesis submission, upload thesis, thesis upload, submit master thesis, submit bachelor thesis, final thesis submission, odevzdani diplomky, final thesis upload, pdf/a, abstract, keywords, submission deadline, editing application, insert additional information, insert the thesis and the appendices"
    ),
    (
        "TASK_THESIS_ERRATA",
        "portal_student",
        "Post-Defense Thesis Errata Submission (§ 47b)",
        "Vložení errat k obhájené práci (§ 47b)",
        "Final Thesis",
        "/auth/student/zp.pl",
        "https://insis.vse.cz/auth/student/zp.pl?lang=en",
        "http://localhost:8502/auth/student/zp.pl",
        "Personal administration > Student's portal > Final thesis > Editing application > Insert errata (Vložit errata)",
        "1. Open **My College** → **Student's portal** → **Final thesis** (`/auth/student/zp.pl`).\n2. Scroll to **Editing application** at the bottom of the page and click **Insert errata** (*Vložit errata*).\n3. Prepare a concise 1–2 page **PDF** listing page/line corrections (consult your thesis supervisor beforehand).\n4. Upload the Errata PDF and confirm submission so it is attached to your permanent thesis record in InSIS and Theses.cz.",
        "Used after submission/defense pursuant to Czech Higher Education Act No. 111/1998 Sb. § 47b.",
        "Errata does not overwrite the locked thesis PDF; it is published alongside your thesis as an official corrective annex.",
        "errata, insert errata, vlozit errata, vložit errata, thesis errata, post-defense corrections, 47b, opravy po obhajobe, thesis error fix, submit errata, post defense errata, where is errata"
    ),
    (
        "TASK_COURSE_REGISTRATION",
        "portal_student",
        "Course Registration & Enrollment (Zápis předmětů)",
        "Registrace a zápis předmětů",
        "Enrollment",
        "/auth/student/registrace.pl",
        "https://insis.vse.cz/auth/student/registrace.pl?lang=en",
        "http://localhost:8502/auth/student/registrace.pl",
        "Personal administration > My College > Student's portal > Registration/Enrollment",
        "1. Open **My College** → **Student's portal** and click **Registration/Enrollment** (`/auth/student/registrace.pl`).\n2. Select the upcoming semester and add compulsory (`oP`), specialization (`sP`), or elective (`vP`) courses to your registration basket.\n3. During your enrollment round (*zápis*), confirm concrete lecture/seminar timetable slots.\n4. Verify that total enrolled ECTS stays within your remaining credit voucher balance.",
        "Enrollment runs in timed phases (Round 1 pre-registration, Round 2 automated allocation, Round 3 schedule adjustments).",
        "You must earn at least 9 ECTS in your first semester and 20 ECTS per academic year to continue studies.",
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
        "/auth/student/zkousky.pl",
        "https://insis.vse.cz/auth/student/zkousky.pl?lang=en",
        "http://localhost:8502/auth/student/zkousky.pl",
        "Personal administration > My College > Student's portal > Register for examinations (Přihlašování na zkoušky)",
        "1. Go to InSIS > Student's portal.\n2. Click the icon under 'Register for examinations' (/auth/student/zkousky.pl).\n3. Browse active course exam dates (termíny zkoušek).\n4. Review capacity, room number, examiner name, and cancellation deadline.\n5. Click 'Sign up' next to your preferred date.\n6. Confirm that the status updates to 'Registered'.",
        "Must be actively enrolled in the course and have met any semester prerequisite conditions (zápočet / continuous assessment threshold).",
        "Cancelling registration after the deadline or failing to appear without an excused medical absence results in grade '4 - Nevyhověl' (Fail) and burns an exam attempt.",
        "exam dates, register exam, exam registration, test dates, termin zkousky, sign up for exam, exam cancellation, zkousky"
    ),
    (
        "TASK_TIMETABLE_VIEW",
        "portal_public",
        "Personal Timetable & Weekly Schedule (Rozvrh)",
        "Osobní rozvrh hodin",
        "Schedule",
        "/katalog/rozvrhy_view.pl",
        "https://insis.vse.cz/katalog/rozvrhy_view.pl?lang=en",
        "http://localhost:8502/katalog/rozvrhy_view.pl",
        "Personal administration > My College > Student's portal > My lectures sheet (or InSIS Public Portal > Timetables)",
        "1. Log into InSIS (or view public schedule at https://insis.vse.cz/katalog/rozvrhy_view.pl?lang=en).\n2. Go to 'Student's portal' > 'My lectures sheet' (or 'My timetable' in quick links).\n3. Select the active semester.\n4. View weekly grid: Green/blue blocks show your lecture and seminar rooms (e.g. SB M1, NB B, RB 211).\n5. Optional: Click 'Export schedule to Office 365 / Google Calendar' to generate an iCal subscription link.",
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
        "/auth/student/potvrzeni.pl",
        "https://insis.vse.cz/auth/student/potvrzeni.pl?lang=en",
        "http://localhost:8502/auth/student/potvrzeni.pl",
        "Personal administration (or My College / Moje studium) > Student's portal > Confirmation of study",
        "1. Open VŠE InSIS (https://insis.vse.cz/auth/?lang=en) and log in using your student credentials.\n2. Navigate to My College (Moje studium) → Student's Portal.\n3. Click 'Confirmation of study' (/auth/student/potvrzeni.pl) or check the 'Study details' tab.\n4. Select academic year and language (Czech or English).\n5. Click 'Generate digitally signed PDF' to download your official confirmation with VŠE qualified electronic seal.",
        "Student must be actively enrolled for the requested semester.",
        "For Czech immigration (MVČR / OAMP), official authorities accept the qualified electronic PDF directly. Do NOT print a scanned color copy if electronic submission is required.",
        "confirmation of study, download confirmation of study, get confirmation of study, potvrzeni o studiu, proof of enrollment, study certificate, mvcr visa letter, digital seal, study confirmation, confirmation pdf"
    ),
    (
        "TASK_COURSEWORK_DROPBOX",
        "portal_student",
        "Coursework Submissions / Drop-in Box (Odevzdávárna)",
        "Odevzdávárna seminárních prací a projektů",
        "Assignments",
        "/auth/student/odevzdavarna.pl",
        "https://insis.vse.cz/auth/student/odevzdavarna.pl?lang=en",
        "http://localhost:8502/auth/student/odevzdavarna.pl",
        "Personal administration (or My College / Moje studium) > Student's portal > Coursework submissions (Odevzdávárna)",
        "1. Open VŠE InSIS (https://insis.vse.cz/auth/?lang=en) and log in using your student credentials.\n2. Navigate to My College (Moje studium) → Student's Portal.\n3. Click the 'Coursework submissions' tab (Odevzdávárna) at the top of the portal table (/auth/student/odevzdavarna.pl).\n4. Select your enrolled course and the target assignment dropbox.\n5. Upload your solution (.pdf, .zip) and confirm submission to receive your timestamped protocol.",
        "Must be enrolled in the course for the current semester.",
        "Check deadline and file size limits specified by the teacher. After the deadline, the drop-box locks automatically.",
        "coursework submissions, coursework assignment, submit coursework, submit assignment, odevzdavarna, homework dropbox, upload seminar work, project submission, seminar paper submission, odevzdani prace, how to submit assignment"
    ),
    (
        "TASK_TUITION_PAYMENT",
        "portal_finances",
        "Tuition Fees, Bank Account & Variable Symbol",
        "Poplatky za studium, bankovní spojení a variabilní symbol",
        "Finances",
        "/auth/financovani/index.pl",
        "https://insis.vse.cz/auth/financovani/index.pl?lang=en",
        "http://localhost:8502/auth/financovani/index.pl",
        "Personal administration > Financing of study and scholarships > Student Study Financing, Bank Accounts & Variable Symbol",
        "1. Open InSIS **Study Financing** (`/auth/financovani/index.pl`) or navigate via **My College** → **Student's portal**.\n2. Copy the mandatory payment details for your faculty:\n   - **Bank Account / IBAN** & **SWIFT/BIC** (`CEKOCZPP` for ČSOB international transfers)\n   - **Variable Symbol (VS)**: Your unique 8-digit InSIS student ID\n3. Always include your **Variable Symbol** so the automated clearing system pairs the payment to your account.",
        "Fee assessment is issued each semester for English-taught degree programmes according to the Dean's decree.",
        "Always specify your 8-digit Variable Symbol (VS). Payments sent without a Variable Symbol cannot be automatically matched.",
        "tuition fee, pay tuition, bank account, variable symbol, variabilni symbol, iban, swift, school fees, csob, poplatky"
    ),
    (
        "TASK_CONTACT_CENTRE",
        "portal_eagenda",
        "Contact Centre & Document Office: General Application / Query",
        "Kontaktní centrum a Úřadovna – Hledání řešení a Obecná žádost / dotaz",
        "Contact Centre & Official Queries",
        "/auth/uradovna/",
        "https://insis.vse.cz/auth/uradovna/?lang=en",
        "http://localhost:8502/auth/uradovna/",
        "Personal administration > Contact centre > Searching for solution > General application/query",
        "1. Log into InSIS **Personal administration** (`https://insis.vse.cz/auth/?lang=en`).\n2. Under **eAgenda**, open **Contact centre** (*Kontaktní centrum*) or **Document office** (*Úřadovna*, `/auth/uradovna/`).\n3. Open the **Searching for solution** tab and pick your topic, or click **General application/query**.\n4. Enter your subject and message, attach any supporting PDF documents, and submit.\n5. Track replies under **My queries**.",
        "Available to all registered students.",
        "Submit official study petitions and administrative inquiries here rather than emailing unmonitored addresses.",
        "general query, general querry, general application, general application/query, searching for solution, my queries, contact centre, contact center, kontaktní centrum, kontaktni centrum, uradovna, úřadovna, submit query, submit inquiry, student ticket, message study department, ask coordinator in insis, study issues, study abroad query, scholarship query, submit request, find query in insis, where to find general query, where to find general querry, where is general query, where is general querry, how to find general query, how to find general querry, general query in insis, general querry in insis"
    ),
    (
        "TASK_DORM_ISKAM",
        "portal_finances",
        "VŠE Dormitory Booking Portal (ISKaM)",
        "Ubytovací systém ISKaM a koleje SÚZ VŠE",
        "Accommodation",
        "https://iskam-web.vse.cz/",
        "https://iskam-web.vse.cz/",
        "https://accommodation.vse.cz/",
        "SÚZ VŠE Accommodation Portal > ISKaM Housing System (https://iskam-web.vse.cz/)",
        "1. Open the VŠE **ISKaM** housing portal (`https://iskam-web.vse.cz/`) and sign in with your InSIS username and password.\n2. Submit your dormitory housing application during the intake window (Jarov, Blanice, Vltava, or Rooseveltova).\n3. Pay the refundable booking deposit (*kauce*) by card or bank transfer to confirm your room reservation.\n4. Request or download your signed **Proof of Accommodation** (*Doklad o zajištění ubytování*) for visa purposes.",
        "Requires active VŠE InSIS credentials. Booking windows open in June/July for autumn and November for spring.",
        "ISKaM (`https://iskam-web.vse.cz/`) is a dedicated housing portal separate from InSIS, operated by SÚZ VŠE (`https://accommodation.vse.cz/`).",
        "dormitory, dorms, iskam, student housing, koleje, room reservation, jarov, rooseveltova, dorm room, campus bed, suz housing"
    ),
    (
        "TASK_PASSWORD_OTP",
        "portal_tech",
        "Change Password & Configure OTP Two-Factor Authentication",
        "Změna hesla a nastavení OTP autentizace",
        "Security",
        "/auth/system/totp.pl",
        "https://insis.vse.cz/auth/system/totp.pl?lang=en",
        "http://localhost:8502/auth/system/totp.pl",
        "Personal administration > Information system set-up > Setting of authentication using one-time passwords (OTP)",
        "1. Log into InSIS **Personal administration** (`https://insis.vse.cz/auth/?lang=en`).\n2. Under **Information system set-up**, click **Setting of authentication using one-time passwords (OTP)** (`/auth/system/totp.pl`).\n3. Scan the QR code using Microsoft Authenticator or Google Authenticator and confirm the 6-digit code.\n4. To change your password, open **Adjustment of the information system** → **User settings** → **Change password**.",
        "Passwords must be at least 12 characters long and include uppercase, lowercase, numbers, and symbols.",
        "Changing your InSIS password also updates Microsoft 365 and campus eduroam Wi-Fi within ~15 minutes—remember to update saved Wi-Fi credentials on your phone and laptop.",
        "change password, otp, two factor authentication, 2fa, mfa, eduroam password, reset password, authenticator app, totp"
    ),
    (
        "TASK_STUDY_RECORD_GRADES",
        "portal_student",
        "Electronic Study Record & Grades (E-výkaz o studiu)",
        "E-výkaz o studiu a přehled známek",
        "Grades",
        "/auth/student/arch_studia.pl",
        "https://insis.vse.cz/auth/student/arch_studia.pl?lang=en",
        "http://localhost:8502/auth/student/arch_studia.pl",
        "Personal administration > My College > Student's portal > E-study record",
        "1. Open **My College** → **Student's portal**.\n2. Click the **E-study record** tab (`/auth/student/arch_studia.pl`) for final grades and GPA, or **My lectures sheet** (`/auth/student/zaznamnik.pl`) for continuous semester points.\n3. Check recorded grades (`1` = Excellent, `2` = Very Good, `3` = Good, `4` = Fail, `Zap` = Unweighted Credit) and total earned ECTS.",
        "Grades appear immediately once recorded by your examiner in InSIS.",
        "VŠE uses an inverted 1–4 grading scale: 1 is the best grade (90–100%), 3 is the lowest passing grade (60–74%), and 4 is Fail (<60%).",
        "grades, study record, index, znamky, gpa, transcripts, results, failed course, credits earned, arch_studia, zaznamnik"
    ),
    (
        "TASK_COURSE_CATALOGUE",
        "portal_public",
        "Course Catalogue & Syllabus Search",
        "Katalog předmětů a sylaby",
        "Catalog",
        "/katalog/",
        "https://insis.vse.cz/katalog/?lang=en",
        "http://localhost:8502/katalog/",
        "InSIS Public Portal > Course catalogue (or Personal administration > Public information portal > Course catalogue)",
        "1. Open InSIS Public Portal > 'Course catalogue' (https://insis.vse.cz/katalog/?lang=en).\n2. Filter by Faculty (e.g. FIS - Faculty of Informatics and Statistics), Language (English), or Department.\n3. Click any course name or code (e.g. 4IT445, 4IZ440) to view full syllabus:\n   - Course objectives and learning outcomes\n   - ECTS credits and hours\n   - Grading criteria (points breakdown)\n   - Required textbooks and literature.",
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
        "/katalog/plany.pl",
        "https://insis.vse.cz/katalog/plany.pl?lang=en",
        "http://localhost:8502/katalog/plany.pl",
        "InSIS Public Portal > Study plans (or Personal administration > Public information portal > Study plans)",
        "1. Open InSIS Public Portal (https://insis.vse.cz/katalog/plany.pl?lang=en) or navigate via 'Public information portal' > 'Study plans'.\n2. Select your Faculty and degree type (Bachelor / Master).\n3. Find your study programme (e.g. Information Systems Management - ISM, Economics, International Business).\n4. View recommended study trajectory per semester to guarantee graduation in standard duration (4 semesters for Master's, 6 for Bachelor's).",
        "Publicly accessible without logging in.",
        "Study plans outline required courses by group (oP = compulsory, sP = specialization, vP = free elective). Ensure you complete all required group quotas.",
        "study plan, degree structure, curriculum, recommended trajectory, studijni plan, ism curriculum, specialization, plany"
    ),
    (
        "TASK_COURSE_EVALUATION",
        "portal_student",
        "Course Evaluation by Students (Semester Feedback Survey)",
        "Studentská evaluace předmětů",
        "Surveys",
        "/auth/anketa/",
        "https://insis.vse.cz/auth/anketa/?lang=en",
        "http://localhost:8502/auth/anketa/",
        "Personal administration > My College > Course evaluation by students",
        "1. Open InSIS **Personal administration** → **My College** → **Course evaluation by students** (`/auth/anketa/`).\n2. Select each completed course and fill out the anonymous feedback questionnaire.\n3. Submit ratings on teaching quality and materials (instructors see aggregated results only after grades are finalized).",
        "Open during the examination period and the opening weeks of the next semester.",
        "Completing course evaluations often grants priority time slots in subsequent course registration rounds.",
        "course evaluation, student feedback, survey, evaluace, rate professor, course rating, anonymous feedback, anketa"
    ),
    (
        "TASK_DOCUMENT_SERVER",
        "portal_personal",
        "Document Server & Official University Regulations",
        "Dokumentový server VŠE",
        "Documents",
        "/dok_server/",
        "https://insis.vse.cz/dok_server/?lang=en",
        "http://localhost:8502/dok_server/",
        "Personal administration > Personal management > Document server (or Public Portal > Public document server)",
        "1. Open the VŠE **Document server** (`https://insis.vse.cz/dok_server/?lang=en`) or click **Document server** under **Personal management**.\n2. Browse Rectorate study regulations, faculty noticeboards (e.g., FIS folder), Dean's decrees, and official thesis templates.\n3. Download official PDF regulations directly.",
        "Public folders are accessible without login; internal folders require InSIS sign-in.",
        "Check your faculty subfolder for the latest Dean's decrees on tuition, thesis formatting, and state exams.",
        "document server, templates, dean decrees, directives, download forms, dokumentovy server, university regulations"
    ),
    (
        "TASK_INTERNAL_MAIL",
        "portal_personal",
        "InSIS Internal Mailbox & Notifications",
        "Pošta v InSIS a systémová oznámení",
        "Communications",
        "/auth/posta/",
        "https://insis.vse.cz/auth/posta/?lang=en",
        "http://localhost:8502/auth/posta/",
        "Personal administration > Personal management > Mail box",
        "1. Open InSIS **Personal administration** → **Personal management** → **Mail box** (`/auth/posta/`).\n2. Read official administrative notices, exam alerts, and study department messages.\n3. Optional: Under **Adjustment of the information system** → **Configure transfer of events to Office 365**, enable automatic forwarding to your `@vse.cz` Outlook email.",
        "Internal messaging system within VŠE.",
        "Official administrative notices delivered to your InSIS mailbox carry formal validity—enable Office 365 forwarding so you never miss deadlines.",
        "mailbox, internal mail, messages, posta, notifications, study department email, notifications forwarding"
    ),
    (
        "TASK_ISIC_ID_PHOTO",
        "portal_tech",
        "Personal Data, ID Photo Upload & Student Card (ISIC)",
        "Osobní údaje, změna fotografie a průkaz studenta",
        "Identity",
        "/auth/lide/moje_udaje.pl",
        "https://insis.vse.cz/auth/lide/moje_udaje.pl?lang=en",
        "http://localhost:8502/karty/platnost.pl",
        "Personal administration > Adjustment of the information system > Change photo / Personal data",
        "1. Log into InSIS **Personal administration** (`https://insis.vse.cz/auth/?lang=en`).\n2. Under **Adjustment of the information system**, click **Change photo** (or verify your details under **Personal data**, `/auth/lide/moje_udaje.pl`).\n3. Upload a passport-style portrait on a plain light background.\n4. Once approved, pick up your physical ISIC student card at the **Card Centre (Room SB 01, Old Building ground floor)**.",
        "Required upon initial enrollment at VŠE.",
        "Use a clear front-facing portrait without filters, hats, or sunglasses. Card validity can also be checked publicly at `/karty/platnost.pl`.",
        "student id, isic card, upload photo, change photo, id card center, prukaz studenta, identification card, personal data, moje udaje"
    ),
    (
        "TASK_ELECTIONS_SURVEYS",
        "portal_eagenda",
        "eSurveys & Academic Senate Student Elections",
        "Elektronické volby a ankety",
        "Elections",
        "/auth/anketa/",
        "https://insis.vse.cz/auth/anketa/?lang=en",
        "http://localhost:8502/auth/anketa/",
        "Personal administration > eAgenda > My Elections / eSurveys",
        "1. Log into InSIS **Personal administration** (`https://insis.vse.cz/auth/?lang=en`).\n2. In the **eAgenda** tile, click **My Elections** or **eSurveys** (`/auth/anketa/`).\n3. Select active ballots for the Faculty or University Academic Senate and cast your encrypted vote.",
        "Active during published academic election windows.",
        "International degree students are full members of the academic community and are eligible to vote in Academic Senate elections.",
        "elections, academic senate, vote, esurveys, volby, student chamber, student representation"
    ),
    (
        "TASK_SCHOLARSHIP_ACCOMMODATION",
        "portal_finances",
        "Scholarships & Accommodation Grant Application",
        "Žádosti o stipendia a ubytovací stipendium",
        "Finances & Scholarships",
        "/auth/stipendia/",
        "https://insis.vse.cz/auth/stipendia/?lang=en",
        "http://localhost:8502/auth/stipendia/",
        "Personal administration > Financing of study and scholarships > Scholarships (Žádosti o stipendia)",
        "1. Open the **Scholarships** portal directly below (`/auth/stipendia/`), or navigate via **My College** → **Student's portal** → **Scholarships** (*Žádosti o stipendia*).\n2. Select **Accommodation scholarship** (*Žádost o ubytovací stipendium*) and submit the online application during the semester intake window.\n3. Verify that an active **Czech bank account** is saved under **Study Financing & Bank Accounts** (`/auth/financovani/index.pl`) so quarterly payouts can be deposited.",
        "Eligible for full-time degree students within standard study duration (+ max 1 year) without permanent residence in Prague.",
        "The Accommodation Scholarship is a quarterly cash grant paid to your Czech bank account—separate from booking a dormitory room in ISKaM.",
        "accommodation scholarship, accomodation scholarship, accommodation benefit, accomodation benefit, ubytovaci stipendium, ubytovací stipendium, scholarship, apply for scholarship, stipendia, zadost o ubytovaci stipendium, zadosti o stipendia, housing grant, living allowance, housing benefit, money for accommodation, how to apply for scholarship, how do i apply for accommodation benefit, how do i apply for accomodation benefit, apply for accommodation benefit, apply for accomodation benefit, student scholarship, accommodation grant, where to find accommodation benefit, where to find accomodation benefit"
    ),
    (
        "TASK_BANK_ACCOUNT_FINANCING",
        "portal_finances",
        "Student Study Financing, Bank Accounts & Variable Symbol",
        "Financování studia a bankovní spojení",
        "Finances & Scholarships",
        "/auth/financovani/index.pl",
        "https://insis.vse.cz/auth/financovani/index.pl?lang=en",
        "http://localhost:8502/auth/financovani/index.pl",
        "Personal administration > Financing of study and scholarships > Student Study Financing, Bank Accounts & Variable Symbol",
        "1. Open **Study Financing & Bank Accounts** (`/auth/financovani/index.pl`) while logged into InSIS.\n2. Enter your active **Czech bank account** (*číslo účtu / kód banky* or IBAN) to receive accommodation and merit scholarships.\n3. View your tuition fee prescriptions, faculty bank details, and 8-digit **Variable Symbol (VS)**.",
        "Active student account; scholarship payouts require a bank account held in the Czech Republic.",
        "Because dashboard tiles vary by portlet settings, using the direct `/auth/financovani/index.pl` link works reliably on every student account.",
        "bank account, bank accounts, bankovni spojeni, enter bank account, register bank account, iban, scholarship payout account, variable symbol, variabilni symbol, financovani studia, study financing, financing of study"
    ),
    (
        "TASK_INSIS_PORTLETS",
        "portal_tech",
        "Portlets in InSIS & Student Navigation Sidebar",
        "Portlety v InSIS – Navigační lišta pro studenty",
        "Customization & Navigation",
        "/auth/system/portlety.pl",
        "https://insis.vse.cz/auth/system/portlety.pl?lang=en",
        "http://localhost:8502/auth/system/portlety.pl?lang=en",
        "Personal administration > Adjustment of the information system > Portlets in InSIS",
        "1. Log into InSIS **Personal administration** (`https://insis.vse.cz/auth/?lang=en`).\n2. Scroll to **Adjustment of the information system** and click **Portlets in InSIS** (`/auth/system/portlety.pl`).\n3. Under **Placing of portlets**, select **`Navigation bar for students`**, choose **`Basic - to the left from the page content`**, and click **Add**.\n4. A green **Student** quick-link sidebar will appear on the left with 14 academic shortcuts (*Mail box, Timetables, Exams, Plan of study, Results, Registration/enrollment, Final thesis assignment, Coursework submissions*).",
        "Authenticated InSIS account (portlets are not displayed in simplified/GPRS modes).",
        "The 'Navigation bar for students' portlet omits Scholarships (/auth/stipendia/), Study Financing & Bank Accounts (/auth/financovani/index.pl), Electronic Confirmation of Study (/auth/student/potvrzeni.pl), and Contact Centre (/auth/uradovna/). If a portlet breaks display, log in via https://insis.vse.cz/quick to remove it.",
        "portlets, portlet, portlets in insis, navigation bar for students, student navigation bar, left sidebar insis, customize insis, personal administration tiles, switch off portlets, insis quick, navigation guide for students"
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
        mod_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM insis_routes;")
        route_count = cur.fetchone()[0]
        if mod_count == 0 or route_count != len(ROUTES_DATA) or force_refresh:
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
        try:
            return init_database()
        except Exception:
            pass
    try:
        conn = sqlite3.connect(f"file:{DB_PATH.resolve().as_posix()}?mode=ro", uri=True)
    except Exception:
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
    raw_tokens = re.findall(r"[a-zA-Z0-9_\u00c0-\u017f]+", clean_q)
    if not raw_tokens:
        return []

    # Normalize common typos and filter boilerplate words for precise navigation matching
    typo_map = {
        "whre": "where",
        "querry": "query",
        "accomodation": "accommodation",
        "documnt": "document",
    }
    stopwords_nav = {"to", "the", "in", "on", "at", "where", "whre", "how", "can", "i", "find", "get", "is", "do", "of", "a", "an", "for"}
    normalized = [typo_map.get(t.lower(), t) for t in raw_tokens if len(t) > 1]
    substantive = [t for t in normalized if t.lower() not in stopwords_nav]
    active_tokens = substantive if substantive else normalized
        
    fts_match_expr = " OR ".join(f'"{t}"*' for t in active_tokens)
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
        placeholders = " OR ".join(["r.keywords LIKE ? OR r.title_en LIKE ? OR r.breadcrumbs LIKE ?"] * len(active_tokens[:4]))
        params = []
        for t in active_tokens[:4]:
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
    raw_tokens = re.findall(r"[a-zA-Z0-9_\u00c0-\u017f]+", query_str.strip())
    if not raw_tokens:
        conn.close()
        return []

    stopwords_pol = {
        "what", "happens", "happen", "if", "when", "where", "how", "why", "who",
        "can", "do", "does", "did", "is", "are", "am", "be", "to", "the", "in",
        "on", "at", "of", "for", "with", "from", "by", "an", "a", "my", "you",
        "your", "vse", "vše", "insis", "university", "prague", "student", "students",
        "rule", "rules", "policy", "policies", "times", "time",
    }
    substantive = [t for t in raw_tokens if len(t) > 1 and t.lower() not in stopwords_pol]
    if "3" in raw_tokens and ("fail" in query_str.lower() or "exam" in query_str.lower()):
        substantive.extend(["retake", "second", "attempt"])
    tokens = substantive if substantive else [t for t in raw_tokens if len(t) > 1]
    if not tokens:
        conn.close()
        return []

    fts_match_expr = " OR ".join(f'"{t}"*' for t in tokens)
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
    raw_tokens = re.findall(r"[a-zA-Z0-9_\u00c0-\u017f]+", query_str.strip())
    if not raw_tokens:
        conn.close()
        return []

    stopwords_loc = {
        "where", "whre", "is", "are", "the", "nearest", "closest", "find", "locate",
        "how", "to", "get", "in", "on", "at", "of", "for", "a", "an", "my", "vse", "vše",
    }
    substantive = [t for t in raw_tokens if len(t) > 1 and t.lower() not in stopwords_loc]
    tokens = substantive if substantive else [t for t in raw_tokens if len(t) > 1]
    if not tokens:
        conn.close()
        return []

    fts_match_expr = " OR ".join(f'"{t}"*' for t in tokens)
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
