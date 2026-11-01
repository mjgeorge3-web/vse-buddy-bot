"""Tests for Public No-Login InSIS Access, Smart Topic Switch, Ideas 1, 2 & 3."""

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import student_profile


def test_public_no_login_eapplication_context():
    ctx = {
        "logged_in": False,
        "page_key": "public_home",
        "page_title": "Public Information Portal",
        "page_url": "https://insis.vse.cz/?lang=en",
    }
    chunks = student_profile.build_dynamic_context_chunks(
        "How do I submit the E-application form to study at VŠE?", ctx
    )
    assert len(chunks) == 1
    assert chunks[0]["id"] == "public_insis_context"
    assert "https://insis.vse.cz/prihlaska/?lang=en" in chunks[0]["text"]
    assert "WITHOUT Login" in chunks[0]["text"]


def test_public_no_login_courses_and_plans_context():
    ctx = {"logged_in": False, "page_key": "public_home"}
    chunks = student_profile.build_dynamic_context_chunks(
        "Can I browse the Course catalogue and Study plans without an account?", ctx
    )
    assert len(chunks) == 1
    assert "https://insis.vse.cz/katalog/?lang=en" in chunks[0]["text"]


def test_public_no_login_visa_question_skips_insis_menu_clutter():
    ctx = {"logged_in": False, "page_key": "public_home"}
    chunks = student_profile.build_dynamic_context_chunks(
        "Do I need to register with the Foreign Police within 3 days of arrival?", ctx
    )
    assert chunks == []


def test_public_no_login_explicit_no_account_dorm_question():
    ctx = {"logged_in": False, "page_key": "public_home"}
    chunks = student_profile.build_dynamic_context_chunks(
        "What can I access on this page without an account?", ctx
    )
    assert len(chunks) == 1
    assert chunks[0]["id"] == "public_insis_context"


def test_logged_in_idea1_screen_context_master_thesis():
    ctx = {
        "logged_in": True,
        "personalised": True,
        "user_name": "George Joseph",
        "page_key": "master_thesis",
        "page_title": "Master's Thesis",
        "page_url": "https://insis.vse.cz/auth/student/zp.pl?lang=en",
    }
    chunks = student_profile.build_dynamic_context_chunks(
        "What do the 3 red X icons on this page mean?", ctx
    )
    ids = [c["id"] for c in chunks]
    assert "live_page_master_thesis" in ids
    assert "student_personal_profile" in ids


def test_logged_in_idea2_personal_vouchers_and_gdpr_toggle():
    ctx_on = {
        "logged_in": True,
        "personalised": True,
        "user_name": "George Joseph",
        "page_key": "student_portal",
    }
    chunks_on = student_profile.build_dynamic_context_chunks(
        "How many credit vouchers do I have left?", ctx_on
    )
    assert len(chunks_on) == 1
    assert chunks_on[0]["id"] == "student_personal_profile"
    assert "120 remaining out of 144" in chunks_on[0]["text"]

    # GDPR Opt-Out: personalised=False must NOT inject personal study profile
    ctx_off = dict(ctx_on, personalised=False)
    chunks_off = student_profile.build_dynamic_context_chunks(
        "How many credit vouchers do I have left?", ctx_off
    )
    assert chunks_off == []


def test_logged_in_smart_topic_switch_ignores_open_insis_screen():
    ctx = {
        "logged_in": True,
        "personalised": True,
        "user_name": "George Joseph",
        "page_key": "master_thesis",
    }
    chunks = student_profile.build_dynamic_context_chunks(
        "Where is the nearest washroom in Rajská Building and how does visa extension work?",
        ctx,
    )
    assert chunks == []


def test_idea3_onboarding_checklist_variants():
    flat_items = student_profile.get_onboarding_checklist(
        origin="non_eu", housing="flat", stage="arrival"
    )
    assert any("Foreign Police" in item["task"] and "3 Working Days" in item["task"] for item in flat_items)

    dorm_items = student_profile.get_onboarding_checklist(
        origin="non_eu", housing="dorm", stage="arrival"
    )
    assert any("automatically" in item["task"] for item in dorm_items)


def test_public_home_html_contains_all_seven_authentic_sections():
    html = (BASE_DIR / "insis_demo" / "index.html").read_text(encoding="utf-8")
    expected_headings = [
        "Personal administration",
        "Admission procedure",
        "Information about VŠE",
        "Study information",
        "Science and research information",
        "Jobs portal",
        "About the information system",
        "Log in to the Personal administration of InSIS",
        "E-application form to study at VŠE",
        "Česká verze informačního systému (Czech version)",
        "Slovenská verzia informačného systému (Slovak version)",
    ]
    for heading in expected_headings:
        assert heading in html, f"Missing expected public InSIS text: {heading}"


def test_custom_user_login_profile_uses_exact_logged_in_name():
    ctx = {
        "logged_in": True,
        "personalised": True,
        "user_name": "Maria Novak",
        "page_key": "student_portal",
    }
    chunks = student_profile.build_dynamic_context_chunks(
        "How many credit vouchers do I have left?", ctx
    )
    assert len(chunks) == 1
    assert "Maria Novak" in chunks[0]["title"]
    assert "Authenticated Student: Maria Novak" in chunks[0]["text"]
    assert "George Joseph" not in chunks[0]["text"]


def test_logged_out_context_never_contains_student_name():
    ctx = {
        "logged_in": False,
        "personalised": False,
        "user_name": "Guest",
        "page_key": "public_home",
    }
    chunks = student_profile.build_dynamic_context_chunks(
        "How many credit vouchers do I have left?", ctx
    )
    for c in chunks:
        assert "George Joseph" not in c["text"]
        assert "student_personal_profile" != c["id"]


def test_login_password_and_clean_logout_in_frontend():
    app_js = (BASE_DIR / "insis_demo" / "app.js").read_text(encoding="utf-8")
    html = (BASE_DIR / "insis_demo" / "index.html").read_text(encoding="utf-8")
    assert 'REQUIRED_INSIS_PASSWORD = "ism_mastersthesis"' in app_js
    assert 'localStorage.removeItem("insis_session_user_v3")' in app_js
    assert "resetBotConversationForSession()" in app_js
    assert "George Joseph" not in html
    assert "George Joseph" not in app_js


def test_multiturn_accommodation_query_isolation(monkeypatch):
    from bot import BuddyBot
    bot = BuddyBot()
    # Bypass remote embedding call in unit test so it executes instantaneously offline
    monkeypatch.setattr(bot.retriever, "embed_query", lambda q: None)

    history = [
        {"role": "user", "content": "What are the visa and 3-day Foreign Police registration rules for international students?"},
        {"role": "assistant", "content": "You must register with the Czech Foreign Police within 3 working days."}
    ]
    query = bot.build_retrieval_query("how to find accomodation", history)
    assert query == "how to find accomodation"
    assert "visa" not in query.lower()
    assert "police" not in query.lower()

    # Verify retrieval returns dormitory / accommodation information
    chunks, top_score, mode = bot.retriever.retrieve(query)
    found_accomodation = any("dorm" in (c.get("title", "") + c.get("text", "")).lower() or "housing" in (c.get("title", "") + c.get("text", "")).lower() for c in chunks)
    assert found_accomodation, "Failed to retrieve dormitory or accommodation chunk!"


def test_multiturn_credit_vouchers_query_isolation():
    from bot import BuddyBot
    bot = BuddyBot()
    history = [
        {"role": "user", "content": "Where do I submit errata for my Master thesis in InSIS?"},
        {"role": "assistant", "content": "Under Master thesis editing page click Insert errata."}
    ]
    query = bot.build_retrieval_query("how many credit vouchers i have left", history)
    assert query == "how many credit vouchers i have left"
    assert "errata" not in query.lower()
    assert "thesis" not in query.lower()

    # Verify dynamic profile returns student voucher info
    ctx = {"logged_in": True, "personalised": True, "user_name": "Alexander Kovac", "page_key": "student_portal"}
    dyn_chunks = student_profile.build_dynamic_context_chunks(query, ctx)
    assert len(dyn_chunks) == 1
    assert "Alexander Kovac" in dyn_chunks[0]["title"]
    assert "120" in dyn_chunks[0]["text"]
    assert "144" in dyn_chunks[0]["text"]


def test_vse_logo_and_academic_demo_disclaimers():
    html = (BASE_DIR / "insis_demo" / "index.html").read_text(encoding="utf-8")
    css = (BASE_DIR / "insis_demo" / "styles.css").read_text(encoding="utf-8")
    app_js = (BASE_DIR / "insis_demo" / "app.js").read_text(encoding="utf-8")

    # Logo assets exist and are linked in header
    assert (BASE_DIR / "insis_demo" / "assets" / "vse_logo.svg").exists()
    assert (BASE_DIR / "insis_demo" / "assets" / "vse_logo.png").exists()
    assert 'src="assets/vse_logo.svg"' in html
    assert 'alt="VŠE Prague Logo"' in html

    # Visible academic demo disclaimer banner at the top of the portal
    assert 'class="insis-demo-banner"' in html
    assert "DEMO / EXPERIMENTAL" in html
    assert "Master's Thesis Simulation" in html
    assert "official VŠE InSIS portal" in html
    assert "https://insis.vse.cz" in html

    # Demo pill next to title and meta note
    assert "SIMULATION DEMO" in html
    assert "Academic Research Environment" in html

    # Prominent footer disclaimer
    assert "insis-academic-disclaimer-footer" in html
    assert "Academic Master's Thesis Prototype" in html

    # In-bot research disclaimer
    assert "Academic Master's Thesis Prototype" in app_js
    assert "Demo Prototype" in app_js
