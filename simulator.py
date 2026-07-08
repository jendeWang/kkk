#!/usr/bin/env python3
"""
IoT 智慧大棚设备模拟器
支持完整物模型：6个传感器 + 3个执行器 + 5个服务 + 设备影子
"""
import paho.mqtt.client as mqtt
import json
import time
import random
import os

MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER', 'tksm4ju31ci0r0j8')
MQTT_PASS = os.environ.get('MQTT_PASS', '7cTf9UQYgcDK52zoRpNKnFdQ3EPlTkaV')
DEVICE_KEY = os.environ.get('DEVICE_KEY', 'f60sh4j17aks0dbx')
DEVICE_SECRET = os.environ.get('DEVICE_SECRET', '9Owfvqg0lwdbExHGYTIMsuIU5XbTj60U')

device_state = {
    'fan_status': False,
    'light_status': False,
    'pump_status': False,
    'brightness': 60,
    'work_mode': 'manual',
    'temperature': 25.0,
    'humidity': 55.0,
    'light_intensity': 5000.0,
    'soil_moisture': 45.0,
    'co2': 800.0,
    'soil_temperature': 22.0,
}


def send_response(client, command_id, status, output_data=None, error_message=None):
    response = {
        'device_secret': DEVICE_SECRET,
        'command_id': command_id,
        'status': status,
        'output_data': output_data or {},
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    if error_message:
        response['error_message'] = error_message
    client.publish(f"devices/{DEVICE_KEY}/commands/response", json.dumps(response))
    print(f"  >> Response: {status}")


def handle_command(client, command_id, service_id, params):
    if service_id == 'set_fan':
        status = params.get('status', False)
        device_state['fan_status'] = bool(status)
        state_str = '开启' if device_state['fan_status'] else '关闭'
        print(f"  >> 通风扇{state_str}")
        send_response(client, command_id, 'executed', {
            'result': 'success',
            'fan_status': device_state['fan_status'],
            'message': f'通风扇已{state_str}'
        })

    elif service_id == 'set_light':
        status = params.get('status', False)
        brightness = int(params.get('brightness', device_state['brightness']))
        device_state['light_status'] = bool(status)
        device_state['brightness'] = max(0, min(100, brightness))
        state_str = '开启' if device_state['light_status'] else '关闭'
        print(f"  >> 补光灯{state_str}，亮度: {device_state['brightness']}%")
        send_response(client, command_id, 'executed', {
            'result': 'success',
            'light_status': device_state['light_status'],
            'brightness': device_state['brightness'],
            'message': f'补光灯已{state_str}，亮度{device_state["brightness"]}%'
        })

    elif service_id == 'set_pump':
        status = params.get('status', False)
        duration = params.get('duration', 0)
        device_state['pump_status'] = bool(status)
        state_str = '开启' if device_state['pump_status'] else '关闭'
        print(f"  >> 灌溉水泵{state_str}，时长: {duration}秒")
        send_response(client, command_id, 'executed', {
            'result': 'success',
            'pump_status': device_state['pump_status'],
            'duration': duration,
            'message': f'灌溉水泵已{state_str}'
        })

    elif service_id == 'set_mode':
        mode = params.get('mode', 'manual')
        if mode not in ['manual', 'auto']:
            print(f"  >> 无效模式: {mode}")
            send_response(client, command_id, 'failed',
                          error_message=f'无效模式 {mode}，可选: manual, auto')
        else:
            device_state['work_mode'] = mode
            mode_str = '手动' if mode == 'manual' else '自动'
            print(f"  >> 工作模式切换为: {mode_str}")
            send_response(client, command_id, 'executed', {
                'result': 'success',
                'mode': mode,
                'message': f'工作模式已切换为{mode_str}'
            })

    elif service_id == 'raw_command':
        data = params.get('data', {})
        print(f"  >> 自定义命令: {data}")
        send_response(client, command_id, 'executed', {
            'result': 'success',
            'echo': data,
            'message': '自定义命令执行成功'
        })

    else:
        print(f"  >> 未知服务: {service_id}")
        send_response(client, command_id, 'failed',
                      error_message=f'未知服务: {service_id}')


def update_shadow(client):
    shadow_msg = {
        'device_secret': DEVICE_SECRET,
        'state': {
            'reported': {
                'temperature': round(device_state['temperature'], 1),
                'humidity': round(device_state['humidity'], 1),
                'light_intensity': round(device_state['light_intensity'], 0),
                'soil_moisture': round(device_state['soil_moisture'], 1),
                'co2': round(device_state['co2'], 0),
                'soil_temperature': round(device_state['soil_temperature'], 1),
                'fan_status': device_state['fan_status'],
                'light_status': device_state['light_status'],
                'pump_status': device_state['pump_status'],
                'brightness': device_state['brightness'],
                'work_mode': device_state['work_mode'],
            }
        },
        'version': 1,
    }
    client.publish(f"devices/{DEVICE_KEY}/shadow/update", json.dumps(shadow_msg))


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"已连接MQTT Broker (rc={rc})")
        client.subscribe(f"devices/{DEVICE_KEY}/commands")
        client.subscribe(f"devices/{DEVICE_KEY}/shadow/update/desired")
        client.subscribe(f"devices/{DEVICE_KEY}/shadow/get/response")
        print(f"已订阅命令主题: devices/{DEVICE_KEY}/commands")
        print(f"已订阅影子主题: devices/{DEVICE_KEY}/shadow/update/desired")
        status_msg = {
            'device_secret': DEVICE_SECRET,
            'status': 'online'
        }
        client.publish(f"devices/{DEVICE_KEY}/status", json.dumps(status_msg))
    else:
        print(f"连接失败 rc={rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except:
        print(f"  消息解析失败: {msg.topic}")
        return

    if msg.topic.endswith('/commands'):
        print(f"\n[CMD] 收到命令:")
        command_id = payload.get('command_id', 'unknown')
        params = payload.get('input_params') or payload.get('parameters', {})
        service_id = payload.get('service_identifier', 'unknown')
        print(f"  command_id={command_id}, service={service_id}")
        print(f"  params={params}")
        handle_command(client, command_id, service_id, params)

    elif msg.topic.endswith('/shadow/update/desired'):
        print(f"\n[SHADOW] 收到期望状态更新:")
        state = payload.get('state', {})
        desired = state.get('desired', {})
        print(f"  desired={desired}")
        for key, value in desired.items():
            if key in device_state:
                device_state[key] = value
                print(f"  更新 {key} = {value}")
        update_shadow(client)


def publish_telemetry(client):
    device_state['temperature'] += random.uniform(-0.3, 0.3)
    device_state['temperature'] = max(10, min(45, device_state['temperature']))
    if device_state['fan_status']:
        device_state['temperature'] -= 0.2

    device_state['humidity'] += random.uniform(-0.5, 0.5)
    device_state['humidity'] = max(20, min(95, device_state['humidity']))
    if device_state['pump_status']:
        device_state['humidity'] += 0.3
        device_state['soil_moisture'] += 0.5

    device_state['light_intensity'] += random.uniform(-200, 200)
    device_state['light_intensity'] = max(0, min(80000, device_state['light_intensity']))
    if device_state['light_status']:
        device_state['light_intensity'] += 500

    device_state['soil_moisture'] += random.uniform(-0.3, 0.2)
    device_state['soil_moisture'] = max(5, min(90, device_state['soil_moisture']))

    device_state['co2'] += random.uniform(-20, 20)
    device_state['co2'] = max(300, min(2000, device_state['co2']))
    if device_state['fan_status']:
        device_state['co2'] -= 10

    device_state['soil_temperature'] += random.uniform(-0.2, 0.2)
    device_state['soil_temperature'] = max(5, min(40, device_state['soil_temperature']))

    base = {
        'device_secret': DEVICE_SECRET,
        'quality': 'good',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }

    props = [
        ('temperature', round(device_state['temperature'], 2)),
        ('humidity', round(device_state['humidity'], 2)),
        ('light_intensity', round(device_state['light_intensity'], 0)),
        ('soil_moisture', round(device_state['soil_moisture'], 2)),
        ('co2', round(device_state['co2'], 0)),
        ('soil_temperature', round(device_state['soil_temperature'], 2)),
    ]

    for prop, val in props:
        msg = {**base, 'property_identifier': prop, 'value': str(val)}
        client.publish(f"devices/{DEVICE_KEY}/telemetry", json.dumps(msg))

    print(f"[TLM] 温度:{device_state['temperature']:.1f}℃ 湿度:{device_state['humidity']:.1f}% "
          f"光照:{device_state['light_intensity']:.0f}lux 土壤湿度:{device_state['soil_moisture']:.1f}% "
          f"CO2:{device_state['co2']:.0f}ppm")


def main():
    print("=" * 50)
    print("智慧大棚设备模拟器")
    print("=" * 50)
    print(f"设备: {DEVICE_KEY}")
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print("=" * 50)

    client = mqtt.Client(client_id=f"sim-{DEVICE_KEY}")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    time.sleep(1)
    update_shadow(client)

    try:
        while True:
            publish_telemetry(client)
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n停止模拟器...")
        status_msg = {
            'device_secret': DEVICE_SECRET,
            'status': 'offline'
        }
        client.publish(f"devices/{DEVICE_KEY}/status", json.dumps(status_msg))
        client.loop_stop()


if __name__ == '__main__':
    main()
