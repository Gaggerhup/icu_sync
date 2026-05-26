# Database Schema

เอกสารนี้สรุป database schema ของตัวเว็บจากโค้ดที่ใช้งานจริงในโปรเจกต์ `Antigravity` โดยอ้างอิงจากไฟล์ schema ใต้ `src/database/schemas` และคำสั่ง SQL ใน `src/actions/patient-detail-store.ts` กับ `src/lib/server-sessions.ts`

## ภาพรวม

ระบบแบ่งข้อมูลหลักออกเป็น 4 กลุ่ม:

1. Provider และการตั้งค่าผู้ใช้งาน
2. Case consultation และข้อมูลคนไข้
3. Notification
4. Authentication session

ความสัมพันธ์หลักของข้อมูล:

- `provider` 1:N `notification`
- `provider` 1:N `case_note`
- `app_patient` 1:N `app_patient_condition`
- `app_patient` 1:N `patient_allergy`
- `app_patient` 1:N `case_register`
- `case_register` 1:N `case_workflow_episode`
- `case_register` 1:N `case_vital`
- `case_register` 1:N `case_lab`
- `case_register` 1:N `case_medication`
- `case_register` 1:N `case_note`
- `case_register` 1:N `case_file`
- `provider` logical 1:N `provider_session` ผ่าน `account_id`

## ER Overview

```text
provider
  |-< notification
  |-< case_note
  `-< provider_session (logical by account_id)

app_patient
  |-< app_patient_condition
  |-< patient_allergy
  `-< case_register
       |-< case_workflow_episode
       |-< case_vital
       |-< case_lab
       |-< case_medication
       |-< case_note
       `-< case_file
```

## ตาราง `provider`

เก็บข้อมูลผู้ให้คำปรึกษา หรือผู้ใช้งานฝั่ง provider ของระบบ

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `provider_code` | `VARCHAR(191)` | No | - | รหัส provider |
| `title` | `VARCHAR(32)` | Yes | `Dr.` | คำนำหน้า |
| `first_name` | `VARCHAR(191)` | No | - | ชื่อ |
| `last_name` | `VARCHAR(191)` | No | - | นามสกุล |
| `specialty` | `VARCHAR(191)` | Yes | - | สาขา |
| `hospital` | `VARCHAR(255)` | Yes | - | โรงพยาบาล |
| `email` | `VARCHAR(191)` | Yes | - | อีเมล |
| `avatar_url` | `TEXT` | Yes | - | รูปโปรไฟล์ |
| `phone_number` | `VARCHAR(32)` | Yes | - | เบอร์โทร |
| `license` | `VARCHAR(191)` | Yes | - | เลขใบประกอบวิชาชีพ |
| `is_accepting_cases` | `BOOLEAN` | No | `true` | เปิดรับเคสหรือไม่ |
| `is_accepting_notifications` | `BOOLEAN` | No | `true` | เปิดรับแจ้งเตือนหรือไม่ |
| `status` | `VARCHAR(255)` | No | `online` | สถานะผู้ใช้งาน |
| `notif_prefs` | `TEXT` | Yes | - | JSON string ของ notification preferences |
| `telegram_chat_id` | `VARCHAR(64)` | Yes | - | Telegram chat id สำหรับส่งแจ้งเตือน |

## ตาราง `notification`

เก็บ in-app notifications ที่แสดงใน header และ dashboard

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `user_id` | `INT` | No | - | อ้างถึง `provider.id` |
| `notify_date` | `VARCHAR(10)` | No | - | วันที่แจ้งเตือน |
| `notify_time` | `VARCHAR(8)` | No | - | เวลาแจ้งเตือน |
| `title` | `VARCHAR(255)` | No | - | หัวข้อแจ้งเตือน |
| `message` | `TEXT` | No | - | รายละเอียด |
| `read` | `BOOLEAN` | No | `false` | อ่านแล้วหรือยัง |
| `type` | `VARCHAR(32)` | No | `alert` | ประเภท เช่น `request`, `message`, `alert` |

## ตาราง `app_patient`

เก็บข้อมูลคนไข้หลักที่ใช้คู่กับ consultation case

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `hn` | `VARCHAR(64)` | Yes | - | Hospital Number |
| `cid` | `VARCHAR(32)` | Yes | - | CID หรือ identifier |
| `first_name` | `VARCHAR(191)` | Yes | - | ชื่อ |
| `last_name` | `VARCHAR(191)` | Yes | - | นามสกุล |
| `gender` | `VARCHAR(32)` | Yes | - | เพศ |
| `birth_date` | `DATE` | Yes | - | วันเกิด |
| `reported_age` | `INT` | Yes | - | อายุที่กรอกไว้ |
| `blood_type` | `VARCHAR(16)` | Yes | - | กรุ๊ปเลือด |
| `phone_number` | `VARCHAR(32)` | Yes | - | เบอร์โทร |
| `district` | `VARCHAR(191)` | Yes | - | อำเภอ |
| `province` | `VARCHAR(191)` | Yes | - | จังหวัด |

## ตาราง `app_patient_condition`

เก็บโรคประจำตัวหรือ condition ของคนไข้แบบหลายรายการ

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `patient_id` | `INT` | No | - | อ้างถึง `app_patient.id` |
| `condition_name` | `VARCHAR(255)` | No | - | ชื่อโรคหรือ condition |
| `item_order` | `INT` | No | `1` | ลำดับการแสดงผล |

## ตาราง `patient_allergy`

เก็บประวัติแพ้ยา/แพ้อาหารของคนไข้แบบหลายรายการ

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `patient_id` | `INT` | No | - | อ้างถึง `app_patient.id` |
| `allergy_name` | `VARCHAR(255)` | No | - | รายการแพ้ |
| `item_order` | `INT` | No | `1` | ลำดับการแสดงผล |

## ตาราง `case_register`

ตารางศูนย์กลางของ consultation request และ active case

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `patient_id` | `INT` | No | - | อ้างถึง `app_patient.id` |
| `an` | `VARCHAR(64)` | Yes | - | Admission Number |
| `hospital` | `VARCHAR(255)` | Yes | - | โรงพยาบาลต้นทาง |
| `record_date` | `DATE` | No | - | วันที่สร้างหรืออัปเดตเคส |
| `record_time` | `TIME` | Yes | - | เวลาที่บันทึก |
| `status` | `VARCHAR(32)` | No | - | เช่น `Pending`, `Active`, `Critical`, `Declined` |
| `priority` | `VARCHAR(32)` | No | - | เช่น `IMMEDIATE`, `EMERGENCY`, `URGENT` |
| `specialty` | `VARCHAR(191)` | Yes | - | สาขาที่ขอปรึกษา |
| `reason` | `TEXT` | Yes | - | เหตุผลที่ขอ consult |
| `current_symptoms` | `TEXT` | Yes | - | อาการปัจจุบัน |
| `initial_diagnosis` | `TEXT` | Yes | - | Initial diagnosis |
| `clinical_notes` | `TEXT` | Yes | - | หมายเหตุทางคลินิก |
| `sender_id` | `VARCHAR(191)` | Yes | - | ผู้ส่งเคส |
| `last_action` | `VARCHAR(191)` | Yes | - | action ล่าสุด |
| `last_active_time` | `VARCHAR(64)` | Yes | - | ข้อความเวลาแบบแสดงผล |

หมายเหตุ:

- ในระดับ application model มี field ที่ derive จากตารางนี้เพิ่ม เช่น `requestedAt`, `chiefComplaint`, `presentIllness`
- `chiefComplaint` map มาจากคอลัมน์ `reason`
- `presentIllness` map มาจากคอลัมน์ `current_symptoms`
- `requestedAt` ประกอบจาก `record_date` + `record_time`

## ตาราง `case_workflow_episode`

เก็บประวัติ workflow ของ request/consult เช่น สร้างคำขอ อนุมัติ ปฏิเสธ ปิดเคส เปิดใหม่ หรือเปิดคำขอจาก case monitor

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `case_register_id` | `INT` | No | - | อ้างถึง `case_register.id` |
| `patient_id` | `INT` | Yes | - | อ้างถึง `app_patient.id` |
| `episode_type` | `VARCHAR(32)` | No | - | ประเภท episode เช่น `request`, `consult` |
| `status` | `VARCHAR(32)` | No | - | สถานะที่เกิดขึ้นตอนบันทึก |
| `action` | `VARCHAR(191)` | No | - | ชื่อ action เช่น `Created`, `Approved`, `Reactivated` |
| `actor_id` | `VARCHAR(191)` | Yes | - | ผู้ที่ทำ action |
| `note` | `TEXT` | Yes | - | บันทึกเพิ่มเติม |
| `created_at` | `DATETIME(3)` | No | - | เวลาที่บันทึก event |

หมายเหตุ:

- ตารางนี้ถูกสร้างอัตโนมัติใน runtime โดย `src/actions/case-workflow-episodes.ts`
- มี index ตามการใช้งานจริงบน `case_register_id`, `patient_id`, `episode_type`, `status`

## ตาราง `case_vital`

เก็บ vital signs ต่อเคส หลายรายการตามเวลา

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `case_register_id` | `INT` | No | - | อ้างถึง `case_register.id` |
| `record_date` | `DATE` | No | - | วันที่บันทึก |
| `record_time` | `TIME` | Yes | - | เวลาที่บันทึก |
| `bp` | `VARCHAR(32)` | Yes | - | Blood pressure |
| `hr` | `VARCHAR(32)` | Yes | - | Heart rate |
| `temp` | `VARCHAR(32)` | Yes | - | Temperature |
| `rr` | `VARCHAR(32)` | Yes | - | Respiratory rate |
| `spo2` | `VARCHAR(32)` | Yes | - | Oxygen saturation |
| `gcs` | `VARCHAR(32)` | Yes | - | Glasgow Coma Scale |

## ตาราง `case_lab`

เก็บผล lab ต่อเคส

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `case_register_id` | `INT` | No | - | อ้างถึง `case_register.id` |
| `lab_date` | `DATE` | No | - | วันที่บันทึกผล |
| `lab_time` | `TIME` | Yes | - | เวลา |
| `name` | `VARCHAR(191)` | No | - | ชื่อแลบ |
| `result` | `VARCHAR(191)` | Yes | - | ผลตรวจ |
| `unit` | `VARCHAR(64)` | Yes | - | หน่วย |
| `ref_range` | `VARCHAR(191)` | Yes | - | ช่วงอ้างอิง |
| `status` | `VARCHAR(64)` | Yes | - | สถานะ เช่น `normal`, `high`, `low`, `critical` |

## ตาราง `case_medication`

เก็บยาที่เกี่ยวข้องกับเคส

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `case_register_id` | `INT` | No | - | อ้างถึง `case_register.id` |
| `start_date` | `DATE` | No | - | วันที่เริ่มยา |
| `start_time` | `TIME` | Yes | - | เวลาเริ่มยา |
| `name` | `VARCHAR(191)` | No | - | ชื่อยา |
| `dose` | `VARCHAR(191)` | Yes | - | ขนาดยา |
| `freq` | `VARCHAR(191)` | Yes | - | ความถี่ |
| `route` | `VARCHAR(64)` | Yes | - | วิธีให้ยา |
| `category` | `VARCHAR(64)` | Yes | - | หมวดหมู่ยา |

## ตาราง `case_note`

เก็บโน้ตหรือ comment ในเคส

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `case_register_id` | `INT` | No | - | อ้างถึง `case_register.id` |
| `record_date` | `DATE` | No | - | วันที่จด note |
| `record_time` | `TIME` | Yes | - | เวลา |
| `provider_id_do_note` | `INT` | Yes | - | อ้างถึง `provider.id` |
| `color` | `VARCHAR(32)` | Yes | - | สีประจำผู้เขียนหรือ note |
| `note_text` | `TEXT` | No | - | เนื้อหา note |

## ตาราง `case_file`

เก็บไฟล์แนบของเคส เช่น image, PDF, CSV, text

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `INT` | No | auto increment | Primary key |
| `case_register_id` | `INT` | No | - | อ้างถึง `case_register.id` |
| `file_date` | `DATE` | No | - | วันที่อัปโหลด |
| `file_time` | `TIME` | Yes | - | เวลาอัปโหลด |
| `privder_id_do_file` | `VARCHAR(64)` | Yes | - | ผู้แนบไฟล์ |
| `file_name` | `VARCHAR(255)` | No | - | ชื่อไฟล์ต้นฉบับ |
| `file_type` | `VARCHAR(64)` | Yes | - | ประเภทไฟล์ที่ระบบตีความ |
| `category` | `VARCHAR(64)` | Yes | - | หมวดหมู่ไฟล์ |
| `mime_type` | `VARCHAR(191)` | Yes | - | MIME type |
| `file_url` | `TEXT` | No | - | path หรือ URL ของไฟล์ |
| `size_kb` | `INT` | Yes | - | ขนาดไฟล์เป็น KB |
| `description` | `TEXT` | Yes | - | คำอธิบายไฟล์ |
| `is_previewable` | `BOOLEAN` | No | `false` | preview ในเว็บได้หรือไม่ |

## ตาราง `provider_session`

เก็บ session ฝั่ง server สำหรับการล็อกอินและจัดการอุปกรณ์

| Column | Type | Null | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `VARCHAR(64)` | No | - | Primary key, session id |
| `account_id` | `VARCHAR(191)` | No | - | รหัส account จาก Provider ID |
| `device` | `VARCHAR(191)` | No | - | ชื่ออุปกรณ์ที่ derive จาก browser/OS |
| `user_agent` | `TEXT` | Yes | - | User agent |
| `platform` | `VARCHAR(191)` | Yes | - | platform ของ browser |
| `ip_address` | `VARCHAR(64)` | Yes | - | IP ที่ตรวจพบ |
| `is_mock` | `BOOLEAN` | No | `false` | เป็น mock login หรือไม่ |
| `created_at` | `DATETIME(3)` | No | - | วันเวลาสร้าง session |
| `last_seen_at` | `DATETIME(3)` | No | - | heartbeat ล่าสุด |
| `expires_at` | `DATETIME(3)` | No | - | วันหมดอายุ |
| `revoked_at` | `DATETIME(3)` | Yes | - | วันเวลาที่ revoke |

## ค่าที่ระบบใช้งานบ่อย

### `case_register.status`

ค่าที่พบจากโค้ดฝั่งเว็บ:

- `Pending`
- `Approved`
- `Declined`
- `Cancelled`
- `Active`
- `Critical`
- `Inactive`
- `Archived`
- `Discharge`
- `Step Down`
- `Referred`
- `Dead`

### `case_register.priority`

ค่าที่พบจากโค้ดฝั่งเว็บ:

- `IMMEDIATE`
- `EMERGENCY`
- `URGENT`
- `SEMI-URGENT`
- `NON-URGENT`

### `notification.type`

ค่าที่พบจากโค้ดฝั่งเว็บ:

- `request`
- `message`
- `alert`

### `case_workflow_episode.episode_type`

ค่าที่พบจากโค้ดฝั่งเว็บ:

- `request`
- `consult`

### `case_workflow_episode.action`

ค่าที่พบจากโค้ดฝั่งเว็บ:

- `Created`
- `Approved`
- `Declined`
- `Cancelled request`
- `Closed: Discharge`
- `Closed: Referred`
- `Closed: Dead`
- `Closed: Step Down`
- `Reactivated`
- `Requested again`
- `Activated consult request`
- `Consult request from monitor`
- `Deactivated consult`

## หมายเหตุสำคัญ

- เอกสารนี้สะท้อน schema ที่ “ตัวเว็บใช้งาน” ไม่ได้อ้างว่าเป็น schema ครบทั้งหมดของฐานข้อมูลโรงพยาบาล
- บางตารางในระบบเก่าอาจมีคอลัมน์มากกว่านี้ แต่เอกสารนี้สรุปเฉพาะคอลัมน์ที่โค้ดเว็บอ่านหรือเขียนอยู่ตอนนี้
- ยังไม่ได้ประกาศ foreign key constraint ใน Drizzle schema ปัจจุบัน แม้เชิงตรรกะจะมีความสัมพันธ์กันตามที่ระบุไว้ด้านบน
- ตาราง `case_workflow_episode` ถูก `CREATE TABLE IF NOT EXISTS` ตอน runtime ไม่ได้พึ่ง migration อย่างเดียว
- คอลัมน์ `last_active_time` ใน `case_register` เป็นข้อความสำหรับแสดงผล ไม่ใช่ timestamp มาตรฐาน
- คอลัมน์ `notif_prefs` ใน `provider` ถูกใช้เป็น JSON string
- ชื่อคอลัมน์ `privder_id_do_file` ใน `case_file` สะกดตามที่โค้ดใช้อยู่จริง
- กลุ่มสถานะ active consult ที่โค้ดใช้จริงคือ `Approved`, `Active`, `Critical`
- กลุ่มสถานะ archived/request-closed ที่โค้ดใช้จริงรวม `Declined`, `Cancelled`, `Discharge`, `Referred`, `Dead`, `Step Down`

## Source of Truth ในโปรเจกต์

- `src/database/schemas/users.ts`
- `src/database/schemas/notifications.ts`
- `src/database/schemas/cases.ts`
- `src/database/schemas/sessions.ts`
- `src/actions/patient-detail-store.ts`
- `src/actions/case-workflow-episodes.ts`
- `src/actions/case-monitor.ts`
- `src/lib/server-sessions.ts`
