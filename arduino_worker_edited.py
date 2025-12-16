print("[INFO] Worker script started.")
import serial
import time
import redis
import json
import sys

# ==============================================================================
# --- CẤU HÌNH HỆ THỐNG ---
# ==============================================================================
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
SERIAL_PORT = '/dev/ttyUSB0' # Sửa lại đúng cổng USB của bạn (vd: /dev/ttyUSB0 hoặc COM3)
BAUD_RATE = 115200
ARDUINO_COMMAND_TIMEOUT = 120.0 
MAX_TRAYS_OUT = 1
PRIORITY_QUEUES = ['queue:high', 'queue:medium', 'queue:low']

# ==============================================================================
# --- KẾT NỐI ---
# ==============================================================================
print("[INFO] Connecting to Redis...")
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    print(f"[INFO] Redis connected: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    sys.exit(f"[ERROR] Redis connection failed: {e}")

print("[INFO] Connecting to Arduino...")
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1) # Timeout nhỏ để loop nhanh
    time.sleep(2) # Chờ Arduino khởi động lại sau khi mở Serial
    print(f"[INFO] Serial connected: {SERIAL_PORT}")
except Exception as e:
    sys.exit(f"[ERROR] Serial connection failed: {e}")

# Reset trạng thái
r.setnx('trays_out_count', 0)
# r.set('current_shelf', 1) # Có thể bỏ dòng này để giữ trạng thái cũ nếu muốn

# ==============================================================================
# ---  ĐỒNG BỘ TRẠNG THÁI BAN ĐẦU (SYNC STATE) ---
# ==============================================================================
def sync_initial_state():
    # 1. Lấy vị trí kệ được lưu lần cuối trong Redis
    saved_shelf = r.get('current_shelf')
    
    # Nếu chưa có (chạy lần đầu), mặc định là 1
    if not saved_shelf:
        saved_shelf = 1
        r.set('current_shelf', 2)
    
    print(f"[INFO] Đang đồng bộ vị trí kệ {saved_shelf} xuống Arduino...")

    # 2. Gửi lệnh SET xuống (Lệnh này chỉ set biến, không xoay)
    # Lưu ý: Chúng ta dùng hàm ExecuteOnArduino nhưng cần định nghĩa lệnh SET trong Arduino
    ser.reset_input_buffer()
    ser.write(f"SET:{saved_shelf}\n".encode())
    
    # 3. Chờ xác nhận từ Arduino
    start_time = time.time()
    while time.time() - start_time < 3: # Chờ tối đa 3s
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("DONE"):
                print(f"[SUCCESS] Arduino đã nhận diện kệ hiện tại là: {saved_shelf}")
                return
        time.sleep(0.1)
    
    print("[WARNING] Không nhận được phản hồi đồng bộ từ Arduino.")

# GỌI HÀM VỪA VIẾT
sync_initial_state()

# ==============================================================================
# --- HÀM GỬI LỆNH & XỬ LÝ PHẢN HỒI ---
# ==============================================================================

def send_response_to_web(msg_type, data):
    """Gửi tin nhắn phản hồi vào kênh Redis để consumers.py đọc"""
    msg = {
        "type": msg_type,
        **data
    }
    r.publish('arduino_responses', json.dumps(msg))

def ExecuteOnArduino(command_str):
    """
    Gửi lệnh xuống Arduino và lắng nghe phản hồi.
    Hỗ trợ đọc:
    - DONE:X -> Hoàn thành, cập nhật kệ hiện tại là X
    - SHELF:X -> (Tùy chọn) Arduino báo đang đi qua kệ X
    - ERROR:Msg -> Lỗi
    """
    print(f"  [TX] -> ARDUINO: {command_str}")
    
    # Xóa buffer cũ và gửi lệnh mới
    ser.reset_input_buffer()
    ser.write(f"{command_str}\n".encode())
    
    start_time = time.time()
    
    while True:
        # Timeout
        if time.time() - start_time > ARDUINO_COMMAND_TIMEOUT:
            print(f"  [ERROR] Timeout lệnh {command_str}")
            return False, -1

        # Đọc dữ liệu từ Serial
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
            except:
                continue
            
            if not line: continue
            
            print(f"  [RX] <- {line}") # Log để debug

            # 1. Xử lý hoàn tất
            if line.startswith("DONE"):
                # Cấu trúc mong đợi: DONE:3 (Đã xong, đang ở kệ 3)
                parts = line.split(':')
                final_shelf = -1
                if len(parts) > 1 and parts[1].isdigit():
                    final_shelf = int(parts[1])
                return True, final_shelf

            # 2. Xử lý cập nhật vị trí real-time (Nếu Arduino code có in ra SHELF:X)
            elif line.startswith("SHELF"):
                # Cấu trúc: SHELF:2 (Đang đi qua kệ 2)
                parts = line.split(':')
                if len(parts) > 1 and parts[1].isdigit():
                    s_val = int(parts[1])
                    # Gửi ngay lên Web để số nhảy
                    send_response_to_web("shelf_update", {"shelf": s_val})
                    r.set('current_shelf', s_val)

            # 3. Xử lý lỗi
            elif line.startswith("ERROR"):
                print(f"  [ARDUINO ERROR] {line}")
                return False, -1

        time.sleep(0.01) # Nghỉ nhẹ để giảm tải CPU

# ==============================================================================
# --- MAIN LOOP ---
# ==============================================================================
print("\n[INFO] Worker HARDWARE đang chạy...")

while True:
    try:
        # Lắng nghe Redis (Blocking)
        task_raw = r.blpop(PRIORITY_QUEUES, timeout=1)
        
        if task_raw:
            source_queue, task_json = task_raw
            task = json.loads(task_json)
            
            # Hỗ trợ cả 2 loại key (giống bản testing)
            cmd_type = task.get('command') or task.get('cmd')
            
            print(f"\n[TASK] Nhận lệnh: {cmd_type} | Data: {task}")

            if cmd_type == 'HOMING':
                success, new_shelf = ExecuteOnArduino("HOMING")
                if success:
                    final_shelf = 2 if new_shelf == -1 else new_shelf
                    
                    r.set('current_shelf', final_shelf)
                    
                    # Báo xong việc
                    send_response_to_web("HOMING_COMPLETE", {"shelf": final_shelf})
                    
                    # Cập nhật số hiển thị
                    send_response_to_web("shelf_update", {"shelf": final_shelf})

                    

            elif cmd_type in ['FETCH', 'FETCH_TRAY']:
                # Logic kiểm tra số lượng khay lấy ra
                current_out = int(r.get('trays_out_count') or 0)
                if current_out >= MAX_TRAYS_OUT:
                    print("  [INFO] Đã max khay out. Đẩy lại vào hàng đợi.")
                    r.rpush(source_queue, task_json) # Đẩy lại vào cuối hàng đợi
                    time.sleep(2)
                    continue

                t_shelf = task.get('shelf')
                t_tray = task.get('tray')
                
                # Gửi lệnh FETCH xuống Arduino
                # Arduino tự lo việc xoay 1 chiều hay 2 chiều
                success, final_shelf = ExecuteOnArduino(f"FETCH:{t_shelf}:{t_tray}")
                
                if success:
                    if final_shelf != -1: 
                        r.set('current_shelf', final_shelf)
                        send_response_to_web("shelf_update", {"shelf": final_shelf})

                    r.incr('trays_out_count')
                    
                    send_response_to_web("FETCH_COMPLETE", {
                        "shelf": t_shelf,
                        "tray": t_tray,
                        "dropoff": task.get('dropoff', 1)
                    })

            elif cmd_type in ['STORE', 'STORE_TRAY']:
                t_shelf = task.get('shelf')
                t_tray = task.get('tray')
                
                success, final_shelf = ExecuteOnArduino(f"STORE:{t_shelf}:{t_tray}")
                
                if success:
                    if final_shelf != -1: 
                        r.set('current_shelf', final_shelf)
                        send_response_to_web("shelf_update", {"shelf": final_shelf})

                    old_val = int(r.get('trays_out_count') or 1)
                    if old_val > 0: r.decr('trays_out_count')
                    
                    send_response_to_web("STORE_COMPLETE", {
                        "shelf": t_shelf,
                        "tray": t_tray,
                        "dropoff": task.get('dropoff', 1)
                    })

            else:
                print(f"  [WARN] Lệnh không xác định: {cmd_type}")

    except KeyboardInterrupt:
        print("\n[STOP] Đóng kết nối Serial.")
        ser.close()
        break
    except Exception as e:
        print(f"\n[ERROR] Lỗi Worker: {e}")
        time.sleep(2)