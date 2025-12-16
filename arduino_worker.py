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
SERIAL_PORT = '/dev/ttyUSB1'
BAUD_RATE = 115200
ARDUINO_COMMAND_TIMEOUT = 120.0  # Thời gian chờ tối đa cho một chu trình của Arduino
MAX_TRAYS_OUT = 1
PRIORITY_QUEUES = ['queue:high', 'queue:medium', 'queue:low']

# ==============================================================================
# --- KẾT NỐI VÀ HÀM THỰC THI ---
# ==============================================================================
print("[INFO] Connecting to Redis...")
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    print(f"[INFO] Đã kết nối tới Redis Server tại {REDIS_HOST}:{REDIS_PORT}")
except redis.exceptions.ConnectionError as e:
    sys.exit(f"[ERROR] Không thể kết nối tới Redis Server. Lỗi: {e}")
print("[INFO] Redis connection successful.")

print("[INFO] Connecting to Arduino...")
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    initial_message = ser.readline().decode().strip()
    if initial_message: print(f"[ARDUINO] Sẵn sàng: '{initial_message}'")
    print(f"[INFO] Đã kết nối thành công tới Arduino tại cổng {SERIAL_PORT}")
except serial.SerialException as e:
    sys.exit(f"[ERROR] Không thể mở cổng Serial '{SERIAL_PORT}'. Lỗi: {e}")
print("[INFO] Arduino connection successful.")

# Khởi tạo các giá trị trạng thái trong Redis nếu chưa tồn tại
r.setnx('trays_out_count', 0)
r.setnx('current_shelf', 1)

def ExecuteOnArduino(command_str):
    """Gửi lệnh tới Arduino và đợi phản hồi 'DONE:' hoặc 'ERROR:'."""
    print(f"  [TX] -> Gửi lệnh tới Arduino: {command_str}")
    ser.reset_input_buffer()
    ser.write(f"{command_str}\n".encode())
    start_time = time.time()

    response = ""
    new_shelf_pos = -1

    while True:
        if time.time() - start_time > ARDUINO_COMMAND_TIMEOUT:
            print(f"  [ERROR] Lệnh '{command_str}' bị timeout sau {ARDUINO_COMMAND_TIMEOUT} giây.")
            return False, new_shelf_pos

        if ser.in_waiting > 0:
            line = ser.readline().decode().strip()
            print(f"  [RX] <- Phản hồi từ Arduino: {line}") # In ra mọi phản hồi để debug
            if line.startswith("DONE"):
                parts = line.split(':')
                if len(parts) > 1:
                    try:
                        new_shelf_pos = int(parts[1])
                    except (ValueError, IndexError):
                        print(f"  [WARNING] Không thể đọc vị trí từ phản hồi: {line}")
                return True, new_shelf_pos
            elif line.startswith("ERROR") or line.startswith("Syntax error"):
                print(f"  [ERROR] Arduino báo lỗi: {line}")
                return False, new_shelf_pos

        time.sleep(0.05)

# ==============================================================================
# --- VÒNG LẶP CHÍNH CỦA WORKER ---
# ==============================================================================
print("\n[INFO] Worker đã sẵn sàng. Đang chờ nhiệm vụ...")
while True:
    try:
        source_queue, task_json = r.blpop(PRIORITY_QUEUES, timeout=0)
        task = json.loads(task_json)
        cmd_type = task.get('cmd')
        print(f"\n[TASK] Nhận nhiệm vụ '{cmd_type}' từ hàng đợi '{source_queue}'")

        command_to_send = ""
        task_successful = False

        if cmd_type == 'HOMING':
            command_to_send = "HOMING"
            success, new_shelf = ExecuteOnArduino(command_to_send)
            if success:
                r.set('current_shelf', new_shelf)
                print("[SUCCESS] Quá trình Homing hoàn tất.")
                response_message = {"type": "HOMING_COMPLETE"}
                r.publish('arduino_responses', json.dumps(response_message))
            else:
                print("[FAILURE] Quá trình Homing thất bại.")

        elif cmd_type == 'FETCH_TRAY':
            current_out = int(r.get('trays_out_count'))
            print(f"  [CHECK] Kiểm tra điều kiện: {current_out}/{MAX_TRAYS_OUT} khay đang ở ngoài.")
            if current_out >= MAX_TRAYS_OUT:
                print(f"  [INFO] Cửa ra đã có hàng. Đẩy lại nhiệm vụ vào hàng đợi '{PRIORITY_QUEUES[-1]}'.")
                r.lpush(PRIORITY_QUEUES[-1], task_json)
                time.sleep(1)
                continue

            target_shelf = task.get('shelf')
            target_tray = task.get('tray')
            command_to_send = f"FETCH:{target_shelf}:{target_tray}"

            success, new_shelf = ExecuteOnArduino(command_to_send)
            if success:
                r.set('current_shelf', new_shelf)
                r.incr('trays_out_count')
                print(f"[SUCCESS] Lấy khay {target_shelf}-{target_tray} thành công. Số khay bên ngoài: {r.get('trays_out_count')}")
                response_message = {
                    "type": "FETCH_COMPLETE",
                    "shelf": task.get('shelf'),
                    "tray": task.get('tray'),
                    "dropoff": task.get('dropoff'),
                }
                r.publish('arduino_responses', json.dumps(response_message))
            else:
                 print(f"[FAILURE] Nhiệm vụ '{cmd_type}' thất bại.")

        elif cmd_type == 'STORE_TRAY':
            target_shelf = task.get('shelf')
            target_tray = task.get('tray')
            command_to_send = f"STORE:{target_shelf}:{target_tray}"

            success, new_shelf = ExecuteOnArduino(command_to_send)
            if success:
                r.set('current_shelf', new_shelf)
                r.decr('trays_out_count')
                print(f"[SUCCESS] Cất khay {target_shelf}-{target_tray} thành công. Số khay bên ngoài: {r.get('trays_out_count')}")
                response_message = {
                    "type": "STORE_COMPLETE",
                    "shelf": task.get('shelf'),
                    "tray": task.get('tray'),
                    "dropoff": task.get('dropoff'),
                }
                r.publish('arduino_responses', json.dumps(response_message))
            else:
                print(f"[FAILURE] Nhiệm vụ '{cmd_type}' thất bại.")
        else:
            print(f"[WARNING] Unknown command type: {cmd_type}")

    except KeyboardInterrupt:
        print("\n[INFO] Nhận tín hiệu thoát. Worker sẽ dừng lại.")
        ser.close()
        break
    except Exception as e:
        print(f"\n[FATAL ERROR] Worker gặp lỗi không xác định: {e}")
        print("[INFO] Sẽ thử lại sau 5 giây...")
        time.sleep(5)