<template>
  <div class="dashboard">
    <div class="stat-cards">
      <el-card class="stat-card stat-product">
        <div class="stat-inner">
          <div class="stat-icon-wrap">
            <el-icon :size="32"><Goods /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">产品数量</div>
            <div class="stat-value">{{ overview.total_products || 0 }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-device">
        <div class="stat-inner">
          <div class="stat-icon-wrap">
            <el-icon :size="32"><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">设备总数</div>
            <div class="stat-value">{{ overview.total_devices || 0 }}</div>
            <div class="stat-sub">
              <span class="online-dot"></span>
              在线 {{ overview.online_devices || 0 }}
            </div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-alert">
        <div class="stat-inner">
          <div class="stat-icon-wrap">
            <el-icon :size="32"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">活跃告警</div>
            <div class="stat-value" :class="{ 'alert-blink': (overview.active_alerts || 0) > 0 }">
              {{ overview.active_alerts || 0 }}
            </div>
            <div class="stat-sub">今日 {{ overview.today_alerts || 0 }} 条</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-green">
        <div class="stat-inner">
          <div class="stat-icon-wrap">
            <el-icon :size="32"><Connection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">在线率</div>
            <div class="stat-value">
              {{ overview.total_devices ? Math.round(overview.online_devices / overview.total_devices * 100) : 0 }}%
            </div>
            <div class="stat-sub">系统正常运行</div>
          </div>
        </div>
      </el-card>
    </div>

    <el-row :gutter="20" class="main-row">
      <el-col :span="16">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">🌡️ 环境实时监测</span>
              <span class="update-time">更新时间: {{ lastUpdateTime }}</span>
            </div>
          </template>
          <div class="sensor-grid">
            <div class="sensor-card sensor-temp">
              <div class="sensor-icon">🌡️</div>
              <div class="sensor-name">温度</div>
              <div class="sensor-value">
                {{ formatValue(sensorData.temperature, 1) }}
                <span class="sensor-unit">°C</span>
              </div>
              <div class="sensor-bar">
                <div class="sensor-bar-fill" :style="{ width: getTempPercent(sensorData.temperature) + '%' }"></div>
              </div>
            </div>
            <div class="sensor-card sensor-humidity">
              <div class="sensor-icon">💧</div>
              <div class="sensor-name">空气湿度</div>
              <div class="sensor-value">
                {{ formatValue(sensorData.humidity, 1) }}
                <span class="sensor-unit">%</span>
              </div>
              <div class="sensor-bar">
                <div class="sensor-bar-fill" :style="{ width: sensorData.humidity + '%' }"></div>
              </div>
            </div>
            <div class="sensor-card sensor-light">
              <div class="sensor-icon">☀️</div>
              <div class="sensor-name">光照强度</div>
              <div class="sensor-value">
                {{ formatValue(sensorData.light_intensity, 0) }}
                <span class="sensor-unit">lux</span>
              </div>
              <div class="sensor-bar">
                <div class="sensor-bar-fill" :style="{ width: getLightPercent(sensorData.light_intensity) + '%' }"></div>
              </div>
            </div>
            <div class="sensor-card sensor-soil">
              <div class="sensor-icon">🌱</div>
              <div class="sensor-name">土壤湿度</div>
              <div class="sensor-value">
                {{ formatValue(sensorData.soil_moisture, 1) }}
                <span class="sensor-unit">%</span>
              </div>
              <div class="sensor-bar">
                <div class="sensor-bar-fill" :style="{ width: sensorData.soil_moisture + '%' }"></div>
              </div>
            </div>
            <div class="sensor-card sensor-co2">
              <div class="sensor-icon">💨</div>
              <div class="sensor-name">CO₂浓度</div>
              <div class="sensor-value">
                {{ formatValue(sensorData.co2, 0) }}
                <span class="sensor-unit">ppm</span>
              </div>
              <div class="sensor-bar">
                <div class="sensor-bar-fill" :style="{ width: getCo2Percent(sensorData.co2) + '%' }"></div>
              </div>
            </div>
            <div class="sensor-card sensor-soil-temp">
              <div class="sensor-icon">🪴</div>
              <div class="sensor-name">土壤温度</div>
              <div class="sensor-value">
                {{ formatValue(sensorData.soil_temperature, 1) }}
                <span class="sensor-unit">°C</span>
              </div>
              <div class="sensor-bar">
                <div class="sensor-bar-fill" :style="{ width: getSoilTempPercent(sensorData.soil_temperature) + '%' }"></div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="section-card chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">📈 环境趋势 (最近6小时)</span>
              <el-radio-group v-model="trendProperty" size="small" @change="loadTrendData">
                <el-radio-button label="temperature">温度</el-radio-button>
                <el-radio-button label="humidity">湿度</el-radio-button>
                <el-radio-button label="soil_moisture">土壤湿度</el-radio-button>
                <el-radio-button label="co2">CO₂</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChart" class="trend-chart"></div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">⚡ 执行器控制</span>
            </div>
          </template>
          <div class="actuator-list">
            <div class="actuator-item" :class="{ active: actuatorData.fan_status }">
              <div class="actuator-icon">{{ actuatorData.fan_status ? '🌀' : '💨' }}</div>
              <div class="actuator-info">
                <div class="actuator-name">通风扇</div>
                <div class="actuator-status">{{ actuatorData.fan_status ? '运行中' : '已关闭' }}</div>
              </div>
              <el-switch
                v-model="actuatorData.fan_status"
                active-color="#67c23a"
                @change="toggleFan"
              />
            </div>
            <div class="actuator-item" :class="{ active: actuatorData.light_status }">
              <div class="actuator-icon">{{ actuatorData.light_status ? '💡' : '🔅' }}</div>
              <div class="actuator-info">
                <div class="actuator-name">补光灯</div>
                <div class="actuator-status">
                  {{ actuatorData.light_status ? `亮度 ${actuatorData.brightness}%` : '已关闭' }}
                </div>
              </div>
              <el-switch
                v-model="actuatorData.light_status"
                active-color="#e6a23c"
                @change="toggleLight"
              />
            </div>
            <div class="actuator-item" :class="{ active: actuatorData.pump_status }">
              <div class="actuator-icon">{{ actuatorData.pump_status ? '🚿' : '💧' }}</div>
              <div class="actuator-info">
                <div class="actuator-name">灌溉水泵</div>
                <div class="actuator-status">{{ actuatorData.pump_status ? '灌溉中' : '已关闭' }}</div>
              </div>
              <el-switch
                v-model="actuatorData.pump_status"
                active-color="#409eff"
                @change="togglePump"
              />
            </div>
            <div class="actuator-item mode-item">
              <div class="actuator-icon">🎯</div>
              <div class="actuator-info">
                <div class="actuator-name">工作模式</div>
                <div class="actuator-status">{{ modeText }}</div>
              </div>
              <el-select v-model="actuatorData.work_mode" size="small" style="width: 100px;" @change="changeMode">
                <el-option label="手动" value="manual" />
                <el-option label="自动" value="auto" />
                <el-option label="节能" value="eco" />
              </el-select>
            </div>
          </div>
        </el-card>

        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">🔔 最近告警</span>
              <el-tag size="small" :type="alertSummary.today_total > 0 ? 'danger' : 'success'">
                今日 {{ alertSummary.today_total || 0 }}
              </el-tag>
            </div>
          </template>
          <div class="alert-list">
            <div v-if="recentAlerts.length === 0" class="empty-alert">
              <el-icon :size="48" color="#909399"><CircleCheck /></el-icon>
              <p>暂无告警，运行正常</p>
            </div>
            <div v-else v-for="alert in recentAlerts" :key="alert.id" class="alert-item">
              <el-tag size="small" :type="getSeverityType(alert.severity)" class="alert-tag">
                {{ getSeverityText(alert.severity) }}
              </el-tag>
              <div class="alert-content">
                <div class="alert-msg">{{ alert.message }}</div>
                <div class="alert-time">{{ formatTime(alert.created_at) }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import api from '../services/api.js'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Goods, Monitor, Warning, Connection, CircleCheck } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()

const overview = reactive({
  total_products: 0,
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
  soil_temperature: 0
})

const actuatorData = reactive({
  fan_status: false,
  light_status: false,
  pump_status: false,
  brightness: 0,
  work_mode: 'manual'
})

const alertSummary = reactive({
  critical_count: 0,
  error_count: 0,
  warning_count: 0,
  info_count: 0,
  today_total: 0,
  last_7d_total: 0
})

const recentAlerts = ref([])
const trendProperty = ref('temperature')
const trendChart = ref(null)
const lastUpdateTime = ref('--')
let trendChartInstance = null
let refreshTimer = null
let currentDeviceId = null

const modeText = computed(() => {
  const map = { manual: '手动模式', auto: '自动模式', eco: '节能模式' }
  return map[actuatorData.work_mode] || actuatorData.work_mode
})

function formatValue(val, decimals) {
  if (val === null || val === undefined || isNaN(val)) return '--'
  return Number(val).toFixed(decimals)
}

function getTempPercent(val) {
  if (!val) return 0
  return Math.min(100, Math.max(0, ((val - 0) / 50) * 100))
}

function getLightPercent(val) {
  if (!val) return 0
  return Math.min(100, (val / 100000) * 100)
}

function getCo2Percent(val) {
  if (!val) return 0
  return Math.min(100, (val / 2000) * 100)
}

function getSoilTempPercent(val) {
  if (!val) return 0
  return Math.min(100, Math.max(0, ((val - 0) / 40) * 100))
}

function getSeverityType(severity) {
  const types = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return types[severity] || 'info'
}

function getSeverityText(severity) {
  const texts = { info: '提示', warning: '警告', error: '错误', critical: '严重' }
  return texts[severity] || severity
}

function formatTime(time) {
  if (!time) return '--'
  const d = new Date(time)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadOverview() {
  try {
    const resp = await api.get('/dashboard/overview')
    Object.assign(overview, resp.data)
  } catch (e) {
    console.error('Failed to load overview:', e)
  }
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
          temperature: device.reported.temperature ?? 0,
          humidity: device.reported.humidity ?? 0,
          light_intensity: device.reported.light_intensity ?? 0,
          soil_moisture: device.reported.soil_moisture ?? 0,
          co2: device.reported.co2 ?? 0,
          soil_temperature: device.reported.soil_temperature ?? 0
        })
        Object.assign(actuatorData, {
          fan_status: device.reported.fan_status ?? false,
          light_status: device.reported.light_status ?? false,
          pump_status: device.reported.pump_status ?? false,
          brightness: device.reported.brightness ?? 0,
          work_mode: device.reported.work_mode ?? 'manual'
        })
      }
      lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
    }
  } catch (e) {
    console.error('Failed to load device realtime:', e)
  }
}

async function loadAlertSummary() {
  try {
    const resp = await api.get('/dashboard/alerts/summary')
    Object.assign(alertSummary, resp.data)
  } catch (e) {
    console.error('Failed to load alert summary:', e)
  }
}

async function loadRecentAlerts() {
  try {
    const resp = await api.get('/dashboard/alerts/recent', { params: { limit: 5 } })
    recentAlerts.value = resp.data.alerts || []
  } catch (e) {
    console.error('Failed to load recent alerts:', e)
  }
}

async function loadTrendData() {
  if (!currentDeviceId) return
  try {
    const resp = await api.get('/dashboard/telemetry/trend', {
      params: {
        device_id: currentDeviceId,
        property_identifier: trendProperty.value,
        hours: 6
      }
    })
    updateTrendChart(resp.data.data || [])
  } catch (e) {
    console.error('Failed to load trend data:', e)
  }
}

function updateTrendChart(data) {
  if (!trendChart.value) return
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
  const values = data.map(d => d.value)

  const propNames = {
    temperature: { name: '温度', unit: '°C', color: '#f56c6c' },
    humidity: { name: '湿度', unit: '%', color: '#409eff' },
    soil_moisture: { name: '土壤湿度', unit: '%', color: '#67c23a' },
    co2: { name: 'CO₂浓度', unit: 'ppm', color: '#e6a23c' }
  }
  const prop = propNames[trendProperty.value] || { name: '', unit: '', color: '#409eff' }

  trendChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: `{b}<br/>${prop.name}: {c} ${prop.unit}`
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: prop.unit,
      axisLabel: { fontSize: 10 }
    },
    series: [{
      name: prop.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: values,
      lineStyle: { color: prop.color, width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: prop.color + '40' },
          { offset: 1, color: prop.color + '05' }
        ])
      }
    }]
  })
}

async function toggleFan(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, {
      service_identifier: 'set_fan',
      input_params: { status: val }
    })
    ElMessage.success(`通风扇已${val ? '开启' : '关闭'}`)
  } catch (e) {
    ElMessage.error('操作失败')
    actuatorData.fan_status = !val
  }
}

async function toggleLight(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, {
      service_identifier: 'set_light',
      input_params: { status: val, brightness: val ? 80 : 0 }
    })
    ElMessage.success(`补光灯已${val ? '开启' : '关闭'}`)
    if (val) actuatorData.brightness = 80
  } catch (e) {
    ElMessage.error('操作失败')
    actuatorData.light_status = !val
  }
}

async function togglePump(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, {
      service_identifier: 'set_pump',
      input_params: { status: val }
    })
    ElMessage.success(`水泵已${val ? '开启' : '关闭'}`)
  } catch (e) {
    ElMessage.error('操作失败')
    actuatorData.pump_status = !val
  }
}

async function changeMode(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, {
      service_identifier: 'set_mode',
      input_params: { mode: val }
    })
    ElMessage.success(`已切换到${modeText.value}`)
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function refreshAll() {
  await Promise.all([
    loadOverview(),
    loadDeviceRealtime(),
    loadAlertSummary(),
    loadRecentAlerts()
  ])
}

onMounted(async () => {
  await refreshAll()
  await nextTick()
  await loadTrendData()
  refreshTimer = setInterval(() => {
    loadDeviceRealtime()
    loadAlertSummary()
    loadRecentAlerts()
  }, 5000)

  window.addEventListener('resize', () => trendChartInstance?.resize())
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (trendChartInstance) trendChartInstance.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  border-radius: 12px;
  overflow: hidden;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-product .stat-icon-wrap { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-device .stat-icon-wrap { background: linear-gradient(135deg, #11998e, #38ef7d); }
.stat-alert .stat-icon-wrap { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-green .stat-icon-wrap { background: linear-gradient(135deg, #4facfe, #00f2fe); }

.stat-info { flex: 1; }

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.online-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #67c23a;
  margin-right: 4px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.alert-blink {
  color: #f56c6c;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.main-row {
  margin-bottom: 20px;
}

.section-card {
  border-radius: 12px;
  margin-bottom: 20px;
}

.section-card :deep(.el-card__header) {
  padding: 14px 20px;
  border-bottom: 1px solid #f0f2f5;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.update-time {
  font-size: 12px;
  color: #909399;
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.sensor-card {
  padding: 16px;
  border-radius: 10px;
  background: #fafafa;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.sensor-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.sensor-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.sensor-name {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.sensor-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 10px;
}

.sensor-unit {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
  margin-left: 2px;
}

.sensor-bar {
  height: 4px;
  background: #e4e7ed;
  border-radius: 2px;
  overflow: hidden;
}

.sensor-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
  background: linear-gradient(90deg, #409eff, #67c23a);
}

.sensor-temp .sensor-bar-fill { background: linear-gradient(90deg, #409eff, #f56c6c); }
.sensor-humidity .sensor-bar-fill { background: linear-gradient(90deg, #909399, #409eff); }
.sensor-light .sensor-bar-fill { background: linear-gradient(90deg, #909399, #e6a23c); }
.sensor-soil .sensor-bar-fill { background: linear-gradient(90deg, #909399, #67c23a); }
.sensor-co2 .sensor-bar-fill { background: linear-gradient(90deg, #67c23a, #e6a23c, #f56c6c); }
.sensor-soil-temp .sensor-bar-fill { background: linear-gradient(90deg, #409eff, #67c23a, #f56c6c); }

.chart-card {
  margin-bottom: 0;
}

.trend-chart {
  height: 280px;
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
  padding: 12px 14px;
  border-radius: 10px;
  background: #fafafa;
  transition: all 0.3s;
}

.actuator-item.active {
  background: #f0f9eb;
}

.actuator-icon {
  font-size: 24px;
}

.actuator-info {
  flex: 1;
}

.actuator-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.actuator-status {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.mode-item {
  background: #f4f4f5;
}

.alert-list {
  min-height: 200px;
}

.empty-alert {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
  color: #909399;
}

.empty-alert p {
  margin-top: 10px;
  font-size: 13px;
}

.alert-item {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f2f5;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-tag {
  flex-shrink: 0;
  margin-top: 2px;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-msg {
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.alert-time {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}

@media (max-width: 1400px) {
  .sensor-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
