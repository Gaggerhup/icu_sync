from contextlib import contextmanager
from typing import Any

from icucons_schema_lib import web_case_payload
from setting_lib import AppSettings


class HosxpConnectionError(RuntimeError):
    """Raised when the HOSxP database connection cannot be opened."""


def _load_pymysql():
    import pymysql
    from pymysql.cursors import DictCursor

    return pymysql, DictCursor


def _driver_error_message(exc: Exception) -> str:
    if len(exc.args) >= 2:
        return f"{exc.args[0]} - {exc.args[1]}"
    return str(exc) or exc.__class__.__name__


def format_hosxp_connection_error(settings: AppSettings, exc: Exception) -> str:
    return (
        "ไม่สามารถเชื่อมต่อฐานข้อมูล HOSxP ได้\n\n"
        f"Host: {settings.hosxp_host}:{settings.hosxp_port}\n"
        f"Database: {settings.hosxp_database or '-'}\n"
        f"User: {settings.hosxp_user or '-'}\n\n"
        f"Error: {_driver_error_message(exc)}"
    )


class HosxpClient:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    @contextmanager
    def connection(self):
        try:
            pymysql, dict_cursor = _load_pymysql()
            conn = pymysql.connect(
                host=self.settings.hosxp_host,
                port=self.settings.hosxp_port,
                user=self.settings.hosxp_user,
                password=self.settings.hosxp_password,
                database=self.settings.hosxp_database,
                charset="utf8mb4",
                cursorclass=dict_cursor,
                autocommit=True,
            )
        except Exception as exc:
            raise HosxpConnectionError(
                format_hosxp_connection_error(self.settings, exc)
            ) from exc

        try:
            yield conn
        finally:
            conn.close()

    def fetch_admitted_patients(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        sql = """
            SELECT
                i.regdate AS admit_date,
                i.regtime AS admit_time,
                p.cid,
                i.an,
                i.hn,
                p.fname AS first_name,
                p.lname AS last_name,
                p.sex AS gender,
                p.birthday AS birth_date,
                p.bloodgrp AS blood_type,
                p.hometel AS phone_number,
                CONCAT(COALESCE(p.pname, ''), COALESCE(p.fname, ''), ' ', COALESCE(p.lname, '')) AS fullname,
                TIMESTAMPDIFF(YEAR, p.birthday, CURDATE()) AS current_agey,
                MOD(TIMESTAMPDIFF(MONTH, p.birthday, CURDATE()), 12) AS age_mon,
                COALESCE(i.provision_dx, i.provision_dx_icd, '') AS porv_dx,
                COALESCE(i.provision_dx, i.provision_dx_icd, '') AS initial_diagnosis,
                COALESCE(w.name, i.ward, '') AS ward
            FROM ipt i
            JOIN patient p ON p.hn = i.hn
            LEFT JOIN ward w ON w.ward = i.ward
            WHERE i.regdate BETWEEN %s AND %s
            ORDER BY i.regdate DESC, i.regtime DESC, i.an DESC
        """
        return self._fetch_all(sql, (start_date, end_date))

    def test_connection(self) -> None:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                cursor.fetchone()

    def fetch_rx(self, an: str) -> list[dict[str, Any]]:
        sql = """
            SELECT
                o.rxdate,
                o.rxtime,
                o.icode,
                COALESCE(d.name, o.item_type, '') AS item_name,
                o.qty,
                COALESCE(du.name1, o.drugusage, '') AS usage_name,
                o.item_type
            FROM opitemrece o
            LEFT JOIN drugitems d ON d.icode = o.icode
            LEFT JOIN drugusage du ON du.drugusage = o.drugusage
            WHERE o.an = %s
            ORDER BY o.rxdate DESC, o.rxtime DESC, o.icode
        """
        return self._fetch_all(sql, (an,))

    def fetch_vital_sign(self, an: str, hn: str) -> list[dict[str, Any]]:
        queries = [
            (
                """
                SELECT
                    DATE(v.vital_sign_datetime) AS vital_date,
                    TIME(v.vital_sign_datetime) AS vital_time,
                    MAX(CASE WHEN v.vital_sign_id = 1 THEN v.vital_sign_value END) AS temperature,
                    COALESCE(
                        MAX(CASE WHEN v.vital_sign_id = 10 THEN v.vital_sign_value END),
                        MAX(CASE WHEN v.vital_sign_id = 2 THEN v.vital_sign_value END)
                    ) AS pulse,
                    MAX(CASE WHEN v.vital_sign_id = 3 THEN v.vital_sign_value END) AS respiratory_rate,
                    MAX(CASE WHEN v.vital_sign_id = 4 THEN v.vital_sign_value END) AS bps,
                    MAX(CASE WHEN v.vital_sign_id = 5 THEN v.vital_sign_value END) AS bpd,
                    NULL AS spo2
                FROM ipt_vital_sign v
                WHERE an = %s
                GROUP BY v.vital_sign_datetime
                ORDER BY vital_date DESC, vital_time DESC
                """,
                (an,),
            ),
            (
                """
                SELECT
                    h.ipt_vital_sign_history_date AS vital_date,
                    h.ipt_vital_sign_history_time AS vital_time,
                    MAX(CASE WHEN d.vital_sign_id = 1 THEN d.vital_sign_value END) AS temperature,
                    COALESCE(
                        MAX(CASE WHEN d.vital_sign_id = 10 THEN d.vital_sign_value END),
                        MAX(CASE WHEN d.vital_sign_id = 2 THEN d.vital_sign_value END)
                    ) AS pulse,
                    MAX(CASE WHEN d.vital_sign_id = 3 THEN d.vital_sign_value END) AS respiratory_rate,
                    MAX(CASE WHEN d.vital_sign_id = 4 THEN d.vital_sign_value END) AS bps,
                    MAX(CASE WHEN d.vital_sign_id = 5 THEN d.vital_sign_value END) AS bpd,
                    NULL AS spo2
                FROM ipt_vital_sign_history h
                JOIN ipt_vital_sign_history_detail d
                    ON d.ipt_vital_sign_history_id = h.ipt_vital_sign_history_id
                WHERE h.an = %s
                GROUP BY
                    h.ipt_vital_sign_history_id,
                    h.ipt_vital_sign_history_date,
                    h.ipt_vital_sign_history_time
                ORDER BY vital_date DESC, vital_time DESC
                """,
                (an,),
            ),
            (
                """
                SELECT
                    DATE(note_datetime) AS vital_date,
                    TIME(note_datetime) AS vital_time,
                    temperature,
                    COALESCE(heart_rate, pulse) AS pulse,
                    respiratory_rate,
                    bp_systolic AS bps,
                    bp_diastolic AS bpd,
                    COALESCE(spo2_ra, spo2_o2) AS spo2
                FROM ipd_nurse_note
                WHERE an = %s
                ORDER BY note_datetime DESC
                """,
                (an,),
            ),
            (
                """
                SELECT
                    o.vstdate AS vital_date,
                    o.vsttime AS vital_time,
                    s.temperature,
                    s.pulse,
                    s.rr AS respiratory_rate,
                    s.bps,
                    s.bpd,
                    s.o2sat AS spo2
                FROM ipt i
                JOIN ovst o ON o.vn = i.vn
                LEFT JOIN opdscreen s ON s.vn = o.vn
                WHERE i.an = %s AND i.hn = %s
                ORDER BY o.vstdate DESC, o.vsttime DESC
                """,
                (an, hn),
            ),
        ]
        return self._fetch_first_non_empty_success(queries)

    def fetch_lab(self, an: str, hn: str) -> list[dict[str, Any]]:
        queries = [
            (
                """
                SELECT
                    lh.order_date,
                    lh.order_time,
                    lo.lab_items_code,
                    COALESCE(li.lab_items_name, lo.lab_items_name_ref, '') AS lab_items_name,
                    lo.lab_order_result,
                    li.lab_items_unit,
                    COALESCE(lo.lab_items_normal_value_ref, li.lab_items_normal_value, '') AS lab_order_normal_value
                FROM lab_head lh
                JOIN ipt i ON i.vn = lh.vn
                JOIN lab_order lo ON lo.lab_order_number = lh.lab_order_number
                LEFT JOIN lab_items li ON li.lab_items_code = lo.lab_items_code
                WHERE i.an = %s AND i.hn = %s
                ORDER BY lh.order_date DESC, lh.order_time DESC, lab_items_name
                """,
                (an, hn),
            ),
            (
                """
                SELECT
                    lh.order_date,
                    lh.order_time,
                    lo.lab_items_code,
                    COALESCE(li.lab_items_name, lo.lab_items_name_ref, '') AS lab_items_name,
                    lo.lab_order_result,
                    li.lab_items_unit,
                    COALESCE(lo.lab_items_normal_value_ref, li.lab_items_normal_value, '') AS lab_order_normal_value
                FROM ipt i
                JOIN lab_head lh
                    ON lh.hn = i.hn
                    AND lh.order_date BETWEEN i.regdate AND COALESCE(NULLIF(i.dchdate, '0000-00-00'), CURDATE())
                JOIN lab_order lo ON lo.lab_order_number = lh.lab_order_number
                LEFT JOIN lab_items li ON li.lab_items_code = lo.lab_items_code
                WHERE i.an = %s AND i.hn = %s
                ORDER BY lh.order_date DESC, lh.order_time DESC, lab_items_name
                """,
                (an, hn),
            ),
            (
                """
                SELECT
                    lh.order_date,
                    lh.order_time,
                    lo.lab_items_code,
                    COALESCE(li.lab_items_name, lo.lab_items_name_ref, '') AS lab_items_name,
                    lo.lab_order_result,
                    li.lab_items_unit,
                    COALESCE(lo.lab_items_normal_value_ref, li.lab_items_normal_value, '') AS lab_order_normal_value
                FROM lab_head lh
                JOIN lab_order lo ON lo.lab_order_number = lh.lab_order_number
                LEFT JOIN lab_items li ON li.lab_items_code = lo.lab_items_code
                WHERE lh.hn = %s
                ORDER BY lh.order_date DESC, lh.order_time DESC, lab_items_name
                LIMIT 300
                """,
                (hn,),
            ),
        ]
        return self._fetch_first_non_empty_success(queries)

    def fetch_admission_case(self, an: str, hn: str | None = None) -> dict[str, Any] | None:
        queries = [
            (
                """
                SELECT
                    i.regdate AS admit_date,
                    i.regtime AS admit_time,
                    p.cid,
                    i.an,
                    i.hn,
                    p.fname AS first_name,
                    p.lname AS last_name,
                    p.sex AS gender,
                    p.birthday AS birth_date,
                    p.bloodgrp AS blood_type,
                    p.hometel AS phone_number,
                    CONCAT(COALESCE(p.pname, ''), COALESCE(p.fname, ''), ' ', COALESCE(p.lname, '')) AS fullname,
                    TIMESTAMPDIFF(YEAR, p.birthday, CURDATE()) AS current_agey,
                    COALESCE(i.provision_dx, i.provision_dx_icd, '') AS porv_dx,
                    COALESCE(i.provision_dx, i.provision_dx_icd, '') AS initial_diagnosis,
                    COALESCE(w.name, i.ward, '') AS ward,
                    'Pending' AS status,
                    'URGENT' AS priority,
                    'Imported from HOSxP' AS last_action
                FROM ipt i
                JOIN patient p ON p.hn = i.hn
                LEFT JOIN ward w ON w.ward = i.ward
                WHERE i.an = %s
                LIMIT 1
                """,
                (an,),
            ),
            (
                """
                SELECT
                    NULL AS admit_date,
                    NULL AS admit_time,
                    p.cid,
                    NULL AS an,
                    p.hn,
                    p.fname AS first_name,
                    p.lname AS last_name,
                    p.sex AS gender,
                    p.birthday AS birth_date,
                    p.bloodgrp AS blood_type,
                    p.hometel AS phone_number,
                    CONCAT(COALESCE(p.pname, ''), COALESCE(p.fname, ''), ' ', COALESCE(p.lname, '')) AS fullname,
                    TIMESTAMPDIFF(YEAR, p.birthday, CURDATE()) AS current_agey,
                    '' AS porv_dx,
                    '' AS initial_diagnosis,
                    '' AS ward,
                    'Pending' AS status,
                    'URGENT' AS priority,
                    'Imported from HOSxP' AS last_action
                FROM patient p
                WHERE p.hn = %s
                LIMIT 1
                """,
                (hn or "",),
            ),
        ]
        rows = self._fetch_first_success(queries)
        return rows[0] if rows else None

    def fetch_conditions(self, hn: str) -> list[dict[str, Any]]:
        queries = [
            (
                """
                SELECT COALESCE(c.name, ch.icd10, ch.clinic, '') AS condition_name
                FROM chronic ch
                LEFT JOIN clinic c ON c.clinic = ch.clinic
                WHERE ch.hn = %s
                ORDER BY condition_name
                """,
                (hn,),
            ),
            (
                """
                SELECT COALESCE(icd10, clinic, '') AS condition_name
                FROM chronic
                WHERE hn = %s
                ORDER BY condition_name
                """,
                (hn,),
            ),
        ]
        return self._fetch_first_success_or_empty(queries)

    def fetch_allergies(self, hn: str) -> list[dict[str, Any]]:
        queries = [
            (
                """
                SELECT COALESCE(agent, symptom, note, '') AS allergy_name
                FROM opd_allergy
                WHERE hn = %s
                ORDER BY COALESCE(report_date, update_datetime) DESC, allergy_name
                """,
                (hn,),
            ),
            (
                """
                SELECT COALESCE(agent, '') AS allergy_name
                FROM opd_allergy
                WHERE hn = %s
                ORDER BY allergy_name
                """,
                (hn,),
            ),
        ]
        return self._fetch_first_success_or_empty(queries)

    def fetch_web_case_payload(self, an: str, hn: str | None = None) -> dict[str, Any]:
        admission_row = self.fetch_admission_case(an, hn)
        if not admission_row:
            raise ValueError(f"No HOSxP admission found for AN {an}.")

        resolved_hn = str(admission_row.get("hn") or hn or "")
        resolved_an = str(admission_row.get("an") or an or "")
        return web_case_payload(
            admission_row,
            self.fetch_conditions(resolved_hn),
            self.fetch_allergies(resolved_hn),
            self.fetch_vital_sign(resolved_an, resolved_hn),
            self.fetch_lab(resolved_an, resolved_hn),
            self.fetch_rx(resolved_an),
        )

    def _fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return list(cursor.fetchall())

    def _fetch_first_success(
        self,
        queries: list[tuple[str, tuple[Any, ...]]],
    ) -> list[dict[str, Any]]:
        last_error: Exception | None = None
        for sql, params in queries:
            try:
                return self._fetch_all(sql, params)
            except Exception as exc:
                if not self._is_schema_error(exc):
                    raise
                last_error = exc
        if last_error:
            raise last_error
        return []

    def _fetch_first_non_empty_success(
        self,
        queries: list[tuple[str, tuple[Any, ...]]],
    ) -> list[dict[str, Any]]:
        last_rows: list[dict[str, Any]] = []
        last_error: Exception | None = None
        for sql, params in queries:
            try:
                rows = self._fetch_all(sql, params)
            except Exception as exc:
                if not self._is_schema_error(exc):
                    raise
                last_error = exc
                continue
            if rows:
                return rows
            last_rows = rows
        if last_error and not last_rows:
            raise last_error
        return last_rows

    def _fetch_first_success_or_empty(
        self,
        queries: list[tuple[str, tuple[Any, ...]]],
    ) -> list[dict[str, Any]]:
        try:
            return self._fetch_first_success(queries)
        except Exception as exc:
            if self._is_schema_error(exc):
                return []
            raise

    def _is_schema_error(self, exc: Exception) -> bool:
        if exc.__class__.__name__ in {"ProgrammingError", "OperationalError"}:
            error_code = exc.args[0] if exc.args else None
            return error_code in {1054, 1146}
        return False
