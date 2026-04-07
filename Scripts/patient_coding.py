import json
import os
import re
from datetime import datetime

import requests

# Configuration
BEARER_TOKEN = "eyJraWQiOiJKeGNJaFF0K2pBZUlSZ2pZOHZ5ZXpHYzUyRzdySHNEQWxHdnVDTjBsOG5FPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3ZGJlbTgxMm5tdDgxaHRndHJuaDI1Y3QycSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiaWNsaW5pYy5wYXRpZW50XC9pbnN1cmFuY2UucmVhZCBpY2xpbmljLmVuY291bnRlclwvcmVhZCBpY2xpbmljLnBhdGllbnRcL21lZGljYWwtaGlzdG9yeS5yZWFkIGljbGluaWMuZW5jb3VudGVyXC93cml0ZSBpY2xpbmljLmxhYm9yYXRvcnlcL3JlYWQgaWNsaW5pYy5kb2N1bWVudFwvcmVhZCBpY2xpbmljLnByb3ZpZGVyXC9yZWFkIGljbGluaWMucGF0aWVudFwvZGVtb2dyYXBoaWMucmVhZCBpY2xpbmljLnNjaGVkdWxpbmdcL3dyaXRlIGljbGluaWMucGF0aWVudFwvZGVtb2dyYXBoaWMud3JpdGUgaWNsaW5pYy5zY2hlZHVsaW5nXC9yZWFkIGljbGluaWMuYmlsbGluZ1wvcmVhZCIsImF1dGhfdGltZSI6MTc3NTU2MzU0NSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfNTYzMTA3UmYzIiwiZXhwIjoxNzc1NTY3MTQ1LCJpYXQiOjE3NzU1NjM1NDUsInZlcnNpb24iOjIsImp0aSI6ImVhYmMyNDVhLTZmYzItNDRlYS04MzI0LTlmY2ExZTAyMTA0OCIsImNsaWVudF9pZCI6IjdkYmVtODEybm10ODFodGd0cm5oMjVjdDJxIn0.rjeIAEf352VpaJAkIs5bT7sPLDenIbwsXD-kZvMAx6v9iJ8RXiBqWGU1OqNXtLIrSVI7kTCMSOtAZxzjEu7N7lfImqxlcv-9VptJWNC3-7ZWQjVStTVjkLnYswDKoC5dmOWNG6aUNDw6pI9sMjeJ-LHVF8yEhlVd3cs5SCLyu_boehrDvWBg6eAiJCFrHAV1HA94uMe1Ysl6u_g5qAOurPJmPD2otXhqYL8o5vvbPGAgEzRkQS6qvZVdhxaKOutQV19iHa1yDET3sMF3RrvTcqiUgHcmAWQ9ymO2dfGKwTOzdxIhWpqUbL2EcI1Lfc55h2sihlwL6SRCTnhVA1CsPQ"  # Paste fresh token here
BASE_URL = "https://partner-api-dev.iclinichealth.dev"

# Mother inputs
CLINIC_ID = 1007
PATIENT_ID = 1002301179
DOS = "2025-10-09"  # Supports YYYY-MM-DD or MM/DD/YYYY

LAST_PREVENTIVE_CODES = {
    "99381", "99382", "99383", "99384", "99385", "99386", "99387",
    "99391", "99392", "99393", "99394", "99395", "99396", "99397",
    "G0438", "G0439",
}
PREVENTIVE_COUNSELLING_CODES = {"99401", "99402", "99403", "99404"}
SMOKING_COUNSELLING_CODES = {"99406", "99407"}
OBESITY_COUNSELLING_CODES = {"G0447"}
DEPRESSION_CODES = {"G0444"}
ALCOHOL_CODES = {"G0442"}
BP_CODES = {"3074F", "3075F", "3077F", "3078F", "3079F", "3080F"}
PREVENTIVE_RFV_KEYWORDS = (
    "annual physical",
    "annual wellness",
    "preventive",
    "physical exam",
    "physical",
)
LAB_BLOOD_KEYWORDS = (
    "cbc", "complete blood count", "cmp", "bmp", "metabolic panel", "comprehensive metabolic",
    "a1c", "hemoglobin", "glycohgb", "tsh", "thyroid", "t3", "t4", "lipid", "pt", "inr", "ptt",
    "prothrombin", "vitamin d", "vitamin b12", "folate", "iron", "ferritin", "tibc", "phosphorus", "uric acid",
    "hiv", "hepatitis", "hbsag", "hepatitis b surface antibody", "crp", "c-reactive", "sedimentation", "esr",
    "ana", "dsdna", "ccp", "hla-b27", "rheumatoid factor", "creatine kinase", "ck", "testosterone", "psa",
    "lead, blood", "abo", "abo group", "rh", "blood typing",
)
LAB_PYLORI_KEYWORDS = ("pylori", "h. pylori", "h pylori", "helicobacter pylori", "helicobacter")


def get_headers():
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }


def ensure_success(response, endpoint_name):
    if response.status_code == 401:
        raise RuntimeError(
            f"{endpoint_name} failed with 401 Unauthorized. "
            "Bearer token is invalid or expired."
        )
    if not response.ok:
        body = response.text.strip().replace("\n", " ")
        if len(body) > 300:
            body = body[:300] + "..."
        raise RuntimeError(f"{endpoint_name} failed ({response.status_code}): {body}")


def clean_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "none":
        return ""
    return text


def parse_date(value):
    if value is None:
        return None
    text = clean_text(value)
    if not text:
        return None

    if "T" in text:
        text = text.split("T", 1)[0]

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue
    return None


def format_mmddyyyy(value):
    dt = parse_date(value)
    if dt is None:
        return ""
    return dt.strftime("%m/%d/%Y")


def calc_age_on_dos(dob_value, dos_value):
    dob_dt = parse_date(dob_value)
    dos_dt = parse_date(dos_value)
    if dob_dt is None or dos_dt is None:
        return None

    age = dos_dt.year - dob_dt.year
    if (dos_dt.month, dos_dt.day) < (dob_dt.month, dob_dt.day):
        age -= 1
    return age


def map_gender(value):
    text = clean_text(value)
    if not text:
        return ""

    code = text.upper()
    if code == "M":
        return "Male"
    if code == "F":
        return "Female"
    if code in ("O", "OTHER"):
        return "Other"

    return text.title()


def to_float_or_none(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def to_int_or_none(value):
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def fetch_demographics(clinic_id, patient_id):
    url = f"{BASE_URL}/iclinic-patient/demographic/v1/clinics/{clinic_id}/patients/{patient_id}"
    response = requests.get(url, headers=get_headers())
    ensure_success(response, "Demographics API")
    return response.json()


def fetch_insurance(clinic_id, patient_id):
    url = f"{BASE_URL}/iclinic-patient/insurance/v1/clinics/{clinic_id}/patients/{patient_id}/insurance"
    response = requests.get(url, headers=get_headers())
    ensure_success(response, "Insurance API")
    return response.json()


def fetch_visits(clinic_id, patient_id):
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/patients/{patient_id}/visits"
    response = requests.get(url, headers=get_headers(), params={"offset": 0, "limit": 50})
    ensure_success(response, "List Visits API")
    return response.json()


def fetch_visit_detail(clinic_id, visit_id):
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}"
    response = requests.get(url, headers=get_headers())
    ensure_success(response, "Get Visit Detail API")
    return response.json()


def fetch_visit_screenings(clinic_id, visit_id):
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/screenings"
    response = requests.get(url, headers=get_headers())
    ensure_success(response, "List Visit Screenings API")
    return response.json()


def fetch_active_medications(clinic_id, patient_id):
    url = (
        f"{BASE_URL}/iclinic-patient/medical-history/v1/clinics/{clinic_id}"
        f"/patients/{patient_id}/medications"
    )
    response = requests.get(
        url,
        headers=get_headers(),
        params={"active_only": "true", "limit": 50, "offset": 0},
    )
    ensure_success(response, "Active Medications API")
    return response.json()


def fetch_historical_icds(clinic_id, patient_id):
    urls = [
        (
            f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
            f"/patients/{patient_id}/metadata/icd-history"
        ),
        (
            f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
            f"/patients/{patient_id}/icd-history"
        ),
    ]

    last_404 = None
    for url in urls:
        response = requests.get(
            url,
            headers=get_headers(),
            params={"system": "ICD10", "limit": 100, "offset": 0},
        )
        if response.status_code == 404:
            last_404 = url
            continue
        ensure_success(response, "Historical ICDs API")
        return response.json()

    print(
        "Warning: Historical ICDs endpoint returned 404 "
        f"(last tried: {last_404}). Continuing with empty ICD history."
    )
    return {"items": []}


def fetch_cpt_history(clinic_id, patient_id):
    urls = [
        (
            f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
            f"/patients/{patient_id}/metadata/cpt-history"
        ),
        (
            f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
            f"/patients/{patient_id}/cpt-history"
        ),
    ]

    # Try the exact form you've confirmed works first (limit only).
    for url in urls:
        response = requests.get(url, headers=get_headers(), params={"limit": 100})
        if response.status_code == 404:
            continue
        ensure_success(response, "CPT History API")
        payload = response.json()
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return {"items": [x for x in payload.get("items") if isinstance(x, dict)]}
        if isinstance(payload, list):
            return {"items": [x for x in payload if isinstance(x, dict)]}
        return {"items": []}

    # Fallback pagination attempt if route supports offset in your environment.
    for url in urls:
        limit = 100
        offset = 0
        all_items = []
        had_success = False

        while True:
            response = requests.get(
                url,
                headers=get_headers(),
                params={"limit": limit, "offset": offset},
            )
            if response.status_code == 404:
                break
            had_success = True
            ensure_success(response, "CPT History API")
            payload = response.json()

            if isinstance(payload, dict) and isinstance(payload.get("items"), list):
                items = [x for x in payload.get("items") if isinstance(x, dict)]
            elif isinstance(payload, list):
                items = [x for x in payload if isinstance(x, dict)]
            else:
                items = []

            if not items:
                break

            all_items.extend(items)
            if len(items) < limit:
                break

            offset += limit
            if offset > 5000:
                break

        if had_success:
            return {"items": all_items}

    raise RuntimeError(
        "CPT History API failed (404) on known routes. "
        "Please verify environment route for cpt-history."
    )


def fetch_claims_history(clinic_id, patient_id, service_date_to):
    url = f"{BASE_URL}/iclinic-billing/v1/clinics/{clinic_id}/patients/{patient_id}/claims"
    limit = 50
    offset = 0
    all_items = []

    while True:
        response = requests.get(
            url,
            headers=get_headers(),
            params={"service_date_to": service_date_to, "offset": offset, "limit": limit},
        )
        ensure_success(response, "Claims history API")
        payload = response.json()

        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            items = [x for x in payload.get("items") if isinstance(x, dict)]
        elif isinstance(payload, list):
            items = [x for x in payload if isinstance(x, dict)]
        else:
            items = []

        if not items:
            break

        all_items.extend(items)

        if len(items) < limit:
            break

        offset += limit
        if offset > 5000:
            break

    return {"items": all_items}


def extract_insurance_name(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        return ""

    items = [x for x in payload.get("items") if isinstance(x, dict)]
    if not items:
        return ""

    primary = next((x for x in items if clean_text(x.get("insu_order_label")).lower() == "primary"), None)
    item = primary or items[0]

    company = item.get("insurance_company") if isinstance(item.get("insurance_company"), dict) else {}
    insured = item.get("insured") if isinstance(item.get("insured"), dict) else {}

    company_name = clean_text(company.get("insu_com_name"))
    relationship = clean_text(insured.get("relationship_label"))
    if not relationship:
        rel_code = clean_text(insured.get("relationship")).upper()
        relationship = "Self" if rel_code == "P" else ""

    if company_name and relationship:
        return f"{company_name} ({relationship})"
    return company_name


def get_dos_matched_visit(visits_payload, dos):
    if isinstance(visits_payload, dict) and isinstance(visits_payload.get("items"), list):
        visits = [x for x in visits_payload.get("items") if isinstance(x, dict)]
    elif isinstance(visits_payload, list):
        visits = [x for x in visits_payload if isinstance(x, dict)]
    else:
        visits = []

    target_dos = parse_date(dos)
    if target_dos is None:
        return None

    for visit in visits:
        visit_date = parse_date(visit.get("visit_date") or visit.get("visit_datetime"))
        if visit_date and visit_date == target_dos:
            return visit
    return None


def extract_header_vitals(visit_detail, dos):
    vitals = visit_detail.get("vitals") if isinstance(visit_detail, dict) else {}
    if not isinstance(vitals, dict):
        vitals = {}

    return {
        "currentbmi": to_float_or_none(vitals.get("bmi")),
        "percentile": vitals.get("bmi_percentile"),
        "systbp": to_int_or_none(vitals.get("bp_systolic")),
        "diastbp": to_int_or_none(vitals.get("bp_diastolic")),
    }


def extract_is_old_patient(visit_detail):
    if not isinstance(visit_detail, dict):
        return False

    complaint = visit_detail.get("complaint")
    if not isinstance(complaint, dict):
        return False

    is_new_patient = complaint.get("is_new_patient")
    if isinstance(is_new_patient, bool):
        return not is_new_patient

    text = clean_text(is_new_patient).lower()
    if text in {"true", "1", "yes", "y"}:
        return False
    if text in {"false", "0", "no", "n"}:
        return True
    return False


def extract_has_prescription_medicine(medications_payload):
    if isinstance(medications_payload, dict):
        if isinstance(medications_payload.get("items"), list):
            return len(medications_payload.get("items")) > 0
        if isinstance(medications_payload.get("medications"), list):
            return len(medications_payload.get("medications")) > 0
        if isinstance(medications_payload.get("data"), list):
            return len(medications_payload.get("data")) > 0
    if isinstance(medications_payload, list):
        return len(medications_payload) > 0
    return False


def extract_calendar_year_icd_cpt_codes(icd_payload, cpt_payload, dos):
    dos_dt = parse_date(dos)
    if dos_dt is None:
        return {}
    target_year = dos_dt.year

    bucket = {}

    if isinstance(icd_payload, dict) and isinstance(icd_payload.get("items"), list):
        icd_items = [x for x in icd_payload.get("items") if isinstance(x, dict)]
    elif isinstance(icd_payload, list):
        icd_items = [x for x in icd_payload if isinstance(x, dict)]
    else:
        icd_items = []

    for item in icd_items:
        used_dt = parse_date(item.get("last_used_date"))
        if used_dt is None or used_dt.year != target_year:
            continue

        date_key = used_dt.strftime("%m/%d/%Y")
        code = clean_text(item.get("icd_code") or item.get("code"))
        if date_key not in bucket:
            bucket[date_key] = {"icd_code_list": [], "cpt_code_list": []}
        if code and code not in bucket[date_key]["icd_code_list"]:
            bucket[date_key]["icd_code_list"].append(code)

    if isinstance(cpt_payload, dict) and isinstance(cpt_payload.get("items"), list):
        cpt_items = [x for x in cpt_payload.get("items") if isinstance(x, dict)]
    elif isinstance(cpt_payload, list):
        cpt_items = [x for x in cpt_payload if isinstance(x, dict)]
    else:
        cpt_items = []

    for item in cpt_items:
        used_dt = parse_date(item.get("last_used_date"))
        if used_dt is None or used_dt.year != target_year:
            continue

        date_key = used_dt.strftime("%m/%d/%Y")
        code = clean_text(item.get("cpt_code") or item.get("code"))
        if date_key not in bucket:
            bucket[date_key] = {"icd_code_list": [], "cpt_code_list": []}
        if code and code not in bucket[date_key]["cpt_code_list"]:
            bucket[date_key]["cpt_code_list"].append(code)

    sorted_keys = sorted(bucket.keys(), key=lambda x: datetime.strptime(x, "%m/%d/%Y").date())
    return {k: bucket[k] for k in sorted_keys}


def extract_smoking_history(icd_payload, dos):
    dos_dt = parse_date(dos)

    if isinstance(icd_payload, dict) and isinstance(icd_payload.get("items"), list):
        items = [x for x in icd_payload.get("items") if isinstance(x, dict)]
    elif isinstance(icd_payload, list):
        items = [x for x in icd_payload if isinstance(x, dict)]
    else:
        items = []

    latest_code = ""
    latest_date = None

    for item in items:
        icd_code = clean_text(item.get("icd_code") or item.get("code")).upper()
        if not icd_code.startswith("F17"):
            continue

        used_dt = (
            parse_date(item.get("last_used_date"))
            or parse_date(item.get("used_date"))
            or parse_date(item.get("visit_date"))
            or parse_date(item.get("dos"))
            or parse_date(item.get("date_of_service"))
            or parse_date(item.get("service_date"))
            or parse_date(item.get("created_date"))
            or parse_date(item.get("create_date"))
            or parse_date(item.get("modified_date"))
            or parse_date(item.get("modify_date"))
        )
        if used_dt is None:
            continue
        if dos_dt is not None and used_dt > dos_dt:
            continue

        if latest_date is None or used_dt > latest_date:
            latest_date = used_dt
            latest_code = icd_code

    if latest_date is None:
        return {"icd": "", "dos": "", "days_ago": None}

    days_ago = (dos_dt - latest_date).days if dos_dt is not None else None
    return {
        "icd": latest_code,
        "dos": latest_date.strftime("%m/%d/%Y"),
        "days_ago": days_ago,
    }


def extract_cpt_candidates(raw_code):
    text = clean_text(raw_code).upper()
    if not text:
        return []

    candidates = []

    direct = re.findall(r"[A-Z]\d{4}|\d{5}", text)
    for code in direct:
        if code not in candidates:
            candidates.append(code)

    parts = re.split(r"[,\s;/|]+", text)
    for part in parts:
        token = part.strip()
        if not token:
            continue
        base = token.split("-", 1)[0].split(".", 1)[0]
        if re.fullmatch(r"[A-Z]\d{4}|\d{5}", base) and base not in candidates:
            candidates.append(base)

    return candidates


def extract_service_date(item):
    return (
        parse_date(item.get("last_used_date"))
        or parse_date(item.get("used_date"))
        or parse_date(item.get("visit_date"))
        or parse_date(item.get("dos"))
        or parse_date(item.get("date_of_service"))
        or parse_date(item.get("service_date"))
        or parse_date(item.get("created_date"))
        or parse_date(item.get("create_date"))
        or parse_date(item.get("modified_date"))
        or parse_date(item.get("modify_date"))
    )


def get_cpt_items(cpt_payload):
    if isinstance(cpt_payload, dict) and isinstance(cpt_payload.get("items"), list):
        return [x for x in cpt_payload.get("items") if isinstance(x, dict)]
    if isinstance(cpt_payload, list):
        return [x for x in cpt_payload if isinstance(x, dict)]
    return []


def get_claim_items(claims_payload):
    if isinstance(claims_payload, dict) and isinstance(claims_payload.get("items"), list):
        return [x for x in claims_payload.get("items") if isinstance(x, dict)]
    if isinstance(claims_payload, list):
        return [x for x in claims_payload if isinstance(x, dict)]
    return []


def find_latest_claim_code_date_and_payer(claims_payload, target_codes, dos_dt):
    claims = get_claim_items(claims_payload)
    latest_date = None
    latest_payer = ""
    latest_approved = False

    for claim in claims:
        service_dt = parse_date(claim.get("service_date"))
        if service_dt is None:
            continue
        if dos_dt is not None and service_dt > dos_dt:
            continue

        line_items = claim.get("line_items")
        if not isinstance(line_items, list):
            continue

        matched = False
        for line in line_items:
            if not isinstance(line, dict):
                continue
            candidates = extract_cpt_candidates(line.get("cpt_code") or line.get("code"))
            if any(code in target_codes for code in candidates):
                matched = True
                break
        if not matched:
            continue

        payer_name = clean_text(claim.get("payer_name"))
        status_display = clean_text(claim.get("status_display")).lower()
        is_approved = "approved" in status_display

        if latest_date is None or service_dt > latest_date:
            latest_date = service_dt
            latest_payer = payer_name
            latest_approved = is_approved
        elif service_dt == latest_date and is_approved and not latest_approved:
            latest_payer = payer_name
            latest_approved = True

    return latest_date, latest_payer


def find_latest_cpt_code_and_date(cpt_items, target_codes, dos_dt):
    latest_code = ""
    latest_date = None
    for item in cpt_items:
        candidates = extract_cpt_candidates(item.get("cpt_code") or item.get("code"))
        matched_code = next((c for c in candidates if c in target_codes), "")
        if not matched_code:
            continue
        used_dt = extract_service_date(item)
        if used_dt is None:
            continue
        if dos_dt is not None and used_dt > dos_dt:
            continue
        if latest_date is None or used_dt > latest_date:
            latest_date = used_dt
            latest_code = matched_code
    return latest_code, latest_date


def extract_company_insurance_name(display_insurance):
    text = clean_text(display_insurance)
    if not text:
        return ""
    if " (" in text:
        return text.split(" (", 1)[0].strip()
    return text


def build_cptdates(cpt_payload, claims_payload, dos, insurance_name):
    dos_dt = parse_date(dos)
    items = get_cpt_items(cpt_payload)
    insurance_company = extract_company_insurance_name(insurance_name)

    _, last99401_date = find_latest_cpt_code_and_date(items, {"99401"}, dos_dt)
    _, lastpreventive_date = find_latest_cpt_code_and_date(items, LAST_PREVENTIVE_CODES, dos_dt)
    _, lastsmoking_date = find_latest_cpt_code_and_date(items, SMOKING_COUNSELLING_CODES, dos_dt)
    _, lastdepression_date = find_latest_cpt_code_and_date(items, DEPRESSION_CODES, dos_dt)
    _, lastalcohol_date = find_latest_cpt_code_and_date(items, ALCOHOL_CODES, dos_dt)
    _, lastobesity_date = find_latest_cpt_code_and_date(items, OBESITY_COUNSELLING_CODES, dos_dt)
    _, last99214_date = find_latest_cpt_code_and_date(items, {"99214"}, dos_dt)
    _, last36415_date = find_latest_cpt_code_and_date(items, {"36415"}, dos_dt)

    bpcount = 0
    visit_dates = set()
    for item in items:
        used_dt = extract_service_date(item)
        if used_dt is None:
            continue
        if dos_dt is not None and used_dt > dos_dt:
            continue
        visit_dates.add(used_dt.isoformat())

        candidates = extract_cpt_candidates(item.get("cpt_code") or item.get("code"))
        if any(code in BP_CODES for code in candidates):
            bpcount += 1

    # Per requirement: mark Yes if related CPT code exists in history up to DOS.
    annualdepression = "Yes" if lastdepression_date else "No"
    annualalchohol = "Yes" if lastalcohol_date else "No"

    # From claims API (service_date + line_items CPT), per requirement.
    claim_lastpreventive_date, claim_lastpreventive_payer = find_latest_claim_code_date_and_payer(
        claims_payload,
        LAST_PREVENTIVE_CODES,
        dos_dt,
    )
    claim_lastg0442_date, claim_lastg0442_payer = find_latest_claim_code_date_and_payer(
        claims_payload,
        {"G0442"},
        dos_dt,
    )

    return {
        "last99401": last99401_date.strftime("%m/%d/%Y") if last99401_date else "",
        "lastpreventive": lastpreventive_date.strftime("%m/%d/%Y") if lastpreventive_date else "",
        "lastsmoking": lastsmoking_date.strftime("%m/%d/%Y") if lastsmoking_date else "",
        "lastdepression": lastdepression_date.strftime("%m/%d/%Y") if lastdepression_date else "",
        "lastalcohol": lastalcohol_date.strftime("%m/%d/%Y") if lastalcohol_date else "",
        "lastobesity": lastobesity_date.strftime("%m/%d/%Y") if lastobesity_date else "",
        "last99214": last99214_date.strftime("%m/%d/%Y") if last99214_date else "",
        "last36415": last36415_date.strftime("%m/%d/%Y") if last36415_date else "",
        "bpcount": bpcount,
        "visitcount": len(visit_dates),
        "lastpreventiveinsurance": claim_lastpreventive_payer if claim_lastpreventive_date else "",
        "annualdepression": annualdepression,
        "annualalchohol": annualalchohol,
        "lastG0444insurance": insurance_company if lastdepression_date else "",
        "lastG0444": lastdepression_date.strftime("%m/%d/%Y") if lastdepression_date else "",
        "lastG0442insurance": claim_lastg0442_payer if claim_lastg0442_date else "",
        "lastG0442": claim_lastg0442_date.strftime("%m/%d/%Y") if claim_lastg0442_date else "",
    }


def build_payment_history_from_claims(claims_payload, dos):
    dos_dt = parse_date(dos)
    if isinstance(claims_payload, dict) and isinstance(claims_payload.get("items"), list):
        items = [x for x in claims_payload.get("items") if isinstance(x, dict)]
    elif isinstance(claims_payload, list):
        items = [x for x in claims_payload if isinstance(x, dict)]
    else:
        items = []

    per_date = {}

    for item in items:
        service_dt = parse_date(item.get("service_date"))
        if service_dt is None:
            continue
        if dos_dt is not None and service_dt > dos_dt:
            continue

        date_key = service_dt.strftime("%m/%d/%Y")
        status_display = clean_text(item.get("status_display")).lower()
        payer_name = clean_text(item.get("payer_name"))
        if not payer_name:
            continue

        is_approved = "approved" in status_display
        current = per_date.get(date_key)
        if current is None:
            per_date[date_key] = {"payer_name": payer_name, "is_approved": is_approved}
        elif is_approved and not current.get("is_approved", False):
            per_date[date_key] = {"payer_name": payer_name, "is_approved": True}

    sorted_keys = sorted(per_date.keys(), key=lambda x: datetime.strptime(x, "%m/%d/%Y").date(), reverse=True)
    return {k: per_date[k]["payer_name"] for k in sorted_keys}


def build_laborders(cpt_payload, dos):
    dos_dt = parse_date(dos)
    items = get_cpt_items(cpt_payload)

    has_blood = False
    has_pylori = False

    for item in items:
        used_dt = extract_service_date(item)
        if used_dt is None:
            continue
        if dos_dt is not None and used_dt > dos_dt:
            continue

        cpt_code = clean_text(item.get("cpt_code") or item.get("code")).lower()
        cpt_name = clean_text(item.get("cpt_name") or item.get("description")).lower()
        text = f"{cpt_code} {cpt_name}".strip()

        if not has_blood and any(keyword in text for keyword in LAB_BLOOD_KEYWORDS):
            has_blood = True
        if not has_pylori and any(keyword in text for keyword in LAB_PYLORI_KEYWORDS):
            has_pylori = True

        if has_blood and has_pylori:
            break

    return {
        # Per requirement: these two move opposite each other by has_blood.
        "cpt36415": "Yes" if has_blood else "No",
        "cpt99000": "No" if has_blood else "Yes",
        "pylori": "Yes" if has_pylori else "No",
    }


def _to_number_or_none(value):
    if value in (None, ""):
        return None
    try:
        n = float(value)
        return int(n) if n.is_integer() else n
    except Exception:
        return None


def build_screening(screenings_payload):
    if isinstance(screenings_payload, dict) and isinstance(screenings_payload.get("items"), list):
        items = [x for x in screenings_payload.get("items") if isinstance(x, dict)]
    elif isinstance(screenings_payload, list):
        items = [x for x in screenings_payload if isinstance(x, dict)]
    else:
        items = []

    screening = {
        "depression": "No",
        "gad7": "No",
        "coa": "No",
        "fallrisk": "No",
        "tobacco": "No",
        "socialneeds": "No",
        "alcohol": "No",
        "depressionscore": None,
        "tobaccoscore": None,
        "alcoholscore": None,
        "fallriskscore": None,
    }

    for item in items:
        form_name = clean_text(item.get("form_name")).lower()
        category = clean_text(item.get("category")).lower()
        text = f"{form_name} {category}".strip()
        score = _to_number_or_none(item.get("total_score"))

        if ("depression" in text) or ("phq" in text):
            screening["depression"] = "Yes"
            if score is not None:
                screening["depressionscore"] = score

        if ("gad7" in text) or ("gad-7" in text) or ("anxiety" in text):
            screening["gad7"] = "Yes"

        if ("coa" in text) or ("cognitive" in text):
            screening["coa"] = "Yes"

        if ("fall" in text and "risk" in text) or ("fallrisk" in text):
            screening["fallrisk"] = "Yes"
            if score is not None:
                screening["fallriskscore"] = score

        if ("tobacco" in text) or ("smoking" in text):
            screening["tobacco"] = "Yes"
            if score is not None:
                screening["tobaccoscore"] = score

        if ("social" in text) or ("sdoh" in text) or ("prapare" in text):
            screening["socialneeds"] = "Yes"

        if ("alcohol" in text) or ("audit" in text):
            screening["alcohol"] = "Yes"
            if score is not None:
                screening["alcoholscore"] = score

    return screening


def extract_last_preventive(cpt_payload, dos):
    dos_dt = parse_date(dos)

    if isinstance(cpt_payload, dict) and isinstance(cpt_payload.get("items"), list):
        items = [x for x in cpt_payload.get("items") if isinstance(x, dict)]
    elif isinstance(cpt_payload, list):
        items = [x for x in cpt_payload if isinstance(x, dict)]
    else:
        items = []

    latest_code = ""
    latest_date = None

    for item in items:
        raw_code = item.get("cpt_code") or item.get("code")
        candidates = extract_cpt_candidates(raw_code)
        matched_code = next((c for c in candidates if c in LAST_PREVENTIVE_CODES), "")
        if not matched_code:
            continue

        used_dt = (
            parse_date(item.get("last_used_date"))
            or parse_date(item.get("used_date"))
            or parse_date(item.get("visit_date"))
            or parse_date(item.get("dos"))
            or parse_date(item.get("date_of_service"))
            or parse_date(item.get("service_date"))
            or parse_date(item.get("created_date"))
            or parse_date(item.get("create_date"))
            or parse_date(item.get("modified_date"))
            or parse_date(item.get("modify_date"))
        )
        if used_dt is None:
            continue

        if dos_dt is not None and used_dt > dos_dt:
            continue

        if latest_date is None or used_dt > latest_date:
            latest_date = used_dt
            latest_code = matched_code

    if latest_date is None:
        return {
            "cpt": "",
            "dos": "",
            "need_preventive": False,
            "is_year_change": False,
            "days_ago": None,
        }

    days_ago = None
    if dos_dt is not None:
        days_ago = (dos_dt - latest_date).days

    is_year_change = bool(dos_dt and latest_date and dos_dt.year != latest_date.year)
    need_preventive = is_year_change
    if days_ago is not None and days_ago >= 365:
        need_preventive = True

    return {
        "cpt": latest_code,
        "dos": latest_date.strftime("%m/%d/%Y"),
        "need_preventive": need_preventive,
        "is_year_change": is_year_change,
        "days_ago": days_ago,
    }


def extract_last_30days_cpt_event(cpt_payload, dos, target_codes):
    dos_dt = parse_date(dos)
    if dos_dt is None:
        return {"cpt": "", "dos": "", "days_ago": None}

    if isinstance(cpt_payload, dict) and isinstance(cpt_payload.get("items"), list):
        items = [x for x in cpt_payload.get("items") if isinstance(x, dict)]
    elif isinstance(cpt_payload, list):
        items = [x for x in cpt_payload if isinstance(x, dict)]
    else:
        items = []

    latest_code = ""
    latest_date = None
    latest_days_ago = None

    for item in items:
        raw_code = item.get("cpt_code") or item.get("code")
        candidates = extract_cpt_candidates(raw_code)
        matched_code = next((c for c in candidates if c in target_codes), "")
        if not matched_code:
            continue

        used_dt = (
            parse_date(item.get("last_used_date"))
            or parse_date(item.get("used_date"))
            or parse_date(item.get("visit_date"))
            or parse_date(item.get("dos"))
            or parse_date(item.get("date_of_service"))
            or parse_date(item.get("service_date"))
            or parse_date(item.get("created_date"))
            or parse_date(item.get("create_date"))
            or parse_date(item.get("modified_date"))
            or parse_date(item.get("modify_date"))
        )
        if used_dt is None or used_dt > dos_dt:
            continue

        days_ago = (dos_dt - used_dt).days
        if days_ago < 0 or days_ago > 30:
            continue

        if latest_date is None or used_dt > latest_date:
            latest_date = used_dt
            latest_code = matched_code
            latest_days_ago = days_ago

    if latest_date is None:
        return {"cpt": "", "dos": "", "days_ago": None}

    return {
        "cpt": latest_code,
        "dos": latest_date.strftime("%m/%d/%Y"),
        "days_ago": latest_days_ago,
    }


def extract_icd_cpt_code_with_modifiers(visit_detail):
    out = {"icd_codes": [], "cpt_codes": []}
    if not isinstance(visit_detail, dict):
        return out

    diagnoses = visit_detail.get("diagnoses")
    if isinstance(diagnoses, list):
        seen_icd = set()
        for item in diagnoses:
            if not isinstance(item, dict):
                continue
            code = clean_text(item.get("icd_code") or item.get("code"))
            description = clean_text(item.get("icd_name") or item.get("description"))
            if not code and not description:
                continue
            key = (code, description)
            if key in seen_icd:
                continue
            seen_icd.add(key)
            out["icd_codes"].append({"code": code, "description": description})

    procedures = visit_detail.get("procedures")
    if isinstance(procedures, list):
        seen_cpt = set()
        for item in procedures:
            if not isinstance(item, dict):
                continue

            raw_code = clean_text(item.get("cpt_code") or item.get("code")).upper()
            description = clean_text(item.get("cpt_name") or item.get("description"))
            if not raw_code and not description:
                continue

            candidates = extract_cpt_candidates(raw_code)
            code = candidates[0] if candidates else raw_code

            raw_modifiers = item.get("modifiers")
            if isinstance(raw_modifiers, list):
                modifier_parts = [clean_text(x).upper() for x in raw_modifiers if clean_text(x)]
                modifiers = ",".join(modifier_parts)
            elif raw_modifiers is None:
                modifiers = ""
            else:
                modifiers = clean_text(raw_modifiers).upper()

            key = (code, description, modifiers)
            if key in seen_cpt:
                continue
            seen_cpt.add(key)
            out["cpt_codes"].append(
                {
                    "code": code,
                    "description": description,
                    "modifiers": modifiers,
                }
            )

    return out


def extract_has_preventive_rfv_from_visit_type(visit_type):
    text = clean_text(visit_type).lower()
    if not text:
        return False
    return any(keyword in text for keyword in PREVENTIVE_RFV_KEYWORDS)


def build_output_json(
    demo,
    insurance_name,
    dos,
    visit,
    visit_detail,
    last_preventive,
    last_30days_preventive_counselling,
    last_30days_smoking_counselling,
    last_30days_obesity_counselling,
    smoking_history,
    payment_history,
    laborders,
    has_prescription_medicine,
    screening,
    cptdates,
    icd_cpt_code_with_modifiers,
    calendar_year_icd_cpt_codes,
):
    visit_type = ""
    if isinstance(visit_detail, dict):
        visit_type = clean_text(
            visit_detail.get("visit_type_name")
            or visit_detail.get("visit_type")
            or visit_detail.get("visit_type_label")
        )
    if not visit_type and isinstance(visit, dict):
        visit_type = clean_text(
            visit.get("visit_type_name")
            or visit.get("visit_type")
            or visit.get("visit_type_label")
        )

    return {
        "headerdob": format_mmddyyyy(demo.get("dob", "")),
        "headergender": map_gender(demo.get("gender", "")),
        "headerinsurance": insurance_name,
        "headerdos": format_mmddyyyy(dos),
        "headerage": calc_age_on_dos(demo.get("dob", ""), dos),
        "headervisittype": visit_type,
        "annul_mentioned": ("annual" in visit_type.lower()) or ("annul" in visit_type.lower()),
        "vitals": extract_header_vitals(visit_detail, dos),
        "calendar_year_icd_cpt_codes": calendar_year_icd_cpt_codes,
        "is_old_patient": extract_is_old_patient(visit_detail),
        "last_preventive": last_preventive,
        "last_30days_preventive_counselling": last_30days_preventive_counselling,
        "last_30days_smoking_counselling": last_30days_smoking_counselling,
        "last_30days_obesity_counselling": last_30days_obesity_counselling,
        "smoking_history": smoking_history,
        "payment_history": payment_history,
        "laborders": laborders,
        "has_preventive_rfv": extract_has_preventive_rfv_from_visit_type(visit_type),
        "has_prescription_medicine": has_prescription_medicine,
        "screening": screening,
        "cptdates": cptdates,
        "icd_cpt_code_with_modifiers": icd_cpt_code_with_modifiers,
    }


def main():
    try:
        print(f"Fetching demographic for patient={PATIENT_ID}, clinic={CLINIC_ID}...")
        demo = fetch_demographics(CLINIC_ID, PATIENT_ID)

        print("Fetching insurance...")
        insurance_payload = fetch_insurance(CLINIC_ID, PATIENT_ID)
        insurance_name = extract_insurance_name(insurance_payload)

        print("Fetching visits and matching DOS...")
        visits_payload = fetch_visits(CLINIC_ID, PATIENT_ID)
        matched_visit = get_dos_matched_visit(visits_payload, DOS)
        if not matched_visit:
            raise RuntimeError(f"No visit found for DOS={DOS}")

        visit_id = matched_visit.get("visit_id")
        if visit_id in (None, ""):
            raise RuntimeError("DOS-matched visit has no visit_id")

        print(f"Fetching visit detail for visit_id={visit_id}...")
        visit_detail = fetch_visit_detail(CLINIC_ID, visit_id)
        print("Fetching visit screenings...")
        screenings_payload = fetch_visit_screenings(CLINIC_ID, visit_id)
        print("Fetching active medications...")
        medications_payload = fetch_active_medications(CLINIC_ID, PATIENT_ID)
        has_prescription_medicine = extract_has_prescription_medicine(medications_payload)

        print("Fetching ICD/CPT history for DOS-year aggregation...")
        historical_icd_payload = fetch_historical_icds(CLINIC_ID, PATIENT_ID)
        cpt_history_payload = fetch_cpt_history(CLINIC_ID, PATIENT_ID)
        service_date_to = parse_date(DOS).strftime("%Y-%m-%d") if parse_date(DOS) else DOS
        print("Fetching claims payment history...")
        claims_payload = fetch_claims_history(CLINIC_ID, PATIENT_ID, service_date_to)
        calendar_year_icd_cpt_codes = extract_calendar_year_icd_cpt_codes(
            historical_icd_payload,
            cpt_history_payload,
            DOS,
        )
        smoking_history = extract_smoking_history(historical_icd_payload, DOS)
        payment_history = build_payment_history_from_claims(claims_payload, DOS)
        laborders = build_laborders(cpt_history_payload, DOS)
        icd_cpt_code_with_modifiers = extract_icd_cpt_code_with_modifiers(visit_detail)
        cptdates = build_cptdates(cpt_history_payload, claims_payload, DOS, insurance_name)
        screening = build_screening(screenings_payload)
        last_preventive = extract_last_preventive(cpt_history_payload, DOS)
        last_30days_preventive_counselling = extract_last_30days_cpt_event(
            cpt_history_payload,
            DOS,
            PREVENTIVE_COUNSELLING_CODES,
        )
        last_30days_smoking_counselling = extract_last_30days_cpt_event(
            cpt_history_payload,
            DOS,
            SMOKING_COUNSELLING_CODES,
        )
        last_30days_obesity_counselling = extract_last_30days_cpt_event(
            cpt_history_payload,
            DOS,
            OBESITY_COUNSELLING_CODES,
        )

        output_json = build_output_json(
            demo,
            insurance_name,
            DOS,
            matched_visit,
            visit_detail,
            last_preventive,
            last_30days_preventive_counselling,
            last_30days_smoking_counselling,
            last_30days_obesity_counselling,
            smoking_history,
            payment_history,
            laborders,
            has_prescription_medicine,
            screening,
            cptdates,
            icd_cpt_code_with_modifiers,
            calendar_year_icd_cpt_codes,
        )

        output_file = f"patient_Coding_{PATIENT_ID}_{CLINIC_ID}.json"
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2)

        print(f"Done! Output saved to: {output_path}")
        print(json.dumps(output_json, indent=2))
    except Exception as exc:
        print(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
