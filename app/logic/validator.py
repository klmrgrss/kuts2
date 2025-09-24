# app/logic/validator.py
from pathlib import Path
from .models import ApplicantData, Qualification, EligibilityPackage
from typing import List, Dict, Tuple

# Use the standard library tomllib if available (Python 3.11+)
# Fall back to tomli for older Python versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib

class ValidationEngine:
    """
    Loads qualification rules from a TOML file and validates applicant data against them.
    """
    def __init__(self, rules_path: Path):
        self.qualifications = self._load_rules(rules_path)
        print(f"✅ Validation engine initialized with {len(self.qualifications)} qualifications.")

    def _load_rules(self, rules_path: Path) -> List[Qualification]:
        """Loads and parses the TOML rules file into Qualification objects."""
        with open(rules_path, 'rb') as f:
            rules_data = tomllib.load(f)
        
        loaded_quals = []
        for q_data in rules_data.get('qualifications', []):
            qual = Qualification(
                id=q_data['id'],
                name=q_data['name'],
                level=q_data['level'],
                eligibility_packages=[
                    EligibilityPackage(**p) for p in q_data.get('eligibility_packages', [])
                ]
            )
            loaded_quals.append(qual)
        return loaded_quals

    def _check_package(self, applicant: ApplicantData, package: EligibilityPackage) -> Tuple[bool, Dict]:
        """Checks if an applicant meets the requirements of a single eligibility package."""
        details = {}
        checks_passed = []

        # 1. Education Check
        edu_ok = applicant.education == package.education_requirement
        details["education"] = {"met": edu_ok, "required": package.education_requirement, "provided": applicant.education}
        checks_passed.append(edu_ok)

        # 2. Total Experience Check
        exp_ok = applicant.work_experience_years >= package.total_experience_years
        details["total_experience"] = {"met": exp_ok, "required": package.total_experience_years, "provided": applicant.work_experience_years}
        checks_passed.append(exp_ok)

        # 3. Matching Experience Check
        match_exp_ok = applicant.matching_experience_years >= package.matching_experience_years
        details["matching_experience"] = {"met": match_exp_ok, "required": package.matching_experience_years, "provided": applicant.matching_experience_years}
        checks_passed.append(match_exp_ok)
        
        # 4. Base Training Check
        training_ok = applicant.base_training_hours >= package.base_training_hours
        details["base_training"] = {"met": training_ok, "required": package.base_training_hours, "provided": applicant.base_training_hours}
        checks_passed.append(training_ok)

        # 5. Prior Level 4 Check (only if required by package)
        if package.requires_prior_level_4:
            prior_level_ok = applicant.has_prior_level_4
            details["prior_level_4"] = {"met": prior_level_ok, "required": True, "provided": applicant.has_prior_level_4}
            checks_passed.append(prior_level_ok)

        return all(checks_passed), details

    def validate(self, applicant: ApplicantData, qualification_id: str) -> Dict:
        """
        Validates an applicant against all possible eligibility packages for a given qualification.
        
        Returns a dictionary with the results of each package check.
        """
        qualification = next((q for q in self.qualifications if q.id == qualification_id), None)
        if not qualification:
            return {"error": f"Qualification with id '{qualification_id}' not found in rules."}

        results = []
        for package in qualification.eligibility_packages:
            is_met, details = self._check_package(applicant, package)
            results.append({"package_id": package.id, "is_met": is_met, "details": details})
        
        return {"qualification_id": qualification_id, "results": results}