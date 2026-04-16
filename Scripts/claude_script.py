import json
from pathlib import Path
import re
import sys

import requests


BEARER_TOKEN = "eyJraWQiOiJKeGNJaFF0K2pBZUlSZ2pZOHZ5ZXpHYzUyRzdySHNEQWxHdnVDTjBsOG5FPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3ZGJlbTgxMm5tdDgxaHRndHJuaDI1Y3QycSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiaWNsaW5pYy5wYXRpZW50XC9pbnN1cmFuY2UucmVhZCBpY2xpbmljLmVuY291bnRlclwvcmVhZCBpY2xpbmljLnBhdGllbnRcL21lZGljYWwtaGlzdG9yeS5yZWFkIGljbGluaWMuZW5jb3VudGVyXC93cml0ZSBpY2xpbmljLmxhYm9yYXRvcnlcL3JlYWQgaWNsaW5pYy5kb2N1bWVudFwvcmVhZCBpY2xpbmljLnByb3ZpZGVyXC9yZWFkIGljbGluaWMucGF0aWVudFwvcW0ucmVhZCBpY2xpbmljLnBhdGllbnRcL2RlbW9ncmFwaGljLnJlYWQgaWNsaW5pYy5zY2hlZHVsaW5nXC93cml0ZSBpY2xpbmljLnBhdGllbnRcL2RlbW9ncmFwaGljLndyaXRlIGljbGluaWMuc2NoZWR1bGluZ1wvcmVhZCBpY2xpbmljLmJpbGxpbmdcL3JlYWQiLCJhdXRoX3RpbWUiOjE3NzYyNDQ3ODIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xXzU2MzEwN1JmMyIsImV4cCI6MTc3NjI0ODM4MiwiaWF0IjoxNzc2MjQ0NzgyLCJ2ZXJzaW9uIjoyLCJqdGkiOiJhZWY2OWY0Zi02Y2Y2LTQxNWMtOTYyOS1iZWM0OTMxN2MwZTEiLCJjbGllbnRfaWQiOiI3ZGJlbTgxMm5tdDgxaHRndHJuaDI1Y3QycSJ9.vT8i0g0gpavHOpRFIdZaCeasfI1y4-fzgYJWWsZ5ZrmwabQCpJaChKXDT6yjMMMjdHx8iuAERPXIkN82jFSa3PA5DmGc1G1evzqeVgh33tOA3IVBSl3Pkn8ZB-3bumroShrVbn7rKk1O9PARFuIRJWNTy90hf88I95YFVjpumWFI5PF_8Pk5meHawS9OzGt8htOuy0hS2MOyTCVzrMEUhO_mq2erN8_0s8LGJ0dBoKtGcRMbrtX3OqUfHnktkDNY2QpJqSRR2fcUkLcnlQeczFT4RPTqqO3jVmCMOFx4klex6n0pi6mmc2vA75LsqqrPU4B_zb44AmE7nYJo4kKy1g"
BASE_URL = "https://partner-api-dev.iclinichealth.dev"

CLINIC_ID = 1007
VISIT_ID = 1002729470
DOCTOR_ID = 1000000068
GU_SYSTEM_ID = 22

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_JSON_FILE = PROJECT_DIR / "JSON Outputs" / "api_update.json"


#We need to get the Gender to update The ROS and PE items correctly. For example, GU system and genital exam items differ based



ROS_SYSTEM_MAP = {
    "head/neck": 1,
    "ent": 2,
    "resp": 3,
    "cardiovas": 4,
    "gi": 5,
    "gu (male)": 6,
    "breast": 7,
    "gyn": 8,
    "skin": 9,
    "muscular/skeletal": 10,
    "neuro": 11,
    "endocrine": 12,
    "constitution": 13,
    "allergy/immun": 14,
    "eyes": 15,
    "heme/lym": 16,
    "psych": 17,
    "viral exposure": 18,
    "drug exposure": 19,
    "rad exposure": 20,
    "infectious dis": 21,
    "gu (female)": 22,

    "constitutional": 13,
    "eye": 15,
    "cardiovascular": 4,
    "respiratory": 3,
    "neurological": 11,
    "psychiatric": 17,
    "musculoskeletal": 10,
    "muscular skeletal": 10,
    "gu": GU_SYSTEM_ID,
}


# Need to update PE_ITEM_MAP to match the item_name

PE_ITEM_MAP = {
    "head/scalp/face": [1],
    "head": [1],
    "eyes": [2],
    "ears": [3],
    "nose/sinus": [4],
    "throat/mouth": [5],
    "neck": [6],
    "chest/lung": [7],
    "heart": [8],
    "breast": [9],
    "abdomen": [10],
    "rectal": [11],
    "genitalies (male)": [12],
    "genitalies (female)": [13],
    "extremities": [14],
    "skin/membrane": [15],
    "skin": [15],
    "neurological": [16],
    "muscular": [17],
    "mental status": [18],
    "esophagus": [19],
    "eg junction": [20],
    "cardia": [21],
    "fundus": [22],
    "body": [23],
    "antrum": [24],
    "pylorus": [25],
    "duodenum": [26],
    "anal canal": [27],
    "rectum": [28],
    "sigmoid colon": [29],
    "descending colon": [30],
    "splenic flexure": [31],
    "transverse colon": [32],
    "hepatic flexure": [33],
    "ascending colon": [34],
    "cecum": [35],
    "ileum": [36],
}


def get_headers():
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }


def load_input_json(filepath):
    file_path = Path(filepath)
    if not file_path.is_absolute():
        file_path = PROJECT_DIR / file_path

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_first_present(data, *keys):
    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)
        if value not in (None, "", []):
            return value
    return None


def load_complaint_data(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    reason_for_visit = get_first_present(data, "reason_for_visit", "chief_complaint")
    if reason_for_visit is None and isinstance(patient_charting, dict):
        reason_for_visit = get_first_present(
            patient_charting,
            "reason_for_visit",
            "chief_complaint",
        )

    if not reason_for_visit:
        raise ValueError("No 'reason_for_visit' or 'chief_complaint' key found in JSON.")

    if isinstance(reason_for_visit, list):
        chief_complaint = "\n".join(str(item).strip() for item in reason_for_visit if str(item).strip())
    else:
        chief_complaint = str(reason_for_visit).strip()

    present_illness = get_first_present(data, "history_of_present_illness", "present_illness")
    if present_illness is None and isinstance(patient_charting, dict):
        present_illness = get_first_present(
            patient_charting,
            "history_of_present_illness",
            "present_illness",
        )

    if present_illness is not None:
        present_illness = str(present_illness).strip()

    return {
        "chief_complaint": chief_complaint,
        "present_illness": present_illness,
    }


def load_ros_systems(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    ros_lines = get_first_present(data, "review_of_systems")
    if ros_lines is None and isinstance(patient_charting, dict):
        ros_lines = get_first_present(patient_charting, "review_of_systems")

    if not ros_lines:
        return []
    if not isinstance(ros_lines, list):
        raise ValueError("'review_of_systems' must be a list.")

    systems = []
    for raw_line in ros_lines:
        line = str(raw_line).strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"ROS line missing ':' separator: {line}")

        label, detail = line.split(":", 1)
        label_key = label.strip().lower()
        system_id = ROS_SYSTEM_MAP.get(label_key)
        if system_id is None:
            raise ValueError(f"Unsupported ROS system label: {label.strip()}")

        systems.append(
            {
                "system_id": system_id,
                "abnormal": False,
                "detail": detail.strip(),
            }
        )

    return systems


def load_physical_exam_items(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    physical_exam_lines = get_first_present(data, "physical_exam")
    if physical_exam_lines is None and isinstance(patient_charting, dict):
        physical_exam_lines = get_first_present(patient_charting, "physical_exam")

    if not physical_exam_lines:
        return []
    if not isinstance(physical_exam_lines, list):
        raise ValueError("'physical_exam' must be a list.")

    items_by_id = {}
    skipped_labels = []
    for raw_line in physical_exam_lines:
        line = str(raw_line).strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Physical exam line missing ':' separator: {line}")

        label, description = line.split(":", 1)
        label_key = label.strip().lower()
        pe_item_ids = PE_ITEM_MAP.get(label_key)
        if pe_item_ids is None:
            skipped_labels.append(label.strip())
            continue

        description_text = description.strip()
        for pe_item_id in pe_item_ids:
            existing = items_by_id.get(pe_item_id)
            if existing:
                existing["description"] = f"{existing['description']} {description_text}".strip()
            else:
                items_by_id[pe_item_id] = {
                    "pe_item_id": pe_item_id,
                    "status": "normal",
                    "description": description_text,
                }

    return [items_by_id[key] for key in sorted(items_by_id)], skipped_labels


def normalize_icd_code(value):
    text = str(value).strip()
    match = re.match(r"^([A-Z][A-Z0-9.]*)", text, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not parse ICD code from: {text}")
    return match.group(1).upper()


def load_diagnoses(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    sorted_icd_codes = get_first_present(data, "sorted_icd_codes")
    if sorted_icd_codes is None and isinstance(patient_charting, dict):
        sorted_icd_codes = get_first_present(patient_charting, "sorted_icd_codes")

    if not sorted_icd_codes:
        return []
    if not isinstance(sorted_icd_codes, list):
        raise ValueError("'sorted_icd_codes' must be a list.")

    diagnoses = []
    for item in sorted_icd_codes:
        code = normalize_icd_code(item)
        diagnoses.append(
            {
                "icd_code": code,
                "code_system": "ICD10",
                "doctor_id": DOCTOR_ID,
            }
        )

    return diagnoses


def load_note_diagnoses(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    icd_codes = get_first_present(data, "icd_codes", "sorted_icd_codes")
    if icd_codes is None and isinstance(patient_charting, dict):
        icd_codes = get_first_present(patient_charting, "icd_codes", "sorted_icd_codes")

    if not icd_codes:
        return []
    if not isinstance(icd_codes, list):
        raise ValueError("'icd_codes' must be a list.")

    diagnoses = []
    for item in icd_codes:
        code = normalize_icd_code(item)
        diagnoses.append(
            {
                "icd_code": code,
                "code_system": "ICD10",
                "doctor_id": DOCTOR_ID,
            }
        )

    return diagnoses


def load_assessment_plan_items(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    assessment_entries = get_first_present(data, "assessment")
    if assessment_entries is None and isinstance(patient_charting, dict):
        assessment_entries = get_first_present(patient_charting, "assessment")

    if not assessment_entries:
        return []
    if not isinstance(assessment_entries, list):
        raise ValueError("'assessment' must be a list.")

    assessments = []
    for entry in assessment_entries:
        if not isinstance(entry, dict):
            raise ValueError("Each assessment entry must be an object.")

        icd_code_raw = get_first_present(entry, "icd_code")
        plan_detail = get_first_present(entry, "assessment_plan", "plan_detail")
        if not icd_code_raw:
            raise ValueError("Assessment entry missing 'icd_code'.")
        if not plan_detail:
            raise ValueError(f"Assessment entry missing plan text for ICD {icd_code_raw}.")

        assessments.append(
            {
                "icd_code": normalize_icd_code(icd_code_raw),
                "plan_detail": str(plan_detail).strip(),
            }
        )

    return assessments


def load_procedures(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    procedure_entries = get_first_present(data, "linkicd_icd_with_cpt_data")
    if procedure_entries is None and isinstance(patient_charting, dict):
        procedure_entries = get_first_present(patient_charting, "linkicd_icd_with_cpt_data")

    if not procedure_entries:
        return []
    if not isinstance(procedure_entries, list):
        raise ValueError("'linkicd_icd_with_cpt_data' must be a list.")

    procedures = []
    for entry in procedure_entries:
        if not isinstance(entry, dict):
            raise ValueError("Each procedure entry must be an object.")

        cpt_code = str(get_first_present(entry, "cpt_code") or "").strip().upper()
        if not cpt_code:
            raise ValueError("Procedure entry missing 'cpt_code'.")

        raw_icd_links = get_first_present(entry, "linked_icd", "icd_links")
        if not isinstance(raw_icd_links, list) or not raw_icd_links:
            raise ValueError(f"Procedure entry missing linked ICD list for CPT {cpt_code}.")

        icd_links = []
        for icd in raw_icd_links[:4]:
            icd_links.append(normalize_icd_code(icd))

        procedure_payload = {
            "cpt_code": cpt_code,
            "units": 1,
            "icd_links": icd_links,
            "doctor_id": DOCTOR_ID,
        }

        modifier = str(get_first_present(entry, "modifier") or "").strip().upper()
        if modifier:
            procedure_payload["modifiers"] = [modifier]

        procedures.append(procedure_payload)

    return procedures


def load_basic_cpt_procedures(data, existing_cpt_codes=None):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    cpt_codes = get_first_present(data, "cpt_codes")
    if cpt_codes is None and isinstance(patient_charting, dict):
        cpt_codes = get_first_present(patient_charting, "cpt_codes")

    if not cpt_codes:
        return []
    if not isinstance(cpt_codes, list):
        raise ValueError("'cpt_codes' must be a list.")

    existing = set(existing_cpt_codes or [])
    basic_procedures = []
    for item in cpt_codes:
        cpt_code = str(item).strip().upper()
        if not cpt_code or cpt_code in existing:
            continue
        basic_procedures.append(
            {
                "cpt_code": cpt_code,
                "doctor_id": DOCTOR_ID,
            }
        )

    return basic_procedures


def load_deleted_cpt_codes(data):
    patient_charting = data.get("patient_charting") if isinstance(data, dict) else None

    deleted_block = get_first_present(data, "deleted")
    if deleted_block is None and isinstance(patient_charting, dict):
        deleted_block = get_first_present(patient_charting, "deleted")

    if not deleted_block:
        return []
    if not isinstance(deleted_block, dict):
        raise ValueError("'deleted' must be an object.")

    deleted_cpt_codes = deleted_block.get("cpt", [])
    if not deleted_cpt_codes:
        return []
    if not isinstance(deleted_cpt_codes, list):
        raise ValueError("'deleted.cpt' must be a list.")

    cleaned = []
    for item in deleted_cpt_codes:
        code = str(item).strip().upper()
        if code:
            cleaned.append(code)
    return cleaned


def ensure_success(response, label):
    if response.status_code == 401:
        raise RuntimeError(f"{label} failed with 401 Unauthorized. Paste a fresh token.")
    if not response.ok:
        raise RuntimeError(f"{response.status_code}: {response.text.strip()[:300]}")


def fetch_existing_visit_procedures(clinic_id, visit_id):
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/procedures"
    response = requests.get(url, headers=get_headers())
    ensure_success(response, "Get existing procedures")

    payload = response.json()
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return [payload]
    return []


def build_procedure_code_index(procedures):
    procedures_by_code = {}
    for item in procedures:
        cpt_code = str(item.get("cpt_code") or "").strip().upper()
        cpt_id = item.get("cpt_id")
        if not cpt_code or cpt_id in (None, ""):
            continue
        procedures_by_code.setdefault(cpt_code, []).append(int(cpt_id))
    return procedures_by_code


def write_complaint(clinic_id, visit_id, doctor_id, complaint_data):
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/complaint"
    payload = {
        "doctor_id": doctor_id,
        "chief_complaint": complaint_data["chief_complaint"],
    }
    if complaint_data.get("present_illness"):
        payload["present_illness"] = complaint_data["present_illness"]

    print(f"Sending to: {url}")
    print(f"Payload   : {json.dumps(payload, indent=2)}")

    response = requests.put(url, headers=get_headers(), json=payload)
    ensure_success(response, "Complaint update")

    print(f"\nComplaint update success! Response: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


def write_ros(clinic_id, visit_id, doctor_id, ros_systems):
    if not ros_systems:
        print("No review_of_systems found. Skipping ROS update.")
        return

    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/ros"
    payload = {
        "doctor_id": doctor_id,
        "systems": ros_systems,
    }

    print(f"Sending to: {url}")
    print(f"Payload   : {json.dumps(payload, indent=2)}")

    response = requests.put(url, headers=get_headers(), json=payload)
    ensure_success(response, "ROS update")

    print(f"\nROS update success! Response: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


def write_physical_exam(clinic_id, visit_id, doctor_id, pe_items):
    if not pe_items:
        print("No physical_exam found. Skipping physical exam update.")
        return

    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/physical-exam/detail"
    payload = {
        "doctor_id": doctor_id,
        "items": pe_items,
    }

    print(f"Sending to: {url}")
    print(f"Payload   : {json.dumps(payload, indent=2)}")

    response = requests.put(url, headers=get_headers(), json=payload)
    ensure_success(response, "Physical exam update")

    print(f"\nPhysical exam update success! Response: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


def write_diagnoses(clinic_id, visit_id, diagnoses):
    if not diagnoses:
        print("No sorted_icd_codes found. Skipping diagnoses update.")
        return

    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/diagnoses"
    payload = {
        "diagnoses": diagnoses,
    }

    print(f"Sending to: {url}")
    print(f"Payload   : {json.dumps(payload, indent=2)}")

    response = requests.put(url, headers=get_headers(), json=payload)
    ensure_success(response, "Diagnoses update")

    print(f"\nDiagnoses update success! Response: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


def write_assessment_plan(clinic_id, visit_id, doctor_id, assessments):
    if not assessments:
        print("No assessment found. Skipping assessment-plan update.")
        return

    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/assessment-plan"
    payload = {
        "doctor_id": doctor_id,
        "assessments": assessments,
    }

    print(f"Sending to: {url}")
    print(f"Payload   : {json.dumps(payload, indent=2)}")

    response = requests.put(url, headers=get_headers(), json=payload)
    ensure_success(response, "Assessment-plan update")

    print(f"\nAssessment-plan update success! Response: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


def write_procedures(clinic_id, visit_id, procedures, existing_cpt_codes=None):
    if not procedures:
        print("No linkicd_icd_with_cpt_data found. Skipping procedures update.")
        return

    existing = {str(code).strip().upper() for code in (existing_cpt_codes or set()) if str(code).strip()}
    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/procedures"

    for index, procedure in enumerate(procedures, start=1):
        cpt_code = str(procedure.get("cpt_code") or "").strip().upper()
        if cpt_code and cpt_code in existing:
            print(f"Skipping linked CPT already on visit: {cpt_code}")
            continue

        print(f"Sending to: {url}")
        print(f"Procedure payload {index}/{len(procedures)}: {json.dumps(procedure, indent=2)}")

        response = requests.post(url, headers=get_headers(), json=procedure)
        ensure_success(response, f"Procedures update {index}/{len(procedures)}")

        print(f"\nProcedures update {index}/{len(procedures)} success! Response: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)


def write_basic_cpt_procedures(clinic_id, visit_id, procedures):
    if not procedures:
        print("No standalone cpt_codes found. Skipping basic procedures update.")
        return

    url = f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}/visits/{visit_id}/procedures"

    for index, procedure in enumerate(procedures, start=1):
        print(f"Sending to: {url}")
        print(f"Basic CPT payload {index}/{len(procedures)}: {json.dumps(procedure, indent=2)}")

        response = requests.post(url, headers=get_headers(), json=procedure)
        ensure_success(response, f"Basic procedures update {index}/{len(procedures)}")

        print(f"\nBasic procedures update {index}/{len(procedures)} success! Response: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)


def bulk_update_diagnoses(clinic_id, visit_id, diagnoses):
    if not diagnoses:
        print("No sorted_icd_codes found. Skipping bulk diagnosis update.")
        return

    write_diagnoses(clinic_id, visit_id, diagnoses)


def delete_procedure_by_cpt_id(clinic_id, visit_id, cpt_id, doctor_id):
    url = (
        f"{BASE_URL}/iclinic-encounter/clinical/v1/clinics/{clinic_id}"
        f"/visits/{visit_id}/procedures/{cpt_id}"
    )

    print(f"Deleting procedure cpt_id={cpt_id} via: {url}")
    response = requests.delete(
        url,
        headers=get_headers(),
        params={"doctor_id": doctor_id},
    )
    ensure_success(response, f"Delete procedure {cpt_id}")

    print(f"Delete procedure success! cpt_id={cpt_id} status={response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


def delete_existing_cpts_for_linked_procedures(clinic_id, visit_id, doctor_id, procedures_by_code, linked_procedures):
    if not linked_procedures:
        return

    for procedure in linked_procedures:
        cpt_code = str(procedure.get("cpt_code") or "").strip().upper()
        if not cpt_code:
            continue

        existing_cpt_ids = procedures_by_code.get(cpt_code, [])
        if not existing_cpt_ids:
            continue

        print(f"Deleting existing CPTs before linked insert for {cpt_code}: {existing_cpt_ids}")
        for cpt_id in existing_cpt_ids:
            delete_procedure_by_cpt_id(clinic_id, visit_id, cpt_id, doctor_id)


def update_medical_note_sections(clinic_id, visit_id, doctor_id, note_data):
    complaint_data = load_complaint_data(note_data)
    ros_systems = load_ros_systems(note_data)
    physical_exam_items, skipped_pe_labels = load_physical_exam_items(note_data)
    diagnoses = load_note_diagnoses(note_data)
    assessments = load_assessment_plan_items(note_data)
    existing_procedures = fetch_existing_visit_procedures(clinic_id, visit_id)
    existing_cpt_ids = {
        int(item["cpt_id"])
        for item in existing_procedures
        if item.get("cpt_id") not in (None, "")
    }
    existing_cpt_codes = {
        str(item.get("cpt_code")).strip().upper()
        for item in existing_procedures
        if str(item.get("cpt_code") or "").strip()
    }
    basic_cpt_procedures = load_basic_cpt_procedures(
        note_data,
        existing_cpt_codes=existing_cpt_codes,
    )

    print(f"Complaint text loaded:\n{complaint_data['chief_complaint']}\n")
    if complaint_data.get("present_illness"):
        print(f"Present illness loaded:\n{complaint_data['present_illness']}\n")
    if ros_systems:
        print(f"ROS systems loaded: {len(ros_systems)}\n")
    if physical_exam_items:
        print(f"Physical exam items loaded: {len(physical_exam_items)}\n")
    if diagnoses:
        print(f"Diagnoses loaded: {len(diagnoses)}\n")
    if assessments:
        print(f"Assessment-plan items loaded: {len(assessments)}\n")
    if existing_cpt_ids:
        print(f"Existing visit CPT IDs found: {len(existing_cpt_ids)}\n")
    if basic_cpt_procedures:
        print(f"Basic CPT procedures loaded: {len(basic_cpt_procedures)}\n")
    if skipped_pe_labels:
        print(f"Skipped PE labels (no exact approved match): {', '.join(skipped_pe_labels)}\n")

    write_complaint(clinic_id, visit_id, doctor_id, complaint_data)
    write_ros(clinic_id, visit_id, doctor_id, ros_systems)
    write_physical_exam(clinic_id, visit_id, doctor_id, physical_exam_items)
    bulk_update_diagnoses(clinic_id, visit_id, diagnoses)
    write_assessment_plan(clinic_id, visit_id, doctor_id, assessments)
    write_basic_cpt_procedures(clinic_id, visit_id, basic_cpt_procedures)


def sync_sorted_codes_and_procedure_links(clinic_id, visit_id, doctor_id, coding_data):
    diagnoses = load_diagnoses(coding_data)
    # For workflow 2, CPT work comes only from linkicd_icd_with_cpt_data.
    # sorted_cpt_codes is ordering/reference data and is not posted separately.
    existing_procedures = fetch_existing_visit_procedures(clinic_id, visit_id)
    procedures_by_code = build_procedure_code_index(existing_procedures)
    procedures = load_procedures(coding_data)
    deleted_cpt_codes = load_deleted_cpt_codes(coding_data)

    if diagnoses:
        print(f"Sorted diagnoses loaded: {len(diagnoses)}\n")
    if procedures_by_code:
        print(f"Existing visit CPT codes found before linked CPT sync: {len(procedures_by_code)}\n")
    if procedures:
        print(f"Linked procedures loaded: {len(procedures)}\n")
    if deleted_cpt_codes:
        print(f"Deleted CPT codes loaded: {len(deleted_cpt_codes)}\n")

    bulk_update_diagnoses(clinic_id, visit_id, diagnoses)
    delete_existing_cpts_for_linked_procedures(
        clinic_id,
        visit_id,
        doctor_id,
        procedures_by_code,
        procedures,
    )

    procedures_after_delete = fetch_existing_visit_procedures(clinic_id, visit_id)
    existing_cpt_codes_after_delete = {
        str(item.get("cpt_code") or "").strip().upper()
        for item in procedures_after_delete
        if str(item.get("cpt_code") or "").strip()
    }
    write_procedures(
        clinic_id,
        visit_id,
        procedures,
        existing_cpt_codes=existing_cpt_codes_after_delete,
    )

    refreshed_procedures = fetch_existing_visit_procedures(clinic_id, visit_id)
    procedures_by_code = build_procedure_code_index(refreshed_procedures)

    if procedures_by_code:
        print(f"Current visit procedure codes indexed: {len(procedures_by_code)}\n")

    for deleted_code in deleted_cpt_codes:
        cpt_ids = procedures_by_code.get(deleted_code, [])
        if not cpt_ids:
            print(f"Deleted CPT not found on visit, skipping: {deleted_code}")
            continue

        for cpt_id in cpt_ids:
            delete_procedure_by_cpt_id(clinic_id, visit_id, cpt_id, doctor_id)


def select_update_workflow():
    options = {
        "1": ("medical_note_sections", update_medical_note_sections),
        "2": ("sorted_codes_and_procedure_links", sync_sorted_codes_and_procedure_links),
    }

    if len(sys.argv) > 1:
        raw_choice = sys.argv[1].strip().lower()
        aliases = {
            "1": "1",
            "note": "1",
            "medical_note_sections": "1",
            "2": "2",
            "coding": "2",
            "sorted_codes_and_procedure_links": "2",
        }
        selected_key = aliases.get(raw_choice)
        if selected_key:
            return options[selected_key]
        raise ValueError(
            "Invalid mode. Use 1|note|medical_note_sections or 2|coding|sorted_codes_and_procedure_links."
        )

    print("Select workflow to run:")
    print("1. medical_note_sections")
    print("2. sorted_codes_and_procedure_links")

    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice in options:
            return options[choice]
        print("Invalid choice. Enter 1 or 2.")


def main():
    input_data = load_input_json(INPUT_JSON_FILE)
    workflow_name, workflow_fn = select_update_workflow()
    print(f"Running workflow: {workflow_name}\n")
    workflow_fn(CLINIC_ID, VISIT_ID, DOCTOR_ID, input_data)


if __name__ == "__main__":
    main()
