def create_scam_report_flex(result: dict) -> dict:
    level = result["level"]
    raw_text = result["raw_text"]
    cat = result["top_category"]
    risk = result["risk_scores"]
    entities = result["entities_detected"]

    # Visual theme by alert level
    if level == 2:
        header_color = "#D9534F"  # Red
        title_text = "🚨 ตรวจพบ: ข้อความมิจฉาชีพ"
        badge_text = "ระดับความเสี่ยง: อันตรายสูง (Scam)"
        cat_badge_color = "#FFEBEB"
        cat_text_color = "#C9302C"
    elif level == 1:
        header_color = "#F0AD4E"  # Orange/Yellow
        title_text = "⚠️ ตรวจพบ: ข้อความน่าสงสัย"
        badge_text = "ระดับความเสี่ยง: เฝ้าระวัง (Suspicious)"
        cat_badge_color = "#FFF8E1"
        cat_text_color = "#B78103"
    else:
        header_color = "#2ECC71"  # Green
        title_text = "✅ ปลอดภัย: ข้อความปกติ"
        badge_text = "ระดับความเสี่ยง: ไม่พบพฤติกรรมหลอกลวง"
        cat_badge_color = "#E8F8F0"
        cat_text_color = "#1E8449"

    # Entities summary text
    detected_items = []
    if entities.get("url"):
        detected_items.append("🔗 ลิงก์/เว็บไซต์")
    if entities.get("phone"):
        detected_items.append("📞 เบอร์โทรศัพท์")
    if entities.get("line_id"):
        detected_items.append("💬 LINE ID")
    if entities.get("bank_acc"):
        detected_items.append("💳 เลขบัญชีธนาคาร")
    
    entity_str = " | ".join(detected_items) if detected_items else "ไม่พบข้อมูลติดต่อผิดปกติ"

    preview_text = raw_text if len(raw_text) <= 90 else raw_text[:87] + "..."

    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": header_color,
            "paddingAll": "16px",
            "contents": [
                {
                    "type": "text",
                    "text": "KU SCAMGUARD AI",
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "size": "xs",
                    "letterSpacing": "1px"
                },
                {
                    "type": "text",
                    "text": title_text,
                    "weight": "bold",
                    "color": "#FFFFFF",
                    "size": "lg",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": badge_text,
                    "color": "#F9F9F9",
                    "size": "xs",
                    "margin": "xs"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "18px",
            "spacing": "md",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#F7F9FA",
                    "cornerRadius": "8px",
                    "paddingAll": "12px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ข้อความที่ตรวจสอบ:",
                            "size": "xs",
                            "color": "#888888",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": f'"{preview_text}"',
                            "size": "sm",
                            "color": "#333333",
                            "wrap": True,
                            "margin": "xs"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": cat_badge_color,
                    "cornerRadius": "8px",
                    "paddingAll": "12px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "ประเภทกลโกง:",
                            "size": "xs",
                            "color": "#888888",
                            "weight": "bold"
                        },
                        {
                            "type": "text",
                            "text": cat["title"],
                            "weight": "bold",
                            "color": cat_text_color,
                            "size": "md",
                            "margin": "xs"
                        },
                        {
                            "type": "text",
                            "text": cat["description"],
                            "size": "xs",
                            "color": "#555555",
                            "wrap": True,
                            "margin": "xs"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📊 ค่าความน่าจะเป็น:",
                            "size": "xs",
                            "color": "#888888",
                            "weight": "bold"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "ความเสี่ยงมิจฉาชีพ", "size": "xs", "color": "#666666", "flex": 3},
                                {"type": "text", "text": f"{risk['scam']*100:.1f}%", "size": "xs", "align": "end", "weight": "bold", "color": "#D9534F" if risk['scam']>=0.5 else "#333333", "flex": 2}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "ความน่าสงสัย", "size": "xs", "color": "#666666", "flex": 3},
                                {"type": "text", "text": f"{risk['suspicious']*100:.1f}%", "size": "xs", "align": "end", "weight": "bold", "color": "#F0AD4E" if risk['suspicious']>=0.5 else "#333333", "flex": 2}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "ข้อความปกติ", "size": "xs", "color": "#666666", "flex": 3},
                                {"type": "text", "text": f"{risk['normal']*100:.1f}%", "size": "xs", "align": "end", "weight": "bold", "color": "#2ECC71" if risk['normal']>=0.5 else "#333333", "flex": 2}
                            ]
                        }
                    ]
                },
                {
                    "type": "separator"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"🔍 ข้อมูลที่ตรวจพบ: {entity_str}",
                            "size": "xs",
                            "color": "#777777",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": f"💡 ข้อแนะนำ: {cat['advice']}",
                            "size": "xs",
                            "color": "#222222",
                            "weight": "bold",
                            "wrap": True,
                            "margin": "xs"
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "12px",
            "contents": [
                {
                    "type": "text",
                    "text": "📞 สายด่วนตำรวจไซเบอร์ โทร 1441 (24 ชม.)",
                    "size": "xxs",
                    "color": "#999999",
                    "align": "center"
                }
            ]
        }
    }
    return bubble
