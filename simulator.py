#!/usr/bin/env python3
"""
IoT Device Simulator
Subscribes to commands and publishes telemetry via MQTT
"""
import paho.mqtt.client as mqtt
import json
import time
import random
import os

DEVICE_KEY = os.environ.get('DEVICE_KEY', 'tksm4ju31ci0r0j8')
DEVICE_SECRET = os.environ.get('DEVICE_SECRET', '7cTf9UQYgcDK52zoRpNKnFdQ3EPlTkaV')
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))

# Device state
device_state = {
    'light_on': False,
    'brightness': 50,
    'mode': 'normal',
}


def send_response(client, command_id, status, output_data):
    response = {
        'command_id': command_id,
        'status': status,
        'output_data': output_data,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    client.publish(f"devices/{DEVICE_KEY}/commands/response", json.dumps(response))
    print(f"  >> Response sent: {response}")


def handle_command(client, command_id, service_id, params):
    """Handle incoming commands"""
    if service_id == 'set_light':
        state = params.get('state', False)
        device_state['light_on'] = state
        print(f"  >> Light switched {'ON' if state else 'OFF'}")
        send_response(client, command_id, 'executed', {
            'result': 'success',
            'state': state,
            'message': f"Light turned {'on' if state else 'off'}"
        })

    elif service_id == 'set_brightness':
        brightness = float(params.get('brightness', 50))
        brightness = max(0, min(100, brightness))
        device_state['brightness'] = brightness
        print(f"  >> Brightness set to {brightness}%")
        send_response(client, command_id, 'executed', {
            'result': 'success',
            'brightness': brightness,
            'message': f"Brightness set to {brightness}%"
        })

    elif service_id == 'set_mode':
        mode = params.get('mode', 'normal')
        valid_modes = ['normal', 'eco', 'sleep', 'boost']
        if mode not in valid_modes:
            print(f"  >> Unknown mode: {mode}")
            send_response(client, command_id, 'failed', {
                'result': 'error',
                'message': f"Unknown mode '{mode}'. Valid: {valid_modes}"
            })
        else:
            device_state['mode'] = mode
            print(f"  >> Mode set to: {mode}")
            send_response(client, command_id, 'executed', {
                'result': 'success',
                'mode': mode,
                'message': f"Mode changed to {mode}"
            })

    elif service_id == 'raw_command':
        print(f"  >> Raw command received: {params}")
        send_response(client, command_id, 'executed', {
            'result': 'success',
            'echo': params,
            'message': 'Raw command executed successfully'
        })

    else:
        print(f"  >> Unknown service: {service_id}")
        send_response(client, command_id, 'failed', {
            'result': 'error',
            'message': f"Unknown service: {service_id}"
        })


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker (rc={rc})")
        client.subscribe(f"devices/{DEVICE_KEY}/commands")
        print(f"Subscribed to: devices/{DEVICE_KEY}/commands")
    else:
        print(f"Connection failed with rc={rc}")


def on_message(client, userdata, msg):
    print(f"\n[CMD] Received on {msg.topic}:")
    try:
        payload = json.loads(msg.payload.decode())
        command_id = payload.get('command_id', 'unknown')
        # Support both 'input_params' (backend standard) and 'parameters' (legacy)
        params = payload.get('input_params') or payload.get('parameters', {})
        service_id = payload.get('service_identifier', 'unknown')
        print(f"  command_id={command_id}, service={service_id}, params={params}")
        handle_command(client, command_id, service_id, params)
    except Exception as e:
        print(f"  Error processing command: {e}")


def publish_telemetry(client):
    temperature = round(25 + random.uniform(-3, 10), 2)
    humidity = round(50 + random.uniform(-10, 20), 2)
    light = round(500 + random.uniform(-200, 500), 0)

    base = {
        'device_secret': DEVICE_SECRET,
        'quality': 'good',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }

    for prop, val in [('temperature', temperature), ('humidity', humidity), ('light', light)]:
        msg = {**base, 'property_identifier': prop, 'value': val}
        client.publish(f"devices/{DEVICE_KEY}/telemetry", json.dumps(msg))
        print(f"[TLM] {prop}: {val}")


def main():
    print(f"Starting simulator for device: {DEVICE_KEY}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")

    client = mqtt.Client()
    client.username_pw_set(DEVICE_KEY, DEVICE_SECRET)
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
