"""Unit tests for safety module (crisis and sensitive topic detection)."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from safety import check_crisis, check_sensitive, get_crisis_response


class TestCrisisDetection:
    """Tests deterministic crisis detection."""

    @pytest.mark.parametrize(
        "query",
        [
            "I want to commit suicide",
            "I feel so hopeless, I want to kill myself",
            "I don't want to live anymore",
            "I do not want to live",
            "I am thinking to end my life",
            "Thoughts of self harm",
            "I want to hurt myself",
            "I want to die",
            "přemýšlím o sebevraždě",
            "už nechci žít",
            "chci se zabít",
            "chci umřít",
        ],
    )
    def test_crisis_positive(self, query):
        assert check_crisis(query) is True

    @pytest.mark.parametrize(
        "query",
        [
            "Where is the admission office?",
            "What is the emergency number in Czech Republic?",
            "How do I find a dorm at VŠE?",
            "Can I get a student discount on public transport?",
            "How do I kill a background task in python?",
        ],
    )
    def test_crisis_negative(self, query):
        assert check_crisis(query) is False

    def test_crisis_response_content(self):
        resp = get_crisis_response()
        assert "112" in resp
        assert "116 123" in resp
        assert "ac@vse.cz" in resp


class TestSensitiveTopicDetection:
    """Tests deterministic detection of sensitive topics."""

    @pytest.mark.parametrize(
        "query,expected_topic",
        [
            ("Do I need a visa to study at VŠE? I am from India.", "visa_residence"),
            ("Do I need a student visa to study at VŠE, and what are the requirements?", "visa_residence"),
            ("Where do I apply for my student visa?", "visa_residence"),
            ("As a non-EU student do I have to register with the Foreign Police?", "foreign_police"),
            ("Can I work part-time as a non-EU student?", "employment_work"),
            ("What health insurance do I need as an international student?", "health_insurance"),
            ("What happens if I fail an exam twice?", "academic_failure_expulsion"),
            ("How much is the tuition fee payment?", "tuition_payment"),
        ],
    )
    def test_sensitive_positive(self, query, expected_topic):
        is_sensitive, topic = check_sensitive(query)
        assert is_sensitive is True
        assert topic == expected_topic

    @pytest.mark.parametrize(
        "query",
        [
            "What Bachelor programmes does VŠE teach in English?",
            "How do I connect to Wi-Fi on campus?",
            "What are the opening hours of the library in Žižkov?",
            "Where can I eat cheaply near campus?",
            "Are there sports courses in English?",
        ],
    )
    def test_sensitive_negative(self, query):
        is_sensitive, topic = check_sensitive(query)
        assert is_sensitive is False
        assert topic is None
