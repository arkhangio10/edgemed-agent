SCHEMA_VERSION = "1.0.0"

REQUIRED_FIELDS = [
    "chief_complaint",
    "hpi",
    "assessment",
    "plan",
    "medications",
    "allergies",
]

CRITICAL_FIELDS = ["medications", "allergies", "assessment"]

ALL_FIELDS = REQUIRED_FIELDS + [
    "red_flags",
    "follow_up",
    "patient_summary_plain_language",
]

CONFIDENCE_LEVELS = ("low", "medium", "high")
CONFIDENCE_NUMERIC = {"low": 0.33, "medium": 0.66, "high": 1.0}

SUPPORTED_LOCALES = ("en", "es")

MAX_REPAIR_ATTEMPTS = 2
COMPLETENESS_THRESHOLD = 0.8
