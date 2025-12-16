import os
import sys
import time
import json
import redis
import django
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# ==============================================================================
# 1. CẤU HÌNH DJANGO
# ==============================================================================
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_management.settings") 

try:
    django.setup()
    print("✅ Connected to Django Environment.")
except Exception as e:
    print(f"❌ Lỗi setup Django: {e}")
    sys.exit(1)

# ==============================================================================
# 2. REDIS & CHANNELS
# ==============================================================================
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ Redis Connected.")
except Exception as e:
    print(f"❌ Lỗi kết nối Redis: {e}")
    sys.exit(1)

channel_layer = get_channel_layer()
GROUP_NAME = "carousel_control"

CURRENT_HARDWARE_SHELF = 1 
TOTAL_SHELVES = 8 # Tổng số kệ trong hệ thống

# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================

def send_to_web(msg_type, data):
    message_json = json.dumps({
        "type": msg_type,
        **data
    })
    r.publish("arduino_responses", message_json)

def simulate_rotation(target_shelf):
    """
    Hàm mô phỏng quay 1 chiều (Horizontal Carousel).
    Luôn tăng dần: 1 -> 2 -> ... -> 8 -> 1 -> ...
    """
    global CURRENT_HARDWARE_SHELF
    
    if CURRENT_HARDWARE_SHELF == target_shelf:
        print("✅ Shelf is at right place.")
        return

    print(f"🔄 Start moving from {CURRENT_HARDWARE_SHELF} to {target_shelf}...")
    
    # Vòng lặp tiếp diễn cho đến khi shelf hiện tại trùng với shelf đích
    while CURRENT_HARDWARE_SHELF != target_shelf:
        # Luôn tăng 1 đơn vị (Quay theo 1 chiều)
        CURRENT_HARDWARE_SHELF += 1
        
        # Nếu vượt quá tổng số kệ (8) thì quay về 1
        if CURRENT_HARDWARE_SHELF > TOTAL_SHELVES:
            CURRENT_HARDWARE_SHELF = 1
            
        print(f"   ... Moving to {CURRENT_HARDWARE_SHELF}")
        time.sleep(2) # Giả lập thời gian quay
        
        # Gửi cập nhật vị trí ngay lập tức lên Web
        send_to_web("shelf_update", {"shelf": CURRENT_HARDWARE_SHELF})

    print(f"✅ Move to {CURRENT_HARDWARE_SHELF} sucessfully.")


# ==============================================================================
# 4. LOGIC XỬ LÝ TASK
# ==============================================================================

def process_store_task(task_data):
    try:
        target_shelf = int(task_data.get('shelf'))
        target_tray = int(task_data.get('tray'))
        dropoff_id = task_data.get('dropoff', 1)
    except: return

    print(f"\n🚀 [STORE] STORE COMMAND: SHELF {target_shelf} - TRAY {target_tray}")

    # 1. XOAY KỆ 1 CHIỀU
    simulate_rotation(target_shelf)

    # 2. GANTRY CHỜ
    print(f"🤖 Gantry is storing tray... Type 'DONE' to complete.")
    while True:
        if input(">>> (DONE): ").strip().upper() == "DONE": break

    # 3. HOÀN TẤT
    print("💾 Update web...")
    send_to_web("STORE_COMPLETE", {
        "shelf": target_shelf,
        "tray": target_tray,
        "dropoff": dropoff_id
    })
    print("✅ Action completed.\n")

def process_fetch_task(task_data):
    global CURRENT_HARDWARE_SHELF
    try:
        target_shelf = int(task_data.get('shelf'))
        target_tray = int(task_data.get('tray'))
        dropoff_id = task_data.get('dropoff', 1)
    except: return
    
    print(f"\n🚀 [FETCH] FETCH COMMAND: SHELF {target_shelf} - TRAY {target_tray}")

    # 1. XOAY KỆ 1 CHIỀU
    simulate_rotation(target_shelf)

    # 2. GANTRY CHỜ
    print(f"👉 Gantry is taking tray... Type 'DONE' to complete .")
    while True:
        if input(">>> (DONE): ").strip().upper() == "DONE": break
            
    # 3. HOÀN TẤT
    send_to_web("FETCH_COMPLETE", {
        "shelf": target_shelf,
        "tray": target_tray,
        "dropoff": dropoff_id
    })
    print("✅ Action completed.\n")

# ==============================================================================
# 5. MAIN
# ==============================================================================
def main():
    print("Worker is running... (Click Ctrl+C to stop)")
    try:
        while True:
            task_raw = r.blpop(['queue:high', 'queue:medium'], timeout=1)
            if task_raw:
                _, task_json = task_raw
                data = json.loads(task_json)
                command = data.get('command') or data.get('cmd')
                
                print(f"📥 Nhận lệnh: {command}")

                if command in ['STORE', 'STORE_TRAY']:
                    process_store_task(data)
                elif command in ['FETCH', 'FETCH_TRAY']:
                    process_fetch_task(data)
                elif command == 'HOMING':
                    print("⚠️ HOMING...")
                    simulate_rotation(1) # Về kệ 1
                    send_to_web("HOMING_COMPLETE", {})
                else:
                    print(f"❓ Lệnh lạ: {command}")

    except KeyboardInterrupt:
        print("\n🛑 Worker Stopped.")

if __name__ == "__main__":
    main()