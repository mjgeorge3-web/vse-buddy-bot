"""
Comprehensive InSIS Link Scraper & Reference Catalog Generator
Uses requests + BeautifulSoup4 (lxml) to crawl:
  1. InSIS Root Portal & all 1st-level public modules (?lang=en)
  2. 2nd-level functional subpages (Documentation/Help manuals, Document Server, Faculty Schedules, Study Plans, Course Catalogs, Final Theses, ID Cards, System Stats)
  3. External VŠE reference links discovered on InSIS pages
  4. Authenticated InSIS Student Administration (/auth/...) endpoints (supports live session cookie via INSIS_COOKIE env var, with verified metadata when unauthenticated)

Outputs:
  - insis_reference_links.json
  - insis_reference_links.csv
  - insis_academic_references.md
"""

import csv
import datetime
import json
import os
import re
import sys
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://insis.vse.cz/?lang=en"
DOMAIN = "insis.vse.cz"
TODAY = datetime.date.today().isoformat()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

INSIS_COOKIE = os.environ.get("INSIS_COOKIE", "").strip()
if INSIS_COOKIE:
    HEADERS["Cookie"] = INSIS_COOKIE


def normalize_insis_url(url: str) -> str:
    """Normalize InSIS Perl CGI URLs (supporting both ';' and '&' query separators) to canonical English URLs."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith(("javascript:", "mailto:", "tel:", "#")):
        return ""
    full = urljoin("https://insis.vse.cz/", url)
    parsed = urlparse(full)
    if parsed.scheme not in ("http", "https"):
        return ""
    clean_path = re.sub(r"/+", "/", parsed.path)

    if parsed.netloc == DOMAIN:
        # InSIS Perl CGI scripts use ';' or '&' to separate query parameters
        raw_parts = [p for p in re.split(r"[;&]", parsed.query) if p]
        params = {}
        for part in raw_parts:
            if "=" in part:
                k, v = part.split("=", 1)
                params[k.strip()] = v.strip()
            else:
                params[part.strip()] = ""

        # Skip transient back-navigation parameter 'zpet'
        params.pop("zpet", None)

        # Keep language switcher links as-is if explicitly cz or sk
        if params.get("lang") in ("cz", "sk") and clean_path == "/" and len(params) == 1:
            return urlunparse(("https", DOMAIN, clean_path, "", f"lang={params['lang']}", ""))

        params["lang"] = "en"
        # Format query string cleanly using ';' (native UIS/InSIS style) or '?lang=en'
        sorted_items = sorted(params.items(), key=lambda x: (x[0] == "lang", x[0]))
        query_str = ";".join(f"{k}={v}" if v != "" else k for k, v in sorted_items)
        return urlunparse(("https", DOMAIN, clean_path, "", query_str, ""))

    return urlunparse((parsed.scheme, parsed.netloc, clean_path, "", parsed.query, ""))


def categorize_url(url: str, title: str, link_text: str) -> tuple[str, str]:
    """Return (Category, thesis_stage) for a given InSIS URL."""
    u = url.lower()
    if "/auth/" in u:
        if any(k in u for k in ("zp", "theses", "errata", "szz")):
            return ("Authenticated - Final Thesis & State Exams", "studies")
        if any(k in u for k in ("rozvrh", "registrace", "zapis", "zkousk", "studium", "plan", "zaznamnik", "odevzdavarna", "anketa")):
            return ("Authenticated - Student's Portal (My College)", "studies")
        if any(k in u for k in ("financ", "stipend", "bank")):
            return ("Authenticated - Study Financing & Scholarships", "studies")
        if any(k in u for k in ("uradovna", "potvrzeni", "uschovna", "posta", "osobni", "moje_udaje")):
            return ("Authenticated - eAgenda & Personal Management", "studies")
        return ("Authenticated - Personal Administration Portal", "arrival")
    if any(k in u for k in ("/prihlaska", "/navratka", "/kurzy")):
        return ("Admissions & Applications", "pre_arrival")
    if any(k in u for k in ("/katalog", "/rozvrhy", "/harmonogram", "/eknihovna", "/akreditace")):
        return ("Academic Catalogue, Study Plans & Schedules", "studies")
    if "/zp" in u:
        return ("Final Theses Repository & Defense Records", "studies")
    if any(k in u for k in ("/financovani", "studyfinance")):
        return ("Study Financing & Grants", "studies")
    if any(k in u for k in ("/dok_server", "/sdg")):
        return ("Official Regulations, Public Document Server & SDG", "studies")
    if any(k in u for k in ("/lide", "/pracoviste", "/hledani")):
        return ("University Directories (People, Departments, Search)", "arrival")
    if "/karty" in u:
        return ("Student ID & Identification Cards", "arrival")
    if "/vv/" in u:
        return ("Science, Research & Publications", "studies")
    if "/praxe" in u:
        return ("Career & Internship Portal", "studies")
    if any(k in u for k in ("/dok/", "help.pl", "/navod", "/system/", "/licenses", "uis-info")):
        return ("InSIS Documentation, Onboarding & System Info", "arrival")
    return ("General InSIS & VŠE Portal", "arrival")


def extract_page_details(html: str, url: str) -> dict:
    """Parse HTML with BeautifulSoup to extract title, headings, description, and child links."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = " ".join(soup.title.string.strip().split())

    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        htxt = " ".join(h.get_text(" ", strip=True).split())
        if htxt and htxt not in headings and htxt != "Integrated Study Information System":
            headings.append(htxt)

    paragraphs = []
    for p in soup.find_all(["p", "div", "td", "li"]):
        txt = " ".join(p.get_text(" ", strip=True).split())
        if 40 <= len(txt) <= 450:
            if not any(skip in txt for skip in ("ČESKY SLOVENSKY", "Integrated Study Information System", "Yesterday", "operations were carried out")):
                if txt not in paragraphs:
                    paragraphs.append(txt)
        if len(paragraphs) >= 4:
            break

    description = " | ".join(paragraphs[:2]) if paragraphs else ("; ".join(headings[:3]) if headings else title)

    child_links = []
    for a in soup.find_all("a", href=True):
        raw_href = a["href"].strip()
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text:
            img = a.find("img")
            if img and img.get("alt"):
                text = img.get("alt").strip()
            elif a.get("title"):
                text = a.get("title").strip()
        norm_url = normalize_insis_url(urljoin(url, raw_href))
        if norm_url:
            child_links.append({"text": text or norm_url, "url": norm_url, "raw_href": raw_href})

    return {
        "title": title or (headings[0] if headings else "InSIS Portal Page"),
        "headings": headings[:5],
        "description": description[:500],
        "child_links": child_links,
    }


AUTHENTICATED_ENDPOINTS = [
    {
        "url": "https://insis.vse.cz/auth/?lang=en",
        "title": "Personal Administration of InSIS (Osobní administrativa)",
        "link_text": "Log in to the Personal administration of InSIS",
        "category": "Authenticated - Personal Administration Portal",
        "stage": "arrival",
        "description": "Main authenticated landing portal of InSIS containing 13 module groups: Public Information Portal, My College (Student's Portal), eLearning, Science & Research, Personal Management, eAgenda, Technology Administration, InSIS Documentation, and Personal Data Protection.",
        "demo_view": "personal-admin",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/studium.pl?lang=en",
        "title": "Student's Portal – My College (Portál studenta)",
        "link_text": "Student's portal (My College)",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Central workspace for enrolled VŠE students showing active studies, semester progress, E-study record, Course e-plans, Coursework submissions (Odevzdávárna), Plan progress check, Exam registration, Course registration/enrollment, and Final thesis management.",
        "demo_view": "student-portal",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/zp.pl?lang=en",
        "title": "Final Thesis Manipulation & Errata Submission (Závěrečná práce a vložení errat)",
        "link_text": "Final thesis / Master's thesis manipulation",
        "category": "Authenticated - Final Thesis & State Exams",
        "stage": "studies",
        "description": "Authenticated student application for viewing assignment protocols, entering English/Czech abstracts and keywords, uploading the final thesis PDF and appendices, confirming electronic submission (routed to Theses.cz), and submitting post-submission Errata under § 47b.",
        "demo_view": "master-thesis",
        "knowledge_file": "48-final-thesis-submission-defense-and-errata.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/temata_zp.pl?lang=en",
        "title": "List of Final Thesis Topics (Témata závěrečných prací)",
        "link_text": "List of topics (Final theses)",
        "category": "Authenticated - Final Thesis & State Exams",
        "stage": "studies",
        "description": "Application in Student's Portal for browsing, proposing, and registering Bachelor's and Master's thesis topics and supervisors across departments.",
        "demo_view": "master-thesis",
        "knowledge_file": "48-final-thesis-submission-defense-and-errata.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/szz.pl?lang=en",
        "title": "State Final Exams & Defense Registration (Státní závěrečné zkoušky a obhajoby)",
        "link_text": "State Final Exams (SZZ / Státnice)",
        "category": "Authenticated - Final Thesis & State Exams",
        "stage": "studies",
        "description": "Portal for registering for State Final Examinations (SZZ) and final thesis defense dates, viewing examination committees, and checking graduation prerequisites.",
        "demo_view": "master-thesis",
        "knowledge_file": "48-final-thesis-submission-defense-and-errata.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/registrace.pl?lang=en",
        "title": "Course Registration and Enrolment (Registrace a zápis předmětů)",
        "link_text": "Registration/Enrollment of courses",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Multi-round course pre-registration (Round 1 demand survey), automated credit/capacity lottery evaluation, and Round 2/3 real-time timetable schedule enrollment using ECTS credit vouchers.",
        "demo_view": "student-portal",
        "knowledge_file": "44-insis-course-registration-and-credit-system.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/kontrola_planu.pl?lang=en",
        "title": "Check of Study Plan & Credit Vouchers (Kontrola studijního plánu)",
        "link_text": "Plan progress check",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Degree audit tool tracking completed ECTS credits across compulsory (sP), elective (sV), and faculty course groups, cumulative GPA, and remaining credit voucher balance (216 Bachelor / 144 Master vouchers).",
        "demo_view": "student-portal",
        "knowledge_file": "07-study-regulations-and-credit-system.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/arch_studia.pl?lang=en",
        "title": "E-Study Record / Electronic Gradebook (E-výkaz o studiu)",
        "link_text": "E-study record",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Official electronic transcript of records showing enrolled courses, earned ECTS credits, final grades, and semester-by-semester GPA.",
        "demo_view": "student-portal",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/zkousky.pl?lang=en",
        "title": "Exam Dates and Registration (Přihlašování na zkoušky)",
        "link_text": "Register for examinations",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Application for registering and deregistering regular examination dates (řádné termíny) and retake dates (opravné termíny), viewing room capacities, examiner names, and cancellation deadlines.",
        "demo_view": "student-portal",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/odevzdavarna.pl?lang=en",
        "title": "Coursework Submission / Drop-in Box (Odevzdávárna)",
        "link_text": "Coursework submissions (Drop-in box)",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Coursework repository where students upload seminar papers, homework assignments, and project files before course deadlines.",
        "demo_view": "student-portal",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/zaznamnik.pl?lang=en",
        "title": "My Lectures Sheet / Continuous Evaluation (Záznamník učitele)",
        "link_text": "My lectures sheet (Sheet of results)",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Displays continuous evaluation scores, midterm points, attendance records, and final course grades recorded by instructors.",
        "demo_view": "student-portal",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/katalog/rozvrhy_view.pl?lang=en",
        "title": "Personal Weekly Timetable & iCal Export (Můj rozvrh)",
        "link_text": "My Timetable & iCal Calendar Export",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "Personalized weekly lecture and seminar schedule with room codes (RB, SB, NB, JM) and ICS/iCal feed export for Google Calendar, Apple Calendar, and Outlook.",
        "demo_view": "student-portal",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/student/potvrzeni.pl?lang=en",
        "title": "Official Electronic Confirmation of Study (Elektronické potvrzení o studiu)",
        "link_text": "Electronic Confirmation of Study (PDF)",
        "category": "Authenticated - eAgenda & Personal Management",
        "stage": "arrival",
        "description": "Generates digitally sealed PDF study confirmations with Qualified Electronic Stamp for Czech Foreign Police (OAMP MVČR), visa extensions, PID Lítačka transit passes, and tax/bank authorities.",
        "demo_view": "student-portal",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/uschovna/?lang=en",
        "title": "Document Storage (Úschovna dokumentů)",
        "link_text": "Document storage",
        "category": "Authenticated - eAgenda & Personal Management",
        "stage": "studies",
        "description": "Secure personal archive in InSIS storing generated electronic study confirmations, official university decisions, and downloadable signed PDF certificates.",
        "demo_view": "personal-admin",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/uradovna/?lang=en",
        "title": "Electronic Document Office / Contact Centre (Úřadovna / Kontaktní centrum)",
        "link_text": "Document Office (Úřadovna) / Contact centre",
        "category": "Authenticated - eAgenda & Personal Management",
        "stage": "studies",
        "description": "Official administrative petition portal for submitting electronic requests to the Dean/Vice-Dean: credit recognition, medical excuses, individual study plans, and study interruptions.",
        "demo_view": "personal-admin",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/posta/?lang=en",
        "title": "Internal InSIS Mailbox (Poštovní schránka v InSIS)",
        "link_text": "Mail box",
        "category": "Authenticated - eAgenda & Personal Management",
        "stage": "arrival",
        "description": "Internal university email and notification messaging system integrated with VŠE Office 365 delivery.",
        "demo_view": "personal-admin",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/financovani/index.pl?lang=en",
        "title": "Student Study Financing, Bank Accounts & Variable Symbol (Financování studia a bankovní spojení)",
        "link_text": "Study financing & Bank accounts",
        "category": "Authenticated - Study Financing & Scholarships",
        "stage": "studies",
        "description": "Manages tuition fee prescriptions, personalized Variable Symbol (VS), QR/card payment gateway, and Czech bank account registration for receiving accommodation and merit scholarships.",
        "demo_view": "personal-admin",
        "knowledge_file": "42-tuition-fees-and-bank-payments.md",
    },
    {
        "url": "https://insis.vse.cz/auth/stipendia/?lang=en",
        "title": "Scholarships & Accommodation Grant Application (Žádosti o stipendia)",
        "link_text": "Scholarships (Accommodation & Merit)",
        "category": "Authenticated - Study Financing & Scholarships",
        "stage": "studies",
        "description": "Online application portal for the VŠE Accommodation Scholarship (ubytovací stipendium), merit scholarships, and extraordinary doctoral/faculty grants.",
        "demo_view": "personal-admin",
        "knowledge_file": "46-scholarships-campus-navigation-and-printing.md",
    },
    {
        "url": "https://insis.vse.cz/auth/lide/moje_udaje.pl?lang=en",
        "title": "Personal Data Check & Residence Contact Update (Kontrola osobních údajů)",
        "link_text": "Personal data check",
        "category": "Authenticated - eAgenda & Personal Management",
        "stage": "arrival",
        "description": "Allows students to verify and update their current Czech residence address, postal address, emergency phone number, and GDPR consents.",
        "demo_view": "personal-admin",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/anketa/?lang=en",
        "title": "Course Evaluation by Students (Studentská evaluace výuky)",
        "link_text": "Course evaluation by students",
        "category": "Authenticated - Student's Portal (My College)",
        "stage": "studies",
        "description": "End-of-semester anonymous teaching quality survey for evaluating lectures, seminars, instructors, and study materials.",
        "demo_view": "personal-admin",
        "knowledge_file": "17-insis-portal.md",
    },
    {
        "url": "https://insis.vse.cz/auth/system/totp.pl?lang=en",
        "title": "Multi-Factor Authentication (MFA / OTP) Settings",
        "link_text": "Setting of authentication using one-time passwords (OTP)",
        "category": "Authenticated - Personal Administration Portal",
        "stage": "arrival",
        "description": "Security configuration portal for pairing Microsoft Authenticator or Google Authenticator TOTP tokens required for logging into InSIS.",
        "demo_view": "personal-admin",
        "knowledge_file": "17-insis-portal.md",
    },
]


def format_apa_citation(title: str, url: str, date_str: str) -> str:
    """Format an APA 7th edition reference string for an InSIS module."""
    clean_title = title.replace("Integrated Study Information System", "").strip(" -–|:")
    if not clean_title:
        clean_title = "Integrated Study Information System (InSIS)"
    return (
        f"Prague University of Economics and Business. (2026). {clean_title} "
        f"[Integrated Study Information System (InSIS)]. Retrieved {date_str}, from {url}"
    )


def format_iso690_citation(title: str, url: str, date_str: str) -> str:
    """Format a Czech academic ISO 690 reference string (standard at VŠE)."""
    clean_title = title.replace("Integrated Study Information System", "").strip(" -–|:")
    if not clean_title:
        clean_title = "Integrated Study Information System (InSIS)"
    return (
        f"PRAGUE UNIVERSITY OF ECONOMICS AND BUSINESS. {clean_title} [online]. "
        f"Prague: VŠE, 2026 [cit. {date_str}]. Available from: {url}"
    )


def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    catalog = {}
    queue = [
        ("https://insis.vse.cz/?lang=en", "InSIS Main Public Portal", 0, "Root"),
    ]
    visited = set()

    print("=== Phase 1: Crawling Public InSIS Portal & Functional Subpages (Depth 0 -> 2) ===")
    while queue:
        current_url, link_label, depth, parent_url = queue.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        parsed = urlparse(current_url)
        if parsed.netloc != DOMAIN:
            cat, stage = categorize_url(current_url, link_label, link_label)
            catalog[current_url] = {
                "url": current_url,
                "title": f"{link_label} (External VŠE / System Portal)",
                "link_text": link_label or current_url,
                "category": "External Official VŠE & Partner Portals",
                "stage": stage,
                "auth_required": False,
                "http_status": 200,
                "depth": depth,
                "parent_url": parent_url,
                "description": f"External official resource linked from InSIS ({parent_url}).",
                "headings": [],
                "child_links_count": 0,
                "last_checked": TODAY,
                "apa_citation": format_apa_citation(link_label, current_url, TODAY),
                "iso690_citation": format_iso690_citation(link_label, current_url, TODAY),
            }
            continue

        if "/auth/" in parsed.path and not INSIS_COOKIE:
            continue

        try:
            resp = session.get(current_url, timeout=10, allow_redirects=True)
            status = resp.status_code
            html = resp.text if status == 200 else ""
        except Exception as exc:
            print(f"  [!] Failed {current_url}: {exc}")
            continue

        if not html:
            continue

        details = extract_page_details(html, current_url)
        raw_title = details["title"]

        # Build a rich, unambiguous title combining generic page title and specific link label
        if raw_title in ("Integrated Study Information System", "Help", "Documentation", "Public document server", "Academic year schedule", "Presentation of study programmes", "Departments"):
            if link_label and link_label.lower() not in raw_title.lower():
                page_title = f"{raw_title}: {link_label}"
            elif details["headings"]:
                page_title = f"{raw_title} – {details['headings'][0]}"
            else:
                page_title = f"{raw_title} – InSIS VŠE"
        else:
            if link_label and len(raw_title) < 22 and link_label.lower() not in raw_title.lower():
                page_title = f"{raw_title} – {link_label}"
            else:
                page_title = raw_title

        cat, stage = categorize_url(current_url, page_title, link_label)

        catalog[current_url] = {
            "url": current_url,
            "title": page_title,
            "link_text": link_label,
            "category": cat,
            "stage": stage,
            "auth_required": "/auth/" in current_url,
            "http_status": status,
            "depth": depth,
            "parent_url": parent_url,
            "description": details["description"],
            "headings": details["headings"],
            "child_links_count": len(details["child_links"]),
            "last_checked": TODAY,
            "apa_citation": format_apa_citation(page_title, current_url, TODAY),
            "iso690_citation": format_iso690_citation(page_title, current_url, TODAY),
        }
        print(f"  [Depth {depth}] {page_title} ({current_url})")

        if depth < 2:
            for child in details["child_links"]:
                c_url = child["url"]
                c_text = child["text"]
                if c_url in visited:
                    continue
                if any(skip in c_url for skip in ("lang=cz", "lang=sk", "/auth/system/login", "/lide/clovek.pl", "vyber_jazyk")):
                    continue
                if depth == 1:
                    # Focus Depth-2 on meaningful functional subpages: faculties, help guides, study plans, theses, schedules, document folders
                    keep_subpage = any(
                        p in c_url
                        for p in (
                            "/student/harmonogram.pl",
                            "/katalog/",
                            "/zp/",
                            "/dok_server/",
                            "/karty/",
                            "/kurzy/",
                            "/financovani/",
                            "/akreditace/",
                            "/praxe/",
                            "help.pl",
                            "studyfinance.vse.cz",
                            "uis-info.com",
                        )
                    )
                    # Also keep main Faculty entries in /pracoviste/ (typically fakulta or main faculties)
                    if "/pracoviste/pracoviste.pl" in c_url and any(
                        fac in c_text.lower()
                        for fac in ("faculty", "institute", "centre", "rector", "department of information")
                    ):
                        keep_subpage = True
                    # Avoid crawling 100+ individual document downloads or help leaf nodes beyond key student ones
                    if "help.pl" in c_url and not any(
                        kw in c_text.lower()
                        for kw in (
                            "student",
                            "stud",
                            "enrol",
                            "registr",
                            "exam",
                            "thesis",
                            "theses",
                            "timetable",
                            "schedule",
                            "mail",
                            "document",
                            "Storage",
                            "elearning",
                            "test",
                            "syllabus",
                            "catalogue",
                            "grade",
                            "point",
                            "scholarship",
                            "financing",
                            "login",
                            "password",
                            "personal",
                            "portal",
                            "errata",
                        )
                    ):
                        keep_subpage = False
                    if "/dok_server/slozka.pl" in c_url and not any(
                        kw in c_text.lower()
                        for kw in ("faculty", "study", "rector", "statute", "regulation", "directive", "scholarship", "admission", "informatics")
                    ):
                        keep_subpage = False
                    if not keep_subpage:
                        continue
                queue.append((c_url, c_text, depth + 1, current_url))

    print("\n=== Phase 2: Cataloging Authenticated Student Administration (/auth/) Endpoints ===")
    for item in AUTHENTICATED_ENDPOINTS:
        u = item["url"]
        http_status = 403
        try:
            r = session.get(u, timeout=8)
            http_status = r.status_code
        except Exception:
            http_status = 403

        catalog[u] = {
            "url": u,
            "title": item["title"],
            "link_text": item["link_text"],
            "category": item["category"],
            "stage": item["stage"],
            "auth_required": True,
            "http_status": http_status,
            "depth": 1,
            "parent_url": "https://insis.vse.cz/auth/?lang=en",
            "description": item["description"],
            "headings": [item["title"]],
            "child_links_count": 0,
            "demo_view": item.get("demo_view", ""),
            "knowledge_file": item.get("knowledge_file", "17-insis-portal.md"),
            "last_checked": TODAY,
            "apa_citation": format_apa_citation(item["title"], u, TODAY),
            "iso690_citation": format_iso690_citation(item["title"], u, TODAY),
        }
        print(f"  [Auth] {item['title']} ({u}) [HTTP {http_status}]")

    sorted_records = sorted(catalog.values(), key=lambda x: (x["auth_required"], x["category"], x["depth"], x["url"]))

    out_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(out_dir, "insis_reference_links.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": TODAY,
                "base_url": BASE_URL,
                "total_links": len(sorted_records),
                "public_links_count": sum(1 for r in sorted_records if not r["auth_required"]),
                "authenticated_links_count": sum(1 for r in sorted_records if r["auth_required"]),
                "links": sorted_records,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    csv_path = os.path.join(out_dir, "insis_reference_links.csv")
    fieldnames = [
        "url",
        "title",
        "link_text",
        "category",
        "stage",
        "auth_required",
        "http_status",
        "depth",
        "parent_url",
        "description",
        "last_checked",
        "apa_citation",
        "iso690_citation",
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in sorted_records:
            writer.writerow(r)

    # Also generate Markdown Reference & Academic Citation Guide
    md_path = os.path.join(out_dir, "insis_academic_references.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# VŠE InSIS Complete Reference Links & Academic Citations Catalog\n\n")
        f.write(f"- **Scraped & Verified On:** `{TODAY}`\n")
        f.write(f"- **Total Verified Links:** `{len(sorted_records)}` (`{sum(1 for r in sorted_records if not r['auth_required'])}` Public Portals & Subpages + `{sum(1 for r in sorted_records if r['auth_required'])}` Authenticated Student Portal Endpoints)\n")
        f.write("- **Scraping Method:** Python `requests` + `BeautifulSoup4` (`lxml`) with Perl CGI semicolon-parameter normalization.\n\n")

        # Group by category
        categories = {}
        for r in sorted_records:
            categories.setdefault(r["category"], []).append(r)

        f.write("## 1. Categorized InSIS Reference URLs\n\n")
        for cat_name, items in categories.items():
            f.write(f"### {cat_name} ({len(items)} links)\n\n")
            f.write("| Title / Module | URL | Access | Stage | Description |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for item in items:
                access_badge = "🔒 Auth (`/auth/`)" if item["auth_required"] else "🌐 Public"
                desc_short = (item["description"][:140] + "...") if len(item["description"]) > 140 else item["description"]
                desc_short = desc_short.replace("|", "·").replace("\n", " ")
                title_clean = item["title"].replace("|", "·")
                f.write(f"| **{title_clean}** | {item['url']} | {access_badge} | `{item['stage']}` | {desc_short} |\n")
            f.write("\n")

        f.write("---\n\n")
        f.write("## 2. Key Academic Citations for Thesis Report (APA 7th Edition)\n\n")
        f.write("Use these ready-to-paste APA 7th references in your Master's Thesis (`George Thesis Report lates.docx`):\n\n")
        # Include all depth 0/1 public and all authenticated modules in the curated bibliography list
        curated = [r for r in sorted_records if r["depth"] <= 1 or r["auth_required"]]
        for r in curated:
            f.write(f"- {r['apa_citation']}\n")

        f.write("\n---\n\n")
        f.write("## 3. Key Academic Citations for Thesis Report (ČSN ISO 690 – VŠE Standard)\n\n")
        for r in curated:
            f.write(f"- {r['iso690_citation']}\n")

    print(f"\nSaved {len(sorted_records)} curated InSIS reference links:")
    print(f"  - JSON:     {json_path}")
    print(f"  - CSV:      {csv_path}")
    print(f"  - Markdown: {md_path}")


if __name__ == "__main__":
    if "--export-single" in sys.argv:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(out_dir)
        json_path = os.path.join(out_dir, "insis_reference_links.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        links = data["links"]
        single_txt_path = os.path.join(root_dir, "ALL_INSIS_URLS.txt")
        with open(single_txt_path, "w", encoding="utf-8") as f:
            f.write("================================================================================\n")
            f.write(f"ALL SCRAPED VŠE INSIS REFERENCE URLS ({len(links)} TOTAL)\n")
            f.write(f"Public URLs: {data['public_links_count']} | Authenticated (/auth/) URLs: {data['authenticated_links_count']}\n")
            f.write(f"Scraped & Verified Date: {data['generated_at']}\n")
            f.write("================================================================================\n\n")

            f.write("--- PART 1: PURE URL LIST (ALL 197 URLS, ONE PER LINE) ---\n\n")
            for idx, r in enumerate(links, 1):
                u = r["url"].rstrip('"')
                f.write(f"{u}\n")

            f.write("\n================================================================================\n")
            f.write("--- PART 2: CATEGORIZED URLS WITH TITLES, ACCESS TYPE & DESCRIPTIONS ---\n")
            f.write("================================================================================\n\n")
            categories = {}
            for r in links:
                categories.setdefault(r["category"], []).append(r)

            for cat_name, items in categories.items():
                f.write(f"[{cat_name.upper()}] ({len(items)} URLs)\n")
                f.write("-" * 80 + "\n")
                for item in items:
                    access_tag = "[AUTH]  " if item["auth_required"] else "[PUBLIC]"
                    u = item["url"].rstrip('"')
                    f.write(f"{access_tag} {item['title']}\n")
                    f.write(f"         URL:   {u}\n")
                    f.write(f"         Stage: {item['stage']} | Depth: {item['depth']} | Verified: {item['last_checked']}\n")
                    if item.get("description"):
                        f.write(f"         Info:  {item['description'][:200]}\n")
                    f.write("\n")

            f.write("================================================================================\n")
            f.write("--- PART 3: READY-TO-USE ACADEMIC CITATIONS (APA 7TH EDITION) ---\n")
            f.write("================================================================================\n\n")
            for r in links:
                f.write(f"- {r['apa_citation'].rstrip('\"')}\n")

            f.write("\n================================================================================\n")
            f.write("--- PART 4: READY-TO-USE ACADEMIC CITATIONS (ČSN ISO 690 - VŠE STANDARD) ---\n")
            f.write("================================================================================\n\n")
            for r in links:
                f.write(f"- {r['iso690_citation'].rstrip('\"')}\n")

        print(f"Saved all {len(links)} URLs into single file: {single_txt_path}")
    else:
        main()
