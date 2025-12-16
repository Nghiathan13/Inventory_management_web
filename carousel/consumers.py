import json
import asyncio
import redis.asyncio as redis
from channels.generic.websocket import AsyncWebsocketConsumer

REDIS_URL = 'redis://localhost:6379'

class CarouselConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "carousel_control" # Khớp với worker
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        self.r = redis.from_url(REDIS_URL, decode_responses=True)
        self.pubsub = self.r.pubsub()
        await self.pubsub.subscribe("arduino_responses")
        self.listen_task = asyncio.create_task(self.listen_to_redis())
        
        print("[WS] Connected.")

    async def disconnect(self, close_code):
        if hasattr(self, 'listen_task'): self.listen_task.cancel()
        if hasattr(self, 'pubsub'): await self.pubsub.unsubscribe("arduino_responses")
        if hasattr(self, 'r'): await self.r.close()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get('command')
            print(f"[WS RX] Command: {command}")

            r_push = redis.from_url(REDIS_URL, decode_responses=True)

            if command == 'FETCH':
                task = {
                    "cmd": "FETCH_TRAY",
                    "shelf": int(data.get('shelf')),
                    "tray": int(data.get('tray')),
                    "dropoff": 1
                }
                await r_push.rpush('queue:medium', json.dumps(task))
                await r_push.set("system_status", "moving")
                await self.send(text_data=json.dumps({'type': 'SYSTEM_MOVING'}))

            elif command == 'STORE':
                # --- SỬA LOGIC: Ưu tiên dữ liệu từ Client gửi lên ---
                shelf = data.get('shelf')
                tray = data.get('tray')
                dropoff_id = data.get('dropoff_id', 1)

                # Nếu client không gửi shelf/tray (logic cũ), mới tìm trong Redis
                if not shelf or not tray:
                    content = await r_push.get(f"dropoff_content:{dropoff_id}")
                    if content:
                        shelf, tray = map(int, content.split(':'))
                
                if shelf and tray:
                    task = {
                        "cmd": "STORE_TRAY",
                        "shelf": int(shelf),
                        "tray": int(tray),
                        "dropoff": dropoff_id
                    }
                    await r_push.rpush('queue:medium', json.dumps(task))
                    await r_push.set("system_status", "moving")
                    await self.send(text_data=json.dumps({'type': 'SYSTEM_MOVING'}))
                else:
                    print("[WS] Lỗi: Không có thông tin shelf/tray để Store")

            elif command == 'RESET':
                 # Thêm logic RESET/HOMING
                 await r_push.rpush('queue:high', json.dumps({"cmd": "HOMING"}))
                 await self.send(text_data=json.dumps({'type': 'SYSTEM_MOVING'}))

            await r_push.close()

        except Exception as e:
            print(f"[WS ERROR] {e}")

    async def listen_to_redis(self):
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await self.send_worker_update({'message': message['data']})
                await asyncio.sleep(0.01)
        except Exception as e:
            pass

    async def send_worker_update(self, event):
        message_json = event['message']
        data = json.loads(message_json)
        msg_type = data.get('type')
        
        r_state = redis.from_url(REDIS_URL, decode_responses=True)
        response = None

        if msg_type == 'shelf_update':
            # Worker gửi tin nhắn xoay kệ
            current_shelf = data.get('shelf')
            await r_state.set("current_shelf", current_shelf)
            response = {'type': 'shelf_update', 'shelf': current_shelf}

        elif msg_type == 'FETCH_COMPLETE':
            s, t, d = data['shelf'], data['tray'], data['dropoff']
            await r_state.set(f"dropoff_content:{d}", f"{s}:{t}")
            await r_state.set(f"tray_status:{s}:{t}", "out")
            await r_state.set("system_status", "ready")
            response = {'type': 'UPDATE_FETCH', 'shelf': str(s), 'tray': t}

        elif msg_type == 'STORE_COMPLETE':
            s, t, d = data['shelf'], data['tray'], data['dropoff']
            await r_state.delete(f"dropoff_content:{d}")
            await r_state.set(f"tray_status:{s}:{t}", "in")
            await r_state.set("system_status", "ready")
            response = {'type': 'UPDATE_STORE', 'shelf': str(s), 'tray': t}
            
        elif msg_type == 'HOMING_COMPLETE':
             await r_state.set("system_status", "ready")
             # Reset kệ về 1
             await r_state.set("current_shelf", 2) 
             response = {'type': 'HOMING_COMPLETE', 'shelf': 2}

        await r_state.close()
        if response:
            await self.send(text_data=json.dumps(response))