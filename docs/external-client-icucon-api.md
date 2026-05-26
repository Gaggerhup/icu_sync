# วิธีส่งข้อมูลเข้า ICUCON จาก External Client

เอกสารนี้อธิบายวิธีเรียก API สำหรับส่งข้อมูลผู้ป่วยและคำขอ consult เข้า ICUCON จากระบบภายนอก เช่น HIS, HOSxP, middleware, integration service หรือ script อัตโนมัติ

## Endpoint

```text
POST https://icucons.plkhealth.go.th/api/icu
```

สำหรับเครื่อง local/dev ให้เปลี่ยน host ตาม environment ที่รันอยู่ เช่น

```text
POST http://localhost:3000/api/icu
```

## Authentication

API รองรับ token จาก environment variable `ICU_API_TOKEN`

ถ้าตั้งค่า `ICU_API_TOKEN` ไว้บน server, external client ต้องส่ง token แบบใดแบบหนึ่ง:

```http
Authorization: Bearer YOUR_ICU_API_TOKEN
```

หรือ

```http
x-api-key: YOUR_ICU_API_TOKEN
```

ถ้า server ไม่ได้ตั้ง `ICU_API_TOKEN` ระบบจะไม่บังคับ authentication แต่ production ควรตั้ง token เสมอ

## Header ที่ต้องส่ง

```http
Content-Type: application/json
Authorization: Bearer YOUR_ICU_API_TOKEN
```

## รูปแบบการทำงาน

API นี้มี 2 โหมด ขึ้นกับ payload ที่ส่งมา

1. ส่งเฉพาะข้อมูลผู้ป่วย

ถ้า payload ไม่มี key `case`, `consult` หรือ `request` ระบบจะบันทึก/อัปเดตข้อมูลผู้ป่วยเท่านั้น และยังไม่สร้าง consult case

2. ส่งข้อมูลผู้ป่วยพร้อมคำขอ consult

ถ้า payload มี key `case`, `consult` หรือ `request` ระบบจะสร้าง/อัปเดต consult case และบันทึกข้อมูลประกอบ เช่น vital signs, labs, medications และ notes

## Payload สำหรับสร้าง Consult Case

ตัวอย่าง payload แนะนำ:

```json
{
  "patient": {
    "hn": "68000123",
    "cid": "1234567890123",
    "name": "สมชาย ใจดี",
    "gender": "male",
    "age": 67,
    "dob": "1959-03-12",
    "phone": "0812345678",
    "district": "เมืองพิษณุโลก",
    "province": "พิษณุโลก",
    "bloodType": "O",
    "allergies": ["Penicillin"],
    "conditions": ["Hypertension", "Diabetes mellitus"]
  },
  "case": {
    "hospital": "โรงพยาบาลตัวอย่าง",
    "priority": "High",
    "specialty": "Pulmonary Medicine and Critical Care",
    "reason": "ขอ consult ผู้ป่วย respiratory failure",
    "senderId": "external-his-001",
    "an": "AN6800001",
    "presentIllness": "เหนื่อยมากขึ้น 2 ชั่วโมงก่อนมาโรงพยาบาล",
    "initialDiagnosis": "Acute respiratory failure",
    "clinicalNotes": "On HFNC, BP stable, pending CXR"
	  },
	  "vitals": [
	    {
	      "recordedAt": "2026-05-25T09:30:00+07:00",
	      "createdAt": "2026-05-25T09:31:00+07:00",
	      "bp": "130/82",
	      "hr": "118",
	      "temp": "38.2",
	      "rr": "30",
	      "spo2": "91",
      "gcs": "E4V5M6"
    }
	  ],
	  "labs": [
	    {
	      "name": "WBC",
	      "createdAt": "2026-05-25T09:31:00+07:00",
	      "result": "14500",
	      "unit": "cells/uL",
	      "refRange": "4000-10000",
	      "status": "abnormal"
    }
	  ],
	  "medications": [
	    {
	      "name": "Ceftriaxone",
	      "createdAt": "2026-05-25T09:31:00+07:00",
	      "dose": "2 g",
	      "freq": "OD",
	      "route": "IV",
	      "start": "2026-05-25",
      "category": "antibiotic"
    }
	  ],
	  "notes": [
	    {
	      "body": "ส่ง consult จากระบบ HIS",
	      "createdAt": "2026-05-25T09:31:00+07:00",
	      "authorName": "HIS Integration",
	      "authorRole": "External System"
	    }
	  ]
}
```

## Field ที่ API รองรับ

### patient

| Field | ชื่อสำรองที่รองรับ | รายละเอียด |
| --- | --- | --- |
| `name` | `patientName` | ชื่อ-นามสกุลผู้ป่วย |
| `firstName` | `first_name` | ชื่อ กรณีไม่ส่ง `name` |
| `lastName` | `last_name` | นามสกุล กรณีไม่ส่ง `name` |
| `hn` | - | Hospital number |
| `cid` | `nationalId` | เลขบัตรประชาชน/เลขประจำตัว |
| `age` | `reportedAge` | อายุ ถ้าไม่มีวันเกิด |
| `dob` | `birthDate`, `birth_date` | วันเกิด รูปแบบ `YYYY-MM-DD` |
| `phone` | `phoneNumber` | เบอร์โทร |
| `district` | - | อำเภอ |
| `province` | - | จังหวัด |
| `bloodType` | `blood_type` | หมู่เลือด |
| `gender` | - | เพศ |
| `allergies` | - | array หรือ comma-separated string |
| `conditions` | `diagnoses` | array หรือ comma-separated string |

ถ้าไม่ส่งชื่อผู้ป่วย API จะพยายามสร้างชื่อจาก `firstName`/`lastName` ถ้ายังไม่มีจะ fallback เป็น `Unknown patient {hn/cid}`

### case, consult หรือ request

สามารถใช้ชื่อ key หลักเป็น `case`, `consult` หรือ `request` ได้ โดย field ภายในรองรับดังนี้

| Field | ชื่อสำรองที่รองรับ | รายละเอียด |
| --- | --- | --- |
| `hospital` | body-level `hospital`, patient-level `hospital`, `hospitalName` | โรงพยาบาลต้นทาง |
| `priority` | body-level `priority`, `urgency` | ความเร่งด่วน ค่า default คือ `Medium` |
| `specialty` | body-level `specialty`, `department` | สาขาที่ต้องการ consult |
| `reason` | body-level `reason`, `chiefComplaint` | เหตุผล/อาการนำ |
| `senderId` | body-level `senderId`, `requesterId` | id ผู้ส่งหรือระบบต้นทาง |
| `an` | patient-level `an`, body-level `an` | Admission number |
| `presentIllness` | `present_illness` | ประวัติปัจจุบัน |
| `currentSymptoms` | `current_symptoms`, body-level `symptoms` | อาการปัจจุบัน |
| `initialDiagnosis` | `initial_diagnosis`, body-level `diagnosis` | วินิจฉัยเบื้องต้น |
| `clinicalNotes` | `clinical_notes`, body-level `note` | note เพิ่มเติม |

### vitals

ส่งเป็น array ของ object

| Field | ชื่อสำรองที่รองรับ |
| --- | --- |
| `recordedAt` | `recorded_at`, `datetime`, `createdAt` |
| `createdAt` | `created_at` |
| `bp` | `bloodPressure`, `blood_pressure` |
| `hr` | `heartRate`, `heart_rate` |
| `temp` | `temperature` |
| `rr` | `respiratoryRate`, `respiratory_rate` |
| `spo2` | `spo2Percent`, `oxygenSaturation` |
| `gcs` | - |

ถ้าไม่ส่ง `recordedAt` ระบบจะใช้เวลาปัจจุบันของ server สำหรับเวลาที่วัด vital sign และถ้าไม่ส่ง `createdAt` ระบบจะใช้เวลาปัจจุบันของ server สำหรับเวลาที่ระบบรับข้อมูล

### labs

ส่งเป็น array ของ object

| Field | ชื่อสำรองที่รองรับ |
| --- | --- |
| `name` | `labName`, `lab_name`, `test` |
| `createdAt` | `created_at` |
| `result` | `value` |
| `unit` | - |
| `refRange` | `ref_range`, `referenceRange` |
| `status` | - |

รายการ lab ที่ไม่มี `name` จะถูกข้าม ถ้าไม่ส่ง `createdAt` ระบบจะใช้เวลาปัจจุบันของ server

### medications

ส่งเป็น array ของ object

| Field | ชื่อสำรองที่รองรับ |
| --- | --- |
| `name` | `drugName`, `drug_name` |
| `createdAt` | `created_at` |
| `dose` | - |
| `freq` | `frequency` |
| `route` | - |
| `start` | `startDate`, `start_date` |
| `category` | - |

รายการยาที่ไม่มี `name` จะถูกข้าม ถ้าไม่ส่ง `createdAt` ระบบจะใช้เวลาปัจจุบันของ server

### notes

ส่งเป็น array ของ object

| Field | ชื่อสำรองที่รองรับ |
| --- | --- |
| `body` | `noteText`, `note_text`, `text` |
| `createdAt` | `created_at` |
| `authorId` | `providerId` |
| `authorName` | `author` |
| `authorRole` | `role` |
| `authorColor` | `color` |

รายการ note ที่ไม่มี `body` จะถูกข้าม ถ้าไม่ส่ง `createdAt` ระบบจะใช้เวลาปัจจุบันของ server

## ตัวอย่าง curl

```bash
curl -X POST "https://icucons.plkhealth.go.th/api/icu" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ICU_API_TOKEN" \
  -d '{
    "patient": {
      "hn": "68000123",
      "cid": "1234567890123",
      "name": "สมชาย ใจดี",
      "age": 67,
      "gender": "male",
      "allergies": "Penicillin",
      "conditions": "Hypertension, Diabetes mellitus"
    },
    "case": {
      "hospital": "โรงพยาบาลตัวอย่าง",
      "priority": "High",
      "specialty": "Critical Care",
      "reason": "Respiratory failure",
      "senderId": "external-his-001"
	    },
	    "vitals": [
	      {
	        "createdAt": "2026-05-25T09:31:00+07:00",
	        "bp": "130/82",
        "hr": "118",
        "rr": "30",
        "spo2": "91"
      }
    ]
  }'
```

## ตัวอย่าง JavaScript

```js
const response = await fetch('https://icucons.plkhealth.go.th/api/icu', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${process.env.ICU_API_TOKEN}`,
  },
  body: JSON.stringify({
    patient: {
      hn: '68000123',
      cid: '1234567890123',
      name: 'สมชาย ใจดี',
      age: 67,
    },
    case: {
      hospital: 'โรงพยาบาลตัวอย่าง',
      priority: 'High',
      specialty: 'Critical Care',
      reason: 'Respiratory failure',
      senderId: 'external-his-001',
    },
  }),
});

const data = await response.json();

if (!response.ok) {
  throw new Error(data.error || 'Failed to send ICUCON data');
}

console.log(data);
```

## ตัวอย่าง Python

```python
import os
import requests

url = "https://icucons.plkhealth.go.th/api/icu"
token = os.environ["ICU_API_TOKEN"]

payload = {
    "patient": {
        "hn": "68000123",
        "cid": "1234567890123",
        "name": "สมชาย ใจดี",
        "age": 67,
    },
    "case": {
        "hospital": "โรงพยาบาลตัวอย่าง",
        "priority": "High",
        "specialty": "Critical Care",
        "reason": "Respiratory failure",
        "senderId": "external-his-001",
    },
}

response = requests.post(
    url,
    json=payload,
    headers={"Authorization": f"Bearer {token}"},
    timeout=15,
)
response.raise_for_status()
print(response.json())
```

## Response เมื่อสำเร็จ

กรณีสร้าง/อัปเดต consult case:

```json
{
  "success": true,
  "caseId": "123",
  "case": {
    "id": "123",
    "patientName": "สมชาย ใจดี",
    "hospital": "โรงพยาบาลตัวอย่าง",
    "status": "Pending",
    "priority": "High"
  },
  "inserted": {
    "vitals": 1,
    "labs": 1,
    "medications": 1,
    "notes": 1
  }
}
```

กรณีบันทึกเฉพาะข้อมูลผู้ป่วย:

```json
{
  "success": true,
  "patientId": "45",
  "patient": {
    "id": 45,
    "patientName": "สมชาย ใจดี",
    "hn": "68000123",
    "cid": "1234567890123"
  },
  "caseId": null,
  "case": null,
  "registered": false
}
```

## Error Response

### Token ไม่ถูกต้อง

```json
{
  "success": false,
  "error": "Unauthorized ICU API request"
}
```

HTTP status: `401`

### JSON ไม่ถูกต้อง

```json
{
  "success": false,
  "error": "Request body must be valid JSON"
}
```

HTTP status: `400`

### Body ไม่ใช่ JSON object

```json
{
  "success": false,
  "error": "Request body must be a JSON object"
}
```

HTTP status: `400`

## ข้อควรระวัง

- ระบบค้นหาผู้ป่วยเดิมด้วย `cid` ก่อน แล้วจึงใช้ `hn` ถ้าเจอจะอัปเดตข้อมูลผู้ป่วยเดิม
- การสร้าง consult case จะใช้ patient เดิมถ้าเจอ และจะอัปเดต case เดิมของ patient นั้นถ้ามีอยู่แล้ว
- ถ้าต้องการสร้าง consult case ต้องส่ง key `case`, `consult` หรือ `request` อย่างน้อยหนึ่ง key
- `allergies` และ `conditions` ส่งได้ทั้ง array และ string คั่นด้วย comma
- `vitals`, `labs`, `medications` และ `notes` จะถูกบันทึกหลังจากสร้าง/อัปเดต consult case สำเร็จ
- ค่า date/time ควรส่งเป็น ISO 8601 เช่น `2026-05-25T09:30:00+07:00`
- Production ควรเปิดใช้งาน HTTPS และตั้งค่า `ICU_API_TOKEN` เสมอ

## Checklist สำหรับ External Client

- เตรียม URL endpoint ให้ตรงกับ environment
- ตั้งค่า token ตรงกับ `ICU_API_TOKEN` บน server
- ส่ง `Content-Type: application/json`
- ส่ง `Authorization: Bearer ...` หรือ `x-api-key: ...`
- ใส่ `patient.hn` หรือ `patient.cid` เพื่อให้ระบบจับคู่ผู้ป่วยได้แม่นยำ
- ใส่ `case`, `consult` หรือ `request` เมื่อต้องการเปิด consult case
- ตรวจ `response.ok` หรือ HTTP status ทุกครั้ง
- log `caseId` ที่ได้กลับมาเพื่อ trace กลับจากระบบต้นทาง
