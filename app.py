"""
KU ScamGuard - Flask webhook สำหรับ LINE Messaging API
โหลดโมเดลที่เทรนไว้ในเครื่อง (ku_scamguard_model/) หรือ Hugging Face Hub
แล้วตัดสินระดับความเสี่ยงของข้อความที่ถูกส่งเข้ามาใน LINE จากนั้นตอบกลับตามระดับ Red / Yellow / Silent
"""

import os
import sys
import re
import json
import logging

# รองรับ UTF-8 Console บน Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

import torch
import torch.nn as nn
from flask import Flask, request, abort
from transformers import AutoTokenizer, AutoModel

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ku_scamguard")

# --------------------------------------------------------------------------
# ค่าที่ตั้งผ่าน Environment Variables หรือ .env
# --------------------------------------------------------------------------
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "").strip()
MODEL_DIR = os.getenv("MODEL_DIR", "models/wangchanberta")
if not os.path.exists(MODEL_DIR) and os.path.exists("ku_scamguard_model"):
    MODEL_DIR = "ku_scamguard_model"
PORT = int(os.getenv("PORT", 5000))

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    log.warning("⚠️  LINE_CHANNEL_ACCESS_TOKEN หรือ LINE_CHANNEL_SECRET ยังไม่ได้ตั้งค่าใน .env")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
log.info("device: %s", DEVICE)

# --------------------------------------------------------------------------
# ฟังก์ชันทำความสะอาดข้อความ (logic เดียวกับตอนเทรน ห้ามแก้ไขต่างกัน)
# --------------------------------------------------------------------------
URL_RE = re.compile(
    r'(?i)(?:https?://|www\.)\S+|\b[a-z0-9][a-z0-9\-]*(?:\.[a-z0-9\-]+)*\.'
    r'(?:invalid|com|net|org|io|co|me|th|ly|link|xyz|top|info)\b(?:/\S*)?|\bbit\.ly/\S+'
)
LINE_RE = re.compile(
    r'(?i)(?:\b(?:line(?:\s*id)?|ไลน์|ไอดีไลน์)\s*[:：]?\s*)?@[A-Za-z0-9._\-]+'
)
PHONE_RE = re.compile(r'(?<!\d)0\d[\dxX][- ]?[\dxX]{3}[- ]?[\dxX]{3,4}(?!\d)')
BANK_RE = re.compile(r'(?i)\b(?:x{2,}\d{2,}|\d{3}-\d-\d{5}-\d|\d{10,12})\b')


def clean_text(t: str) -> str:
    t = URL_RE.sub('[URL]', t)
    t = LINE_RE.sub('[LINE_ID]', t)
    t = PHONE_RE.sub('[PHONE]', t)
    t = BANK_RE.sub('[BANK_ACC]', t)
    return re.sub(r'\s+', ' ', t).strip()


# --------------------------------------------------------------------------
# โหลดโมเดลผ่าน ScamGuardPredictor (รองรับทั้ง model.safetensors และ model.pt)
# --------------------------------------------------------------------------
from predictor import ScamGuardPredictor

log.info("กำลังโหลดโมเดลจากโฟลเดอร์ %s ...", MODEL_DIR)
predictor = ScamGuardPredictor(model_dir=MODEL_DIR)
log.info("✅ โมเดลโหลดสำเร็จ: Device=%s | Thresholds: T_red=%.2f, T_yellow=%.2f", predictor.device, predictor.t_red, predictor.t_yellow)


def build_alert_message(result: dict) -> str | None:
    """แปลงผลจาก predictor.predict() เป็นข้อความที่จะตอบกลับ"""
    p_scam = result["risk_scores"].get("scam", 0.0)
    p_sus = result["risk_scores"].get("suspicious", 0.0)
    cat = result["top_category"]

    if result["level"] == 2:  # Scam
        return (
            f"🚨 ระวัง! ข้อความนี้มีลักษณะหลอกลวง ({p_scam:.0%})\n"
            f"ประเภทที่พบ: {cat['title']}\n"
            f"💡 คำแนะนำ: {cat['advice']}\n"
            "⚠️ อย่าโอนเงิน อย่ากดลิงก์ อย่าให้ OTP/รหัสผ่าน\n"
            "📞 สายด่วนตำรวจไซเบอร์ โทร 1441"
        )
    if result["level"] == 1:  # Suspicious
        return (
            f"⚠️ ข้อควรระวัง! ข้อความนี้น่าสงสัย ({max(p_sus, p_scam):.0%})\n"
            f"อาจเกี่ยวข้องกับ: {cat['title']}\n"
            f"💡 คำแนะนำ: {cat['advice']}\n"
            "โปรดตรวจสอบแหล่งที่มาให้แน่ใจก่อนดำเนินการใด ๆ"
        )
    return None   # silent: ไม่ตอบกลับในกลุ่มเมื่อข้อความเป็นปกติ


# --------------------------------------------------------------------------
# Flask + LINE webhook
# --------------------------------------------------------------------------
app = Flask(__name__)

if LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN:
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
else:
    handler = None
    line_config = None


@app.route("/callback", methods=["POST"])
def callback():
    if handler is None:
        log.error("LINE credentials ยังไม่ได้ตั้งค่าใน .env")
        abort(500)
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


if handler:
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_message(event):
        text = event.message.text.strip()
        log.info("ได้รับข้อความ: %r", text)

        # คำสั่งช่วยเหลือ
        if text.lower() in ["help", "วิธีใช้", "คู่มือ", "สวัสดี"]:
            help_text = (
                "🛡️ KU ScamGuard AI Bot พร้อมทำงาน!\n\n"
                "• ส่งข้อความที่น่าสงสัยมาให้บอทตรวจสอบได้ตลอดเวลา\n"
                "• หรือดึงบอทเข้ากลุ่มไลน์ บอทจะแจ้งเตือนอัตโนมัติเมื่อพบข้อความมิจฉาชีพ 🚨\n"
                "• ข้อความปกติทั่วไป บอทจะไม่ส่งข้อความรบกวนครับ"
            )
            with ApiClient(line_config) as api_client:
                MessagingApi(api_client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=help_text)],
                    )
                )
            return

        result = predictor.predict(text)
        log.info("ผลการตรวจ msg=%r -> level=%s (score=%.2f)", text, result["level_name"], result["risk_scores"].get("scam", 0.0))

        reply_text = build_alert_message(result)
        if reply_text is None:
            # ตรวจสอบว่าเป็นแชตเดี่ยว (user) หรือแชตกลุ่ม (group/room)
            source_type = getattr(event.source, "type", "user")
            if source_type == "user":
                # แชตส่วนตัว: ตอบให้ทราบว่าปลอดภัย จะได้ไม่เงียบจนคิดว่าบอทไม่ทำงาน
                reply_text = "✅ ข้อความปกติ: ไม่พบพฤติกรรมหลอกลวงหรือน่าสงสัยครับ"
            else:
                return   # แชตกลุ่ม: silent mode ไม่ส่งข้อความรบกวน

        # พยายามส่งการ์ด Flex Message ก่อน ถ้ามีปัญหาให้ fallback เป็น Text Message
        try:
            from flex_messages import create_scam_report_flex
            from linebot.v3.messaging import FlexMessage, FlexContainer

            flex_content = create_scam_report_flex(result)
            flex_container = FlexContainer.from_dict(flex_content)
            alt_text = f"ผลตรวจสอบข้อความ: {result['color_badge']} ({result['top_category']['title']})"
            msg_payload = FlexMessage(alt_text=alt_text, contents=flex_container)
        except Exception as fe:
            log.warning("ไม่สามารถสร้าง Flex Message ได้ ใช้ Text ธรรมดาแทน: %s", fe)
            msg_payload = TextMessage(text=reply_text)

        with ApiClient(line_config) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[msg_payload],
                )
            )


@app.route("/", methods=["GET"])
def health():
    return {
        "status": "online",
        "service": "KU ScamGuard LINE Bot",
        "device": DEVICE,
        "line_configured": bool(handler is not None)
    }


if __name__ == "__main__":
    log.info("Starting KU ScamGuard LINE Bot on port %d...", PORT)
    app.run(host="0.0.0.0", port=PORT)
