#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # 订阅所有主题
    client.subscribe("#")

def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")

print("=== 启动MQTT监听器 ===")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

print("\n=== 发送命令响应 ===")
response = {
    'command_id': 'cmd-eb655610-ccfe-4681-a05f-a63c86e69a29',
    'status': 'executed',
    'output_data': {'result': 'success', 'state': True},
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
}
client.publish("devices/qe6feuj9k807wwqb/commands/response", json.dumps(response))
print(f"Published response: {response}")

time.sleep(3)

client.loop_stop()
