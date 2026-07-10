<template>
  <div class="dashboard">
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title"><SvgIcon name="leaf" :size="24" /> 智慧大棚监控中心</h2>
        <p class="page-subtitle">实时监测环境数据，智能控制设备运行</p>
      </div>
      <el-button type="primary" :icon="FullScreen" @click="openBigScreen">进入大屏</el-button>
    </div>

    <div class="greenhouse-tabs">
      <el-tabs v-model="activeGreenhouse" @tab-change="handleGreenhouseChange" type="card">
        <el-tab-pane label="农场总览" name="all">
        </el-tab-pane>
        <el-tab-pane
          v-for="gh in greenhouses"
          :key="gh.id"
          :label="`${gh.active_alerts > 0 ? '🔴' : '🟢'} ${gh.name} (${gh.online_count}/${gh.device_count})`"
          :name="String(gh.id)"
        >
        </el-tab-pane>
      </el-tabs>
    </div>

    <div class="stat-cards">
      <el-card class="stat-card stat-product">
        <div class="stat-inner">
          <div class="stat-icon-wrap"><el-icon :size="32"><Goods /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">产品数量</div>
            <div class="stat-value">{{ overview.total_products || 0 }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-device">
        <div class="stat-inner">
          <div class="stat-icon-wrap"><el-icon :size="32"><Monitor /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">设备总数</div>
            <div class="stat-value">{{ overview.total_devices || 0 }}</div>
            <div class="stat-sub"><span class="online-dot"></span>在线 {{ overview.online_devices || 0 }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-alert">
        <div class="stat-inner">
          <div class="stat-icon-wrap"><el-icon :size="32"><Warning /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">未处理告警</div>
            <div class="stat-value" :class="{ 'alert-blink': (overview.active_alerts || 0) > 0 }">{{ overview.active_alerts || 0 }}</div>
            <div class="stat-sub">今日新增 {{ overview.today_alerts || 0 }} 条</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-green">
        <div class="stat-inner">
          <div class="stat-icon-wrap"><el-icon :size="32"><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-label">在线率</div>
            <div class="stat-value">{{ overview.total_devices ? Math.round(overview.online_devices / overview.total_devices * 100) : 0 }}%</div>
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
              <span class="card-title"><SvgIcon name="thermometer" :size="20" /> 环境实时监测</span>
              <span class="update-time">更新时间: {{ lastUpdateTime }}</span>
            </div>
          </template>
          <div class="sensor-grid">
            <SensorCard icon="thermometer" name="空气温度" :value="sensorData.temperature" unit="°C" :normal-range="{min:15,max:30}" />
            <SensorCard icon="droplet" name="空气湿度" :value="sensorData.humidity" unit="%" :normal-range="{min:40,max:80}" />
            <SensorCard icon="sun" name="光照强度" :value="sensorData.light_intensity" unit="lux" :normal-range="{min:5000,max:50000}" :decimals="0" />
            <SensorCard icon="leaf" name="土壤湿度" :value="sensorData.soil_moisture" unit="%" :normal-range="{min:50,max:80}" />
            <SensorCard icon="wind" name="CO₂浓度" :value="sensorData.co2" unit="ppm" :normal-range="{min:400,max:1500}" :decimals="0" />
            <SensorCard icon="soil" name="土壤温度" :value="sensorData.soil_temperature" unit="°C" :normal-range="{min:15,max:28}" />
            <SensorCard icon="flask" name="土壤pH" :value="sensorData.soil_ph" unit="pH" :normal-range="{min:5.5,max:7.5}" />
            <SensorCard icon="cloud" name="风速" :value="sensorData.wind_speed" unit="m/s" :normal-range="{min:0,max:10}" />
            <SensorCard icon="rain" name="雨量" :value="sensorData.rainfall" unit="mm" :normal-range="{min:0,max:10}" />
          </div>
        </el-card>

        <el-card class="section-card chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title"><SvgIcon name="trendUp" :size="20" /> 环境趋势 (最近6小时)</span>
              <el-radio-group v-model="trendProperty" size="small" @change="loadTrendData">
                <el-radio-button label="temperature">温度</el-radio-button>
                <el-radio-button label="humidity">湿度</el-radio-button>
                <el-radio-button label="soil_moisture">土壤湿度</el-radio-button>
                <el-radio-button label="co2">CO₂</el-radio-button>
                <el-radio-button label="soil_temperature">地温</el-radio-button>
                <el-radio-button label="soil_ph">pH</el-radio-button>
                <el-radio-button label="wind_speed">风速</el-radio-button>
                <el-radio-button label="rainfall">雨量</el-radio-button>
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
              <span class="card-title"><SvgIcon name="bolt" :size="20" /> 执行器控制</span>
            </div>
          </template>
          <div class="actuator-grid">
            <el-card class="actuator-card" :class="{ active: actuatorData.fan_status }">
              <div class="actuator-icon-wrap"><SvgIcon :name="actuatorData.fan_status ? 'fan' : 'wind'" :size="32" /></div>
              <div class="actuator-name">通风扇</div>
              <div class="actuator-status">{{ actuatorData.fan_status ? '运行中' : '已关闭' }}</div>
              <el-switch v-model="actuatorData.fan_status" active-color="#67c23a" @change="toggleFan" />
            </el-card>
            <el-card class="actuator-card" :class="{ active: actuatorData.light_status }">
              <div class="actuator-icon-wrap"><SvgIcon :name="actuatorData.light_status ? 'bulb' : 'dim'" :size="32" /></div>
              <div class="actuator-name">补光灯</div>
              <div class="actuator-status">{{ actuatorData.light_status ? `亮度 ${actuatorData.brightness}%` : '已关闭' }}</div>
              <el-switch v-model="actuatorData.light_status" active-color="#e6a23c" @change="toggleLight" />
            </el-card>
            <el-card class="actuator-card" :class="{ active: actuatorData.pump_status }">
              <div class="actuator-icon-wrap"><SvgIcon :name="actuatorData.pump_status ? 'shower' : 'droplet'" :size="32" /></div>
              <div class="actuator-name">灌溉水泵</div>
              <div class="actuator-status">{{ actuatorData.pump_status ? '灌溉中' : '已关闭' }}</div>
              <el-switch v-model="actuatorData.pump_status" active-color="#409eff" @change="togglePump" />
            </el-card>
            <el-card class="actuator-card mode-card">
              <div class="actuator-icon-wrap"><SvgIcon name="gear" :size="32" /></div>
              <div class="actuator-name">工作模式</div>
              <div class="actuator-status">{{ modeText }}</div>
              <el-select v-model="actuatorData.work_mode" size="small" @change="changeMode">
                <el-option label="手动" value="manual" />
                <el-option label="自动" value="auto" />
                <el-option label="节能" value="eco" />
              </el-select>
            </el-card>
          </div>
        </el-card>

        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title"><SvgIcon name="bell" :size="20" /> 最近告警</span>
              <el-tag size="small" :type="alertSummary.today_total > 0 ? 'danger' : 'success'">今日 {{ alertSummary.today_total || 0 }}</el-tag>
            </div>
          </template>
          <div class="alert-list">
            <div v-if="recentAlerts.length === 0" class="empty-alert">
              <el-icon :size="48" color="#909399"><CircleCheck /></el-icon>
              <p>暂无告警，运行正常</p>
            </div>
            <div v-else v-for="alert in recentAlerts" :key="alert.id" class="alert-item">
              <el-tag size="small" :type="getSeverityType(alert.severity)" class="alert-tag">{{ getSeverityText(alert.severity) }}</el-tag>
              <div class="alert-content">
                <div class="alert-msg">{{ formatAlertMessage(alert) }}</div>
                <div class="alert-time">{{ formatTime(alert.created_at) }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">快捷操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" plain size="small" @click="refreshAll">刷新数据</el-button>
            <el-button type="success" plain size="small" @click="goToDevices">设备管理</el-button>
            <el-button type="warning" plain size="small" @click="goToAlerts">告警中心</el-button>
            <el-button type="info" plain size="small" @click="goToScenes">场景联动</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useDeviceStore } from '../stores/device.js'
import api from '../services/api.js'
import sseManager from '../services/sse.js'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Goods, Monitor, Warning, Connection, CircleCheck, FullScreen } from '@element-plus/icons-vue'
import { formatAlertMessage } from '../services/propertyMapper.js'
import SensorCard from '../components/SensorCard.vue'

const deviceStore = useDeviceStore()
const router = useRouter()

const overview = reactive({ total_products: 0, total_devices: 0, online_devices: 0, offline_devices: 0, active_alerts: 0, today_alerts: 0 })
const sensorData = reactive({ temperature: 0, humidity: 0, light_intensity: 0, soil_moisture: 0, co2: 0, soil_temperature: 0, soil_ph: 0, wind_speed: 0, rainfall: 0 })
const actuatorData = reactive({ fan_status: false, light_status: false, pump_status: false, brightness: 0, work_mode: 'manual' })
const alertSummary = reactive({ critical_count: 0, error_count: 0, warning_count: 0, info_count: 0, today_total: 0, last_7d_total: 0 })

const recentAlerts = ref([])
const trendProperty = ref('temperature')
const trendChart = ref(null)
const lastUpdateTime = ref('--')
let trendChartInstance = null
let currentDeviceId = null

const activeGreenhouse = ref('all')
const greenhouses = ref([])

const modeText = computed(() => {
  const map = { manual: '手动模式', auto: '自动模式', eco: '节能模式' }
  return map[actuatorData.work_mode] || actuatorData.work_mode
})

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

function getGroupIdParam() {
  return activeGreenhouse.value === 'all' ? null : parseInt(activeGreenhouse.value)
}

async function loadOverview() {
  try {
    const params = {}
    const groupId = getGroupIdParam()
    if (groupId !== null) params.group_id = groupId
    const resp = await api.get('/dashboard/overview', { params })
    Object.assign(overview, resp.data)
  } catch (e) { console.error('Failed to load overview:', e) }
}

async function loadDeviceRealtime() {
  try {
    const params = {}
    const groupId = getGroupIdParam()
    if (groupId !== null) params.group_id = groupId
    const resp = await api.get('/dashboard/devices/realtime', { params })
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
          soil_temperature: device.reported.soil_temperature ?? 0,
          soil_ph: device.reported.soil_ph ?? 0,
          wind_speed: device.reported.wind_speed ?? 0,
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
      lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
    }
  } catch (e) { console.error('Failed to load device realtime:', e) }
}

async function loadAlertSummary() {
  try {
    const params = {}
    const groupId = getGroupIdParam()
    if (groupId !== null) params.group_id = groupId
    const resp = await api.get('/dashboard/alerts/summary', { params })
    Object.assign(alertSummary, resp.data)
  } catch (e) { console.error('Failed to load alert summary:', e) }
}

async function loadRecentAlerts() {
  try {
    const params = { limit: 5 }
    const groupId = getGroupIdParam()
    if (groupId !== null) params.group_id = groupId
    const resp = await api.get('/dashboard/alerts/recent', { params })
    recentAlerts.value = resp.data.alerts || []
  } catch (e) { console.error('Failed to load recent alerts:', e) }
}

async function loadGreenhouses() {
  try {
    const resp = await api.get('/dashboard/greenhouses')
    greenhouses.value = resp.data.greenhouses || []
  } catch (e) { console.error('Failed to load greenhouses:', e) }
}

function handleGreenhouseChange(val) {
  activeGreenhouse.value = val
  currentDeviceId = null
  refreshAll()
}

async function loadTrendData() {
  if (!currentDeviceId) return
  try {
    const resp = await api.get('/dashboard/telemetry/trend', {
      params: { device_id: currentDeviceId, property_identifier: trendProperty.value, hours: 6 }
    })
    updateTrendChart(resp.data.data || [])
  } catch (e) { console.error('Failed to load trend data:', e) }
}

function updateTrendChart(data) {
  if (!trendChart.value) return
  if (!trendChartInstance) trendChartInstance = echarts.init(trendChart.value)

  const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
  const values = data.map(d => d.value)

  const propNames = {
    temperature: { name: '温度', unit: '°C', color: '#f56c6c' },
    humidity: { name: '湿度', unit: '%', color: '#409eff' },
    soil_moisture: { name: '土壤湿度', unit: '%', color: '#67c23a' },
    co2: { name: 'CO₂浓度', unit: 'ppm', color: '#e6a23c' },
    soil_temperature: { name: '土壤温度', unit: '°C', color: '#f78989' },
    soil_ph: { name: '土壤pH', unit: 'pH', color: '#b37feb' },
    wind_speed: { name: '风速', unit: 'm/s', color: '#36cfc9' },
    rainfall: { name: '雨量', unit: 'mm', color: '#597ef7' }
  }
  const prop = propNames[trendProperty.value] || { name: '', unit: '', color: '#409eff' }

  trendChartInstance.setOption({
    tooltip: { trigger: 'axis', formatter: `{b}<br/>${prop.name}: {c} ${prop.unit}` },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: labels, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: prop.unit, axisLabel: { fontSize: 10 } },
    series: [{
      name: prop.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      data: values,
      lineStyle: { color: prop.color, width: 2 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: prop.color + '40' },
        { offset: 1, color: prop.color + '05' }
      ])}
    }]
  })
}

async function toggleFan(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, { service_identifier: 'set_fan', input_params: { status: val } })
    ElMessage.success(`通风扇已${val ? '开启' : '关闭'}`)
  } catch (e) { ElMessage.error('操作失败'); actuatorData.fan_status = !val }
}

async function toggleLight(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, { service_identifier: 'set_light', input_params: { status: val, brightness: val ? 80 : 0 } })
    ElMessage.success(`补光灯已${val ? '开启' : '关闭'}`)
    if (val) actuatorData.brightness = 80
  } catch (e) { ElMessage.error('操作失败'); actuatorData.light_status = !val }
}

async function togglePump(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, { service_identifier: 'set_pump', input_params: { status: val } })
    ElMessage.success(`水泵已${val ? '开启' : '关闭'}`)
  } catch (e) { ElMessage.error('操作失败'); actuatorData.pump_status = !val }
}

async function changeMode(val) {
  if (!currentDeviceId) return
  try {
    await api.post(`/devices/${currentDeviceId}/commands`, { service_identifier: 'set_mode', input_params: { mode: val } })
    ElMessage.success(`已切换到${modeText.value}`)
  } catch (e) { ElMessage.error('操作失败') }
}

function openBigScreen() { router.push('/big-screen') }
function goToDevices() { router.push('/devices') }
function goToAlerts() { router.push('/alerts') }
function goToScenes() { router.push('/scenes') }

function handleDeviceStatus(data) {
  const eventData = data.data || data
  if (eventData.device_id === currentDeviceId && eventData.property_identifier) {
    const prop = eventData.property_identifier
    const val = parseFloat(eventData.value)
    if (prop in sensorData) sensorData[prop] = isNaN(val) ? eventData.value : val
    if (prop in actuatorData) actuatorData[prop] = isNaN(val) ? eventData.value : val
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
  }
}

function handleNewAlert(data) { loadAlertSummary(); loadRecentAlerts(); loadOverview() }

async function refreshAll() {
  await Promise.all([loadOverview(), loadDeviceRealtime(), loadAlertSummary(), loadRecentAlerts()])
  ElMessage.success('数据已刷新')
}

onMounted(async () => {
  await loadGreenhouses()
  await refreshAll()
  await nextTick()
  await loadTrendData()
  sseManager.on('devices', 'device_status', handleDeviceStatus)
  sseManager.on('alerts', 'new_alert', handleNewAlert)
  window.addEventListener('resize', () => trendChartInstance?.resize())
})

onUnmounted(() => {
  sseManager.off('devices', 'device_status', handleDeviceStatus)
  sseManager.off('alerts', 'new_alert', handleNewAlert)
  if (trendChartInstance) trendChartInstance.dispose()
})
</script>

<style scoped>
.dashboard { padding: 0; }

.greenhouse-tabs {
  margin-bottom: 20px;
}

.greenhouse-tabs :deep(.el-tabs__header) {
  border-bottom: 2px solid #e4e7ed;
}

.greenhouse-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.greenhouse-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  padding: 12px 20px;
  margin-right: 8px;
  border-radius: 8px 8px 0 0;
  transition: all 0.3s;
  color: #606266;
}

.greenhouse-tabs :deep(.el-tabs__item:hover) {
  color: #409eff;
  background: #ecf5ff;
}

.greenhouse-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: none;
}

.greenhouse-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: #fff;
}

.header-info { flex: 1; }

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}

.page-subtitle {
  margin: 6px 0 0;
  font-size: 14px;
  color: rgba(255,255,255,0.8);
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card { border: none; border-radius: 12px; }
.stat-card :deep(.el-card__body) { padding: 20px; }

.stat-inner { display: flex; align-items: center; gap: 16px; }

.stat-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  overflow: visible;
}

.stat-product .stat-icon-wrap { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-device .stat-icon-wrap { background: linear-gradient(135deg, #11998e, #38ef7d); }
.stat-alert .stat-icon-wrap { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-green .stat-icon-wrap { background: linear-gradient(135deg, #4facfe, #00f2fe); }

.stat-info { flex: 1; }

.stat-label { font-size: 13px; color: #909399; margin-bottom: 6px; }

.stat-value { font-size: 28px; font-weight: 700; color: #303133; line-height: 1.2; }

.stat-sub { font-size: 12px; color: #909399; margin-top: 4px; }

.online-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #67c23a;
  margin-right: 4px;
  animation: pulse 2s infinite;
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.alert-blink { color: #f56c6c; animation: blink 1s infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

.main-row { margin-bottom: 20px; }

.section-card { border-radius: 12px; margin-bottom: 20px; }

.section-card :deep(.el-card__header) { padding: 14px 20px; border-bottom: 1px solid #f0f2f5; }

.card-header { display: flex; align-items: center; justify-content: space-between; }

.card-title { font-size: 15px; font-weight: 600; color: #303133; }

.update-time { font-size: 12px; color: #909399; }

.sensor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }

.chart-card { margin-bottom: 0; }

.trend-chart { height: 280px; }

.actuator-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }

.actuator-card {
  border-radius: 12px;
  text-align: center;
  padding: 16px;
  transition: all 0.3s;
  border: 2px solid #ebeef5;
}

.actuator-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

.actuator-card.active { border-color: #67c23a; background: rgba(103, 194, 58, 0.05); }

.actuator-card.mode-card { border-color: #409eff; }

.actuator-icon-wrap { font-size: 32px; margin-bottom: 8px; color: #606266; }

.actuator-name { font-size: 14px; font-weight: 600; color: #303133; margin-bottom: 4px; }

.actuator-status { font-size: 12px; color: #909399; margin-bottom: 12px; }

.alert-list { min-height: 180px; }

.empty-alert {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
  color: #909399;
}

.empty-alert p { margin-top: 8px; font-size: 13px; }

.alert-item { display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f0f2f5; }
.alert-item:last-child { border-bottom: none; }

.alert-tag { flex-shrink: 0; margin-top: 2px; }

.alert-content { flex: 1; min-width: 0; }

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

.alert-time { font-size: 11px; color: #909399; margin-top: 4px; }

.quick-actions { display: flex; flex-wrap: wrap; gap: 8px; }

@media (max-width: 1400px) {
  .sensor-grid { grid-template-columns: repeat(2, 1fr); }
  .actuator-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>