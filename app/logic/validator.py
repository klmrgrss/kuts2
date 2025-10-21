# app/logic/validator.py
from pathlib import Path
from .models import (
    ApplicantData, Qualification, EligibilityPackage,
    ComplianceCheck, ComplianceDashboardState
)
from typing import List, Dict, Tuple

try:
    import tomllib
except ImportError:
    import tomli as tomllib

EDUCATION_HIERARCHY = {
    "any": 0, "keskharidus": 1, "ehitustehniline_keskeriharidus": 2,
    "mittevastav_kõrgharidus_180_eap": 3, "vastav_kõrgharidus_180_eap": 4,
    "mittevastav_kõrgharidus_240_eap": 5, "vastav_kõrgharidus_240_eap": 6,
    "tehniline_kõrgharidus_300_eap": 7, "mittevastav_kõrgharidus_300_eap": 8,
    "vastav_kõrgharidus_300_eap": 9,
}

class ValidationEngine:
    def __init__(self, rules_path: Path):
        self.qualifications = self._load_rules(rules_path)
        print(f"✅ Validation engine initialized with {len(self.qualifications)} qualifications.")

    def dict_to_state(self, state_dict: Dict) -> ComplianceDashboardState:
        """
        Recursively converts a dictionary back into a ComplianceDashboardState object.
        """
        # Create ComplianceCheck objects for all nested check dictionaries
        state_fields = ComplianceDashboardState.__dataclass_fields__.keys()
        checks = {}
        scalar_fields = {}

        for key, value in state_dict.items():
            if key not in state_fields:
                continue
            if isinstance(value, dict):
                checks[key] = ComplianceCheck(**value)
            else:
                scalar_fields[key] = value

        # Create the main state object, unpacking scalar values alongside
        # the reconstructed ComplianceCheck objects so comment fields and
        # evaluator toggles survive round-trips through JSON.
        return ComplianceDashboardState(
            **scalar_fields,
            **checks
        )


    def _load_rules(self, rules_path: Path) -> List[Qualification]:
        with open(rules_path, 'rb') as f:
            rules_data = tomllib.load(f)
        
        return [
            Qualification(
                id=q_data['id'], name=q_data['name'], level=q_data['level'],
                eligibility_packages=[
                    EligibilityPackage(**p) for p in q_data.get('eligibility_packages', [])
                ]
            ) for q_data in rules_data.get('qualifications', [])
        ]

    def _build_state_for_package(self, applicant: ApplicantData, package: EligibilityPackage) -> ComplianceDashboardState:
        """Builds the complete compliance state for a single package."""
        state = ComplianceDashboardState(package_id=package.id, overall_met=True)
        
        # Education
        if package.education_requirement:
            state.education.is_relevant = True
            state.education.required = package.education_requirement
            state.education.provided = applicant.education
            required_rank = EDUCATION_HIERARCHY.get(package.education_requirement, 0)
            provided_rank = EDUCATION_HIERARCHY.get(applicant.education, 0)
            state.education.is_met = provided_rank >= required_rank
            if not state.education.is_met: state.overall_met = False

        # Total Experience
        if package.total_experience_years is not None:
            state.total_experience.is_relevant = True
            state.total_experience.required = f"{package.total_experience_years}a"
            state.total_experience.provided = f"{applicant.work_experience_years}a"
            state.total_experience.is_met = applicant.work_experience_years >= package.total_experience_years
            if not state.total_experience.is_met: state.overall_met = False
            
        # Matching Experience
        if package.matching_experience_years is not None:
            state.matching_experience.is_relevant = True
            state.matching_experience.required = f"{package.matching_experience_years}a"
            state.matching_experience.provided = f"{applicant.matching_experience_years}a"
            state.matching_experience.is_met = applicant.matching_experience_years >= package.matching_experience_years
            if not state.matching_experience.is_met: state.overall_met = False

        # Base Training
        if package.base_training_hours > 0:
            state.base_training.is_relevant = True
            state.base_training.required = f"{package.base_training_hours}h"
            state.base_training.provided = f"{applicant.base_training_hours}h"
            state.base_training.is_met = applicant.base_training_hours >= package.base_training_hours
            if not state.base_training.is_met: state.overall_met = False

        # Conditional Training
        if package.conditional_training:
            trigger = package.conditional_training.get("trigger")
            if trigger == "haridus_vanem_kui_10a_või_välisriik" and applicant.is_education_old_or_foreign:
                state.conditional_training.is_relevant = True
                required_hours = package.conditional_training.get("base_training_hours", 0)
                state.conditional_training.required = f"{required_hours}h"
                state.conditional_training.provided = f"{applicant.base_training_hours}h"
                state.conditional_training.is_met = applicant.base_training_hours >= required_hours
                if not state.conditional_training.is_met: state.overall_met = False

        # Manager Training
        if package.manager_base_training_hours is not None and package.manager_base_training_hours > 0:
            state.manager_training.is_relevant = True
            state.manager_training.required = f"{package.manager_base_training_hours}h"
            state.manager_training.provided = f"{applicant.manager_training_hours}h"
            state.manager_training.is_met = applicant.manager_training_hours >= package.manager_base_training_hours
            if not state.manager_training.is_met: state.overall_met = False

        # ... other checks like CPD training can be added here ...

        state.education_old_or_foreign = applicant.is_education_old_or_foreign

        return state

    def validate(self, applicant: ApplicantData, qualification_id: str) -> List[ComplianceDashboardState]:
        """
        Validates an applicant against all packages and returns a list of state objects.
        """
        qualification = next((q for q in self.qualifications if q.id == qualification_id), None)
        if not qualification:
            raise ValueError(f"Qualification '{qualification_id}' not found in rules.")

        all_states = [self._build_state_for_package(applicant, pkg) for pkg in qualification.eligibility_packages]
        return all_states