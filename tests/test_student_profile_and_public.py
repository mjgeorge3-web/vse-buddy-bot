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
