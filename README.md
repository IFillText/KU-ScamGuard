# KU ScamGuard - Deployment & Tunnel Service

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Model](https://img.shields.io/badge/Model-WangchanBERTa-orange.svg)](https://huggingface.co/airesearch/wangchanberta-base-att-spm-uncased)

KU ScamGuard เป็นบริการ Webhook และ AI Inference Service สำหรับตรวจจับข้อความหลอกลวง / มิจฉาชีพ (Scam Detection) บน **LINE Messaging API** ขับเคลื่อนด้วยโมเดลภาษาไทย **WangchanBERTa** (Multi-task Classification: Risk Level & Scam Category)

---

## 📁 โครงสร้างโปรเจกต์ (Clean Deployment Structure)

```text
Scammer_local/
├── models/                       # โฟลเดอร์รวมโมเดล (รองรับหลายโมเดลเพื่อเปรียบเทียบ)
│   ├── wangchanberta/            # 1. โมเดล WangchanBERTa (ค่าเริ่มต้น)
│   ├── phayathaibert/            # 2. โมเดล PhayaThaiBERT
│   └── xlm_roberta/              # 3. โมเดล XLM-RoBERTa
├── train_phayathaibert_colab.ipynb # Colab Notebook สำหรับเทรน PhayaThaiBERT
├── train_xlm_roberta_colab.ipynb   # Colab Notebook สำหรับเทรน XLM-RoBERTa
├── KU_ScamGuard_dataset_Rezero2.xlsx # Dataset สำหรับใช้เทรน
├── app.py                        # Flask Web Server & LINE Webhook Controller
├── predictor.py                  # Class Inference (ScamGuardPredictor รองรับทุกโมเดล)
├── flex_messages.py              # เทมเพลต LINE Flex Message สำหรับแจ้งเตือน
├── tunnel.py                     # Cloudflare Tunnel สำหรับรัน Localhost สู่ Public HTTPS
├── requirements.txt              # Production Dependencies
├── .env                          # Configuration & API Keys (Private)
├── .env.example                  # ตัวอย่างการตั้งค่า Environment Variables
├── .gitignore                    # Git Ignore rules
└── README.md                     # คู่มือการใช้งานระบบ
```

---

## 🚀 การติดตั้งและตั้งค่าเริ่มต้น (Getting Started)

### 1. ติดตั้ง Dependencies
แนะนำให้สร้างและใช้งาน Virtual Environment (`venv`):
```bash
# บน Windows
python -m venv venv
venv\Scripts\activate

# ติดตั้งแพ็กเกจที่จำเป็นสำหรับการ Deploy
pip install -r requirements.txt
```

### 2. ตั้งค่า Environment Variables
คัดลอกไฟล์ `.env.example` เป็น `.env` แล้วระบุค่า Token จาก [LINE Developers Console](https://developers.line.biz/):
```env
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here
PORT=5000
MODEL_DIR=models/wangchanberta
```
> **Tip การสลับโมเดลเพื่อเปรียบเทียบ:** สามารถเปลี่ยนค่า `MODEL_DIR` ใน `.env` เป็นโฟลเดอร์โมเดลอื่น เช่น `MODEL_DIR=models/another_model` เพื่อสลับไปใช้งานโมเดลใหม่ได้ทันทีโดยไม่ต้องแก้โค้ด!

---

## 💻 วิธีการรันระบบ (Running the Services)

### 1. รันเซิร์ฟเวอร์ AI Webhook (`app.py`)
```bash
python app.py
```
* เซิร์ฟเวอร์จะเริ่มต้นทำงานที่พอร์ต `5000` (หรือพอร์ตที่ระบุใน `.env`)
* ตรวจสอบสถานะการทำงานได้ที่: `http://localhost:5000/`

### 2. รัน Public Tunnel (`tunnel.py`)
เปิดอีกหนึ่ง Terminal เพื่อสร้าง Public HTTPS URL สำหรับเชื่อมต่อกับ LINE Webhook:
```bash
python tunnel.py
```
* ระบบจะแสดง **Public Tunnel URL** เช่น `https://xxxx-xxxx-xxxx.trycloudflare.com`
* นำ URL นี้ไปต่อท้ายด้วย `/callback` แล้วนำไปใส่ใน **Webhook URL** ใน LINE Developers Console:
  ```
  https://xxxx-xxxx-xxxx.trycloudflare.com/callback
  ```
* กด **Verify** และเปิดใช้งานสวิตช์ **Use webhook**

---

## 📡 Endpoints

| Method | Endpoint | รายละเอียด |
| :--- | :--- | :--- |
| `GET` | `/` | Health check endpoint แสดงสถานะเซิร์ฟเวอร์และอุปกรณ์คำนวณ (CUDA / CPU) |
| `POST` | `/callback` | LINE Webhook endpoint รับข้อความและส่งการแจ้งเตือนกลับอัตโนมัติ |

---

## 🧠 สถาปัตยกรรมโมเดล (Model Architecture)
* **Base Model:** `airesearch/wangchanberta-base-att-spm-uncased`
* **Tasks:**
  1. **Risk Level Classifier:** Normal, Scam, Suspicious
  2. **Category Classifier:** Delivery, Fake Scholarship, Impersonation, Job, Marketplace, None, OTP, Phishing, Refund, TU
* **Thresholds:**
  * Red Alert (Scam): $P(\text{scam}) \ge 0.55$
  * Yellow Alert (Suspicious): $P(\text{suspicious}) \ge 0.45$
  * Normal: Silent Mode เมื่ออยู่ในแชตกลุ่ม / แจ้งปลอดภัยเมื่อคุยส่วนตัว
