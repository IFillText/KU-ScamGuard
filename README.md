# README.md

## KU ScamGuard Dataset & Service

**Version:** v3.0  
**Created:** October 2026  
**Institution:** Kasetsart University, Kamphaeng Saen Campus  

---

## 1. Dataset Description

This dataset contains Thai text messages collected from LINE chat groups, social media platforms, and university student communities for scam message detection and hierarchical risk classification.

* **Number of messages:** 2,999
* **Number of risk levels:** 3 classes (Normal, Suspicious, Scam)
* **Number of scam sub-categories:** 10 categories
* **Language:** Thai (with common English transliterations and abbreviations)
* **Format:** Excel (`.xlsx`) / Structured Text

---

## 2. Class Labels

### 2.1 Primary Risk Level (Level 1)

| Label | Class | Description | Samples |
| :---: | :--- | :--- | :---: |
| 0 | Normal | ข้อความสนทนาทั่วไป ข่าวสาร การสอบถามข้อมูล ไม่มีความเสี่ยง | 999 |
| 1 | Suspicious | ข้อความน่าสงสัย มีความเสี่ยงปานกลาง (เชิญชวนทำงาน, แจกของ, ให้คลิกลิงก์) | 1,000 |
| 2 | Scam | ข้อความหลอกลวง มิจฉาชีพชัดเจน (หลอกโอนเงิน, หลอกขอ OTP, ปลอมทุนการศึกษา) | 1,000 |

### 2.2 Scam Sub-Categories (Level 2 - 2,000 Messages)

| Category | Description | Samples |
| :--- | :--- | :---: |
| `marketplace` | หลอกขายสินค้าออนไลน์ / สินค้าราคาถูกผิดปกติ / ไม่ส่งของ | 395 |
| `phishing` | ลิงก์ฟิชชิ่ง ดักขโมยรหัสผ่านหรือข้อมูลส่วนตัว | 275 |
| `ku` | ข้อความหลอกลวงที่แอบอ้าง ม.เกษตรศาสตร์ / กิจกรรม / ทุนภายใน มก. | 227 |
| `job` | หลอกทำงานออนไลน์ / รับสมัครงานพาร์ตไทม์รายได้สูง / กดรับออเดอร์ | 227 |
| `impersonation` | แอบอ้างเป็นบุคคล สถาบัน เจ้าหน้าที่รัฐ หรือองค์กรต่างๆ | 211 |
| `otp` | ล่อลวงให้บอกรหัส OTP หรือรหัสความปลอดภัยทางการเงิน | 191 |
| `fake_scholarship` | ทุนการศึกษาปลอม / อ้างสิทธิ์รับทุนแต่ต้องจ่ายค่าธรรมเนียมล่วงหน้า | 189 |
| `refund` | หลอกคืนเงิน / พัสดุตีกลับ / ขอเคลมเงินภาษีหรือค่าสินค้า | 145 |
| `delivery` | แอบอ้างบริษัทขนส่ง แจ้งว่ามีพัสดุตกค้างหรือต้องชำระค่าธรรมเนียม | 140 |
| `none` | ข้อความปกติทั่วไป (Normal) ไม่จัดเป็นกลโกง | 999 |

---

## 3. Dataset Structure

```text
KU-ScamGuard/
├── KU_ScamGuard_dataset_Rezero2.xlsx   # Cleaned & balanced dataset (2,999 samples)
├── models/                             # Pre-trained & Fine-tuned Multi-task Models
│   ├── phayathaibert/                  # PhayaThaiBERT (Default best model - Macro F1: 0.9891)
│   ├── wangchanberta/                  # WangchanBERTa (Macro F1: 0.9782)
│   └── xlm_roberta/                    # XLM-RoBERTa (Macro F1: 0.9803)
├── app.py                              # Flask Web Server & LINE Webhook Controller
├── predictor.py                        # Hierarchical Inference Engine & Threshold Manager
├── flex_messages.py                    # LINE Alert UI Templates (Red / Yellow Card)
├── tunnel.py                           # Cloudflare Tunnel for Public Webhook
├── requirements.txt                    # Python Dependencies
├── .env.example                        # Environment Variable Configuration Template
└── README.md                           # Dataset & System Documentation
```

---

## 4. Data Source

1. **Initial Open Dataset:** รวบรวมข้อมูลเริ่มต้นจาก Open Dataset (`tu_scam`) จำนวน 2,999 ข้อความ
2. **Data Cleansing & Deduplication:**
   * กรองข้อความที่ซ้ำกันทุกประการ (Exact Duplicates): ลบออก 107 ข้อความ
   * ลดข้อความที่มีแพทเทิร์นใกล้เคียงกันสูง (Near-Duplicates): ลบออก 1,460 ข้อความ เพื่อป้องกัน Data Leakage และลด Overfitting (เหลือ 1,432 ข้อความ)
3. **Data Augmentation & New Collection:**
   * เพิ่มชุดข้อมูลข้อความใหม่ที่เกิดขึ้นจริงในกลุ่ม LINE และสังคมมหาวิทยาลัยเกษตรศาสตร์ จำนวน 1,567 ข้อความ
4. **Final Balanced Dataset:** รวมเป็นชุดข้อมูล Final Dataset v3 ทั้งหมด **2,999 ข้อความ** มีความสมดุลทุกคลาส (Scam 1,000 / Suspicious 1,000 / Normal 999)

---

## 5. Annotation

* ทำการตรวจสอบและจำแนกประเภท (Labeling) แบบ **Hierarchical 2 Levels** (ระดับความเสี่ยง และ หมวดหมู่กลโกงย่อย)
* ผ่านการตรวจสอบความถูกต้องโดยกลุ่มผู้พัฒนา **ULTRATHINK++** ตามเกณฑ์การวิเคราะห์กลโกงข้อความทางไซเบอร์ในบริบทภาษาไทย

---

## 6. Recommended Data Split

แบ่งชุดข้อมูลด้วยเทคนิค **Stratified Split (70 / 15 / 15)** เพื่อรักษาสัดส่วนของคลาสให้เท่ากันในทุกชุด:

| Subset | Percentage | Scam | Suspicious | Normal | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Training** | 69.4% (~70%) | 695 | 689 | 696 | **2,080** |
| **Validation** | 15.3% (~15%) | 151 | 157 | 152 | **460** |
| **Testing** | 15.3% (~15%) | 154 | 154 | 151 | **459** |
| **Total** | **100%** | **1,000** | **1,000** | **999** | **2,999** |

---

## 7. Version History

| Version | Description |
| :---: | :--- |
| **v1.0** | ชุดข้อมูลดิบตั้งต้นจากแหล่งรวบรวมสาธารณะ (tu_scam raw collection) |
| **v2.0** | ทำ Data Cleansing โดยตัดข้อความซ้ำ (-107) และกรองข้อความ Near-duplicates (-1,460) |
| **v3.0** | เพิ่มข้อความเฉพาะกลุ่มนิสิตและมิจฉาชีพยุคใหม่ (+1,567), ปรับสมดุลข้อมูล 3 คลาส (1,000/1,000/999) และจัดทำ 10 Scam Categories |

---

## 8. Deployment & Running Guide

### 8.1 การติดตั้งสภาพแวดล้อม (Installation)
```bash
# สร้างและเปิดใช้งาน venv
python -m venv venv
venv\Scripts\activate

# ติดตั้ง Dependencies
pip install -r requirements.txt
```

### 8.2 การตั้งค่า (.env)
คัดลอกไฟล์ `.env.example` เป็น `.env` และกรอก Channel Secret / Access Token:
```env
LINE_CHANNEL_ACCESS_TOKEN=your_token_here
LINE_CHANNEL_SECRET=your_secret_here
PORT=5000
MODEL_DIR=models/phayathaibert
```

### 8.3 การรันระบบ (Server & Tunnel)
```bash
# Terminal 1: รัน AI Webhook Server
python app.py

# Terminal 2: รัน Cloudflare Tunnel สำหรับเชื่อมต่อ LINE Developers Webhook
python tunnel.py
```

* **Hybrid Threshold Spec:**
  * 🔴 **Red Alert (Scam):** $P(\text{scam}) \ge 0.80$
  * 🟡 **Yellow Alert (Suspicious):** $0.45 \le P(\text{suspicious}) < 0.80$
  * ⚪ **Normal:** โหมดเงียบในกลุ่ม (Silent) / แจ้งปลอดภัยในการคุยเดี่ยว

---

## 9. Contact

**Project Team:** ULTRATHINK++  
Department of Computer Engineering, Faculty of Engineering at Kamphaeng Saen,  
Kasetsart University, Kamphaeng Saen Campus, Nakhon Pathom, Thailand  

**Advisor & Lab:**  
Dr. Seksan Mathulaprangsan  
Pattern REcognition and Computational InTElligence Laboratory (PRECITE Lab),  
Department of Computer Engineering, Faculty of Engineering at Kamphaeng Saen,  
Kasetsart University, Thailand  
E-mail: seksan.m@ku.th  
GitHub Repository: [IFillText/KU-ScamGuard](https://github.com/IFillText/KU-ScamGuard)
