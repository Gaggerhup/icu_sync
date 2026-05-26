# ICU-Sync Module Specification

เอกสารนี้บรรยายหน้าที่ของแต่ละ module ใน repo `icu_sync` เพื่อให้การพัฒนา UI, logic, database access, และ integration แยกขอบเขตกันชัดเจน

## Module Overview

### Runtime Dependencies

- ใช้ `PyQt6==6.9.1` เพื่อให้ macOS platform plugin `cocoa` โหลดได้เสถียรใน `.venv` นี้

### `start.py`

Entry point หลักของโปรแกรม

- import `main` จาก `Main_logic.py`
- ใช้สำหรับ run application ด้วยคำสั่ง `uv run start.py`
- ต้อง run ภายใต้ virtual environment ของ repo นี้เท่านั้น (`.venv` ที่จัดการด้วย `uv`)
- ห้าม run ด้วย global Python หรือ virtual environment อื่น
- ตั้งค่า `tool.uv.package = false` เพื่อให้ `uv run start.py` รัน script โดยไม่ติดขั้น build editable package
- ติดตั้ง console exception hook เพื่อแสดง traceback ของ error ที่ไม่ถูก handle ลง `stderr`
- เมื่อถูก build เป็น PyInstaller `.exe` แบบ console บน Windows จะ pause ด้วย `Press Enter to close ICU-Sync...` ก่อน process exit เพื่อกัน console ปิดทันที
- ตั้งค่า Qt plugin path จาก PyQt6 ใน `.venv` ก่อนสร้าง `QApplication` เพื่อให้ macOS หา platform plugin `cocoa` เจอ
- แสดง startup log ใน console และสั่ง main window ให้ show/activate ตอนเริ่มโปรแกรม

### `Main_logic.py`

Application logic หลักของ main window

- สร้าง `QApplication` และ `MainWindowLogic`
- ตั้งค่า global `QLocale` ผ่าน `app_locale_lib.py` ก่อนสร้าง UI เพื่อให้ date picker และ number input แสดงเลขอารบิก `0-9` แทนเลขไทย
- ใช้ `app_single_instance_lib.py` ทำ single-instance lock ถ้าโปรแกรมเปิดอยู่แล้ว instance ใหม่จะแสดง dialog และ exit
- เก็บ reference ของ main window ไว้ใน `QApplication` และ activate หน้าต่างตอน startup
- bind event จาก main UI เช่น Settings, Load Patient, Sync Patient
- โหลดและบันทึก setting ผ่าน `SettingsLogic`
- ถ้า save settings ไม่สำเร็จ เช่นเขียน Windows startup registry ไม่ผ่าน จะแสดง error dialog และคงค่าเดิมใน main window
- startup ต้องแสดง main window ได้เสมอโดยไม่ test/connect HOSxP database อัตโนมัติ
- ถ้า load settings ไม่สำเร็จให้ใช้ `AppSettings` default และแสดง warning หลัง main window เปิดแล้ว
- เรียก `HosxpClient` เพื่อดึงรายการผู้ป่วย admit ตามช่วงวันที่
- เก็บรายการผู้ป่วยล่าสุดไว้ใน `self.patient_rows` สำหรับ filter ฝั่ง UI
- refresh ตัวเลือก ward จากข้อมูลผู้ป่วยที่โหลดมา และ filter ตารางผ่าน `apply_ward_filter()`
- populate ตารางผู้ป่วยใน main window
- ควบคุม state ของปุ่ม `Sync Patient to ICUCONS` ให้ active เมื่อมี checkbox ถูกเลือก
- เปิด `DlgPatientDetail` เพื่อแสดง RX, vital sign, และ LAB ของผู้ป่วยแต่ละราย
- กด `Sync Patient to ICUCONS` แล้วดึงข้อมูล HOSxP เพิ่มเติม ประกอบ payload ตาม schema เว็บใน `database-schema.md` และ POST เข้า ICUCONS
- workflow sync เป็นการนำเข้า/upsert เท่านั้น ไม่ลบเคสออกจากฐานข้อมูลเว็บ
- ใช้ `PatientSchemaFetchWorker` บน `QThread` สำหรับ workflow ที่ query หลายตาราง เพื่อไม่ให้ UI ค้าง
- sync ผ่าน `IcuconsultApiClient` ไปยัง endpoint ที่ตั้งค่าไว้ เช่น `https://icucons.plkhealth.go.th/api/icu`
- ถ้า setting `icucons_post_interval_minutes` มากกว่า `0` worker จะหน่วงเวลาตามนาทีที่ตั้งไว้หลัง POST แต่ละ patient ก่อนเริ่ม POST รายถัดไป
- request body ที่ส่งออกต้องยึดตามเอกสาร external client API ที่ `/Users/admin/Documents/OROPOH Phitsanulok/Antigravity/docs/external-client-icucon-api.md`
- แสดง status/error message ใน status bar และ message box
- ถ้าเปิด connection ไป HOSxP ไม่สำเร็จ จะแสดง message box หัวข้อ `เชื่อมต่อ HOSxP ไม่สำเร็จ` พร้อมรายละเอียด host, port, database, user, และ error จาก database driver

หมายเหตุ: workflow sync จะยิง request จริงเมื่อ user กดปุ่ม `Sync Patient to ICUCONS`

### `Main_ui.py`

UI definition ของ main window

- สร้าง layout หลักของหน้าจอ ICU-Sync
- กำหนดขนาด window เริ่มต้น `1280 x 960`
- สร้าง header panel ที่มี date picker สำหรับเลือกช่วงวัน admit
- date picker ใช้ locale เดียวกับ app เพื่อแสดงเลขอารบิก `0-9`
- สร้าง `QComboBox` สำหรับกรอง Ward โดยมีค่าเริ่มต้น `All wards`
- สร้างปุ่ม `Load Patient` และ `Settings`
- สร้าง label แสดง connection summary ของ HOSxP
- สร้าง `QTableWidget` สำหรับรายการผู้ป่วย โดย sort ได้ทุก column
- กำหนด column ของ patient table:
  - checkbox
  - `admit_date`
  - `cid`
  - `an`
  - `fullname`
  - `current agey`
  - `age mon`
  - `porv_dx`
  - `ward`
  - `action`
- สร้างปุ่ม `Sync Patient to ICUCONS` ด้านล่างตาราง
- ดูแล styling เบื้องต้นของ main window

### `DlgSetting.py`

Settings dialog สำหรับตั้งค่าการเชื่อมต่อระบบ

- แสดง form สำหรับตั้งค่า HOSxP database connection
- รับค่า host, port, database, user, password
- รับค่า ICUCONS API endpoint แบบเต็มตามเอกสาร external client เช่น `https://icucons.plkhealth.go.th/api/icu`
- รับค่า ICUCONS API token และ timeout
- รับค่า `POST /api/icu interval` เป็นนาที ค่า `0` หมายถึงไม่หน่วงระหว่าง request
- มี checkbox `Run ICU-Sync when Windows starts` ที่บรรทัดล่างของ dialog สำหรับเปิด/ปิดการรันอัตโนมัติเมื่อ Windows boot
- checkbox auto-start จะ enabled เฉพาะบน Windows เพราะใช้ Windows registry `Run` key
- number input เช่น HOSxP port และ ICUCONS timeout ใช้ locale เดียวกับ app เพื่อแสดงเลขอารบิก `0-9`
- คืนค่าเป็น `AppSettings` ผ่าน method `values()`
- ส่งผลลัพธ์กลับไปให้ `Main_logic.py` บันทึกผ่าน `SettingsLogic`
- ปุ่มทดสอบเชื่อมต่อแสดง error dialog ภาษาไทยเมื่อ HOSxP database connect ไม่ผ่าน โดยไม่แสดง password

ขอบเขตที่ควรมีตาม requirement ล่าสุด:

- เพิ่มปุ่ม `Test Connection`
- เพิ่มตัวเลือก charset เป็น `tis620` และ `utf8`
- default charset เป็น `tis620`

### `DlgPatientDetail.py`

Dialog สำหรับแสดงรายละเอียดผู้ป่วยรายคน

- รับ patient record จาก main table
- แสดงข้อมูลหัว dialog เช่น fullname, AN, CID
- สร้าง tab จำนวน 3 tab:
  - `RX`
  - `Viatal Sign`
  - `LAB`
- แต่ละ tab ใช้ table widget สำหรับแสดงข้อมูลตามวันที่ โดย query ฝั่ง `HosxpClient` order แบบ descending
- table ในแต่ละ tab sort ได้ และ resize column ตามข้อมูล

### `hosxp_lib.py`

Database helper สำหรับเชื่อมต่อและ query ข้อมูลจาก HOSxP

- สร้าง class `HosxpClient`
- lazy import `pymysql` เฉพาะตอนเปิด connection เพื่อไม่ให้ startup UI ค้างหาก MySQL driver import ช้า
- เปิด connection ไปยัง MySQL/MariaDB ด้วย `pymysql`
- ถ้า connect ไม่สำเร็จจะ raise `HosxpConnectionError` พร้อมข้อความที่ format ผ่าน `format_hosxp_connection_error()` โดยระบุ host, port, database, user, และ error จริงจาก driver แต่ไม่เปิดเผย password
- ใช้ `DictCursor` เพื่อคืนข้อมูลเป็น `dict`
- query รายการผู้ป่วย admit จากตารางหลักของ HOSxP เช่น `ipt`, `patient`, `ward`
- query admission รายเคสด้วย `fetch_admission_case()` เพื่อได้ข้อมูลผู้ป่วยและข้อมูลตั้งต้นของ `case_register`
- query RX จาก `opitemrece`, `drugitems`, `drugusage`
- query vital sign จาก fallback หลาย schema เช่น `ipt_vital_sign`, `ipd_nurse_note`, `opdscreen`
  - HOSxP เครื่องนี้ `ipt_vital_sign` ไม่มี `vital_date`/`vital_time`; ใช้ `vital_sign_datetime` แล้วแยกด้วย `DATE()` และ `TIME()`
  - `ipt_vital_sign` เป็น key-value table จึงต้อง pivot ด้วย `vital_sign_id`: `1=Temperature`, `2=Pulse`, `3=Respiratory Rate`, `4=Blood Pressure Systolic`, `5=Blood Pressure Diastolic`, `10=HR`
  - fallback history ใช้ `ipt_vital_sign_history.ipt_vital_sign_history_date` และ `ipt_vital_sign_history.ipt_vital_sign_history_time`
  - `ipd_nurse_note` ใช้ `note_datetime`, `bp_systolic`, `bp_diastolic`, `spo2_ra`, `spo2_o2`, `heart_rate`/`pulse`, `respiratory_rate`
- query LAB จาก `lab_head`, `lab_order`, `lab_items`
  - HOSxP เครื่องนี้ `lab_order` ไม่มี `lab_order_normal_value`; ใช้ `lab_order.lab_items_normal_value_ref` fallback กับ `lab_items.lab_items_normal_value`
  - `lab_head` ไม่มี `an`; query IPD LAB โดย join `ipt.vn = lab_head.vn` ก่อน และ fallback ด้วย `lab_head.hn` + ช่วงวันที่ admit
- query โรคประจำตัวจาก `chronic` และแพ้ยาจาก `opd_allergy` เพื่อ map ไป `app_patient_condition` และ `patient_allergy`
- มี `fetch_web_case_payload()` สำหรับรวมข้อมูล HOSxP แล้วแปลงเป็น payload ตาม database schema เว็บ
- มี helper `_fetch_all()` สำหรับ query ทั่วไป
- มี helper `_fetch_first_success()` สำหรับลองหลาย query และใช้ query แรกที่ schema รองรับ
- มี helper `_fetch_first_non_empty_success()` สำหรับลอง fallback ถัดไปเมื่อ query แรก schema ถูกแต่ไม่พบ rows
- มี helper `_fetch_first_success_or_empty()` สำหรับ optional table ที่บาง HOSxP อาจไม่มี เช่น chronic/allergy

### `icucons_schema_lib.py`

Mapper สำหรับแปลง raw HOSxP rows ให้ตรงกับ schema เว็บใน `database-schema.md`

- `web_app_patient()` map ข้อมูลผู้ป่วยหลักไป `app_patient`
- `web_patient_conditions()` map chronic/condition ไป `app_patient_condition`
- `web_patient_allergies()` map allergy ไป `patient_allergy`
- `web_case_register()` map admission ไป `case_register`
- `web_case_workflow_episodes()` สร้าง initial workflow event ตาม schema `case_workflow_episode` โดยยังไม่ใส่ FK ที่เว็บต้อง resolve หลัง upsert
- `web_case_vitals()` map vital sign ไป `case_vital`
- `web_case_labs()` map lab order/result ไป `case_lab`
- `web_case_medications()` map medication/RX ไป `case_medication`
- `web_case_payload()` รวม payload เป็น dict ที่แยก key ตามชื่อตารางเว็บ:
  - `app_patient`
  - `app_patient_condition`
  - `patient_allergy`
  - `case_register`
  - `case_workflow_episode`
  - `case_vital`
  - `case_lab`
  - `case_medication`
  - `case_note`
  - `case_file`
- mapper จะ normalize date/time เป็น string รูปแบบ `YYYY-MM-DD` และ `HH:MM:SS`
- mapper ยังไม่ใส่ `id`, `patient_id`, หรือ `case_register_id` เพราะเป็น key ที่ฝั่งเว็บควรสร้างหรือ resolve ตอน insert/upsert

### `icuconsult_api_lib.py`

API helper สำหรับส่งข้อมูลเข้าเว็บ ICUCONS

- สร้าง class `IcuconsultApiClient`
- อ่าน config จาก `AppSettings`
- default endpoint คือ `https://icucons.plkhealth.go.th/api/icu`
- ใช้ค่า `icucons_api_endpoint` จาก Settings dialog เป็น URL ปลายทางสำหรับ `POST`
- ส่ง JSON ด้วย `requests.post()`
- ถ้ามี `icucons_api_token` จะส่งทั้ง header `Authorization: Bearer <token>` และ `x-api-key`
- `api_payload_from_schema()` แปลง payload ที่จัดตาม schema เว็บให้เป็น request body ที่ `app/api/icu/route.ts` ของเว็บรับ:
  - `app_patient` -> `patient`
    - ส่ง field หลักตาม external API เช่น `hn`, `cid`, `name`, `firstName`, `lastName`, `gender`, `dob`, `age`, `phone`, `bloodType`, `district`, `province`, `conditions`, `allergies`
  - `case_register` -> `case`
    - ส่ง field หลักตาม external API เช่น `an`, `hospital`, `priority`, `specialty`, `reason`, `senderId`, `presentIllness`, `initialDiagnosis`, `clinicalNotes`
  - `case_vital` -> `vitals`
    - ส่ง `recordedAt` เป็น ISO 8601 พร้อม timezone `+07:00` เมื่อมีวันเวลา HOSxP
  - `case_lab` -> `labs`
    - ส่ง `refRange` ตามชื่อ field หลักของ external API และข้ามรายการที่ไม่มี `name`
  - `case_medication` -> `medications`
    - ส่ง `start`, `name`, `dose`, `freq`, `route`, `category` และข้ามรายการที่ไม่มี `name`
  - `case_note` -> `notes`
    - ส่ง `body`, `authorId`, `authorColor` และข้ามรายการที่ไม่มี `body`
- ไม่ส่ง `workflowEpisodes` ใน external API payload เพราะ endpoint `/api/icu` รองรับเฉพาะกลุ่มข้อมูล `patient`, `case`/`consult`/`request`, `vitals`, `labs`, `medications`, และ `notes`
- ฝั่งเว็บ ICUCONS endpoint `/api/icu` ควรเรียก schema guard ก่อน insert เพื่อสร้าง table/column ที่ยังขาดตาม `database-schema.md` เช่น `case_register.an`, `case_workflow_episode`, `case_vital`, `case_lab`, `case_medication`, `case_note`, และ `case_file`
- คืนค่า `IcuconsultSyncResult` ที่มี success, case id, inserted summary, และ raw response

### `app_locale_lib.py`

Locale helper สำหรับค่าเลขและวันที่ของ UI

- กำหนด `APP_NUMBER_LOCALE` เป็น English/United States
- `configure_app_locale()` ตั้งค่า `QLocale.setDefault()` ให้ทั้ง application ใช้เลขอารบิก `0-9`
- `apply_widget_number_locale()` ใช้กับ widget เฉพาะจุด เช่น `QDateEdit` และ `QSpinBox` เพื่อไม่ให้แสดงเลขไทยบนเครื่อง Windows ที่ตั้ง locale ไทย

### `app_startup_lib.py`

Startup helper สำหรับ Windows auto-start

- ใช้ registry `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- value name คือ `ICU-Sync`
- ถ้าโปรแกรมรันจาก PyInstaller `.exe` จะบันทึก command เป็น path ของ executable ปัจจุบัน
- ถ้ารันแบบ dev จะบันทึก command เป็น Python executable พร้อม `start.py`
- บน platform ที่ไม่ใช่ Windows helper จะ no-op และรายงานว่า startup ไม่ supported

### `app_single_instance_lib.py`

Single-instance helper สำหรับกันเปิด ICU-Sync ซ้ำ

- ใช้ `QLockFile` สร้าง lock file ชื่อ `PLKHealth-ICU-Sync.lock` ใน temp directory ของระบบ
- `acquire_single_instance_lock()` คืน lock object เมื่อ lock สำเร็จ และต้องเก็บ reference ไว้กับ `QApplication`
- ถ้า lock ไม่สำเร็จจะ raise `SingleInstanceError` เพื่อให้ startup แสดงข้อความ `ICU-Sync is already running.` แล้ว exit

### `setting_lib.py`

Settings helper สำหรับจัดการ configuration ของระบบ

- กำหนด `APP_ORG = "PLKHealth"` และ `APP_NAME = "ICU-Sync"`
- สร้าง dataclass `AppSettings` สำหรับเก็บค่า config
- ใช้ `QSettings` สำหรับ load/save setting ของ application
- default HOSxP connection เป็น `192.168.10.118:3306`
- migrate ค่า default เก่า `localhost:3306` และค่า host ที่ resolve ไม่ได้ `hos-192.168.10.118` ไปเป็น `192.168.10.118:3306` ตอน load setting
- เก็บค่า HOSxP connection:
  - host
  - port
  - database
  - user
  - password
- เก็บค่า ICUCONS API:
  - API endpoint
  - API token
  - request timeout
  - POST interval in minutes
- เก็บค่า application:
  - run on Windows boot
- ยัง save ค่า `icucons/base_url` และ `icucons/api_path` ที่แยกจาก endpoint เพื่อรองรับ setting เดิม แต่ UI ให้แก้ผ่าน endpoint ช่องเดียว
- save key `icucons/post_interval_minutes` สำหรับระยะเวลาหน่วงระหว่าง POST `/api/icu` แต่ละเคส
- save key `app/run_on_windows_boot` และเรียก `app_startup_lib.set_windows_startup_enabled()` เพื่อ sync กับ Windows registry
- ใช้ `normalize_icucons_api_endpoint()` เพื่อ normalize ค่า endpoint ก่อน save/use เช่น path-only `/api/icu` จะถูกเติม host default

ขอบเขตที่ควรเพิ่มตาม requirement ล่าสุด:

- เพิ่ม `hosxp_charset`
- load/save key `hosxp/charset`
- default เป็น `tis620`

## Documentation Files

### `docs/HOSXP_DATABASE_SCHEMA.md`

เอกสารอ้างอิง schema ของ HOSxP

- ใช้เป็น guideline ระหว่างพัฒนา query
- ควรใช้ร่วมกับ `db-cli --skill` เพื่อ research schema จริงก่อนแก้ SQL

### `docs/hosxp_credential.md`

เอกสารเก็บข้อมูล credential สำหรับ environment/dev reference

- ใช้อ้างอิงค่าการเชื่อมต่อ HOSxP ระหว่าง development
- ไม่ควร hardcode credential ลงใน source code

### `docs/icucons_api_endpoint.md`

เอกสาร endpoint ของ ICUCONS

- ใช้เป็น guideline สำหรับ phase ที่ implement sync workflow
- ยังไม่มี module สำหรับส่งข้อมูลเข้า ICUCONS ในโค้ดปัจจุบัน

## Configuration Flow

1. `Main_logic.py` เรียก `SettingsLogic.load()`
2. `setting_lib.py` อ่านค่าจาก `QSettings`
3. `Main_logic.py` ส่ง `AppSettings` เข้า `HosxpClient`
4. `hosxp_lib.py` ใช้ `AppSettings` เพื่อเปิด database connection
5. เมื่อ user แก้ setting ใน `DlgSetting.py`, `Main_logic.py` จะ save ค่ากลับผ่าน `SettingsLogic.save()`

## Patient Data Flow

1. User เลือกช่วงวันที่ admit ใน `Main_ui.py`
2. User กด `Load Patient`
3. `Main_logic.py` validate date range
4. `Main_logic.py` เรียก `HosxpClient.fetch_admitted_patients()`
5. `hosxp_lib.py` query HOSxP database และคืน list ของ patient dict
6. `Main_logic.py` เก็บข้อมูลไว้ใน `self.patient_rows`
7. `Main_logic.py` สร้าง ward filter options จากค่า `ward` ที่มีใน rows
8. `Main_logic.py` render ข้อมูลตาม ward ที่เลือกลง patient table
9. User เปลี่ยน Ward filter ได้โดยไม่ต้อง query HOSxP ใหม่
10. User เลือก checkbox เพื่อ enable ปุ่ม sync
11. User กด action `View` เพื่อเปิด `DlgPatientDetail`
12. `Main_logic.py` query RX, vital sign, LAB แล้วส่งให้ `DlgPatientDetail.py`

## ICUCONS Schema Payload Flow

1. User เลือก patient ใน main table
2. User กด `Sync Patient to ICUCONS`
3. `Main_logic.py` สร้าง `PatientSchemaFetchWorker` และย้ายไปทำงานใน `QThread`
4. Worker เรียก `HosxpClient.fetch_web_case_payload(an, hn)` ต่อผู้ป่วยที่เลือก
5. `HosxpClient` ดึง admission, chronic, allergy, vital sign, LAB, และ RX จาก HOSxP
6. `icucons_schema_lib.py` แปลงข้อมูลทั้งหมดให้ตรงกับ schema เว็บ
7. `IcuconsultApiClient.sync_case()` POST payload เข้า ICUCONS endpoint
8. ถ้ามี patient ถัดไปและตั้ง `POST /api/icu interval` มากกว่า `0` จะรอใน worker thread ตามจำนวนนาทีก่อน POST รอบถัดไป
9. `icuconsult_api_lib.py` แปลง schema payload ภายในเป็น external API payload ตามเอกสาร `external-client-icucon-api.md` ก่อนส่งจริง
10. เว็บ ICUCONS ตรวจและเติม schema ที่ยังขาดก่อน insert เพื่อกัน error `Unknown column ... in INSERT INTO`
11. เว็บ ICUCONS สร้างหรืออัปเดตข้อมูลลงตาราง `app_patient`, `patient_allergy`, `app_patient_condition`, `case_register`, `case_vital`, `case_lab`, `case_medication`, และ `case_note`
12. `Main_logic.py` เก็บ payload ล่าสุดไว้ที่ `self.schema_payloads`
13. UI แสดง summary จำนวน case, vital, lab, medication และ case id ที่เว็บคืนกลับมา

ตอนนี้ฝั่ง server ปลด protection แล้ว จึง sync ได้แม้ไม่ได้ตั้ง ICUCONS API token; ถ้ามี token ใน Settings แอปจะส่ง token ไปกับ request ด้วย

## Naming Convention

ตาม `AGENTS.md`

- logic module ใช้ suffix `_logic`
- UI module ใช้ suffix `_ui`
- dialog module ใช้ prefix `Dlg`
- lib/helper module ใช้ suffix `_lib`
- config ใช้ `QSettings`
- run และ package management ใช้ `uv`
