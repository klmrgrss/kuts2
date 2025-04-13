# models.py

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class User:
    email: str
    full_name: Optional[str] = None
    birthday: Optional[str] = None

@dataclass
class ApplicantProfile:
    user_email: str
    full_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

@dataclass
class ExistingQualification:
    user_email: str
    id: Optional[int] = None
    qualification_name: Optional[str] = None
    level: Optional[str] = None
    specialisation: Optional[str] = None
    activity: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    certificate_number: Optional[str] = None

@dataclass
class AppliedQualification:
    user_email: str
    id: Optional[int] = None
    qualification_name: Optional[str] = None
    level: Optional[str] = None
    specialisation: Optional[str] = None
    activity: Optional[str] = None
    is_renewal: int = 0
    application_date: Optional[str] = None

@dataclass
class WorkExperience:
    user_email: str
    id: Optional[int] = None
    application_id: Optional[str] = None
    competency: Optional[str] = None # NOTE: May become redundant or used differently now
    other_work: Optional[str] = None
    object_address: Optional[str] = None
    object_purpose: Optional[str] = None
    ehr_code: Optional[str] = None
    construction_activity: Optional[str] = None # NOTE: May become redundant or used differently now
    other_activity: Optional[str] = None
    permit_required: int = 0
    start_month: Optional[str] = None
    start_year: Optional[str] = None
    end_month: Optional[str] = None
    end_year: Optional[str] = None
    work_description: Optional[str] = None
    role: Optional[str] = None
    other_role: Optional[str] = None
    contract_type: Optional[str] = None
    company_name: Optional[str] = None
    company_code: Optional[str] = None
    company_contact: Optional[str] = None
    company_email: Optional[str] = None
    company_phone: Optional[str] = None
    client_name: Optional[str] = None
    client_code: Optional[str] = None
    client_contact: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    work_keywords: Optional[str] = None
    # --- NEW FIELD ADDED ---
    associated_activity: Optional[str] = None # Link to qualification activity name

@dataclass
class Education:
    user_email: str
    id: Optional[int] = None
    education_category: Optional[str] = None
    education_detail: Optional[str] = None
    institution: Optional[str] = None
    specialty: Optional[str] = None
    graduation_date: Optional[str] = None

@dataclass
class TrainingFile:
    user_email: str
    id: Optional[int] = None
    applied_qualification_id: Optional[int] = None
    file_description: Optional[str] = None
    original_filename: Optional[str] = None
    storage_identifier: Optional[str] = None
    upload_timestamp: Optional[str] = None

@dataclass
class EmploymentProof:
    user_email: str
    file_description: Optional[str] = None
    original_filename: Optional[str] = None
    storage_identifier: Optional[str] = None
    upload_timestamp: Optional[str] = None