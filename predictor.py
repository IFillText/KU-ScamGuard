import os
import re
import json
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from safetensors.torch import load_file as load_safetensors

# Text cleaning patterns
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


class WangchanBERTaMultiTaskModel(nn.Module):
    def __init__(self, model_name: str, num_risk_labels: int, num_category_labels: int, dropout: float = 0.15):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        h = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.risk_classifier = nn.Linear(h, num_risk_labels)
        self.category_classifier = nn.Linear(h, num_category_labels)

    def forward(self, input_ids, attention_mask=None, token_type_ids=None):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        x = self.dropout(out.last_hidden_state[:, 0, :])
        return self.risk_classifier(x), self.category_classifier(x)


# Universal Alias สำหรับรองรับทั้ง WangchanBERTa, PhayaThaiBERT, etc.
MultiTaskTransformerModel = WangchanBERTaMultiTaskModel


# Thai display mapping and advice
CATEGORY_INFO = {
    "delivery": {
        "title": "พัสดุตกค้าง / ขนส่งพัสดุปลอม",
        "description": "มักอ้างว่ามีพัสดุตกค้าง ตีกลับ หรือติดภาษี/ศุลกากร เพื่อหลอกให้คลิกลิงก์หรือโอนเงินเคลียร์พัสดุ",
        "advice": "อย่าคลิกลิงก์ที่แนบมา ให้ตรวจสอบเลขพัสดุผ่านแอปฯ หรือเว็บไซต์ทางการของขนส่งโดยตรงเท่านั้น"
    },
    "fake_scholarship": {
        "title": "ทุนการศึกษา / แจกเงินปลอม",
        "description": "แอบอ้างแจกทุนการศึกษา เงินช่วยเหลือ หรือสิทธิพิเศษ แต่ต้องจ่ายค่าธรรมเนียมหรือกรอกข้อมูลส่วนบุคคลก่อน",
        "advice": "ทุนการศึกษาจริงจะไม่มีการเรียกเก็บค่าธรรมเนียมใดๆ ทั้งสิ้น ให้ติดต่อสอบถามกองกิจการนิสิต/ฝ่ายทุนโดยตรง"
    },
    "impersonation": {
        "title": "แอบอ้างบุคคลหรือหน่วยงาน",
        "description": "แอบอ้างเป็นตำรวจ เจ้าหน้าที่รัฐ อาจารย์ หรือเพื่อน ขอให้โอนเงินช่วยเหลือฉุกเฉิน",
        "advice": "โทรตรวจสอบกับบุคคลหรือหน่วยงานนั้นโดยตรงผ่านเบอร์ติดต่อทางการ ห้ามโอนเงินเด็ดขาด"
    },
    "job": {
        "title": "หลอกชวนทำงานออนไลน์ / งานกดไลก์",
        "description": "โฆษณางานง่าย รายได้ดี ทำที่บ้านได้ แต่สุดท้ายต้องสำรองจ่ายเงินเพื่อเปิดออเดอร์หรือถอนเงินไม่ได้",
        "advice": "ไม่มีงานกดรับออเดอร์หรือกดไลก์ที่ให้เงินจริง หากมีการเรียกเก็บเงินมัดจำ/สำรองจ่ายให้หยุดทันที"
    },
    "marketplace": {
        "title": "ซื้อขายสินค้าออนไลน์ / ร้านค้าปลอม",
        "description": "ประกาศขายสินค้าราคาถูกผิดปกติ มีการเร่งให้โอนเงินมัดจำ หรือส่งหลักฐานสลิปปลอม",
        "advice": "ซื้อขายผ่านแพลตฟอร์มที่มีระบบคุ้มครองผู้ซื้อ หลีกเลี่ยงการโอนตรงบัญชีบุคคลธรรมดาที่ไม่รู้จัก"
    },
    "otp": {
        "title": "หลอกขอรหัสผ่าน / OTP",
        "description": "หลอกล่อให้บอกรหัส OTP หรือรหัสยืนยันตัวตน เพื่อเข้าถึงแอปธนาคารหรือบัญชีโซเชียล",
        "advice": "รหัส OTP เป็นความลับส่วนบุคคล ห้ามแจ้งให้ใครทราบในทุกกรณีเด็ดขาด"
    },
    "phishing": {
        "title": "เว็บไซต์ปลอม / ฟิชชิ่งดักข้อมูล",
        "description": "ส่งลิงก์หลอกให้เข้าสู่ระบบ หรือดาวน์โหลดแอปดูดเงิน/ไฟล์อันตราย (.apk)",
        "advice": "ห้ามคลิกลิงก์แปลกปลอม และห้ามติดตั้งแอปนอก Google Play Store / Apple App Store"
    },
    "refund": {
        "title": "หลอกคืนเงิน / เคลมภาษี / คืนค่าไฟ",
        "description": "อ้างว่ามีเงินคืนจากการไฟฟ้า ค่าน้ำ หรือเงินภาษีเกิน หลอกให้แอดไลน์ติดตั้งแอปเพื่อรับเงิน",
        "advice": "หน่วยงานรัฐไม่มีนโยบายทักแชตเพื่อคืนเงินหรือส่งลิงก์ดาวน์โหลดแอป ให้ตรวจสอบผ่านแอปทางการเท่านั้น"
    },
    "tu": {
        "title": "แอบอ้างสถาบันการศึกษา / มหาวิทยาลัย",
        "description": "แอบอ้างชื่อมหาวิทยาลัย กิจกรรมนักศึกษา หรือระบบการศึกษาเพื่อหลอกเอารหัสผ่านหรือเงิน",
        "advice": "ตรวจสอบประกาศจากเพจหรือช่องทางทางการของมหาวิทยาลัยเท่านั้น"
    },
    "none": {
        "title": "ข้อความปกติ",
        "description": "ไม่พบพฤติกรรมหลอกลวง",
        "advice": "ข้อความปลอดภัย ไม่พบความเสี่ยงมิจฉาชีพ"
    }
}


class ScamGuardPredictor:
    def __init__(self, model_dir: str = "models/wangchanberta"):
        if not os.path.exists(model_dir) and os.path.exists("ku_scamguard_model"):
            model_dir = "ku_scamguard_model"
        self.model_dir = model_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        config_path = os.path.join(model_dir, "scamguard_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
            
        self.risk_labels = self.config.get("risk_labels", ["normal", "scam", "suspicious"])
        self.categories = self.config.get("categories", [
            "delivery", "fake_scholarship", "impersonation", "job", "marketplace", "none", "otp", "phishing", "refund", "tu"
        ])
        self.max_len = self.config.get("max_len", 192)
        self.t_red = self.config.get("t_red", 0.55)
        self.t_yellow = self.config.get("t_yellow", 0.45)
        
        self.risk2id = {r: i for i, r in enumerate(self.risk_labels)}
        self.category2id = {c: i for i, c in enumerate(self.categories)}
        
        # Build category mask
        # Normal (id 0) -> only 'none' allowed
        # Scam (id 1) & Suspicious (id 2) -> all except 'none'
        self.category_mask = torch.zeros(len(self.risk_labels), len(self.categories), dtype=torch.bool)
        none_idx = self.category2id.get("none", -1)
        if none_idx != -1:
            self.category_mask[self.risk2id["normal"], none_idx] = True
            for r_name in ["scam", "suspicious"]:
                if r_name in self.risk2id:
                    self.category_mask[self.risk2id[r_name], :] = True
                    self.category_mask[self.risk2id[r_name], none_idx] = False

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        
        # Build Model
        self.model = WangchanBERTaMultiTaskModel(
            self.config["base_model"],
            len(self.risk_labels),
            len(self.categories)
        ).to(self.device)
        
        # Load weights (safetensors or pt)
        safetensors_path = os.path.join(model_dir, "model.safetensors")
        pt_path = os.path.join(model_dir, "model.pt")
        
        if os.path.exists(safetensors_path):
            state_dict = load_safetensors(safetensors_path)
            self.model.load_state_dict(state_dict)
        elif os.path.exists(pt_path):
            state_dict = torch.load(pt_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state_dict)
        else:
            raise FileNotFoundError(f"ไม่พบไฟล์น้ำหนักโมเดลใน {model_dir}")
            
        self.model.eval()

    @torch.no_grad()
    def predict(self, raw_text: str) -> dict:
        cleaned = clean_text(raw_text)
        
        inputs = self.tokenizer(
            cleaned,
            truncation=True,
            max_length=self.max_len,
            padding=True,
            return_tensors="pt"
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(self.device == "cuda")):
            risk_logits, cat_logits = self.model(**inputs)
            
        risk_probs = torch.softmax(risk_logits.float(), -1)[0].cpu().numpy()
        
        # Map probabilities: normal, scam, suspicious
        p_normal = float(risk_probs[self.risk2id["normal"]])
        p_scam = float(risk_probs[self.risk2id["scam"]])
        p_suspicious = float(risk_probs[self.risk2id["suspicious"]])
        
        # Threshold decision logic
        if p_scam >= self.t_red:
            level = 2
            level_name = "scam"
            color_badge = "🔴 อันตรายสูง (มิจฉาชีพ)"
            pred_risk_id = self.risk2id["scam"]
        elif max(p_suspicious, p_scam) >= self.t_yellow:
            level = 1
            level_name = "suspicious"
            color_badge = "🟡 เฝ้าระวัง (น่าสงสัย)"
            pred_risk_id = self.risk2id["suspicious"]
        else:
            level = 0
            level_name = "normal"
            color_badge = "🟢 ปลอดภัย (ข้อความปกติ)"
            pred_risk_id = self.risk2id["normal"]
            
        # Apply Category Mask based on predicted risk level
        allowed_cats = self.category_mask[pred_risk_id].to(self.device)
        masked_cat_logits = cat_logits[0].float().masked_fill(~allowed_cats, -1e4)
        masked_cat_probs = torch.softmax(masked_cat_logits, -1).cpu().numpy()
        
        top_cat_idx = int(masked_cat_probs.argmax())
        top_cat_name = self.categories[top_cat_idx]
        top_cat_prob = float(masked_cat_probs[top_cat_idx])
        
        cat_info = CATEGORY_INFO.get(top_cat_name, {
            "title": top_cat_name,
            "description": "ตรวจพบพฤติกรรมเสี่ยง",
            "advice": "โปรดระมัดระวังและตรวจสอบข้อเท็จจริงก่อนทำธุรกรรม"
        })
        
        # Detect entities in raw text
        has_url = bool(URL_RE.search(raw_text))
        has_phone = bool(PHONE_RE.search(raw_text))
        has_line = bool(LINE_RE.search(raw_text))
        has_bank = bool(BANK_RE.search(raw_text))
        
        return {
            "raw_text": raw_text,
            "cleaned_text": cleaned,
            "level": level,
            "level_name": level_name,
            "color_badge": color_badge,
            "risk_scores": {
                "normal": p_normal,
                "suspicious": p_suspicious,
                "scam": p_scam
            },
            "top_category": {
                "name": top_cat_name,
                "title": cat_info["title"],
                "description": cat_info["description"],
                "advice": cat_info["advice"],
                "probability": top_cat_prob
            },
            "entities_detected": {
                "url": has_url,
                "phone": has_phone,
                "line_id": has_line,
                "bank_acc": has_bank
            }
        }
