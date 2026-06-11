#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import random
import os

DEVICE_KEY = os.environ.get('DEVICE_KEY', 'qe6feuj9k807wwqb')
DEVICE_SECRET = os.environ.get('DEVICE_SECRET', 'm4nFP1y5it8i11XvMFNih163imnmYFI7')
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(f"devices/{DEVICE_KEY}/commands")

def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        command_id = payload.get('command_id')
        service_identifier = payload.get('service_identifier')
        params = payload.get('parameters', {})
        
        print(f"Executing command: {service_identifier} with params: {params}")
        
        if service_identifier == 'set_light':
            state = params.get('state', False)
            print(f"Light switched {'ON' if state else 'OFF'}")
            
            response = {
                'command_id': command_id,
                'status': 'executed',
                'output_data': {'result': 'success', 'state': state},
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            client.publish(f"devices/{DEVICE_KEY}/commands/response", json.dumps(response))
            print(f"Sent response: {response}")
            
    except Exception as e:
        print(f"Error processing message: {e}")

def publish_telemetry(client):
    temperature = round(25 + random.uniform(-3, 10), 2)
    humidity = round(50 + random.uniform(-10, 20), 2)
    light = round(500 + random.uniform(-200, 500), 0)
    
    telemetry = {
        'device_secret': DEVICE_SECRET,
        'property_identifier': 'temperature',
        'value': temperature,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'quality': 'good'
    }
    client.publish(f"devices/{DEVICE_KEY}/telemetry", json.dumps(telemetry))
    print(f"Published temperature: {temperature}°C")
    
    telemetry['property_identifier'] = 'humidity'
    telemetry['value'] = humidity
    client.publish(f"devices/{DEVICE_KEY}/telemetry", json.dumps(telemetry))
    print(f"Published humidity: {humidity}%")
    
    telemetry['property_identifier'] = 'light'
    telemetry['value'] = light
    client.publish(f"devices/{DEVICE_KEY}/telemetry", json.dumps(telemetry))
    print(f"Published light: {light} lux")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    try:
        while True:
            publish_telemetry(client)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        client.loop_stop()

if __name__ == '__main__':
    main()
