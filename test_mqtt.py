#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import urllib.request

received_commands = []
device_key = "qe6feuj9k807wwqb"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(f"devices/{device_key}/commands")

def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")
    received_commands.append(msg.payload.decode())
    
    # 模拟设备响应命令
    try:
        payload = json.loads(msg.payload.decode())
        command_id = payload.get('command_id')
        service_identifier = payload.get('service_identifier')
        params = payload.get('input_params', {})
        
        print(f"Executing command: {service_identifier} with params: {params}")
        
        # 模拟执行结果
        if service_identifier == 'set_light':
            state = params.get('state', False)
            print(f"Light switched {'ON' if state else 'OFF'}")
            
            # 发送响应
            response = {
                'command_id': command_id,
                'status': 'executed',
                'output_data': {'result': 'success', 'state': state},
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            response_topic = f"devices/{device_key}/commands/response"
            client.publish(response_topic, json.dumps(response))
            print(f"Sent response to {response_topic}: {response}")
            
    except Exception as e:
        print(f"Error processing command: {e}")

# 获取token
print("=== 获取token ===")
login_data = json.dumps({"username": "admin", "password": "admin123"}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    login_result = json.loads(response.read().decode())
    token = login_result['access_token']
    print(f"Token获取成功")

# 启动订阅者
print("\n=== 启动MQTT订阅者 ===")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

time.sleep(2)

# 发送命令
print("\n=== 发送命令 ===")
command_data = json.dumps({"service_identifier": "set_light", "parameters": {"state": True}}).encode('utf-8')
req = urllib.request.Request(
    'http://localhost:8000/api/v1/devices/9/commands',
    data=command_data,
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
)
with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode())
    print(f"命令ID: {result['command_id'][-15:]}, 状态: {result['status']}")

time.sleep(5)

print(f"\n=== 检查命令状态 ===")
req = urllib.request.Request(
    'http://localhost:8000/api/v1/devices/9/commands',
    headers={'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(req) as response:
    commands = json.loads(response.read().decode())
    latest_cmd = commands[-1]
    print(f"命令ID: {latest_cmd['command_id'][-15:]}, 状态: {latest_cmd['status']}, 输出: {latest_cmd['output_data']}")

client.loop_stop()
