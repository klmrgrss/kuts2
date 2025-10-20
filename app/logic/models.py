# app/logic/models.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ApplicantData:
    """Represents the processed data for a single applicant, including evaluator overrides."""
    education: str
    is_education_old_or_foreign: bool = False
    work_experience_years: float = 0.0
    matching_experience_years: float = 0.0
    has_prior_level_4: bool = False
    base_training_hours: int = 0
    manager_training_hours: int = 0
    cpd_training_hours: int = 0

@dataclass
class ComplianceCheck:
    """Represents the state of a single compliance requirement."""
    is_relevant: bool = False
    is_met: bool = False
    required: str = "N/A"
    provided: str = "N/A"
    evaluator_comment: Optional[str] = None

@dataclass
class ComplianceDashboardState:
    """Holds the complete state for the entire compliance dashboard for one package."""
    package_id: str
    overall_met: bool
    # Main compliance checks
    education: ComplianceCheck = field(default_factory=ComplianceCheck)
    total_experience: ComplianceCheck = field(default_factory=ComplianceCheck)
    matching_experience: ComplianceCheck = field(default_factory=ComplianceCheck)
    base_training: ComplianceCheck = field(default_factory=ComplianceCheck)
    manager_training: ComplianceCheck = field(default_factory=ComplianceCheck)
    conditional_training: ComplianceCheck = field(default_factory=ComplianceCheck)
    cpd_training: ComplianceCheck = field(default_factory=ComplianceCheck)
    prior_level_4: ComplianceCheck = field(default_factory=ComplianceCheck)
    
    # NEW: Top-level comment fields for each main section
    haridus_comment: Optional[str] = None
    tookogemus_comment: Optional[str] = None
    koolitus_comment: Optional[str] = None
    otsus_comment: Optional[str] = None


@dataclass
class EligibilityPackage:
    """
    Defines the requirements for a single eligibility path (e.g., Variant I).
    This model now includes all possible fields from the rules.toml to prevent initialization errors.
    """
    id: str
    description_et: Optional[str] = None
    citation: Optional[str] = None
    education_requirement: Optional[str] = None
    total_experience_years: Optional[int] = None
    matching_experience_years: Optional[int] = None
    
    requires_prior_level_4: Optional[str] = None
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