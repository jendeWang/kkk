import paho.mqtt.client as mqtt
import json
import time
import random
import datetime
import sys

class VirtualDevice:
    def __init__(self, device_key, device_secret, broker_host="localhost", broker_port=1883):
        self.device_key = device_key
        self.device_secret = device_secret
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=device_key)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False
        
        self.sensors = {
            "temperature": 25.0,
            "humidity": 60.0,
            "light_intensity": 500,
            "pressure": 1013.25
        }
        
        self.actuators = {
            "light": False,
            "fan": False,
            "heater": False,
            "aircon": "off"
        }
        
        self.running = False
        self.publish_interval = 5
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"连接失败: {reason_code}")
            self.connected = False
        else:
            print(f"设备 {self.device_key} 连接成功")
            self.connected = True
            client.subscribe(f"devices/{self.device_key}/commands")
            print(f"已订阅命令主题: devices/{self.device_key}/commands")
    
    def on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            print(f"\n收到命令: {payload}")
            
            command_id = payload.get("command_id")
            service_identifier = payload.get("service_identifier")
            input_params = payload.get("input_params", {})
            
            response = self.handle_command(service_identifier, input_params)
            
            response_topic = f"devices/{self.device_key}/commands/response"
            response_payload = {
                "command_id": command_id,
                "service_identifier": service_identifier,
                "status": "executed",
                "output_data": response,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            self.client.publish(response_topic, json.dumps(response_payload))
            print(f"命令响应已发布: {response_payload}")
            
        except Exception as e:
            print(f"处理命令时出错: {e}")
    
    def handle_command(self, service_identifier, input_params):
        if service_identifier == "set_light":
            value = input_params.get("value", False)
            self.actuators["light"] = value
            return {"success": True, "light": self.actuators["light"]}
        
        elif service_identifier == "set_fan":
            value = input_params.get("value", False)
            self.actuators["fan"] = value
            return {"success": True, "fan": self.actuators["fan"]}
        
        elif service_identifier == "set_heater":
            value = input_params.get("value", False)
            self.actuators["heater"] = value
            if value:
                self.sensors["temperature"] += 0.5
            return {"success": True, "heater": self.actuators["heater"]}
        
        elif service_identifier == "set_aircon":
            mode = input_params.get("mode", "off")
            self.actuators["aircon"] = mode
            if mode == "cool":
                self.sensors["temperature"] -= 0.3
            elif mode == "heat":
                self.sensors["temperature"] += 0.3
            return {"success": True, "aircon": self.actuators["aircon"]}
        
        elif service_identifier == "get_status":
            return {
                "sensors": self.sensors,
                "actuators": self.actuators
            }
        
        else:
            return {"success": False, "error": f"未知命令: {service_identifier}"}
    
    def simulate_sensors(self):
        self.sensors["temperature"] += random.uniform(-0.5, 0.5)
        self.sensors["temperature"] = max(15.0, min(35.0, self.sensors["temperature"]))
        
        self.sensors["humidity"] += random.uniform(-2, 2)
        self.sensors["humidity"] = max(30.0, min(90.0, self.sensors["humidity"]))
        
        hour = datetime.datetime.now().hour
        base_light = 600 if 6 <= hour <= 18 else 50
        self.sensors["light_intensity"] = base_light + random.uniform(-50, 50)
        self.sensors["light_intensity"] = max(10, min(1000, self.sensors["light_intensity"]))
        
        self.sensors["pressure"] += random.uniform(-0.5, 0.5)
        self.sensors["pressure"] = max(980, min(1050, self.sensors["pressure"]))
        
        if self.actuators["fan"]:
            self.sensors["temperature"] -= 0.2
        
        if self.actuators["aircon"] == "cool":
            self.sensors["temperature"] -= 0.5
        
        if self.actuators["aircon"] == "heat":
            self.sensors["temperature"] += 0.5
    
    def publish_telemetry(self):
        topic = f"devices/{self.device_key}/telemetry"
        payload = {
            "device_key": self.device_key,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data": self.sensors
        }
        self.client.publish(topic, json.dumps(payload))
        print(f"发布遥测数据: {payload}")
    
    def publish_event(self, event_type, data):
        topic = f"devices/{self.device_key}/events"
        payload = {
            "device_key": self.device_key,
            "event_type": event_type,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data": data
        }
        self.client.publish(topic, json.dumps(payload))
        print(f"发布事件: {payload}")
    
    def run(self):
        self.running = True
        
        try:
            print(f"正在连接到 MQTT broker: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            print(f"等待连接...")
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            if not self.connected:
                print("连接超时，退出")
                self.client.loop_stop()
                return
            
            print(f"虚拟设备 {self.device_key} 已启动，开始发送遥测数据...")
            
            while self.running:
                self.simulate_sensors()
                self.publish_telemetry()
                
                if self.sensors["temperature"] > 30:
                    self.publish_event("temperature_warning", {"temperature": self.sensors["temperature"], "message": "温度过高"})
                if self.sensors["humidity"] > 85:
                    self.publish_event("humidity_warning", {"humidity": self.sensors["humidity"], "message": "湿度过高"})
                
                time.sleep(self.publish_interval)
                
        except Exception as e:
            print(f"设备运行出错: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print(f"设备 {self.device_key} 已停止")
    
    def stop(self):
        self.running = False


def create_virtual_device():
    import requests
    
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        token = response.json().get("access_token")
        print("登录成功")
    except Exception as e:
        print(f"登录失败: {e}")
        return None, None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get("http://localhost:8000/api/v1/products", headers=headers)
        if response.status_code == 200:
            products = response.json()
            if products:
                product_id = products[0]["id"]
                product_key = products[0]["product_key"]
                print(f"使用现有产品: {product_key} (ID: {product_id})")
            else:
                products = None
        else:
            products = None
    except Exception as e:
        print(f"获取产品列表失败: {e}")
        products = None
    
    if not products:
        product_data = {
            "name": "智能传感器设备",
            "category": "传感器",
            "model": "Sensor-001",
            "manufacturer": "Virtual Devices Inc.",
            "description": "虚拟传感器设备，包含温湿度光照等传感器和灯控功能"
        }
        try:
            response = requests.post("http://localhost:8000/api/v1/products", json=product_data, headers=headers)
            if response.status_code == 200:
                product = response.json()
                product_id = product["id"]
                product_key = product["product_key"]
                print(f"产品创建成功: {product_key}")
            else:
                print(f"产品创建失败: {response.text}")
                return None, None
        except Exception as e:
            print(f"创建产品失败: {e}")
            return None, None
    
    device_data = {
        "device_name": "虚拟传感器设备",
        "product_id": product_id
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/devices", json=device_data, headers=headers)
        if response.status_code == 200:
            device = response.json()
            device_key = device["device_key"]
            device_secret = device.get("device_secret", "secret")
            print(f"设备创建成功: {device_key}")
            return device_key, device_secret
        else:
            print(f"设备创建失败: {response.text}")
            return None, None
    except Exception as e:
        print(f"创建设备失败: {e}")
        return None, None


if __name__ == "__main__":
    print("=== 虚拟设备模拟器 ===")
    
    device_key, device_secret = create_virtual_device()
    
    if not device_key:
        device_key = "test_device_001"
        device_secret = "test_secret"
        print(f"使用默认设备: {device_key}")
    
    print(f"\n设备信息:")
    print(f"  Device Key: {device_key}")
    print(f"  Device Secret: {device_secret}")
    
    device = VirtualDevice(device_key, device_secret)
    
    try:
        device.run()
    except KeyboardInterrupt:
        print("\n收到停止信号，正在停止设备...")
        device.stop()