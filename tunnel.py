import sys
import time
from pycloudflared import try_cloudflare

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("กำลังสร้าง Public HTTPS Tunnel ไปยัง Port 5000...", flush=True)
try:
    urls = try_cloudflare(port=5000)
    print("\n" + "=" * 60, flush=True)
    print(f"🌐 Public Tunnel URL: {urls.tunnel}", flush=True)
    print(f"👉 ให้คัดลอก URL นี้ไปใส่ใน LINE Developers Webhook URL:", flush=True)
    print(f"   {urls.tunnel}/callback", flush=True)
    print("=" * 60, flush=True)
    print("\nเปิดค้างไว้ระหว่างใช้งาน (กด Ctrl + C เพื่อปิด Tunnel)\n", flush=True)

    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nปิด Tunnel เรียบร้อยแล้วครับ")
except Exception as e:
    print(f"เกิดข้อผิดพลาดในการสร้าง Tunnel: {e}")
