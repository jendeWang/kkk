<template>
  <div class="big-screen">
    <div class="header">
      <div class="header-left">
        <div class="stat-item">
          <span class="stat-label">设备总数</span>
          <span class="stat-value">{{ overview.total_devices || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">在线设备</span>
          <span class="stat-value online">{{ overview.online_devices || 0 }}</span>
        </div>
      </div>
      <div class="header-center">
        <h1 class="title">智慧大棚物联网监控平台</h1>
        <div class="subtitle">INTELLIGENT GREENHOUSE IOT MONITORING PLATFORM</div>
      </div>
      <div class="header-right">
      <button class="reset-btn" @click="resetAll" title="复位执行器状态+刷新数据">
        <el-icon><Refresh /></el-icon>
        <span>一键复位</span>
      </button>
      <div class="stat-item">
        <span class="stat-label">活跃告警</span>
        <span class="stat-value alert" :class="{ blink: (overview.active_alerts || 0) > 0 }">
          {{ overview.active_alerts || 0 }}
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">当前时间</span>
        <span class="stat-value time">{{ currentTime }}</span>
      </div>
    </div>
  </div>

  <button class="exit-btn" @click="exitBigScreen">
    <el-icon><Close /></el-icon>
    <span>退出大屏</span>
  </button>

  <div class="main-content">
      <div class="left-panel">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">设备状态</span>
            <span class="panel-subtitle">DEVICE STATUS</span>
          </div>
          <div class="panel-body">
            <div class="device-stats">
              <div class="device-stat-item">
                <div class="device-dot online"></div>
                <span class="device-label">在线</span>
                <span class="device-count">{{ overview.online_devices || 0 }}</span>
              </div>
              <div class="device-stat-item">
                <div class="device-dot offline"></div>
                <span class="device-label">离线</span>
                <span class="device-count">{{ overview.offline_devices || 0 }}</span>
              </div>
              <div class="device-stat-item">
                <div class="device-dot alert"></div>
                <span class="device-label">告警</span>
                <span class="device-count">{{ overview.active_alerts || 0 }}</span>
              </div>
            </div>
            <div class="device-list">
              <div v-for="(device, index) in deviceList" :key="index" class="device-item">
                <div class="device-dot" :class="device.status"></div>
                <div class="device-info">
                  <div class="device-name">{{ device.name }}</div>
                  <div class="device-location">{{ device.location }}</div>
                </div>
                <div class="device-status-text">
                  {{ device.status === 'online' ? '在线' : device.status === 'alert' ? '告警' : '离线' }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">实时告警</span>
            <span class="panel-subtitle">REAL-TIME ALERTS</span>
          </div>
          <div class="panel-body alert-panel">
            <div class="alert-marquee">
              <div class="alert-track" ref="alertTrack">
                <div v-for="(alert, index) in alertList" :key="'a-' + index" class="alert-item">
                <div class="alert-level" :class="alert.severity">
                  {{ getSeverityText(alert.severity) }}
                </div>
                <div class="alert-content">
                  <div class="alert-msg">{{ formatAlertMessage(alert) }}</div>
                  <div class="alert-time">{{ formatTime(alert.created_at) }}</div>
                </div>
              </div>
              <div v-for="(alert, index) in alertList" :key="'b-' + index" class="alert-item">
                <div class="alert-level" :class="alert.severity">
                  {{ getSeverityText(alert.severity) }}
                </div>
                <div class="alert-content">
                  <div class="alert-msg">{{ formatAlertMessage(alert) }}</div>
                  <div class="alert-time">{{ formatTime(alert.created_at) }}</div>
                </div>
              </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="center-panel">
        <div class="sensor-grid">
          <div class="sensor-card" v-for="sensor in sensors" :key="sensor.key">
            <div class="sensor-icon-wrap">
              <span class="sensor-icon"><SvgIcon :name="sensor.icon" :size="28" /></span>
            </div>
            <div class="sensor-name">{{ sensor.name }}</div>
            <div class="sensor-value">
              <span class="number-scroll">{{ sensor.displayValue }}</span>
              <span class="sensor-unit">{{ sensor.unit }}</span>
            </div>
            <div class="sensor-bar">
              <div class="sensor-bar-fill" :style="{ width: sensor.percent + '%', background: sensor.gradient }"></div>
            </div>
          </div>
        </div>

        <div class="panel chart-panel">
          <div class="panel-header">
            <span class="panel-title">环境趋势</span>
            <span class="panel-subtitle">ENVIRONMENT TREND</span>
            <div class="chart-legend">
              <span class="legend-item"><i class="legend-dot" style="background:#00d4ff"></i>温度</span>
              <span class="legend-item"><i class="legend-dot" style="background:#67c23a"></i>湿度</span>
            </div>
          </div>
          <div class="panel-body">
            <div ref="trendChart" class="trend-chart"></div>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">执行器状态</span>
            <span class="panel-subtitle">ACTUATOR STATUS</span>
          </div>
          <div class="panel-body">
            <div class="actuator-list">
              <div class="actuator-item" :class="{ active: actuatorData.fan_status }">
                <div class="actuator-icon-wrap">
                  <span class="actuator-icon"><SvgIcon name="fan" :size="32" /></span>
                  <div class="actuator-ring" :class="{ active: actuatorData.fan_status }"></div>
                </div>
                <div class="actuator-info">
                  <div class="actuator-name">通风扇</div>
                  <div class="actuator-status">{{ actuatorData.fan_status ? '运行中' : '已关闭' }}</div>
                </div>
                <div class="actuator-switch" :class="{ on: actuatorData.fan_status }">
                  <div class="switch-dot"></div>
                </div>
              </div>

              <div class="actuator-item" :class="{ active: actuatorData.light_status }">
                <div class="actuator-icon-wrap">
                  <span class="actuator-icon"><SvgIcon name="bulb" :size="32" /></span>
                  <div class="actuator-ring" :class="{ active: actuatorData.light_status }"></div>
                </div>
                <div class="actuator-info">
                  <div class="actuator-name">补光灯</div>
                  <div class="actuator-status">
                    {{ actuatorData.light_status ? `亮度 ${actuatorData.brightness}%` : '已关闭' }}
                  </div>
                </div>
                <div class="actuator-switch" :class="{ on: actuatorData.light_status }">
                  <div class="switch-dot"></div>
                </div>
              </div>

              <div class="actuator-item" :class="{ active: actuatorData.pump_status }">
                <div class="actuator-icon-wrap">
                  <span class="actuator-icon"><SvgIcon name="shower" :size="32" /></span>
                  <div class="actuator-ring" :class="{ active: actuatorData.pump_status }"></div>
                </div>
                <div class="actuator-info">
                  <div class="actuator-name">灌溉水泵</div>
                  <div class="actuator-status">{{ actuatorData.pump_status ? '灌溉中' : '已关闭' }}</div>
                </div>
                <div class="actuator-switch" :class="{ on: actuatorData.pump_status }">
                  <div class="switch-dot"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">自动化场景</span>
            <span class="panel-subtitle">AUTO SCENARIOS</span>
          </div>
          <div class="panel-body">
            <div class="scene-list">
              <div class="scene-item" :class="{ active: scenes[0].active }">
                <div class="scene-icon">🌅</div>
                <div class="scene-info">
                  <div class="scene-name">{{ scenes[0].name }}</div>
                  <div class="scene-desc">{{ scenes[0].desc }}</div>
                </div>
                <div class="scene-status">
                  <span class="status-dot" :class="{ active: scenes[0].active }"></span>
                  {{ scenes[0].active ? '运行中' : '已停用' }}
                </div>
              </div>

              <div class="scene-item" :class="{ active: scenes[1].active }">
                <div class="scene-icon">🌙</div>
                <div class="scene-info">
                  <div class="scene-name">{{ scenes[1].name }}</div>
                  <div class="scene-desc">{{ scenes[1].desc }}</div>
                </div>
                <div class="scene-status">
                  <span class="status-dot" :class="{ active: scenes[1].active }"></span>
                  {{ scenes[1].active ? '运行中' : '已停用' }}
                </div>
              </div>

              <div class="scene-item" :class="{ active: scenes[2].active }">
                <div class="scene-icon"><SvgIcon name="droplet" :size="20" /></div>
                <div class="scene-info">
                  <div class="scene-name">{{ scenes[2].name }}</div>
                  <div class="scene-desc">{{ scenes[2].desc }}</div>
                </div>
                <div class="scene-status">
                  <span class="status-dot" :class="{ active: scenes[2].active }"></span>
                  {{ scenes[2].active ? '运行中' : '已停用' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api.js'
import * as echarts from 'echarts'
import { Close, Refresh } from '@element-plus/icons-vue'
import { formatAlertMessage, loadPropertyMappings } from '../services/propertyMapper.js'

const router = useRouter()

const currentTime = ref('')
let timeTimer = null
let dataTimer = null
let trendChartInstance = null
const trendChart = ref(null)
let currentDeviceId = null

const overview = reactive({
  total_devices: 0,
  online_devices: 0,
  offline_devices: 0,
  active_alerts: 0,
  today_alerts: 0
})

const sensorData = reactive({
  temperature: 0,
  humidity: 0,
  light_intensity: 0,
  soil_moisture: 0,
  co2: 0,
  soil_temperature: 0,
  soil_ph: 0,
  wind_speed: 0,
  rainfall: 0
})

const actuatorData = reactive({
  fan_status: false,
  light_status: false,
  pump_status: false,
  brightness: 0,
  work_mode: 'manual'
})

const deviceList = ref([
  { name: '大棚A-001', location: '东区1号棚', status: 'online' },
  { name: '大棚A-002', location: '东区2号棚', status: 'online' },
  { name: '大棚B-001', location: '西区1号棚', status: 'alert' },
  { name: '大棚B-002', location: '西区2号棚', status: 'online' },
  { name: '大棚C-001', location: '南区1号棚', status: 'offline' },
  { name: '大棚C-002', location: '南区2号棚', status: 'online' }
])

const alertList = ref([
  { id: 1, severity: 'critical', message: '大棚B-001: temperature = 32.5，超过阈值 30', created_at: new Date() },
  { id: 2, severity: 'warning', message: '大棚A-002: soil_moisture = 28.5%，低于阈值 30', created_at: new Date(Date.now() - 120000) },
  { id: 3, severity: 'error', message: '大棚C-001设备离线', created_at: new Date(Date.now() - 300000) },
  { id: 4, severity: 'warning', message: '大棚B-002: co2 = 1650 ppm，超过上限阈值', created_at: new Date(Date.now() - 600000) },
  { id: 5, severity: 'info', message: '系统执行定时灌溉任务完成', created_at: new Date(Date.now() - 900000) }
])

const scenes = reactive([
  { name: '日间模式', desc: '自动通风+补光控制', active: true },
  { name: '夜间模式', desc: '保温保湿+低功耗', active: false },
  { name: '智能灌溉', desc: '根据土壤湿度自动灌溉', active: true }
])

const sensors = computed(() => [
  {
    key: 'temperature',
    name: '温度',
    icon: 'thermometer',
    unit: '°C',
    value: sensorData.temperature,
    displayValue: formatValue(sensorData.temperature, 1),
    percent: Math.min(100, Math.max(0, ((sensorData.temperature - 0) / 50) * 100)),
    gradient: 'linear-gradient(90deg, #00d4ff, #ff6b6b)'
  },
  {
    key: 'humidity',
    name: '空气湿度',
    icon: 'droplet',
    unit: '%',
    value: sensorData.humidity,
    displayValue: formatValue(sensorData.humidity, 1),
    percent: sensorData.humidity,
    gradient: 'linear-gradient(90deg, #00d4ff, #67c23a)'
  },
  {
    key: 'light_intensity',
    name: '光照强度',
    icon: 'sun',
    unit: 'lux',
    value: sensorData.light_intensity,
    displayValue: formatValue(sensorData.light_intensity, 0),
    percent: Math.min(100, (sensorData.light_intensity / 100000) * 100),
    gradient: 'linear-gradient(90deg, #ffd93d, #ff9500)'
  },
  {
    key: 'soil_moisture',
    name: '土壤湿度',
    icon: 'leaf',
    unit: '%',
    value: sensorData.soil_moisture,
    displayValue: formatValue(sensorData.soil_moisture, 1),
    percent: sensorData.soil_moisture,
    gradient: 'linear-gradient(90deg, #00d4ff, #67c23a)'
  },
  {
    key: 'co2',
    name: 'CO₂浓度',
    icon: 'wind',
    unit: 'ppm',
    value: sensorData.co2,
    displayValue: formatValue(sensorData.co2, 0),
    percent: Math.min(100, (sensorData.co2 / 2000) * 100),
    gradient: 'linear-gradient(90deg, #67c23a, #e6a23c, #f56c6c)'
  },
  {
    key: 'soil_temperature',
    name: '土壤温度',
    icon: 'soil',
    unit: '°C',
    value: sensorData.soil_temperature,
    displayValue: formatValue(sensorData.soil_temperature, 1),
    percent: Math.min(100, Math.max(0, ((sensorData.soil_temperature - 0) / 40) * 100)),
    gradient: 'linear-gradient(90deg, #00d4ff, #67c23a, #ff6b6b)'
  },
  {
    key: 'soil_ph',
    name: '土壤pH',
    icon: 'flask',
    unit: 'pH',
    value: sensorData.soil_ph,
    displayValue: formatValue(sensorData.soil_ph, 1),
    percent: Math.min(100, Math.max(0, ((sensorData.soil_ph - 4) / 6) * 100)),
    gradient: 'linear-gradient(90deg, #b37feb, #9254de, #722ed1)'
  },
  {
    key: 'wind_speed',
    name: '风速',
    icon: 'cloud',
    unit: 'm/s',
    value: sensorData.wind_speed,
    displayValue: formatValue(sensorData.wind_speed, 1),
    percent: Math.min(100, (sensorData.wind_speed / 15) * 100),
    gradient: 'linear-gradient(90deg, #36cfc9, #13c2c2, #08979c)'
  },
  {
    key: 'rainfall',
    name: '雨量',
    icon: '🌧️',
    unit: 'mm',
    value: sensorData.rainfall,
    displayValue: formatValue(sensorData.rainfall, 1),
    percent: Math.min(100, (sensorData.rainfall / 20) * 100),
    gradient: 'linear-gradient(90deg, #597ef7, #2f54eb, #1d39c4)'
  }
])

function formatValue(val, decimals) {
  if (val === null || val === undefined || isNaN(val)) return '--'
  return Number(val).toFixed(decimals)
}

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getSeverityText(severity) {
  const texts = { info: '提示', warning: '警告', error: '错误', critical: '严重' }
  return texts[severity] || severity
}

function formatTime(time) {
  if (!time) return '--'
  const d = new Date(time)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

async function loadOverview() {
  try {
    const resp = await api.get('/dashboard/overview')
    Object.assign(overview, resp.data)
    await loadDeviceList()
  } catch (e) {
    console.error('Failed to load overview:', e)
    generateMockData()
  }
}

async function loadDeviceList() {
  try {
    const resp = await api.get('/devices/')
    const devices = resp.data.items || resp.data || []
    if (devices.length > 0) {
      deviceList.value = devices.map(device => ({
        id: device.id,
        name: device.device_name,
        location: device.description || '未设置位置',
        status: device.status
      }))
    } else {
      updateDeviceList()
    }
  } catch (e) {
    console.error('Failed to load device list:', e)
    updateDeviceList()
  }
}

function updateDeviceList() {
  const online = overview.online_devices || 0
  const offline = overview.offline_devices || 0
  const alert = overview.active_alerts || 0
  
  deviceList.value = [
    { name: '大棚A-001', location: '东区1号棚', status: 'online' },
    { name: '大棚A-002', location: '东区2号棚', status: alert > 0 ? 'alert' : 'online' },
    { name: '大棚B-001', location: '西区1号棚', status: 'online' },
    { name: '大棚B-002', location: '西区2号棚', status: 'online' },
    { name: '大棚C-001', location: '南区1号棚', status: offline > 0 ? 'offline' : 'online' },
    { name: '大棚C-002', location: '南区2号棚', status: 'online' }
  ]
}

async function loadDeviceRealtime() {
  try {
    const resp = await api.get('/dashboard/devices/realtime')
    const devices = resp.data.devices
    if (devices && devices.length > 0) {
      const device = devices[0]
      currentDeviceId = device.id
      if (device.reported) {
        Object.assign(sensorData, {
          temperature: device.reported.temperature ?? 25.5,
          humidity: device.reported.humidity ?? 65,
          light_intensity: device.reported.light_intensity ?? 35000,
          soil_moisture: device.reported.soil_moisture ?? 55,
          co2: device.reported.co2 ?? 800,
          soil_temperature: device.reported.soil_temperature ?? 22,
          soil_ph: device.reported.soil_ph ?? 6.5,
          wind_speed: device.reported.wind_speed ?? 2.5,
          rainfall: device.reported.rainfall ?? 0
        })
        Object.assign(actuatorData, {
          fan_status: device.reported.fan_status ?? false,
          light_status: device.reported.light_status ?? false,
          pump_status: device.reported.pump_status ?? false,
          brightness: device.reported.brightness ?? 0,
          work_mode: device.reported.work_mode ?? 'manual'
        })
      }
    }
  } catch (e) {
    console.error('Failed to load device realtime:', e)
    generateMockSensorData()
  }
}

async function loadRecentAlerts() {
  try {
    const resp = await api.get('/dashboard/alerts/recent', { params: { limit: 5 } })
    const alerts = resp.data.alerts || []
    if (alerts.length > 0) {
      alertList.value = alerts
    }
  } catch (e) {
    console.error('Failed to load recent alerts:', e)
  }
}

function generateMockData() {
  overview.total_devices = 12
  overview.online_devices = 10
  overview.offline_devices = 1
  overview.active_alerts = 2
  overview.today_alerts = 5
  updateDeviceList()
}

function generateMockSensorData() {
  sensorData.temperature = 24 + Math.random() * 4
  sensorData.humidity = 60 + Math.random() * 15
  sensorData.light_intensity = 30000 + Math.random() * 20000
  sensorData.soil_moisture = 50 + Math.random() * 20
  sensorData.co2 = 600 + Math.random() * 400
  sensorData.soil_temperature = 20 + Math.random() * 5
  sensorData.soil_ph = 6 + Math.random() * 1.5
  sensorData.wind_speed = Math.random() * 5
  sensorData.rainfall = Math.random() * 5
}

async function loadTrendData() {
  if (!currentDeviceId) {
    generateMockTrendData()
    return
  }
  try {
    const tempResp = await api.get('/dashboard/telemetry/trend', {
      params: { device_id: currentDeviceId, property_identifier: 'temperature', hours: 6 }
    })
    const humResp = await api.get('/dashboard/telemetry/trend', {
      params: { device_id: currentDeviceId, property_identifier: 'humidity', hours: 6 }
    })
    updateTrendChart(tempResp.data.data || [], humResp.data.data || [])
  } catch (e) {
    console.error('Failed to load trend data:', e)
    generateMockTrendData()
  }
}

function generateMockTrendData() {
  const labels = []
  const tempData = []
  const humData = []
  const now = new Date()
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 15 * 60 * 1000)
    labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
    tempData.push(23 + Math.random() * 5 + Math.sin(i / 3) * 2)
    humData.push(55 + Math.random() * 15 + Math.cos(i / 4) * 5)
  }
  
  updateTrendChart(
    labels.map((l, i) => ({ timestamp: l, value: tempData[i] })),
    labels.map((l, i) => ({ timestamp: l, value: humData[i] }))
  )
}

function updateTrendChart(tempData, humData) {
  if (!trendChart.value) return
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  const labels = tempData.map(d => {
    if (typeof d.timestamp === 'string') return d.timestamp
    return new Date(d.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
  const tempValues = tempData.map(d => d.value)
  const humValues = humData.map(d => d.value)

  trendChartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 22, 40, 0.9)',
      borderColor: '#00d4ff',
      borderWidth: 1,
      textStyle: { color: '#fff' },
      axisPointer: {
        type: 'line',
        lineStyle: { color: '#00d4ff', type: 'dashed' }
      }
    },
    legend: {
      show: false
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
      axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 },
      splitLine: { show: false }
    },
    yAxis: [
      {
        type: 'value',
        name: '温度(°C)',
        position: 'left',
        axisLine: { lineStyle: { color: '#00d4ff' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.1)' } }
      },
      {
        type: 'value',
        name: '湿度(%)',
        position: 'right',
        axisLine: { lineStyle: { color: '#67c23a' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.6)', fontSize: 11 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '温度',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: tempValues,
        lineStyle: { color: '#00d4ff', width: 2, shadowColor: '#00d4ff', shadowBlur: 10 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 212, 255, 0.4)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0.05)' }
          ])
        }
      },
      {
        name: '湿度',
        type: 'line',
        smooth: true,
        symbol: 'none',
        yAxisIndex: 1,
        data: humValues,
        lineStyle: { color: '#67c23a', width: 2, shadowColor: '#67c23a', shadowBlur: 10 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
          ])
        }
      }
    ]
  })
}

async function refreshData() {
  await Promise.all([
    loadOverview(),
    loadDeviceRealtime(),
    loadRecentAlerts()
  ])
  await loadTrendData()
}

onMounted(async () => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  
  // 加载物模型属性映射，用于通用口语化
  await loadPropertyMappings()
  
  generateMockSensorData()
  await refreshData()
  
  dataTimer = setInterval(refreshData, 3000)
  
  await nextTick()
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }
  generateMockTrendData()
  
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
})

function handleResize() {
  trendChartInstance?.resize()
}

function exitBigScreen() {
  window.close()
  setTimeout(() => {
    router.push('/dashboard')
  }, 100)
}

async function resetAll() {
  try {
    const ElMessage = (await import('element-plus')).ElMessage
    
    const confirmed = confirm('确认复位吗？\n- 所有执行器将关闭\n- 图表数据将重新拉取\n- 此操作不可撤销')
    if (!confirmed) return
    
    // 1. 关闭所有执行器
    const resetPromises = []
    for (const actuator of ['fan_switch', 'light_switch', 'pump_switch']) {
      resetPromises.push(
        api.post(`/devices/${currentDeviceId || 1}/commands`, {
          command: actuator,
          params: { value: false }
        }).catch(e => console.warn(`关闭${actuator}失败:`, e))
      )
    }
    await Promise.all(resetPromises)
    
    // 2. 重新拉取数据
    await refreshData()
    
    ElMessage.success('复位完成，执行器已全部关闭')
  } catch (e) {
    console.error('复位失败:', e)
    alert('复位失败: ' + (e.message || '未知错误'))
  }
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    exitBigScreen()
  }
}

onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
  if (dataTimer) clearInterval(dataTimer)
  if (trendChartInstance) trendChartInstance.dispose()
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.big-screen {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0a1628 0%, #0d2137 50%, #0a1628 100%);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 15px;
  box-sizing: border-box;
  position: relative;
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(255, 184, 0, 0.15);
  border: 1px solid rgba(255, 184, 0, 0.3);
  border-radius: 4px;
  color: rgba(255, 184, 0, 0.9);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 16px;
}

.reset-btn:hover {
  background: rgba(255, 184, 0, 0.25);
  border-color: rgba(255, 184, 0, 0.5);
  color: #ffb800;
}

.exit-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  backdrop-filter: blur(10px);
}

.exit-btn:hover {
  background: rgba(0, 212, 255, 0.3);
  color: #fff;
  border-color: rgba(0, 212, 255, 0.6);
}

.big-screen::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
  padding: 0 20px;
  position: relative;
  flex-shrink: 0;
}

.header::before,
.header::after {
  content: '';
  position: absolute;
  bottom: 0;
  width: 30%;
  height: 1px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.header::before {
  left: 0;
}

.header::after {
  right: 0;
}

.header-left,
.header-right {
  display: flex;
  gap: 40px;
  flex: 1;
}

.header-right {
  justify-content: flex-end;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #00d4ff;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.stat-value.online {
  color: #67c23a;
  text-shadow: 0 0 10px rgba(103, 194, 58, 0.5);
}

.stat-value.alert {
  color: #f56c6c;
  text-shadow: 0 0 10px rgba(245, 108, 108, 0.5);
}

.stat-value.time {
  font-size: 18px;
  color: #fff;
  text-shadow: none;
}

.blink {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.header-center {
  text-align: center;
  flex: 1;
}

.title {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  background: linear-gradient(90deg, #00d4ff, #fff, #00d4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
}

.subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 6px;
  margin-top: 4px;
}

.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr;
  gap: 15px;
  margin-top: 15px;
  min-height: 0;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.center-panel {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.panel {
  background: rgba(13, 33, 55, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  position: relative;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.panel::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 20px;
  right: 20px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.panel-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  flex-shrink: 0;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  position: relative;
  padding-left: 12px;
}

.panel-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background: linear-gradient(180deg, #00d4ff, transparent);
  border-radius: 2px;
}

.panel-subtitle {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 2px;
}

.panel-body {
  padding: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.device-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 16px;
}

.device-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.device-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.device-dot.online {
  background: #67c23a;
  box-shadow: 0 0 10px rgba(103, 194, 58, 0.8);
  animation: pulse 2s infinite;
}

.device-dot.offline {
  background: #909399;
}

.device-dot.alert {
  background: #f56c6c;
  box-shadow: 0 0 10px rgba(245, 108, 108, 0.8);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}

.device-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.device-count {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  font-family: 'Courier New', monospace;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.device-list::-webkit-scrollbar {
  width: 4px;
}

.device-list::-webkit-scrollbar-track {
  background: rgba(0, 212, 255, 0.1);
}

.device-list::-webkit-scrollbar-thumb {
  background: #00d4ff;
  border-radius: 2px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0, 212, 255, 0.05);
  border-radius: 4px;
  border-left: 3px solid transparent;
  transition: all 0.3s;
}

.device-item:hover {
  background: rgba(0, 212, 255, 0.1);
  border-left-color: #00d4ff;
}

.device-item .device-dot {
  flex-shrink: 0;
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
}

.device-location {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.device-status-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  flex-shrink: 0;
}

.alert-panel {
  padding: 0;
  overflow: hidden;
}

.alert-marquee {
  height: 100%;
  overflow: hidden;
  position: relative;
}

.alert-track {
  animation: marquee 30s linear infinite;
  padding: 16px;
}

.alert-track:hover {
  animation-play-state: paused;
}

@keyframes marquee {
  0% { transform: translateY(0); }
  100% { transform: translateY(-50%); }
}

.alert-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 10px;
  background: rgba(0, 212, 255, 0.05);
  border-radius: 4px;
  border-left: 3px solid;
}

.alert-item.critical { border-left-color: #f56c6c; }
.alert-item.error { border-left-color: #e6a23c; }
.alert-item.warning { border-left-color: #e6a23c; }
.alert-item.info { border-left-color: #00d4ff; }

.alert-level {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  height: fit-content;
}

.alert-level.critical {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

.alert-level.error {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.alert-level.warning {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.alert-level.info {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-msg {
  font-size: 13px;
  color: #fff;
  line-height: 1.4;
}

.alert-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  flex-shrink: 0;
}

.sensor-card {
  background: rgba(13, 33, 55, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  padding: 16px;
  position: relative;
  backdrop-filter: blur(10px);
  transition: all 0.3s;
}

.sensor-card::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 30px;
  right: 30px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
}

.sensor-card:hover {
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
  transform: translateY(-2px);
}

.sensor-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(0, 212, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.sensor-icon {
  font-size: 20px;
}

.sensor-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
}

.sensor-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 12px;
}

.number-scroll {
  font-size: 32px;
  font-weight: 700;
  color: #00d4ff;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
  transition: all 0.3s ease;
}

.sensor-unit {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.sensor-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.sensor-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
  box-shadow: 0 0 10px currentColor;
}

.chart-panel {
  flex: 1;
  min-height: 0;
}

.chart-legend {
  margin-left: auto;
  display: flex;
  gap: 16px;
}

.legend-item {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.trend-chart {
  width: 100%;
  height: 100%;
  min-height: 280px;
}

.actuator-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.actuator-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 212, 255, 0.05);
  border-radius: 4px;
  transition: all 0.3s;
}

.actuator-item.active {
  background: rgba(0, 212, 255, 0.1);
  border-left: 3px solid #00d4ff;
}

.actuator-icon-wrap {
  position: relative;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.actuator-icon {
  font-size: 24px;
  position: relative;
  z-index: 1;
}

.actuator-ring {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

.actuator-ring.active {
  border-color: #00d4ff;
  animation: ring-rotate 2s linear infinite;
  border-top-color: transparent;
}

@keyframes ring-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.actuator-info {
  flex: 1;
  min-width: 0;
}

.actuator-name {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}

.actuator-status {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

.actuator-switch {
  width: 44px;
  height: 22px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 11px;
  position: relative;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
}

.actuator-switch.on {
  background: rgba(0, 212, 255, 0.3);
}

.switch-dot {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  transition: all 0.3s;
}

.actuator-switch.on .switch-dot {
  left: 25px;
  background: #00d4ff;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
}

.scene-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scene-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: rgba(0, 212, 255, 0.05);
  border-radius: 4px;
  transition: all 0.3s;
}

.scene-item.active {
  background: rgba(103, 194, 58, 0.1);
  border-left: 3px solid #67c23a;
}

.scene-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.scene-info {
  flex: 1;
  min-width: 0;
}

.scene-name {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}

.scene-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.scene-status {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #909399;
}

.status-dot.active {
  background: #67c23a;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.8);
  animation: pulse 2s infinite;
}

@media (max-width: 1600px) {
  .sensor-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .number-scroll {
    font-size: 26px;
  }
  
  .title {
    font-size: 26px;
  }
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr 1fr;
  }
  
  .center-panel {
    grid-column: 1 / -1;
    order: -1;
  }
  
  .sensor-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}
</style>
