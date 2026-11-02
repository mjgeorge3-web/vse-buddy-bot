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
    assert "/auth/student/diplomka.pl" in hits[0]["portal_path"]


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
    assert "prihlasovani.pl" in hits[0]["portal_path"]


def test_search_tuition_variable_symbol():
    """Verify that searching for tuition returns TASK_TUITION_PAYMENT."""
    hits = insis_nav_db.search_routes("how to pay tuition fees variable symbol", limit=1)
    assert len(hits) == 1
    assert hits[0]["task_id"] == "TASK_TUITION_PAYMENT"
    assert "poplatky.pl" in hits[0]["portal_path"]


def test_format_navigation_card():
    """Verify that format_navigation_card generates markdown with breadcrumbs and links."""
    route = insis_nav_db.get_route_by_task_id("TASK_THESIS_SUBMISSION")
    assert route is not None
    card_md = insis_nav_db.format_navigation_card(route)
    assert "🧭 InSIS Navigation:" in card_md
    assert "Breadcrumb Trail:" in card_md
    assert "Step-by-Step Instructions:" in card_md
    assert "http://localhost:8502/auth/student/diplomka.pl" in card_md
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

