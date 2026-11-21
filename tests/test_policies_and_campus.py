"""Unit tests for Verified Core VŠE Policies (18) & Campus Service Locations (12)."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import insis_nav_db


def test_policies_database_count():
    """Verify that all 18 verified core VŠE policies are inserted and searchable."""
    insis_nav_db.init_database()
    conn = insis_nav_db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vse_policies;")
        count = cur.fetchone()[0]
        assert count == 18, f"Expected 18 verified core policies, got {count}"
    finally:
        conn.close()


def test_campus_locations_database_count():
    """Verify that all 12 verified campus service locations are inserted and searchable."""
    insis_nav_db.init_database()
    conn = insis_nav_db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM campus_locations;")
        count = cur.fetchone()[0]
        assert count == 12, f"Expected 12 verified campus locations, got {count}"
    finally:
        conn.close()


def test_search_study_coordinator_offices():
    """Verify searching for verified FIS study coordinator office (NB 403) returns official URL."""
    fis_hits = insis_nav_db.search_campus_locations("study coordinator fis ism", limit=1)
    assert len(fis_hits) == 1
    assert "NB 403" in fis_hits[0]["room_number"]
    assert "study_coordinator" in fis_hits[0]["facility_type"]
    assert fis_hits[0]["official_url"] == "https://fis.vse.cz/english/contacts/"


def test_search_library_and_canteen():
    """Verify verified SB Central Library and AV GASTRO Menza (zero dead skm.vse.cz links)."""
    lib_hits = insis_nav_db.search_campus_locations("central library knihovna zizkov", limit=1)
    assert len(lib_hits) == 1
    assert lib_hits[0]["building"] == "SB"
    assert "Mezzanine" in lib_hits[0]["floor"]
    assert lib_hits[0]["official_url"] == "https://library.vse.cz/"

    menza_hits = insis_nav_db.search_campus_locations("menza canteen av gastro", limit=1)
    assert len(menza_hits) == 1
    assert "AV GASTRO" in menza_hits[0]["name"]
    assert "skm.vse.cz" not in menza_hits[0]["directions_from_entrance"]


def test_search_core_academic_policies():
    """Verify searching for 9 ECTS floor, VŠE 4+ retake rule, and Česká spořitelna tuition account."""
    p_cred = insis_nav_db.search_policies("minimum credits first semester 9 ects", limit=1)
    assert len(p_cred) == 1
    assert p_cred[0]["rule_id"] == "POL_001"
    assert "9 ECTS" in p_cred[0]["title"]

    p_retake = insis_nav_db.search_policies("4+ grading scale exam retake", limit=1)
    assert len(p_retake) == 1
    assert p_retake[0]["rule_id"] == "POL_010"
    assert "4+" in p_retake[0]["title"]
    assert "one retake" in p_retake[0]["rule_text"].lower()

    p_tuition = insis_nav_db.search_policies("tuition bank account iban variable symbol", limit=1)
    assert len(p_tuition) == 1
    assert p_tuition[0]["rule_id"] == "POL_015"
    assert "CZ39 0800 0000 0000 2424 2442" in p_tuition[0]["rule_text"]


def test_all_policy_and_location_urls_are_live_verified():
    """Verify zero legacy 404 or dead skm.vse.cz URLs exist in vse_data_fixtures."""
    import vse_data_fixtures as f

    banned = [
        "skm.vse.cz",
        "university-rules-and-regulations",
        "campus-map-and-buildings",
        "suz.vse.cz/english",
        "admissions.vse.cz/tuition-fees",
        "admissions.vse.cz/foreign-education",
    ]
    for p in f.CORE_VSE_POLICIES:
        assert p["official_url"].startswith("https://")
        for b in banned:
            assert b not in p["official_url"], f"Dead URL {b} in {p['rule_id']}"
    for loc in f.CAMPUS_LOCATIONS:
        assert loc["official_url"].startswith("https://")
        for b in banned:
            assert b not in loc["official_url"], f"Dead URL {b} in {loc['location_id']}"


def test_format_policy_and_location_cards():
    """Verify markdown output formatting for policies and locations."""
    p = insis_nav_db.search_policies("minimum credits 9 ects", limit=1)[0]
    p_card = insis_nav_db.format_policy_card(p)
    assert "### 📜 VŠE Policy" in p_card
    assert "Official Ref:" in p_card

    loc = insis_nav_db.search_campus_locations("study coordinator fis", limit=1)[0]
    loc_card = insis_nav_db.format_location_card(loc)
    assert "### 📍 Campus Navigation:" in loc_card
    assert "Walking Directions from Main Entrance:" in loc_card
