from datetime import date, datetime, time
from typing import Any


def _as_date(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        normalized = value.date().isoformat()
        return None if normalized == "0000-00-00" else normalized
    if isinstance(value, date):
        normalized = value.isoformat()
        return None if normalized == "0000-00-00" else normalized
    normalized = str(value)[:10]
    if normalized in {"0000-00-00", "0000-00-0", "0000-00", "0000-0"}:
        return None
    return normalized


def _as_time(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.time().replace(microsecond=0).isoformat()
    if isinstance(value, time):
        return value.replace(microsecond=0).isoformat()
    return str(value)[:8]


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _split_items(value: Any) -> list[str]:
    text = _as_text(value)
    if not text:
        return []
    normalized = text.replace("\r", "\n").replace(";", "\n").replace(",", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _gender_name(value: Any) -> str | None:
    text = _as_text(value)
    if text == "1":
        return "Male"
    if text == "2":
        return "Female"
    return text


def _blood_type(value: Any) -> str | None:
    text = _as_text(value)
    if not text:
        return None
    return text.upper()


def _bp(row: dict[str, Any]) -> str | None:
    systolic = _as_text(row.get("bps"))
    diastolic = _as_text(row.get("bpd"))
    if systolic and diastolic:
        return f"{systolic}/{diastolic}"
    return systolic or diastolic


def _medication_category(row: dict[str, Any]) -> str | None:
    category = _as_text(row.get("category"))
    if category:
        return category
    item_type = _as_text(row.get("item_type"))
    if item_type:
        return item_type
    return "medication"


def web_app_patient(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "hn": _as_text(row.get("hn")),
        "cid": _as_text(row.get("cid")),
        "first_name": _as_text(row.get("first_name") or row.get("fname")),
        "last_name": _as_text(row.get("last_name") or row.get("lname")),
        "gender": _gender_name(row.get("gender") or row.get("sex")),
        "birth_date": _as_date(row.get("birth_date") or row.get("birthday")),
        "reported_age": _as_int(row.get("reported_age") or row.get("current_agey")),
        "blood_type": _blood_type(row.get("blood_type") or row.get("bloodgrp")),
        "phone_number": _as_text(row.get("phone_number") or row.get("hometel")),
        "district": _as_text(row.get("district")),
        "province": _as_text(row.get("province")),
    }


def web_patient_conditions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    for row in rows:
        for condition_name in _split_items(row.get("condition_name") or row.get("name")):
            conditions.append(
                {
                    "condition_name": condition_name,
                    "item_order": len(conditions) + 1,
                }
            )
    return conditions


def web_patient_allergies(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allergies: list[dict[str, Any]] = []
    for row in rows:
        for allergy_name in _split_items(row.get("allergy_name") or row.get("agent")):
            allergies.append(
                {
                    "allergy_name": allergy_name,
                    "item_order": len(allergies) + 1,
                }
            )
    return allergies


def web_case_register(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "an": _as_text(row.get("an")),
        "hospital": _as_text(row.get("hospital")),
        "record_date": _as_date(row.get("record_date") or row.get("admit_date")),
        "record_time": _as_time(row.get("record_time") or row.get("admit_time")),
        "status": _as_text(row.get("status")) or "Pending",
        "priority": _as_text(row.get("priority")) or "URGENT",
        "specialty": _as_text(row.get("specialty")),
        "reason": _as_text(row.get("reason") or row.get("porv_dx")),
        "current_symptoms": _as_text(row.get("current_symptoms")),
        "initial_diagnosis": _as_text(row.get("initial_diagnosis") or row.get("porv_dx")),
        "clinical_notes": _as_text(row.get("clinical_notes") or row.get("ward")),
        "sender_id": _as_text(row.get("sender_id")),
        "last_action": _as_text(row.get("last_action")) or "Imported from HOSxP",
        "last_active_time": _as_text(row.get("last_active_time")),
    }


def web_case_workflow_episodes(row: dict[str, Any]) -> list[dict[str, Any]]:
    status = _as_text(row.get("status")) or "Pending"
    action = _as_text(row.get("last_action")) or "Created"
    record_date = _as_date(row.get("record_date") or row.get("admit_date"))
    record_time = _as_time(row.get("record_time") or row.get("admit_time")) or "00:00:00"
    created_at = f"{record_date}T{record_time}" if record_date else None

    return [
        {
            "episode_type": "request",
            "status": status,
            "action": action,
            "actor_id": _as_text(row.get("sender_id")),
            "note": "Imported from HOSxP by ICU-Sync",
            "created_at": created_at,
        }
    ]


def web_case_vitals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_date": _as_date(row.get("record_date") or row.get("vital_date")),
            "record_time": _as_time(row.get("record_time") or row.get("vital_time")),
            "bp": _bp(row),
            "hr": _as_text(row.get("hr") or row.get("pulse")),
            "temp": _as_text(row.get("temp") or row.get("temperature")),
            "rr": _as_text(row.get("rr") or row.get("respiratory_rate")),
            "spo2": _as_text(row.get("spo2")),
            "gcs": _as_text(row.get("gcs")),
        }
        for row in rows
        if _as_date(row.get("record_date") or row.get("vital_date"))
    ]


def web_case_labs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "lab_date": _as_date(row.get("lab_date") or row.get("order_date")),
            "lab_time": _as_time(row.get("lab_time") or row.get("order_time")),
            "name": _as_text(row.get("name") or row.get("lab_items_name")) or "",
            "result": _as_text(row.get("result") or row.get("lab_order_result")),
            "unit": _as_text(row.get("unit") or row.get("lab_items_unit")),
            "ref_range": _as_text(row.get("ref_range") or row.get("lab_order_normal_value")),
            "status": _as_text(row.get("status")),
        }
        for row in rows
        if _as_date(row.get("lab_date") or row.get("order_date"))
        and _as_text(row.get("name") or row.get("lab_items_name"))
    ]


def web_case_medications(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "start_date": _as_date(row.get("start_date") or row.get("rxdate")),
            "start_time": _as_time(row.get("start_time") or row.get("rxtime")),
            "name": _as_text(row.get("name") or row.get("item_name")) or "",
            "dose": _as_text(row.get("dose") or row.get("qty")),
            "freq": _as_text(row.get("freq") or row.get("usage_name")),
            "route": _as_text(row.get("route")),
            "category": _medication_category(row),
        }
        for row in rows
        if _as_date(row.get("start_date") or row.get("rxdate"))
        and _as_text(row.get("name") or row.get("item_name"))
    ]


def web_case_payload(
    admission_row: dict[str, Any],
    condition_rows: list[dict[str, Any]],
    allergy_rows: list[dict[str, Any]],
    vital_rows: list[dict[str, Any]],
    lab_rows: list[dict[str, Any]],
    medication_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "app_patient": web_app_patient(admission_row),
        "app_patient_condition": web_patient_conditions(condition_rows),
        "patient_allergy": web_patient_allergies(allergy_rows),
        "case_register": web_case_register(admission_row),
        "case_workflow_episode": web_case_workflow_episodes(admission_row),
        "case_vital": web_case_vitals(vital_rows),
        "case_lab": web_case_labs(lab_rows),
        "case_medication": web_case_medications(medication_rows),
        "case_note": [],
        "case_file": [],
    }
