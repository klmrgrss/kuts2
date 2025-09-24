# app/logic/models.py
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
    """Defines the requirements for a single eligibility path (e.g., Variant I)."""
    id: str
    education_requirement: str
    total_experience_years: int
    matching_experience_years: int
    requires_prior_level_4: bool = False
    base_training_hours: int = 0

@dataclass
class Qualification:
    """Represents a full qualification with its various eligibility packages."""
    id: str
    name: str
    level: int
    eligibility_packages: List[EligibilityPackage] = field(default_factory=list)