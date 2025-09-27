# app/logic/models.py


# --- NOTE ON MODEL AND CONFIGURATION SYNC ---
# The dataclasses in this file, particularly EligibilityPackage, must be kept
# in sync with the keys defined in `app/config/rules.toml`.
#
# Previously, missing or unexpected keys in the TOML file would cause
# a `TypeError` when the ValidationEngine tried to initialize these dataclasses.
#
# The models have been updated to include all possible fields from the rules
# configuration, with optional fields defaulted to `None` or an appropriate
# empty value (e.g., False, 0, [], {}). This makes the data loading process
# more robust and prevents initialization errors if a rule package omits an
# optional key.
#
# If you add a new rule or key to `rules.toml`, remember to add a
# corresponding optional attribute here.
# --- END NOTE ---

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ApplicantData:
    """Represents the processed data for a single applicant."""
    education: str
    work_experience_years: float
    matching_experience_years: float
    has_prior_level_4: bool = False
    base_training_hours: int = 0

@dataclass
class EligibilityPackage:
    """
    Defines the requirements for a single eligibility path (e.g., Variant I).
    This model now includes all possible fields from the rules.toml to prevent initialization errors.
    """
    id: str
    education_requirement: Optional[str] = None
    total_experience_years: Optional[int] = None
    matching_experience_years: Optional[int] = None
    
    # --- All optional fields found in rules.toml ---
    requires_prior_level_4: Optional[str] = None # Can be a string like "temporary_cert_in_specialization"
    base_training_hours: int = 0
    total_experience_window_years: Optional[int] = None
    matching_experience_window_years: Optional[int] = None
    base_training_window_years: Optional[int] = None
    role_requirement: Optional[str] = None
    requires_prior_level_4_or_specialization_exam: bool = False
    requires_prior_ej6_within_years: Optional[int] = None
    cpd_training_hours: Optional[int] = None
    cpd_training_window_years: Optional[int] = None
    higher_ed_field: Optional[str] = None
    conditional_rules: list = field(default_factory=list)
    conditional_training: dict = field(default_factory=dict)
    route: Optional[str] = None
    requires_prior_same_level_within_years: Optional[int] = None
    recert_training: dict = field(default_factory=dict)
    requires_specialization_base_courses: bool = False
    specialization_exams_required: bool = False
    manager_base_training_hours: Optional[int] = None
    manager_base_training_window_years: Optional[int] = None


@dataclass
class Qualification:
    """Represents a full qualification with its various eligibility packages."""
    id: str
    name: str
    level: int
    eligibility_packages: List[EligibilityPackage] = field(default_factory=list)