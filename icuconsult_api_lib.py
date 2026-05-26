from dataclasses import dataclass
from typing import Any

import requests

from setting_lib import (
    AppSettings,
    DEFAULT_ICUCONS_API_ENDPOINT,
    normalize_icucons_api_endpoint,
)


@dataclass(slots=True)
class IcuconsultSyncResult:
    success: bool
    case_id: str | None
    inserted: dict[str, Any]
    response: dict[str, Any]


class IcuconsultApiClient:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def sync_case(self, schema_payload: dict[str, Any]) -> IcuconsultSyncResult:
        response = requests.post(
            self.endpoint_url(),
            json=api_payload_from_schema(schema_payload),
            headers=self._headers(),
            timeout=self.settings.icucons_timeout,
        )
        response_data = self._response_json(response)
        if response.status_code >= 400:
            raise ValueError(self._error_message(response, response_data))
        if not response_data.get("success"):
            raise ValueError(response_data.get("error") or "ICUCONS sync failed.")
        return IcuconsultSyncResult(
            success=bool(response_data.get("success")),
            case_id=_as_text(response_data.get("caseId")),
            inserted=response_data.get("inserted") or {},
            response=response_data,
        )

    def endpoint_url(self) -> str:
        return normalize_icucons_api_endpoint(
            self.settings.icucons_api_endpoint.strip() or DEFAULT_ICUCONS_API_ENDPOINT
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        token = self.settings.icucons_api_token.strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["x-api-key"] = token
        return headers

    def _response_json(self, response: requests.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}

    def _error_message(
        self,
        response: requests.Response,
        response_data: dict[str, Any],
    ) -> str:
        server_message = _as_text(response_data.get("error") or response_data.get("message"))
        if not server_message:
            server_message = _as_text(response.text)
        prefix = f"ICUCONS API error {response.status_code}"
        if server_message:
            return f"{prefix}: {server_message}"
        return f"{prefix}: {response.reason}"


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _full_name(patient: dict[str, Any]) -> str:
    first_name = _as_text(patient.get("first_name"))
    last_name = _as_text(patient.get("last_name"))
    full_name = " ".join(part for part in [first_name, last_name] if part)
    if full_name:
        return full_name
    return _as_text(patient.get("hn")) or _as_text(patient.get("cid")) or "Unknown patient"


def _recorded_at(row: dict[str, Any], date_key: str, time_key: str) -> str | None:
    record_date = _as_text(row.get(date_key))
    if not record_date or record_date == "0000-00-00":
        return None
    record_time = _as_text(row.get(time_key)) or "00:00:00"
    return f"{record_date}T{record_time}+07:00"


def _items(rows: list[dict[str, Any]], key: str) -> list[str]:
    values: list[str] = []
    for row in rows:
        value = _as_text(row.get(key))
        if value:
            values.append(value)
    return values


def _compact_dict(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value not in (None, "", [])}


def _compact_list(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [compact_row for row in rows if (compact_row := _compact_dict(row))]


def api_payload_from_schema(schema_payload: dict[str, Any]) -> dict[str, Any]:
    patient = schema_payload.get("app_patient") or {}
    case_register = schema_payload.get("case_register") or {}
    conditions = schema_payload.get("app_patient_condition") or []
    allergies = schema_payload.get("patient_allergy") or []

    return _compact_dict(
        {
            "patient": _compact_dict(
                {
                    "hn": patient.get("hn"),
                    "cid": patient.get("cid"),
                    "firstName": patient.get("first_name"),
                    "lastName": patient.get("last_name"),
                    "name": _full_name(patient),
                    "gender": patient.get("gender"),
                    "dob": patient.get("birth_date"),
                    "age": patient.get("reported_age"),
                    "bloodType": patient.get("blood_type"),
                    "phone": patient.get("phone_number"),
                    "district": patient.get("district"),
                    "province": patient.get("province"),
                    "conditions": _items(conditions, "condition_name"),
                    "allergies": _items(allergies, "allergy_name"),
                }
            ),
            "case": _compact_dict(
                {
                    "an": case_register.get("an"),
                    "hospital": case_register.get("hospital"),
                    "priority": case_register.get("priority"),
                    "specialty": case_register.get("specialty"),
                    "reason": case_register.get("reason"),
                    "presentIllness": case_register.get("current_symptoms"),
                    "initialDiagnosis": case_register.get("initial_diagnosis"),
                    "clinicalNotes": case_register.get("clinical_notes"),
                    "senderId": case_register.get("sender_id"),
                }
            ),
            "vitals": _compact_list(
                [
                    {
                        "recordedAt": _recorded_at(vital, "record_date", "record_time"),
                        "bp": vital.get("bp"),
                        "hr": vital.get("hr"),
                        "temp": vital.get("temp"),
                        "rr": vital.get("rr"),
                        "spo2": vital.get("spo2"),
                        "gcs": vital.get("gcs"),
                    }
                    for vital in schema_payload.get("case_vital", [])
                ]
            ),
            "labs": _compact_list(
                [
                    {
                        "name": lab.get("name"),
                        "result": lab.get("result"),
                        "unit": lab.get("unit"),
                        "refRange": lab.get("ref_range"),
                        "status": lab.get("status"),
                    }
                    for lab in schema_payload.get("case_lab", [])
                    if _as_text(lab.get("name"))
                ]
            ),
            "medications": _compact_list(
                [
                    {
                        "start": medication.get("start_date"),
                        "name": medication.get("name"),
                        "dose": medication.get("dose"),
                        "freq": medication.get("freq"),
                        "route": medication.get("route"),
                        "category": medication.get("category"),
                    }
                    for medication in schema_payload.get("case_medication", [])
                    if _as_text(medication.get("name"))
                ]
            ),
            "notes": _compact_list(
                [
                    {
                        "body": note.get("note_text"),
                        "authorId": note.get("provider_id_do_note"),
                        "authorColor": note.get("color"),
                    }
                    for note in schema_payload.get("case_note", [])
                    if _as_text(note.get("note_text"))
                ]
            ),
        }
    )
