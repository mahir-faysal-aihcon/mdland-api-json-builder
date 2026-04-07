# API Collection README

This folder contains Python scripts that orchestrate multiple MDLand Partner APIs and generate final JSON outputs from three mother inputs:

- `clinic_id`
- `patient_id`
- `dos` (date of service)

## Files

- `patient_charting&pre_visit_summary.py`
  - Builds combined output with:
    - `patient_charting`
    - `previsit_summary`
  - Writes: `patient_<patient_id>_<clinic_id>.json`

- `patient_coding.py`
  - Builds header/previsit coding output
  - Writes: `header_data_<patient_id>_<clinic_id>.json`

## Inputs You Set In Script

In each script, update:

- `BEARER_TOKEN` (paste fresh token)
- `BASE_URL` (currently dev partner API base)
- `CLINIC_ID`
- `PATIENT_ID`
- `DOS`

`DOS` supports `YYYY-MM-DD` and `MM/DD/YYYY`.

## Setup

```powershell
cd "c:\VS Studio\Api collection"
python -m pip install requests
```

## Run

PowerShell note: `&` in filename needs quotes.

```powershell
python ".\patient_charting&pre_visit_summary.py"
python .\patient_coding.py
```

## Core Data Flow (DOS-Matched)

Both scripts follow this pattern for visit-specific fields:

1. Call **List Visits** using `clinic_id + patient_id`
2. Find visit where `visit_date == DOS`
3. Take that `visit_id`
4. Call **Get Visit Detail** (and related visit endpoints)
5. Build output fields from that matched visit context

## Main API Groups Used

- Demographic
- Insurance
- Visits / Visit Detail / Visit Vitals / Visit Screenings
- Active Medications
- ICD history
- CPT history
- Claims (billing/payment history)
- Laboratory Orders + Order Detail

## Output Overview

### `patient_<patient_id>_<clinic_id>.json`
Contains:

- `patient_charting`
  - demographics
  - insurance fields
  - visit type / reason for visit / HPI
  - vital signs
  - active medications
  - lab history
- `previsit_summary`
  - current ICDs
  - historical ICDs
  - last 3 visit ICD/CPT history
  - last blood work / EKG date
  - DOS-year ICD/CPT map

### `header_data_<patient_id>_<clinic_id>.json`
Contains:

- header info (DOB, gender, age, insurance, DOS, visit type)
- DOS-year ICD/CPT code calendar map
- old/new patient flag
- preventive and counseling recency blocks
- smoking history
- payment history
- laborders flags
- screening block (from visit screenings)
- CPT date metrics (`cptdates`)
- ICD/CPT with CPT modifiers

## Common Errors

- `401 Unauthorized`
  - Token expired. Paste a fresh bearer token and rerun.

- `404 Not Found` for ICD/CPT history
  - Environment route mismatch can happen (`/metadata/...` vs non-metadata route).
  - Scripts already try known alternatives in current implementation.

- `No visit found for DOS`
  - DOS does not match any `visit_date` from List Visits.

## Naming Suggestion (Meaningful Output)

If you want more meaningful filenames, include DOS:

- `patient_charting_<patient_id>_<clinic_id>_<YYYY-MM-DD>.json`
- `header_data_<patient_id>_<clinic_id>_<YYYY-MM-DD>.json`

Use normalized DOS (`YYYY-MM-DD`) to keep sorting clean.

## Security Note

Do not commit live bearer tokens into git.
Use a placeholder in code and paste token only when running locally.
