## Patient Profile
    dev
        - POST http://localhost:3000/api/icu
    
    production
        - POST https://icucons.plkhealth.go.th/api/icu

## DX
    dev
        - POST http://localhost:3000/api/icu
    
    production
        - POST https://icucons.plkhealth.go.th/api/icu

## RX
    dev
        - POST http://localhost:3000/api/icu
    
    production
        - POST https://icucons.plkhealth.go.th/api/icu

## LAB
    dev
        - POST http://localhost:3000/api/icu
    
    production
        - POST https://icucons.plkhealth.go.th/api/icu

## Vital Sign
    dev
        - POST http://localhost:3000/api/icu
    
    production
        - POST https://icucons.plkhealth.go.th/api/icu

## Current sync contract

ICU-Sync sends one combined request per selected HOSxP admission.

- Desktop setting default base URL: `https://icucons.plkhealth.go.th`
- Desktop setting default API path: `/api/icu`
- If the web app sets `ICU_API_TOKEN`, the desktop app must set the same token in Settings.
- Token is sent as both `Authorization: Bearer <token>` and `x-api-key: <token>`.
- The web route maps the request into the ICUCONS database schema:
  - `app_patient`
  - `patient_allergy`
  - `app_patient_condition`
  - `case_register`
  - `case_workflow_episode`
  - `case_vital`
  - `case_lab`
  - `case_medication`
- `case.reason` maps to the web app's `chiefComplaint`.
- `case.current_symptoms` maps to the web app's `presentIllness`.
- Sync is import/upsert only. The desktop app does not request deletion from
  the web database.
