"""Safety module for VŠE Buddy Bot.

Runs deterministic checks BEFORE retrieval and LLM generation:
1. Crisis detection (no LLM, deterministic): checks for self-harm/suicide expressions.
   Returns an immediate supportive emergency message without invoking Gemini.
2. Sensitive topic detection: flags visa, immigration, legal, employment, insurance,
   payment, and academic disciplinary matters requiring official administrative referral.
"""

import re
from typing import Optional, Tuple

import config

# List of crisis keywords and phrases (English and Czech)
CRISIS_PATTERNS = [
    r"\bsuicide\b",
    r"\bkill(ing)? myself\b",
    r"\bkill me\b",
    r"\bdon'?t want to live\b",
    r"\bdo not want to live\b",
    r"\bend(ing)? my life\b",
    r"\bself[\s-]harm\b",
    r"\bhurt(ing)? myself\b",
    r"\bharm(ing)? myself\b",
    r"\bwant(ing)? to die\b",
    r"\bwish i were dead\b",
    r"\bsebevražda\b",
    r"\bsebevražd[yěeou]?\b",
    r"\bnechci žít\b",
    r"\b(?:se\s+)?zabít(?:\s+se)?\b",
    r"\b(?:si\s+)?ublížit(?:\s+si)?\b",
    r"\bchci umřít\b",
    r"\bchci zemřít\b",
]

# Sensitive topic dictionary with regex patterns and official topic labels
SENSITIVE_TOPICS = {
    "visa_residence": [
        r"\bvisa\b",
        r"\bvisas\b",
        r"\bresidence permit\b",
        r"\blong[\s-]stay\b",
        r"\bpermit extension\b",
        r"\bstay extension\b",
        r"\bimmigration\b",
        r"\boamp\b",
        r"\bmvcr\b",
        r"\bmzv\b",
        r"\bvize\b",
        r"\bpovolení k pobytu\b",
        r"\bembassy\b",
        r"\bconsulate\b",
    ],
    "foreign_police": [
        r"\bforeign police\b",
        r"\bcizineck[aá] policie\b",
        r"\bpolice registration\b",
        r"\bpolice paper\b",
        r"\bregister with.*police\b",
    ],
    "employment_work": [
        r"\bwork permit\b",
        r"\bworking hours\b",
        r"\bpart[\s-]time work\b",
        r"\bemployment contract\b",
        r"\bpracovní povolení\b",
        r"\bzaměstnání\b",
        r"\bcan i work\b",
    ],
    "health_insurance": [
        r"\bhealth insurance\b",
        r"\bmedical insurance\b",
        r"\bcommercial insurance\b",
        r"\bzdravotní pojištění\b",
        r"\bpvzp\b",
        r"\behic\b",
    ],
    "legal": [
        r"\blegal\b",
        r"\blawyer\b",
        r"\bcourt\b",
        r"\bpolice report\b",
        r"\bprávní\b",
        r"\badvokát\b",
    ],
    "tuition_payment": [
        r"\btuition fee\b",
        r"\btuition payment\b",
        r"\bfee payment\b",
        r"\bpay.*fees?\b",
        r"\b(?:tuition|study|application|semester|school)\s+fees?\b",
        r"\btuition\b",
        r"\bbank transfer\b",
        r"\bvariable symbol\b",
        r"\bpoplatek za studium\b",
        r"\bplatba školného\b",
    ],
    "academic_failure_expulsion": [
        r"\bfail(?:ed|ing)? an? exam\b",
        r"\bfail(?:ed|ing)? twice\b",
        r"\bflunk(?:ed)?\b",
        r"\bcant pass\b",
        r"\bcan't pass\b",
        r"\bexpulsion\b",
        r"\bexpelled\b",
        r"\bretake\b",
        r"\bre-sit\b",
        r"\bneúspěch u zkoušky\b",
        r"\bvyloučení ze studia\b",
        r"\bopravný termín\b",
        r"\bfail(?:ed|ing)?.*(?:defense|thesis)\b",
        r"\bneúspěch u obhajoby\b",
        r"\bterminat(?:ion|ed|ing)?.*stud(?:y|ies)\b",
        r"\bukončení studia\b",
        r"\binterrupt(?:ion|ing)?.*stud(?:y|ies)\b",
        r"\bpřerušení studia\b",
    ],
    "mental_wellbeing": [
        r"\bstressed\b",
        r"\bhomesick\b",
        r"\banxiety\b",
        r"\bdepressed\b",
        r"\bmental health\b",
        r"\bpsychological counselling\b",
    ],
}


REFERRAL_TARGETS = {
    "visa_residence": "the VŠE International Office and the Czech Ministry of the Interior (mvcr.cz)",
    "foreign_police": "the Czech Foreign Police and the VŠE International Office",
    "employment_work": "the Czech Ministry of the Interior (mvcr.cz) and the VŠE International Office",
    "health_insurance": "the official health insurance provider and the VŠE International Office",
    "legal": "the VŠE Legal Department or an authorized legal advisor",
    "tuition_payment": "your faculty Study Department or the VŠE Admission Office",
    "academic_failure_expulsion": "your faculty Study Department and official VŠE Study Regulations",
    "mental_wellbeing": "VŠE Academic Psychological Counselling (ac@vse.cz)",
}

REFERRAL_MARKERS = (
    "confirm with", "confirm this with", "verify with", "verify on",
    "check with", "consult ", "contact ", "reach out to",
    "ac@vse.cz", "ozs@vse.cz", "admissions@vse.cz", "fismasters@vse.cz",
    "ipc.gov.cz", "mvcr.cz", "refer to", "speak with",
)


def has_explicit_referral(text: str) -> bool:
    """Return True if text contains explicit verification or official office contact phrasing."""
    if not text:
        return False
    lowered = text.lower()
    return any(marker in lowered for marker in REFERRAL_MARKERS)


def get_crisis_response() -> str:
    """Return the fixed supportive crisis message.
    
    Contains emergency numbers and VŠE psychological counselling details.
    """
    return (
        f"You are not alone; please call {config.EMERGENCY_NUMBER} (emergency) right now if in danger.\n\n"
        f"• Czech crisis line: {config.CZECH_CRISIS_LINE} (free, 24/7).\n"
        f"• VŠE Academic Psychological Counselling: {config.VSE_COUNSELLING_EMAIL} (free, English)."
    )


def check_crisis(text: str) -> bool:
    """Deterministic crisis check.
    
    Returns True if any self-harm or suicide keyword/phrase is detected.
    Case-insensitive matching.
    """
    if not text:
        return False

    normalized_text = text.lower().strip()
    for pattern in CRISIS_PATTERNS:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            return True
    return False


def check_sensitive(text: str) -> Tuple[bool, Optional[str]]:
    """Deterministic check for sensitive administrative, legal, or policy topics.
    
    Returns (True, topic_key) if sensitive, else (False, None).
    """
    if not text:
        return False, None

    normalized_text = text.lower().strip()
    for topic, patterns in SENSITIVE_TOPICS.items():
        for pattern in patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                return True, topic

    return False, None
