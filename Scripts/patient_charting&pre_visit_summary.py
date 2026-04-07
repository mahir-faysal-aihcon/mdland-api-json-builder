import requests
import json
import os
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURATION — fill these in
# ─────────────────────────────────────────
BEARER_TOKEN = "eyJraWQiOiJKeGNJaFF0K2pBZUlSZ2pZOHZ5ZXpHYzUyRzdySHNEQWxHdnVDTjBsOG5FPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3ZGJlbTgxMm5tdDgxaHRndHJuaDI1Y3QycSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiaWNsaW5pYy5wYXRpZW50XC9pbnN1cmFuY2UucmVhZCBpY2xpbmljLmVuY291bnRlclwvcmVhZCBpY2xpbmljLnBhdGllbnRcL21lZGljYWwtaGlzdG9yeS5yZWFkIGljbGluaWMuZW5jb3VudGVyXC93cml0ZSBpY2xpbmljLmxhYm9yYXRvcnlcL3JlYWQgaWNsaW5pYy5kb2N1bWVudFwvcmVhZCBpY2xpbmljLnByb3ZpZGVyXC9yZWFkIGljbGluaWMucGF0aWVudFwvZGVtb2dyYXBoaWMucmVhZCBpY2xpbmljLnNjaGVkdWxpbmdcL3dyaXRlIGljbGluaWMucGF0aWVudFwvZGVtb2dyYXBoaWMud3JpdGUgaWNsaW5pYy5zY2hlZHVsaW5nXC9yZWFkIGljbGluaWMuYmlsbGluZ1wvcmVhZCIsImF1dGhfdGltZSI6MTc3NTU2MzU0NSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfNTYzMTA3UmYzIiwiZXhwIjoxNzc1NTY3MTQ1LCJpYXQiOjE3NzU1NjM1NDUsInZlcnNpb24iOjIsImp0aSI6ImVhYmMyNDVhLTZmYzItNDRlYS04MzI0LTlmY2ExZTAyMTA0OCIsImNsaWVudF9pZCI6IjdkYmVtODEybm10ODFodGd0cm5oMjVjdDJxIn0.rjeIAEf352VpaJAkIs5bT7sPLDenIbwsXD-kZvMAx6v9iJ8RXiBqWGU1OqNXtLIrSVI7kTCMSOtAZxzjEu7N7lfImqxlcv-9VptJWNC3-7ZWQjVStTVjkLnYswDKoC5dmOWNG6aUNDw6pI9sMjeJ-LHVF8yEhlVd3cs5SCLyu_boehrDvWBg6eAiJCFrHAV1HA94uMe1Ysl6u_g5qAOurPJmPD2otXhqYL8o5vvbPGAgEzRkQS6qvZVdhxaKOutQV19iHa1yDET3sMF3RrvTcqiUgHcmAWQ9ymO2dfGKwTOzdxIhWpqUbL2EcI1Lfc55h2sihlwL6SRCTnhVA1CsPQ"

BASE_URL = "https://partner-api-dev.iclinichealth.dev"

# Input parameters
CLINIC_ID  = 1007
PATIENT_ID = 1002301179
DOS        = "2025-10-09"  # Date of Service (manual input for now)

BLOOD_WORK_TARGETS = {"80053", "85025", "83036", "80061", "36415"}
EKG_TARGETS = {"93000", "93005", "93010"}

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def get_headers():
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }

def _ensure_success(response, endpoint_name):
    if response.status_code == 401:
        raise RuntimeError(
            f"{endpoint_name} failed with 401 Unauthorized. "
            "Your Bearer token is invalid or expired. Paste a fresh token and run again."
        )
    if not response.ok:
        body = response.text.strip().replace("\n", " ")
        if len(body) > 250:
            body = body[:250] + "..."
        raise RuntimeError(f"{endpoint_name} failed ({response.status_code}): {body}")

def format_dob(dob_str):
    """Convert YYYY-MM-DD to MM/DD/YYYY"""
    try:
        return datetime.strptime(dob_str, "%Y-%m-%d").strftime("%m/%d/%Y")
    except Exception:
        return dob_str

def _normalize_to_iso_date(date_str):
    if not date_str:
        return ""
    text = str(date_str).strip()
    if "T" in text:
        text = text.split("T")[0]
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return ""

def _format_visit_datetime(datetime_str):
    if not datetime_str:
        return ""
    text = str(datetime_str).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%m/%d/%Y %I:%M %p")
        except Exception:
            continue
    return text

def _format_inches_to_ft_in(height_value):
    if height_value is None:
        return ""
    text = str(height_value).strip()
    if not text:
        return ""
    if "'" in text or "ft" in text.lower():
        return text
    try:
        inches = float(text)
    except Exception:
        return text
    feet = int(inches // 12)
    rem_inches = inches - (feet * 12)
    return f"{feet}'{rem_inches:.1f} ft/inch"

def _format_weight_lbs(weight_value):
    if weight_value is None:
        return ""
    text = str(weight_value).strip()
    if not text:
        return ""
    if "lb" in text.lower():
        return text
    try:
        num = float(text)
        if num.is_integer():
            return f"{int(num)} lbs"
        return f"{num:.1f} lbs"
    except Exception:
        return f"{text} lbs"

# ─────────────────────────────────────────
# STEP 1: Fetch patient demographics
# ─────────────────────────────────────────
def fetch_demographics(clinic_id, patient_id):
    url = f"{BASE_URL}/iclinic-patient/demographic/v1/clinics/{clinic_id}/patients/{patient_id}"
    response = requests.get(url, headers=get_headers())
    _ensure_success(response, "Demographics API")
    return response.json()

def fetch_active_medications(clinic_id, patient_id):
    url = (
        f"{BASE_URL}/iclinic-patient/medical-history/v1/clinics/{clinic_id}"
        f"/patients/{patient_id}/medications"
    )
    response = requests.get(
        url,
        headers=get_headers(),
        params={"active_only": "true"},
    )
    _ensure_success(response, "Active medications API")
    return response.json()

def fetch_insurance(clinic_id, patient_id):
    url = f"{BASE_URL}/iclinic-patient/insurance/v1/clinics/{clinic_id}/patients/{patient_id}/insurance"
    response = requests.get(url, headers=get_headers())
    _ensure_success(response, "Insurance API")
    return response.json()

def fetch_visits(clinic_id, patient_id):
    url = (
        f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
        f"/patients/{patient_id}/visits"
    )
    response = requests.get(
        url,
        headers=get_headers(),
        params={"offset": 0, "limit": 50},
    )
    _ensure_success(response, "List visits API")
    return response.json()

def fetch_visit_detail(clinic_id, visit_id):
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}"
    response = requests.get(url, headers=get_headers())
    _ensure_success(response, "Get visit detail API")
    return response.json()

def fetch_visit_vitals(clinic_id, visit_id):
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/vitals"
    response = requests.get(url, headers=get_headers())
    _ensure_success(response, "Visit vitals API")
    return response.json()

def fetch_historical_icds(clinic_id, patient_id):
    url = (
        f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
        f"/patients/{patient_id}/icd-history"
    )
    response = requests.get(
        url,
        headers=get_headers(),
        params={"system": "ICD10", "limit": 100},
    )
    _ensure_success(response, "Historical ICDs API")
    return response.json()

def fetch_cpt_history(clinic_id, patient_id):
    url = (
        f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
        f"/patients/{patient_id}/cpt-history"
    )
    response = requests.get(
        url,
        headers=get_headers(),
        params={"limit": 100},
    )
    _ensure_success(response, "CPT history API")
    return response.json()

def fetch_lab_orders(clinic_id, patient_id, order_date_to):
    url = (
        f"{BASE_URL}/iclinic-laboratory/v1/clinics/{clinic_id}"
        f"/patients/{patient_id}/orders"
    )
    limit = 50
    offset = 0
    all_items = []

    while True:
        response = requests.get(
            url,
            headers=get_headers(),
            params={"order_date_to": order_date_to, "offset": offset, "limit": limit},
        )
        _ensure_success(response, "Lab orders API")
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

def fetch_lab_order_detail(clinic_id, patient_id, order_id):
    url = (
        f"{BASE_URL}/iclinic-laboratory/v1/clinics/{clinic_id}"
        f"/patients/{patient_id}/orders/{order_id}"
    )
    response = requests.get(url, headers=get_headers())
    _ensure_success(response, "Lab order detail API")
    return response.json()

def _first_non_empty(item, keys):
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

def _clean_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "none":
        return ""
    return text

def _parse_to_date(value):
    if value is None:
        return None
    text = _clean_text(value)
    if not text:
        return None

    if "T" in text:
        text = text.split("T")[0]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue
    return None

def _format_medication(item):
    if isinstance(item, str):
        return item.strip()
    if not isinstance(item, dict):
        return ""

    # Use a prebuilt display/description string when available.
    preformatted = _first_non_empty(
        item,
        [
            "display",
            "description",
            "medication_text",
            "medication_display",
            "full_text",
            "drug_full_description",
        ],
    )
    if preformatted:
        return preformatted

    name = _first_non_empty(
        item,
        [
            "print_name",
            "medication_name",
            "drug_name",
            "name",
            "medication",
            "generic_name",
            "brand_name",
        ],
    )
    strength = _first_non_empty(item, ["strength", "dosage", "dose", "form"])
    sig = _first_non_empty(item, ["sig", "directions", "instruction", "instructions"])
    if not sig:
        route = _first_non_empty(item, ["route"])
        frequency = _first_non_empty(item, ["frequency"])
        duration = _first_non_empty(item, ["duration"])
        note = _first_non_empty(item, ["note"])
        sig_parts = [part for part in [route, frequency, duration, note] if part]
        if sig_parts:
            sig = ", ".join(sig_parts)
    dispense = _first_non_empty(item, ["dispense", "dispensed_quantity", "quantity", "qty", "dispense_qty"])
    dispense_unit = _first_non_empty(item, ["dispense_unit", "quantity_unit", "unit"])
    refill = _first_non_empty(item, ["refill", "refills", "refill_count"])

    if not name:
        return ""

    line = name
    if strength and strength.lower() not in line.lower():
        line = f"{line} {strength}".strip()
    if sig:
        line = f"{line} SIG: {sig}"
    if dispense:
        disp_value = f"{dispense} {dispense_unit}".strip() if dispense_unit else dispense
        line = f"{line} Disp: {disp_value}"
    if refill:
        line = f"{line} Refill: {refill}"
    return line.strip()

def extract_active_medications(payload):
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("medications"), list):
            items = payload.get("medications")
        elif isinstance(payload.get("items"), list):
            items = payload.get("items")
        elif isinstance(payload.get("data"), list):
            items = payload.get("data")
        elif isinstance(payload.get("results"), list):
            items = payload.get("results")
        else:
            items = []
    else:
        items = []

    meds = []
    seen = set()
    for item in items:
        line = _format_medication(item)
        if line and line not in seen:
            meds.append(line)
            seen.add(line)
    return meds

def _default_lab_tests():
    return {
        "microalb_creat_ratio_panel": None,
        "hemoglobin_a1c": None,
        "lipid_ldl": None,
        "cmp_present": False,
        "gfr": None,
        "serum_creatinine": None,
        "vitamin_d": None,
        "pap_smear_present": False,
        "psa": None,
        "chlamydia_present": False,
        "colon_cancer_fobt_present": False,
    }

def _extract_lab_tests_from_order_detail(detail_payload):
    tests = _default_lab_tests()
    if not isinstance(detail_payload, dict):
        return tests

    test_items = detail_payload.get("test_items")
    if not isinstance(test_items, list):
        return tests

    for item in test_items:
        if not isinstance(item, dict):
            continue
        lab_name = _clean_text(item.get("lab_name")).lower()
        lab_code = _clean_text(item.get("lab_code")).lower()
        text = f"{lab_name} {lab_code}".strip()
        result = _clean_text(item.get("result"))

        if ("microalb" in text) or ("microalbumin" in text) or ("acr" in text) or ("albumin/creatinine" in text):
            tests["microalb_creat_ratio_panel"] = result or tests["microalb_creat_ratio_panel"]
        if ("a1c" in text) or ("hba1c" in text) or ("hemoglobin a1c" in text):
            tests["hemoglobin_a1c"] = result or tests["hemoglobin_a1c"]
        if ("ldl" in text) or ("lipid" in text):
            tests["lipid_ldl"] = result or tests["lipid_ldl"]
        if ("cmp" in text) or ("comprehensive metabolic" in text):
            tests["cmp_present"] = True
        if ("gfr" in text) or ("egfr" in text):
            tests["gfr"] = result or tests["gfr"]
        if "creatinine" in text:
            tests["serum_creatinine"] = result or tests["serum_creatinine"]
        if "vitamin d" in text:
            tests["vitamin_d"] = result or tests["vitamin_d"]
        if ("pap" in text) or ("pap smear" in text):
            tests["pap_smear_present"] = True
        if ("psa" in text) or ("prostate specific antigen" in text):
            tests["psa"] = result or tests["psa"]
        if "chlamydia" in text:
            tests["chlamydia_present"] = True
        if ("fobt" in text) or ("fit" in text) or ("occult blood" in text) or ("colofit" in text):
            tests["colon_cancer_fobt_present"] = True

    return tests

def build_lab_history(clinic_id, patient_id, dos):
    order_date_to = _normalize_to_iso_date(dos) or dos
    orders_payload = fetch_lab_orders(clinic_id, patient_id, order_date_to)
    if isinstance(orders_payload, dict) and isinstance(orders_payload.get("items"), list):
        orders = [x for x in orders_payload.get("items") if isinstance(x, dict)]
    elif isinstance(orders_payload, list):
        orders = [x for x in orders_payload if isinstance(x, dict)]
    else:
        orders = []

    out = []
    for order in orders:
        order_id = order.get("order_id")
        if order_id in (None, ""):
            continue
        try:
            detail = fetch_lab_order_detail(clinic_id, patient_id, order_id)
        except Exception:
            continue

        test_items = detail.get("test_items") if isinstance(detail, dict) else []
        if not isinstance(test_items, list):
            test_items = []
        lab_names = []
        lab_codes = []
        for item in test_items:
            if not isinstance(item, dict):
                continue
            n = _clean_text(item.get("lab_name"))
            c = _clean_text(item.get("lab_code"))
            if n:
                lab_names.append(n)
            if c:
                lab_codes.append(c)

        unique_names = list(dict.fromkeys(lab_names))
        unique_codes = list(dict.fromkeys(lab_codes))
        labname = ", ".join(unique_names)

        out.append(
            {
                "dos": format_dob(_clean_text(detail.get("order_date") or order.get("order_date"))),
                "category": None,
                "description": None,
                "labname": labname,
                "tests": None,
            }
        )

    return out

def extract_vital_signs_from_visit_vitals(payload, fallback_date=""):
    if not isinstance(payload, dict):
        return {
            "date": "",
            "bmi": "",
            "bp": "",
            "height": "",
            "weight": "",
        }

    vitals = payload

    systolic = vitals.get("bp_systolic", vitals.get("systolic_bp"))
    diastolic = vitals.get("bp_diastolic", vitals.get("diastolic_bp"))
    bp = ""
    if systolic not in (None, "") and diastolic not in (None, ""):
        bp = f"{systolic}/{diastolic} mmHg"
    elif systolic not in (None, "") or diastolic not in (None, ""):
        bp = f"{systolic or ''}/{diastolic or ''}".strip("/")

    date_value = (
        vitals.get("visit_datetime")
        or vitals.get("date")
        or vitals.get("created_date")
        or fallback_date
    )

    return {
        "date": _format_visit_datetime(date_value) or format_dob(_clean_text(fallback_date)),
        "bmi": _clean_text(vitals.get("bmi")),
        "bp": bp,
        "height": _format_inches_to_ft_in(vitals.get("height", "")),
        "weight": _format_weight_lbs(vitals.get("weight", "")),
    }

def extract_insurance_fields(payload):
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        items = [x for x in payload.get("items") if isinstance(x, dict)]
    elif isinstance(payload, list):
        items = [x for x in payload if isinstance(x, dict)]
    else:
        items = []

    if not items:
        return {
            "insurance_name": "",
            "insurance_code": "",
            "header_insurance_name": "",
        }

    # Prefer Primary insurance if present.
    primary = next((x for x in items if str(x.get("insu_order_label", "")).lower() == "primary"), None)
    item = primary or items[0]

    insurance_company = item.get("insurance_company") if isinstance(item.get("insurance_company"), dict) else {}
    insured = item.get("insured") if isinstance(item.get("insured"), dict) else {}

    company_name = str(insurance_company.get("insu_com_name", "") or "").strip()

    relationship = str(insured.get("relationship_label", "") or "").strip()
    if not relationship:
        rel_code = str(insured.get("relationship", "") or "").strip().upper()
        relationship = "Self" if rel_code == "P" else ""

    insurance_name = company_name
    if relationship:
        insurance_name = f"{company_name} ({relationship})"

    insurance_code = str(item.get("insured_id", "") or item.get("policy_number", "") or "").strip()
    header_insurance_name = company_name

    return {
        "insurance_name": insurance_name,
        "insurance_code": insurance_code,
        "header_insurance_name": header_insurance_name,
    }

def extract_hpi_from_visit_detail(payload):
    if not isinstance(payload, dict):
        return ""
    complaint = payload.get("complaint")
    if not isinstance(complaint, dict):
        return ""
    return _clean_text(complaint.get("present_illness"))

def extract_reason_for_visit_from_visit_detail(payload):
    if not isinstance(payload, dict):
        return []
    complaint = payload.get("complaint")
    if not isinstance(complaint, dict):
        return []

    chief_complaint = complaint.get("chief_complaint")
    if chief_complaint is None:
        return []

    if isinstance(chief_complaint, list):
        out = []
        for item in chief_complaint:
            text = _clean_text(item)
            if text:
                out.append(text)
        return out

    text = _clean_text(chief_complaint)
    if not text:
        return []

    parts = []
    for raw in text.replace("\r", "\n").split("\n"):
        for chunk in raw.split(";"):
            for piece in chunk.split("|"):
                cleaned = _clean_text(piece)
                if cleaned:
                    parts.append(cleaned)

    if len(parts) > 1:
        return parts

    # Keep comma split as a soft fallback.
    comma_parts = [_clean_text(x) for x in text.split(",")]
    comma_parts = [x for x in comma_parts if x]
    if len(comma_parts) > 1:
        return comma_parts

    return [text]

def extract_current_icds_from_visit_detail(payload):
    if not isinstance(payload, dict):
        return []

    diagnoses = payload.get("diagnoses")
    if not isinstance(diagnoses, list):
        return []

    icds = []
    seen = set()
    for item in diagnoses:
        if not isinstance(item, dict):
            continue
        code = _clean_text(item.get("icd_code"))
        description = _clean_text(item.get("icd_name") or item.get("description"))
        if not code and not description:
            continue

        key = (code, description)
        if key in seen:
            continue
        seen.add(key)
        icds.append(
            {
                "code": code,
                "description": description,
            }
        )
    return icds

def extract_cpts_from_visit_detail(payload):
    if not isinstance(payload, dict):
        return []

    procedures = payload.get("procedures")
    if not isinstance(procedures, list):
        return []

    cpts = []
    seen = set()
    for item in procedures:
        if not isinstance(item, dict):
            continue
        code = _clean_text(item.get("cpt_code") or item.get("code"))
        description = _clean_text(item.get("cpt_name") or item.get("description"))
        if not code and not description:
            continue

        key = (code, description)
        if key in seen:
            continue
        seen.add(key)
        cpts.append(
            {
                "code": code,
                "description": description,
            }
        )
    return cpts

def extract_historical_icds(payload):
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        items = [x for x in payload.get("items") if isinstance(x, dict)]
    elif isinstance(payload, list):
        items = [x for x in payload if isinstance(x, dict)]
    else:
        items = []

    historical_icds = []
    seen = set()
    for item in items:
        code = _clean_text(
            item.get("icd_code")
            or item.get("code")
            or item.get("diagnosis_code")
        )
        description = _clean_text(
            item.get("icd_name")
            or item.get("description")
            or item.get("diagnosis_name")
        )
        if not code and not description:
            continue

        key = (code, description)
        if key in seen:
            continue
        seen.add(key)
        historical_icds.append(
            {
                "code": code,
                "description": description,
            }
        )
    return historical_icds

def extract_last_blood_work_and_ekg_dates(payload):
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        items = [x for x in payload.get("items") if isinstance(x, dict)]
    elif isinstance(payload, list):
        items = [x for x in payload if isinstance(x, dict)]
    else:
        items = []

    latest_blood_date = None
    latest_ekg_date = None

    for item in items:
        cpt_code = _clean_text(item.get("cpt_code") or item.get("code"))
        if not cpt_code:
            continue

        date_obj = (
            _parse_to_date(item.get("last_used_date"))
            or _parse_to_date(item.get("used_date"))
            or _parse_to_date(item.get("visit_date"))
            or _parse_to_date(item.get("dos"))
            or _parse_to_date(item.get("date_of_service"))
            or _parse_to_date(item.get("service_date"))
            or _parse_to_date(item.get("created_date"))
            or _parse_to_date(item.get("create_date"))
            or _parse_to_date(item.get("modified_date"))
            or _parse_to_date(item.get("modify_date"))
        )
        if date_obj is None:
            continue

        if cpt_code in BLOOD_WORK_TARGETS:
            if latest_blood_date is None or date_obj > latest_blood_date:
                latest_blood_date = date_obj

        if cpt_code in EKG_TARGETS:
            if latest_ekg_date is None or date_obj > latest_ekg_date:
                latest_ekg_date = date_obj

    return {
        "last_blood_work_date": latest_blood_date.strftime("%m/%d/%Y") if latest_blood_date else "",
        "last_ekg_date": latest_ekg_date.strftime("%m/%d/%Y") if latest_ekg_date else "",
    }

def extract_calendar_year_icd_cpt_codes(icd_payload, cpt_payload, dos):
    dos_date = _parse_to_date(dos)
    if dos_date is None:
        return {}
    target_year = dos_date.year

    bucket = {}

    # ICD history aggregation by last_used_date for DOS year
    if isinstance(icd_payload, dict) and isinstance(icd_payload.get("items"), list):
        icd_items = [x for x in icd_payload.get("items") if isinstance(x, dict)]
    elif isinstance(icd_payload, list):
        icd_items = [x for x in icd_payload if isinstance(x, dict)]
    else:
        icd_items = []

    for item in icd_items:
        date_obj = _parse_to_date(item.get("last_used_date"))
        if date_obj is None or date_obj.year != target_year:
            continue
        date_key = date_obj.strftime("%m/%d/%Y")
        icd_code = _clean_text(item.get("icd_code") or item.get("code"))
        if date_key not in bucket:
            bucket[date_key] = {"icd_code_list": [], "cpt_code_list": []}
        if icd_code and icd_code not in bucket[date_key]["icd_code_list"]:
            bucket[date_key]["icd_code_list"].append(icd_code)

    # CPT history aggregation by last_used_date for DOS year
    if isinstance(cpt_payload, dict) and isinstance(cpt_payload.get("items"), list):
        cpt_items = [x for x in cpt_payload.get("items") if isinstance(x, dict)]
    elif isinstance(cpt_payload, list):
        cpt_items = [x for x in cpt_payload if isinstance(x, dict)]
    else:
        cpt_items = []

    for item in cpt_items:
        date_obj = _parse_to_date(item.get("last_used_date"))
        if date_obj is None or date_obj.year != target_year:
            continue
        date_key = date_obj.strftime("%m/%d/%Y")
        cpt_code = _clean_text(item.get("cpt_code") or item.get("code"))
        if date_key not in bucket:
            bucket[date_key] = {"icd_code_list": [], "cpt_code_list": []}
        if cpt_code and cpt_code not in bucket[date_key]["cpt_code_list"]:
            bucket[date_key]["cpt_code_list"].append(cpt_code)

    # Return keys sorted by date ascending
    sorted_dates = sorted(bucket.keys(), key=lambda d: datetime.strptime(d, "%m/%d/%Y").date())
    return {date_key: bucket[date_key] for date_key in sorted_dates}

def _visit_date_as_date_obj(visit):
    if not isinstance(visit, dict):
        return None
    iso_date = _normalize_to_iso_date(visit.get("visit_date") or visit.get("visit_datetime"))
    if not iso_date:
        return None
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").date()
    except Exception:
        return None

def _visit_date_as_display(visit):
    if not isinstance(visit, dict):
        return ""
    visit_date = _clean_text(visit.get("visit_date"))
    if visit_date:
        return format_dob(visit_date)
    visit_dt = _clean_text(visit.get("visit_datetime"))
    if visit_dt:
        return _format_visit_datetime(visit_dt).split(" ")[0]
    return ""

def get_last_3_visit_history(clinic_id, patient_id, dos):
    visits_payload = fetch_visits(clinic_id, patient_id)
    if isinstance(visits_payload, dict) and isinstance(visits_payload.get("items"), list):
        visits = [x for x in visits_payload.get("items") if isinstance(x, dict)]
    elif isinstance(visits_payload, list):
        visits = [x for x in visits_payload if isinstance(x, dict)]
    else:
        visits = []

    target_iso = _normalize_to_iso_date(dos)
    try:
        target_date = datetime.strptime(target_iso, "%Y-%m-%d").date() if target_iso else None
    except Exception:
        target_date = None

    filtered = []
    for visit in visits:
        visit_date_obj = _visit_date_as_date_obj(visit)
        if visit_date_obj is None:
            continue
        if target_date is not None and visit_date_obj > target_date:
            continue
        filtered.append((visit_date_obj, visit))

    filtered.sort(key=lambda x: x[0], reverse=True)
    history = []
    for _, visit in filtered:
        visit_id = visit.get("visit_id")
        if visit_id in (None, ""):
            continue
        detail_payload = fetch_visit_detail(clinic_id, visit_id)
        icds = extract_current_icds_from_visit_detail(detail_payload)
        cpts = extract_cpts_from_visit_detail(detail_payload)

        # Keep only visits that have at least one ICD or CPT entry.
        if not icds and not cpts:
            continue

        history.append(
            {
                "date": _visit_date_as_display(visit),
                "icds": icds,
                "cpts": cpts,
            }
        )
        if len(history) == 3:
            break
    return history

def get_visit_context_by_dos(clinic_id, patient_id, dos):
    visits_payload = fetch_visits(clinic_id, patient_id)
    if isinstance(visits_payload, dict) and isinstance(visits_payload.get("items"), list):
        visits = [x for x in visits_payload.get("items") if isinstance(x, dict)]
    elif isinstance(visits_payload, list):
        visits = [x for x in visits_payload if isinstance(x, dict)]
    else:
        visits = []

    target_dos = _normalize_to_iso_date(dos)
    matched_visit = None
    for visit in visits:
        visit_date = _normalize_to_iso_date(visit.get("visit_date") or visit.get("visit_datetime"))
        if visit_date and visit_date == target_dos:
            matched_visit = visit
            break

    if not matched_visit:
        return {
            "visit_type": "",
            "history_of_present_illness": "",
            "reason_for_visit": [],
            "current_icds": [],
            "vital_signs": {
                "date": "",
                "bmi": "",
                "bp": "",
                "height": "",
                "weight": "",
            },
        }

    visit_type = _clean_text(
        matched_visit.get("visit_type_name")
        or matched_visit.get("visit_type")
        or matched_visit.get("visit_type_label")
    )

    visit_id = matched_visit.get("visit_id")
    if visit_id in (None, ""):
        return {
            "visit_type": visit_type,
            "history_of_present_illness": "",
            "reason_for_visit": [],
            "current_icds": [],
            "vital_signs": {
                "date": "",
                "bmi": "",
                "bp": "",
                "height": "",
                "weight": "",
            },
        }

    detail_payload = fetch_visit_detail(clinic_id, visit_id)
    visit_vitals_payload = fetch_visit_vitals(clinic_id, visit_id)
    fallback_vitals_date = (
        matched_visit.get("visit_datetime")
        or matched_visit.get("visit_date")
        or dos
    )
    return {
        "visit_type": visit_type,
        "history_of_present_illness": extract_hpi_from_visit_detail(detail_payload),
        "reason_for_visit": extract_reason_for_visit_from_visit_detail(detail_payload),
        "current_icds": extract_current_icds_from_visit_detail(detail_payload),
        "vital_signs": extract_vital_signs_from_visit_vitals(visit_vitals_payload, fallback_vitals_date),
    }

# ─────────────────────────────────────────
# STEP 2: Build target JSON
# ─────────────────────────────────────────
def build_patient_json(
    demo,
    dos,
    active_medications,
    lab_history,
    vital_signs,
    insurance_fields,
    visit_type,
    history_of_present_illness,
    reason_for_visit,
):
    return {
        "first_name":           demo.get("first_name", ""),
        "last_name":            demo.get("last_name", ""),
        "dob":                  format_dob(demo.get("dob", "")),
        "sex":                  demo.get("gender", ""),
        "home_phone":           demo.get("home_phone", ""),
        "mobile_phone":         demo.get("mobile_phone", ""),
        "insurance_name":       insurance_fields.get("insurance_name", ""),
        "insurance_code":       insurance_fields.get("insurance_code", ""),
        "dos":                  dos,
        "emr_patient_id":       str(demo.get("patient_id", "")),
        "header_insurance_name": insurance_fields.get("header_insurance_name", ""),
        "visit_type":           visit_type,
        "reason_for_visit":     reason_for_visit,
        "history_of_present_illness": history_of_present_illness,
        "vital_signs":          vital_signs,
        "active_medications":   active_medications,
        "lab_history":          lab_history,
    }

def build_previsit_summary_json(
    demo,
    insurance_fields,
    current_icds,
    historical_icds,
    last_3visit_history,
    last_blood_work_date,
    last_ekg_date,
    calendar_year_icd_cpt_codes,
):
    return {
        "first_name": demo.get("first_name", ""),
        "last_name": demo.get("last_name", ""),
        "dob": format_dob(demo.get("dob", "")),
        "insurance": insurance_fields.get("insurance_name", ""),
        "current_icds": current_icds,
        "historical_icds": historical_icds,
        "last_3visit_history": last_3visit_history,
        "last_blood_work_date": last_blood_work_date,
        "last_ekg_date": last_ekg_date,
        "calendar_year_icd_cpt_codes": calendar_year_icd_cpt_codes,
    }

def build_combined_output(charting_json, previsit_summary_json):
    return {
        "patient_charting": charting_json,
        "previsit_summary": previsit_summary_json,
    }

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    try:
        print(f"Fetching demographics for Patient {PATIENT_ID}, Clinic {CLINIC_ID}...")
        demo = fetch_demographics(CLINIC_ID, PATIENT_ID)
        print("Fetching active medications...")
        medications_payload = fetch_active_medications(CLINIC_ID, PATIENT_ID)
        active_medications = extract_active_medications(medications_payload)
        print("Fetching lab history...")
        lab_history = build_lab_history(CLINIC_ID, PATIENT_ID, DOS)
        print("Fetching insurance...")
        insurance_payload = fetch_insurance(CLINIC_ID, PATIENT_ID)
        insurance_fields = extract_insurance_fields(insurance_payload)
        print("Fetching visit context by DOS...")
        visit_context = get_visit_context_by_dos(CLINIC_ID, PATIENT_ID, DOS)
        visit_type = visit_context.get("visit_type", "")
        history_of_present_illness = visit_context.get("history_of_present_illness", "")
        reason_for_visit = visit_context.get("reason_for_visit", [])
        current_icds = visit_context.get("current_icds", [])
        print("Fetching historical ICDs...")
        historical_icd_payload = fetch_historical_icds(CLINIC_ID, PATIENT_ID)
        historical_icds = extract_historical_icds(historical_icd_payload)
        print("Fetching CPT history metadata...")
        cpt_history_payload = fetch_cpt_history(CLINIC_ID, PATIENT_ID)
        cpt_dates = extract_last_blood_work_and_ekg_dates(cpt_history_payload)
        last_blood_work_date = cpt_dates.get("last_blood_work_date", "")
        last_ekg_date = cpt_dates.get("last_ekg_date", "")
        calendar_year_icd_cpt_codes = extract_calendar_year_icd_cpt_codes(
            historical_icd_payload,
            cpt_history_payload,
            DOS,
        )
        print("Fetching last 3 visit history...")
        last_3visit_history = get_last_3_visit_history(CLINIC_ID, PATIENT_ID, DOS)
        print(f"Found {len(last_3visit_history)} visit(s) with ICD/CPT history.")
        vital_signs = visit_context.get("vital_signs", {
            "date": "",
            "bmi": "",
            "bp": "",
            "height": "",
            "weight": "",
        })

        charting_json = build_patient_json(
            demo,
            DOS,
            active_medications,
            lab_history,
            vital_signs,
            insurance_fields,
            visit_type,
            history_of_present_illness,
            reason_for_visit,
        )
        previsit_summary_json = build_previsit_summary_json(
            demo,
            insurance_fields,
            current_icds,
            historical_icds,
            last_3visit_history,
            last_blood_work_date,
            last_ekg_date,
            calendar_year_icd_cpt_codes,
        )
        combined_output_json = build_combined_output(charting_json, previsit_summary_json)

        output_file = f"patient_Charting_previsit_summary.json"
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        with open(output_path, "w") as f:
            json.dump(combined_output_json, f, indent=2)

        print(f"Done! Output saved to: {output_path}")
        print(json.dumps(combined_output_json, indent=2))
    except Exception as exc:
        print(f"ERROR: {exc}")

if __name__ == "__main__":
    main()
