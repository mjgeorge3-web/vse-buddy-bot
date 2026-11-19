"""Unit tests for the InSIS Navigation Database & Semantic Router."""

import os
from pathlib import Path
import sqlite3
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import insis_nav_db


def test_database_initialization():
    """Verify that InSIS navigation database initializes with all tables and rows."""
    conn = insis_nav_db.init_database()
    assert conn is not None
    
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM insis_modules;")
    modules_count = cur.fetchone()[0]
    assert modules_count >= 7, f"Expected at least 7 modules, got {modules_count}"
    
    cur.execute("SELECT COUNT(*) FROM insis_routes;")
    routes_count = cur.fetchone()[0]
    assert routes_count >= 20, f"Expected at least 20 routes, got {routes_count}"


def test_search_thesis_submission():
    """Verify that searching for thesis upload returns the correct task."""
    hits = insis_nav_db.search_routes("where do I upload my master thesis", limit=2)
    assert len(hits) > 0
    task_ids = [h["task_id"] for h in hits]
    assert "TASK_THESIS_SUBMISSION" in task_ids or "TASK_THESIS_REGISTRATION" in task_ids
    assert "/auth/student/zp.pl" in hits[0]["portal_path"]


def test_search_credit_vouchers():
    """Verify that searching for vouchers returns TASK_CREDIT_VOUCHERS."""
    hits = insis_nav_db.search_routes("how do I check remaining credit vouchers", limit=1)
    assert len(hits) == 1
    assert hits[0]["task_id"] == "TASK_CREDIT_VOUCHERS"
    assert "kontrola_planu.pl" in hits[0]["portal_path"]
    assert "144" in hits[0]["step_by_step_instructions"] or "Allocation" in hits[0]["step_by_step_instructions"] or "balance" in hits[0]["step_by_step_instructions"].lower()


def test_search_course_registration():
    """Verify that searching for course enrollment returns TASK_COURSE_REGISTRATION."""
    hits = insis_nav_db.search_routes("course registration zapis", limit=1)
    assert len(hits) == 1
    assert hits[0]["task_id"] == "TASK_COURSE_REGISTRATION"
    assert "registrace.pl" in hits[0]["portal_path"]


def test_search_tuition_variable_symbol():
    """Verify that searching for tuition returns TASK_TUITION_PAYMENT."""
    hits = insis_nav_db.search_routes("how to pay tuition fees variable symbol", limit=1)
    assert len(hits) == 1
    assert hits[0]["task_id"] == "TASK_TUITION_PAYMENT"
    assert "financovani/index.pl" in hits[0]["portal_path"]


def test_format_navigation_card():
    """Verify that format_navigation_card generates markdown with breadcrumbs and links."""
    route = insis_nav_db.get_route_by_task_id("TASK_THESIS_SUBMISSION")
    assert route is not None
    card_md = insis_nav_db.format_navigation_card(route)
    assert "🧭 InSIS Navigation:" in card_md
    assert "Breadcrumb Trail:" in card_md
    assert "Step-by-Step Instructions:" in card_md
    assert "http://localhost:8502/auth/student/zp.pl" in card_md
    assert "https://insis.vse.cz" in card_md


def test_empty_and_unknown_queries():
    """Verify graceful handling of empty or nonsense queries."""
    assert insis_nav_db.search_routes("") == []
    assert insis_nav_db.search_routes("   ") == []
    hits = insis_nav_db.search_routes("xyz123nonexistentterm999")
    assert isinstance(hits, list)


def test_search_accommodation_scholarship_authentic_route():
    """Verify that searching for accommodation scholarship benefit returns authentic InSIS route."""
    hits = insis_nav_db.search_routes("how do i apply for Accomodation scholorship benefit", limit=1)
    assert len(hits) == 1
    hit = hits[0]
    assert hit["task_id"] == "TASK_SCHOLARSHIP_ACCOMMODATION"
    assert hit["official_url"] == "https://insis.vse.cz/auth/stipendia/?lang=en"
    assert "Financing of study and scholarships" in hit["breadcrumbs"]
    assert "Žádosti o stipendia" in hit["breadcrumbs"] or "Scholarships" in hit["breadcrumbs"]
    assert "Czech bank account" in hit["step_by_step_instructions"]


def test_public_catalog_routes_have_no_auth():
    """Verify that public InSIS catalog and study plans endpoints do NOT contain /auth/ prefix."""
    plans = insis_nav_db.get_route_by_task_id("TASK_STUDY_PLANS")
    assert plans is not None
    assert "/auth/" not in plans["official_url"]
    assert plans["official_url"] == "https://insis.vse.cz/katalog/plany.pl?lang=en"

    catalogue = insis_nav_db.get_route_by_task_id("TASK_COURSE_CATALOGUE")
    assert catalogue is not None
    assert "/auth/" not in catalogue["official_url"]
    assert catalogue["official_url"] == "https://insis.vse.cz/katalog/?lang=en"


def test_all_routes_use_verified_official_urls():
    """Verify zero broken/legacy fabricated .pl URLs remain in ROUTES_DATA."""
    banned_legacy_paths = [
        "diplomka.pl",
        "prihlasovani.pl",
        "poplatky.pl",
        "kontaktni_centrum.pl",
        "ubytovani.pl",
        "heslo.pl",
        "studijni_vysledky.pl",
        "hodnoceni.pl",
        "volby.pl",
        "dokumenty.pl",
        "/auth/lide/karty.pl",
    ]
    for route in insis_nav_db.ROUTES_DATA:
        task_id = route[0]
        url = route[6]
        assert url.startswith("https://insis.vse.cz/") or url == "https://iskam-web.vse.cz/"
        for banned in banned_legacy_paths:
            assert banned not in url, f"Legacy broken path {banned} found in {task_id}: {url}"


def test_search_insis_portlets_student_navigation_bar():
    """Verify the new Portlets in InSIS / Navigation bar for students route."""
    hits = insis_nav_db.search_routes("how to enable Navigation bar for students portlet in insis", limit=2)
    assert len(hits) > 0
    assert hits[0]["task_id"] == "TASK_INSIS_PORTLETS"
    assert "portlety.pl" in hits[0]["official_url"]
    assert "Navigation bar for students" in hits[0]["step_by_step_instructions"]
    assert "insis.vse.cz/quick" in hits[0]["common_pitfalls"]


def test_bot_clean_output_workflows_and_policy_routing(monkeypatch):
    """Verify clean answers (zero Route Stepper), Thesis Workflow, Visa & Accommodation, and Policy routing."""
    from bot import BuddyBot
    import insis_nav_db
    bot = BuddyBot()
    monkeypatch.setattr(bot.retriever, "embed_query", lambda q: None)

    # 1. Navigation search returns verified route without robotic stepper formatting
    routes = insis_nav_db.search_routes("How do I apply for the accommodation scholarship in InSIS?")
    assert len(routes) > 0
    assert routes[0]["official_url"] == "https://insis.vse.cz/auth/stipendia/?lang=en"

    # 2. Master's Thesis Workflow retrieval returns thesis documentation
    wf_chunks, wf_score, wf_mode = bot.retriever.retrieve(
        "Walk me through the complete Master's Thesis workflow at VŠE from topic approval to submission, defense, and errata."
    )
    assert wf_mode == "normal"
    assert any("48-final-thesis" in c.get("doc_id", "") for c in wf_chunks)

    # 3. Visa & Accommodation retrieval returns immigration / housing documentation
    va_chunks, va_score, va_mode = bot.retriever.retrieve(
        "What are the visa, dormitory accommodation, and 3-day Foreign Police registration rules for international students?"
    )
    assert va_mode == "normal"
    assert any("12-visa" in c.get("doc_id", "") or "45-foreign-police" in c.get("doc_id", "") for c in va_chunks)

    # 4. Policy consequence question matches the Three-Attempt Exam Rule in SQLite policies DB
    policies = insis_nav_db.search_policies("What happens if I fail an exam 3 times at VŠE?")
    assert len(policies) > 0
    assert "Three-Attempt Exam Rule" in policies[0]["title"]

    # 5. Dynamic context chunks do not leak into public/citations section
    dyn_chunks = [
        {
            "id": "live_page_master_thesis",
            "doc_id": "dynamic_context",
            "title": "Current Open InSIS Screen",
            "source_url": "https://insis.vse.cz/auth/student/zp.pl?lang=en",
            "text": "Insert additional information, Insert the thesis and the appendices, Thesis submission",
            "is_dynamic_context": True,
        }
    ]
    sources_str, _ = bot.format_sources_section("Step 1: Insert additional information [1]", dyn_chunks)
    assert "Current Open InSIS Screen" not in sources_str


