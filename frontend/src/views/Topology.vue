<template>
  <div class="topology-page">
    <div class="topology-container">
      <div class="toolbar">
        <div class="toolbar-left">
        <el-button-group>
          <el-button @click="zoomIn" :disabled="scale >= 2">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button @click="zoomOut" :disabled="scale <= 0.3">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button @click="resetView">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </el-button-group>
        <span class="scale-text">{{ Math.round(scale * 100) }}%</span>
        <el-divider direction="vertical" />
        <el-button-group>
          <el-button :type="viewMode === 'overview' ? 'primary' : 'default'" size="small" @click="switchToOverview">
            🌐 总览
          </el-button>
          <el-button :type="viewMode === 'detail' ? 'primary' : 'default'" size="small" @click="switchToDetail" :disabled="!currentOverviewDevice">
            🏠 大棚详情
          </el-button>
        </el-button-group>
        <el-divider direction="vertical" />
        <template v-if="viewMode === 'detail'">
          <span class="device-name">🏠 {{ deviceInfo.device_name || '智慧大棚' }}</span>
          <el-tag :type="deviceStatusType" size="small">{{ deviceStatusText }}</el-tag>
        </template>
        <template v-else>
          <span class="device-name">🌐 园区总览</span>
          <el-tag type="info" size="small">{{ filteredDevices.length }} 个设备</el-tag>
          <el-divider direction="vertical" />
          <el-select v-model="selectedZone" size="small" style="width: 100px;" placeholder="分区筛选">
            <el-option label="全部" value="" />
            <el-option label="东区" value="east" />
            <el-option label="西区" value="west" />
            <el-option label="南区" value="south" />
            <el-option label="北区" value="north" />
          </el-select>
          <el-input v-model="searchKeyword" size="small" style="width: 150px;" placeholder="搜索大棚..." prefix-icon="Search" />
        </template>
      </div>
        <div class="toolbar-right">
          <el-select v-model="currentTheme" size="default" style="width: 140px; margin-right: 12px;" @change="onThemeChange">
            <el-option label="科技黑" value="tech-dark" />
            <el-option label="简洁白" value="light" />
            <el-option label="大棚绿" value="greenhouse" />
            <el-option label="自定义" value="custom" />
          </el-select>
          <el-switch v-model="editMode" active-text="编辑模式" inactive-text="查看模式" @change="onEditModeChange" />
          <el-button @click="showBgUpload = true" style="margin-left: 12px;">
            <el-icon><Picture /></el-icon>
            背景图
          </el-button>
        </div>
      </div>

      <div
        ref="canvasContainer"
        class="canvas-container"
        :class="[
          'theme-' + currentTheme,
          { 'edit-mode': editMode }
        ]"
        @mousedown="handleCanvasMouseDown"
        @mousemove="handleCanvasMouseMove"
        @mouseup="handleCanvasMouseUp"
        @mouseleave="handleCanvasMouseUp"
        @wheel="handleWheel"
      >
        <div
          class="canvas"
          :class="['canvas-theme-' + currentTheme]"
          :style="canvasStyle"
        >
          <!-- 总览模式：显示所有设备 -->
          <template v-if="viewMode === 'overview'">
            <div class="zone-label zone-east">
              <span class="zone-icon">📍</span>
              <span>东区</span>
              <span class="zone-count">{{ zoneDeviceCounts.east }}</span>
            </div>
            <div class="zone-label zone-west">
              <span class="zone-icon">📍</span>
              <span>西区</span>
              <span class="zone-count">{{ zoneDeviceCounts.west }}</span>
            </div>
            <div class="zone-label zone-south">
              <span class="zone-icon">📍</span>
              <span>南区</span>
              <span class="zone-count">{{ zoneDeviceCounts.south }}</span>
            </div>
            <div class="zone-label zone-north">
              <span class="zone-icon">📍</span>
              <span>北区</span>
              <span class="zone-count">{{ zoneDeviceCounts.north }}</span>
            </div>
            <div
              v-for="device in overviewDeviceNodes"
              :key="device.id"
              class="node-icon overview-device-node"
              :class="[
                'device-' + device.id,
                {
                  'status-online': device.status === 'online',
                  'status-offline': device.status !== 'online',
                  dragging: draggingNode?.id === ('device_' + device.id)
                }
              ]"
              :style="getOverviewDeviceStyle(device)"
              @mousedown.stop="editMode && handleOverviewDeviceMouseDown($event, device)"
              @click.stop="!editMode && handleOverviewDeviceClick(device)"
            >
              <div class="node-icon-inner overview-device-icon">
                <span class="node-emoji">🏠</span>
              </div>
              <div class="overview-device-name">{{ device.device_name }}</div>
              <div class="overview-device-status" :class="'status-' + device.status">
                {{ device.status === 'online' ? '在线' : '离线' }}
              </div>
            </div>
          </template>

          <!-- 详情模式：显示传感器和执行器 -->
          <template v-else>
            <div
              v-if="currentTheme === 'custom' && config.background_image"
              class="background-image"
              :style="{ backgroundImage: 'url(' + config.background_image + ')' }"
            ></div>

            <div v-if="currentTheme === 'tech-dark'" class="tech-dark-bg">
              <div class="grid-lines"></div>
              <div class="glow-effect"></div>
            </div>

            <div v-if="currentTheme === 'light'" class="light-bg">
              <div class="light-grid"></div>
            </div>

            <div v-if="currentTheme === 'greenhouse'" class="background-greenhouse">
              <div class="greenhouse-outline">
                <div class="greenhouse-roof"></div>
                <div class="greenhouse-body">
                  <div class="greenhouse-label">{{ deviceInfo.device_name || '智慧大棚' }}</div>
                </div>
              </div>
            </div>

            <div
              v-for="node in sensorNodes"
              :key="node.id"
              class="node-icon sensor-node"
              :class="[
                'node-' + node.id,
                { 
                  'status-warning': node.isWarning,
                  'status-normal': !node.isWarning && hasData,
                  'status-offline': !hasData,
                  dragging: draggingNode?.id === node.id
                }
              ]"
              :style="getNodeStyle(node)"
              @mousedown.stop="editMode && handleNodeMouseDown($event, node)"
              @click.stop="!editMode && handleSensorClick(node)"
            >
              <div class="node-icon-inner" :style="getNodeIconStyle(node)">
                <span class="node-emoji">{{ node.icon }}</span>
              </div>
              <div class="node-value" v-if="hasData && node.value !== undefined">
                {{ formatValue(node.value, node.decimals) }}
                <span class="node-unit">{{ node.unit }}</span>
              </div>
              <div class="node-value no-data" v-else>--</div>
              <div class="node-label">{{ node.name }}</div>
            </div>

            <div
              v-for="node in actuatorNodes"
              :key="node.id"
              class="node-icon actuator-node"
              :class="[
                'node-' + node.id,
                { 
                  'status-on': node.isOn,
                  'status-off': !node.isOn,
                  dragging: draggingNode?.id === node.id
                }
              ]"
              :style="getNodeStyle(node)"
              @mousedown.stop="editMode && handleNodeMouseDown($event, node)"
              @click.stop="!editMode && handleActuatorClick(node)"
            >
              <div class="node-icon-inner" :class="{ 'rotating': node.isRotating && node.isOn }">
                <span class="node-emoji">{{ node.icon }}</span>
              </div>
              <div class="node-actuator-status">{{ node.isOn ? '运行中' : '已关闭' }}</div>
              <div class="node-label">{{ node.name }}</div>
            </div>
          </template>
        </div>
      </div>

      <div class="legend-bar">
        <div class="legend-item">
          <span class="legend-dot normal"></span>
          <span>正常</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot warning"></span>
          <span>告警</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot offline"></span>
          <span>离线</span>
        </div>
        <el-divider direction="vertical" />
        <div class="legend-item">
          <span class="legend-dot actuator-on"></span>
          <span>执行器运行</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot actuator-off"></span>
          <span>执行器停止</span>
        </div>
        <el-divider direction="vertical" />
        <span class="update-time">更新时间: {{ lastUpdateTime }}</span>
      </div>
    </div>

    <el-dialog v-model="showBgUpload" title="背景图设置" width="500px">
      <el-upload
        class="bg-uploader"
        :show-file-list="false"
        :auto-upload="false"
        accept="image/*"
        :on-change="handleBgFileChange"
      >
        <div v-if="tempBgImage" class="bg-preview">
          <img :src="tempBgImage" alt="preview" />
        </div>
        <div v-else class="bg-uploader-text">
          <el-icon :size="48"><UploadFilled /></el-icon>
          <p>点击上传背景图片（大棚平面图/沙盘照片）</p>
        </div>
      </el-upload>
      <div class="bg-actions">
        <el-button @click="useDefaultBg">使用默认大棚图</el-button>
        <el-button @click="clearBackground" :disabled="!config.background_image">清除背景</el-button>
      </div>
      <template #footer>
        <el-button @click="showBgUpload = false">取消</el-button>
        <el-button type="primary" @click="saveBackground" :loading="savingBg">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSensorDetail" title="" width="360px" :show-close="true">
      <div v-if="selectedSensor" class="sensor-detail">
        <div class="detail-header" :class="{ warning: selectedSensor.isWarning }">
          <span class="detail-icon">{{ selectedSensor.icon }}</span>
          <div class="detail-info">
            <div class="detail-name">{{ selectedSensor.name }}</div>
            <div class="detail-value">
              {{ formatValue(selectedSensor.value, selectedSensor.decimals) }}
              <span class="detail-unit">{{ selectedSensor.unit }}</span>
            </div>
          </div>
        </div>
        <el-descriptions :column="1" border size="small" style="margin-top: 16px;">
          <el-descriptions-item label="状态">
            <el-tag :type="selectedSensor.isWarning ? 'warning' : 'success'" size="small">
              {{ selectedSensor.isWarning ? '超出正常范围' : '正常' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="正常范围">
            {{ selectedSensor.min }} ~ {{ selectedSensor.max }} {{ selectedSensor.unit }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <el-dialog v-model="showActuatorConfirm" title="" width="360px" :show-close="true">
      <div v-if="selectedActuator" class="actuator-confirm">
        <div class="confirm-header">
          <span class="confirm-icon">{{ selectedActuator.icon }}</span>
          <div class="confirm-info">
            <div class="confirm-name">{{ selectedActuator.name }}</div>
            <div class="confirm-status">
              当前状态：
              <el-tag :type="selectedActuator.isOn ? 'success' : 'info'" size="small">
                {{ selectedActuator.isOn ? '运行中' : '已关闭' }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="confirm-action">
          <span>确定要{{ selectedActuator.isOn ? '关闭' : '开启' }}{{ selectedActuator.name }}吗？</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="showActuatorConfirm = false">取消</el-button>
        <el-button type="primary" :loading="sendingCommand" @click="executeActuatorCommand">
          {{ selectedActuator?.isOn ? '关闭' : '开启' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ZoomIn, ZoomOut, Refresh, Picture, UploadFilled } from '@element-plus/icons-vue'
import api from '../services/api.js'

const canvasContainer = ref(null)
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const editMode = ref(false)
const currentTheme = ref('tech-dark')
const viewMode = ref('overview')
const currentOverviewDevice = ref(null)
const selectedZone = ref('')
const searchKeyword = ref('')

const deviceInfo = reactive({
  id: null,
  device_name: '',
  status: 'offline',
  product_id: null
})

const allDevices = ref([])

const config = reactive({
  id: null,
  background_image: null,
  canvas_width: 900,
  canvas_height: 600
})

const showBgUpload = ref(false)
const tempBgImage = ref('')
const savingBg = ref(false)

const draggingNode = ref(null)
const dragOffset = reactive({ x: 0, y: 0 })

const isPanning = ref(false)
const panStart = reactive({ x: 0, y: 0 })

const shadowData = reactive({})
const hasData = ref(false)
const lastUpdateTime = ref('--')
let shadowDataRef = shadowData

const showSensorDetail = ref(false)
const selectedSensor = ref(null)
const showActuatorConfirm = ref(false)
const selectedActuator = ref(null)
const sendingCommand = ref(false)

const sensorConfigs = ref([])
const actuatorConfigs = ref([])

let refreshTimer = null
const nodePositions = reactive({})

const defaultFallbackConfigs = {
  sensors: [
    { id: 'temperature', name: '温度传感器', icon: '🌡️', unit: '°C', decimals: 1, min: 15, max: 30, color: '#f56c6c' },
    { id: 'humidity', name: '空气湿度', icon: '💧', unit: '%', decimals: 1, min: 40, max: 70, color: '#409eff' },
    { id: 'light_intensity', name: '光照传感器', icon: '☀️', unit: 'lux', decimals: 0, min: 1000, max: 50000, color: '#e6a23c' },
    { id: 'soil_moisture', name: '土壤湿度', icon: '🌱', unit: '%', decimals: 1, min: 30, max: 80, color: '#67c23a' },
    { id: 'co2', name: 'CO₂浓度', icon: '💨', unit: 'ppm', decimals: 0, min: 400, max: 1500, color: '#909399' },
    { id: 'soil_temperature', name: '土壤温度', icon: '🪴', unit: '°C', decimals: 1, min: 15, max: 28, color: '#8e44ad' }
  ],
  actuators: [
    { id: 'fan_status', name: '通风扇', icon: '🌀', service: 'set_fan', param: 'fan_status', isRotating: true },
    { id: 'light_status', name: '补光灯', icon: '💡', service: 'set_light', param: 'light_status', isRotating: false },
    { id: 'pump_status', name: '灌溉水泵', icon: '🚿', service: 'set_pump', param: 'pump_status', isRotating: false }
  ],
  positions: {
    temperature: { x: 100, y: 120 },
    humidity: { x: 280, y: 120 },
    light_intensity: { x: 460, y: 120 },
    co2: { x: 640, y: 120 },
    soil_temperature: { x: 190, y: 300 },
    soil_moisture: { x: 370, y: 300 },
    fan_status: { x: 100, y: 460 },
    light_status: { x: 340, y: 460 },
    pump_status: { x: 580, y: 460 }
  }
}

function getPositionsKey() {
  const pid = deviceInfo.product_id || 'default'
  return `topology_positions_${pid}`
}

function getDefaultPositions() {
  const positions = {}
  sensorConfigs.value.forEach(cfg => {
    if (cfg.default_x !== undefined && cfg.default_y !== undefined) {
      positions[cfg.id] = { x: cfg.default_x, y: cfg.default_y }
    }
  })
  actuatorConfigs.value.forEach(cfg => {
    if (cfg.default_x !== undefined && cfg.default_y !== undefined) {
      positions[cfg.id] = { x: cfg.default_x, y: cfg.default_y }
    }
  })
  return Object.keys(positions).length > 0 ? positions : defaultFallbackConfigs.positions
}

const sensorNodes = computed(() => {
  return sensorConfigs.value.map(cfg => {
    const value = shadowData[cfg.id]
    const isWarning = value !== undefined && (value < cfg.min || value > cfg.max)
    const defaultPos = getDefaultPositions()
    const pos = nodePositions[cfg.id] || defaultPos[cfg.id] || { x: 100, y: 100 }
    return {
      ...cfg,
      value,
      isWarning,
      x: pos.x,
      y: pos.y
    }
  })
})

const actuatorNodes = computed(() => {
  return actuatorConfigs.value.map(cfg => {
    const isOn = !!shadowData[cfg.id]
    const defaultPos = getDefaultPositions()
    const pos = nodePositions[cfg.id] || defaultPos[cfg.id] || { x: 100, y: 100 }
    return {
      ...cfg,
      isOn,
      x: pos.x,
      y: pos.y
    }
  })
})

const overviewDeviceNodes = computed(() => {
  return filteredDevices.value.map((device, index) => {
    const posKey = `device_${device.id}`
    const defaultPos = getOverviewDevicePosition(device, index)
    const pos = nodePositions[posKey] || defaultPos
    return {
      ...device,
      x: pos.x,
      y: pos.y
    }
  })
})

const filteredDevices = computed(() => {
  return allDevices.value.filter(device => {
    const matchZone = !selectedZone.value || getDeviceZone(device) === selectedZone.value
    const matchSearch = !searchKeyword.value || 
      (device.device_name && device.device_name.toLowerCase().includes(searchKeyword.value.toLowerCase()))
    return matchZone && matchSearch
  })
})

const zoneDeviceCounts = computed(() => {
  const counts = { east: 0, west: 0, south: 0, north: 0 }
  filteredDevices.value.forEach(device => {
    counts[getDeviceZone(device)]++
  })
  return counts
})

function getDeviceZone(device) {
  const name = (device.device_name || '').toLowerCase()
  if (name.includes('东') || name.includes('a')) return 'east'
  if (name.includes('西') || name.includes('b')) return 'west'
  if (name.includes('南') || name.includes('c')) return 'south'
  if (name.includes('北') || name.includes('d')) return 'north'
  return 'east'
}

function getOverviewDevicePosition(device, index) {
  const zone = getDeviceZone(device)
  const zoneConfigs = {
    east: { startX: 250, startY: 100, cols: 3, gapX: 180, gapY: 160 },
    west: { startX: 550, startY: 100, cols: 3, gapX: 180, gapY: 160 },
    south: { startX: 400, startY: 350, cols: 3, gapX: 180, gapY: 160 },
    north: { startX: 400, startY: 50, cols: 3, gapX: 180, gapY: 160 }
  }
  const config = zoneConfigs[zone] || zoneConfigs.east
  const filteredZoneDevices = allDevices.value.filter(d => getDeviceZone(d) === zone)
  const zoneIndex = filteredZoneDevices.findIndex(d => d.id === device.id)
  const col = zoneIndex % config.cols
  const row = Math.floor(zoneIndex / config.cols)
  return {
    x: config.startX + col * config.gapX,
    y: config.startY + row * config.gapY
  }
}

const deviceStatusType = computed(() => {
  const map = { online: 'success', offline: 'info', error: 'danger' }
  return map[deviceInfo.status] || 'info'
})

const deviceStatusText = computed(() => {
  const map = { online: '在线', offline: '离线', error: '异常' }
  return map[deviceInfo.status] || deviceInfo.status
})

const canvasStyle = computed(() => ({
  width: config.canvas_width + 'px',
  height: config.canvas_height + 'px',
  transform: `translate(${panX.value}px, ${panY.value}px) scale(${scale.value})`,
  transformOrigin: '0 0'
}))

function getNodeStyle(node) {
  return {
    left: node.x + 'px',
    top: node.y + 'px'
  }
}

function getOverviewDeviceStyle(device) {
  return {
    left: device.x + 'px',
    top: device.y + 'px'
  }
}

function getNodeIconStyle(node) {
  if (node.color) {
    return {
      borderColor: node.color,
      boxShadow: `0 0 0 3px ${node.color}33`
    }
  }
  return {}
}

function formatValue(val, decimals) {
  if (val === null || val === undefined || isNaN(val)) return '--'
  return Number(val).toFixed(decimals)
}

function loadPositions() {
  try {
    const key = getPositionsKey()
    const saved = localStorage.getItem(key)
    Object.keys(nodePositions).forEach(key => delete nodePositions[key])
    if (saved) {
      const parsed = JSON.parse(saved)
      Object.assign(nodePositions, parsed)
    }
  } catch (e) {
    Object.keys(nodePositions).forEach(key => delete nodePositions[key])
  }
}

function savePositions() {
  try {
    const key = getPositionsKey()
    localStorage.setItem(key, JSON.stringify(nodePositions))
  } catch (e) {}
}

function loadTheme() {
  try {
    const saved = localStorage.getItem('topology_theme')
    if (saved) {
      currentTheme.value = saved
    }
  } catch (e) {}
}

function saveTheme(theme) {
  try {
    localStorage.setItem('topology_theme', theme)
  } catch (e) {}
}

function onThemeChange(theme) {
  saveTheme(theme)
  if (theme === 'custom' && !config.background_image) {
    showBgUpload.value = true
  }
}

function parseTslProperties(properties) {
  const sensors = []
  const actuators = []

  if (!Array.isArray(properties)) {
    return { sensors, actuators }
  }

  properties.forEach(prop => {
    const specs = prop.specs || {}
    if (!specs.ui_type) return

    const baseConfig = {
      id: prop.identifier,
      name: prop.name || prop.identifier,
      icon: specs.ui_icon || '📦',
      color: specs.ui_color || null
    }

    if (specs.ui_type === 'sensor') {
      sensors.push({
        ...baseConfig,
        unit: specs.ui_unit || '',
        decimals: specs.ui_decimals !== undefined ? specs.ui_decimals : 1,
        min: specs.ui_normal_min !== undefined ? specs.ui_normal_min : 0,
        max: specs.ui_normal_max !== undefined ? specs.ui_normal_max : 100,
        default_x: specs.ui_default_x,
        default_y: specs.ui_default_y
      })
    } else if (specs.ui_type === 'actuator') {
      actuators.push({
        ...baseConfig,
        service: specs.ui_service || '',
        param: specs.ui_service_param || prop.identifier,
        isRotating: prop.identifier === 'fan_status',
        default_x: specs.ui_default_x,
        default_y: specs.ui_default_y
      })
    }
  })

  return { sensors, actuators }
}

async function loadTsl(productId) {
  if (!productId) return
  
  try {
    const res = await api.get(`/products/${productId}/tsl`)
    const tsl = res.data
    const properties = tsl?.properties || []
    const { sensors, actuators } = parseTslProperties(properties)
    
    if (sensors.length > 0 || actuators.length > 0) {
      sensorConfigs.value = sensors
      actuatorConfigs.value = actuators
    } else {
      sensorConfigs.value = defaultFallbackConfigs.sensors
      actuatorConfigs.value = defaultFallbackConfigs.actuators
    }
  } catch (error) {
    console.error('Failed to load TSL:', error)
    sensorConfigs.value = defaultFallbackConfigs.sensors
    actuatorConfigs.value = defaultFallbackConfigs.actuators
  }
}

function zoomIn() {
  if (scale.value < 2) {
    scale.value = Math.min(2, scale.value + 0.1)
  }
}

function zoomOut() {
  if (scale.value > 0.3) {
    scale.value = Math.max(0.3, scale.value - 0.1)
  }
}

function resetView() {
  scale.value = 1
  panX.value = 0
  panY.value = 0
}

function handleWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(0.3, Math.min(2, scale.value + delta))
}

function handleCanvasMouseDown(e) {
  if (e.target.closest('.node-icon')) return
  if (editMode.value) return
  isPanning.value = true
  panStart.x = e.clientX - panX.value
  panStart.y = e.clientY - panY.value
}

function handleCanvasMouseMove(e) {
  if (isPanning.value) {
    panX.value = e.clientX - panStart.x
    panY.value = e.clientY - panStart.y
  }
  if (draggingNode.value) {
    const rect = canvasContainer.value.getBoundingClientRect()
    const x = (e.clientX - rect.left - panX.value - dragOffset.x) / scale.value
    const y = (e.clientY - rect.top - panY.value - dragOffset.y) / scale.value
    
    let newX, newY
    if (viewMode.value === 'overview' && draggingNode.value.id.startsWith('device_')) {
      newX = Math.max(0, Math.min(config.canvas_width - 100, x))
      newY = Math.max(0, Math.min(config.canvas_height - 100, y))
    } else {
      newX = Math.max(0, Math.min(config.canvas_width - 80, x))
      newY = Math.max(0, Math.min(config.canvas_height - 80, y))
    }
    
    draggingNode.value.x = newX
    draggingNode.value.y = newY
    
    if (nodePositions[draggingNode.value.id]) {
      nodePositions[draggingNode.value.id].x = newX
      nodePositions[draggingNode.value.id].y = newY
    } else {
      nodePositions[draggingNode.value.id] = { x: newX, y: newY }
    }
  }
}

function handleCanvasMouseUp() {
  if (isPanning.value) {
    isPanning.value = false
  }
  if (draggingNode.value) {
    if (viewMode.value === 'overview' && draggingNode.value.id.startsWith('device_')) {
      const deviceId = draggingNode.value.id.replace('device_', '')
      nodePositions[draggingNode.value.id] = {
        x: draggingNode.value.x,
        y: draggingNode.value.y
      }
    } else {
      nodePositions[draggingNode.value.id] = {
        x: draggingNode.value.x,
        y: draggingNode.value.y
      }
    }
    savePositions()
    draggingNode.value = null
  }
}

function handleNodeMouseDown(e, node) {
  draggingNode.value = node
  const rect = e.currentTarget.getBoundingClientRect()
  dragOffset.x = e.clientX - rect.left
  dragOffset.y = e.clientY - rect.top
}

function handleOverviewDeviceMouseDown(e, device) {
  draggingNode.value = { id: 'device_' + device.id, x: device.x, y: device.y }
  const rect = e.currentTarget.getBoundingClientRect()
  dragOffset.x = e.clientX - rect.left
  dragOffset.y = e.clientY - rect.top
}

async function handleOverviewDeviceClick(device) {
  currentOverviewDevice.value = device
  deviceInfo.id = device.id
  deviceInfo.device_name = device.device_name
  deviceInfo.status = device.status
  deviceInfo.product_id = device.product_id || device.product_key
  
  viewMode.value = 'detail'
  loadPositions()
  
  if (deviceInfo.product_id) {
    await loadTsl(deviceInfo.product_id)
  }
  
  await loadDeviceShadow()
  refreshTimer = setInterval(() => {
    loadDeviceShadow()
  }, 3000)
}

function switchToOverview() {
  viewMode.value = 'overview'
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  Object.keys(shadowData).forEach(key => delete shadowData[key])
  hasData.value = false
}

function switchToDetail() {
  if (currentOverviewDevice.value) {
    handleOverviewDeviceClick(currentOverviewDevice.value)
  }
}

function handleSensorClick(node) {
  selectedSensor.value = node
  showSensorDetail.value = true
}

function handleActuatorClick(node) {
  selectedActuator.value = node
  showActuatorConfirm.value = true
}

async function executeActuatorCommand() {
  if (!selectedActuator.value || !deviceInfo.id) return
  sendingCommand.value = true
  try {
    const newState = !selectedActuator.value.isOn
    const params = {}
    params[selectedActuator.value.param] = newState
    await api.post(`/devices/${deviceInfo.id}/commands`, {
      service_identifier: selectedActuator.value.service,
      input_params: params
    })
    ElMessage.success(`${selectedActuator.value.name}已${newState ? '开启' : '关闭'}`)
    showActuatorConfirm.value = false
    setTimeout(() => {
      loadDeviceShadow()
    }, 1000)
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    sendingCommand.value = false
  }
}

function onEditModeChange(val) {
  ElMessage.info(val ? '已进入编辑模式，可拖拽调整设备位置' : '已退出编辑模式')
}

function handleBgFileChange(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    tempBgImage.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

function useDefaultBg() {
  tempBgImage.value = ''
  config.background_image = null
  currentTheme.value = 'greenhouse'
  saveTheme('greenhouse')
  ElMessage.success('已切换为默认大棚示意图')
  showBgUpload.value = false
}

async function saveBackground() {
  if (!tempBgImage.value) {
    ElMessage.warning('请先选择图片')
    return
  }
  savingBg.value = true
  try {
    const res = await api.put('/topology/config', {
      background_image: tempBgImage.value
    })
    config.background_image = res.data.background_image
    currentTheme.value = 'custom'
    saveTheme('custom')
    ElMessage.success('背景图保存成功')
    showBgUpload.value = false
    tempBgImage.value = ''
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingBg.value = false
  }
}

async function clearBackground() {
  savingBg.value = true
  try {
    const res = await api.put('/topology/config', {
      background_image: null
    })
    config.background_image = res.data.background_image
    tempBgImage.value = ''
    ElMessage.success('背景图已清除')
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    savingBg.value = false
  }
}

async function loadDevice() {
  try {
    const res = await api.get('/devices/', { params: { page_size: 1 } })
    if (res.data && res.data.length > 0) {
      const device = res.data[0]
      deviceInfo.id = device.id
      deviceInfo.device_name = device.device_name
      deviceInfo.status = device.status
      deviceInfo.product_id = device.product_id || device.product_key
    }
  } catch (error) {
    console.error('Failed to load device:', error)
  }
}

async function loadDeviceShadow() {
  if (!deviceInfo.id) return
  try {
    const res = await api.get(`/devices/${deviceInfo.id}/shadow`)
    if (res.data && res.data.reported) {
      Object.assign(shadowData, res.data.reported)
      hasData.value = true
      lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
    }
  } catch (error) {
    console.error('Failed to load shadow:', error)
  }
}

async function loadConfig() {
  try {
    const res = await api.get('/topology/config')
    config.id = res.data.id
    config.background_image = res.data.background_image
    if (res.data.canvas_width) config.canvas_width = res.data.canvas_width
    if (res.data.canvas_height) config.canvas_height = res.data.canvas_height
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

watch(() => deviceInfo.product_id, (newVal, oldVal) => {
  if (newVal && newVal !== oldVal) {
    loadPositions()
  }
})

onMounted(async () => {
  loadTheme()
  sensorConfigs.value = defaultFallbackConfigs.sensors
  actuatorConfigs.value = defaultFallbackConfigs.actuators
  await loadAllDevices()
  loadPositions()
})

async function loadAllDevices() {
  try {
    const res = await api.get('/devices/', { params: { page_size: 100 } })
    allDevices.value = res.data || []
  } catch (error) {
    console.error('Failed to load devices:', error)
    allDevices.value = []
  }
}

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.topology-page {
  height: 100%;
}

.topology-container {
  height: calc(100vh - 140px);
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: white;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.device-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.scale-text {
  color: #666;
  font-size: 13px;
  min-width: 50px;
}

.canvas-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  cursor: grab;
}

.canvas-container.theme-tech-dark {
  background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 100%);
}

.canvas-container.theme-light {
  background: #f5f7fa;
}

.canvas-container.theme-greenhouse {
  background: #e8f5e9;
}

.canvas-container.theme-custom {
  background: #2c3e50;
}

.canvas-container.edit-mode {
  cursor: default;
}

.canvas-container.theme-tech-dark.edit-mode {
  background: linear-gradient(135deg, #1a2a4a 0%, #2a3a5a 100%);
}

.canvas-container.theme-light.edit-mode {
  background: #fff3e0;
}

.canvas-container.theme-greenhouse.edit-mode {
  background: #fff3e0;
}

.canvas-container.theme-custom.edit-mode {
  background: #34495e;
}

.canvas-container:active:not(.edit-mode) {
  cursor: grabbing;
}

.canvas {
  position: absolute;
  left: 50%;
  top: 50%;
  margin-left: -450px;
  margin-top: -300px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.canvas-theme-tech-dark {
  background: linear-gradient(180deg, #0d1f3c 0%, #152a4a 100%);
  border: 1px solid rgba(64, 158, 255, 0.3);
  box-shadow: 0 0 30px rgba(64, 158, 255, 0.2), 0 2px 12px rgba(0, 0, 0, 0.3);
}

.canvas-theme-light {
  background: #ffffff;
  border: 1px solid #e4e7ed;
}

.canvas-theme-greenhouse {
  background: white;
}

.canvas-theme-custom {
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tech-dark-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(64, 158, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
}

.glow-effect {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 600px;
  height: 600px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(64, 158, 255, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.light-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.light-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(228, 231, 237, 0.8) 1px, transparent 1px),
    linear-gradient(90deg, rgba(228, 231, 237, 0.8) 1px, transparent 1px);
  background-size: 50px 50px;
}

.background-greenhouse {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #87ceeb 0%, #e8f5e9 100%);
}

.greenhouse-outline {
  width: 85%;
  height: 75%;
  display: flex;
  flex-direction: column;
}

.greenhouse-roof {
  flex: 0 0 60px;
  background: linear-gradient(135deg, transparent 50%, rgba(255,255,255,0.6) 50%),
              linear-gradient(225deg, transparent 50%, rgba(255,255,255,0.6) 50%);
  background-size: 40px 40px;
  background-color: rgba(200, 230, 255, 0.5);
  border: 2px solid rgba(100, 150, 200, 0.6);
  border-bottom: none;
  clip-path: polygon(50% 0%, 100% 100%, 0% 100%);
}

.greenhouse-body {
  flex: 1;
  background: rgba(255, 255, 255, 0.3);
  border: 2px solid rgba(100, 150, 200, 0.6);
  border-top: none;
  position: relative;
  background-image:
    linear-gradient(90deg, rgba(100, 150, 200, 0.3) 1px, transparent 1px),
    linear-gradient(rgba(100, 150, 200, 0.3) 1px, transparent 1px);
  background-size: 60px 60px;
}

.greenhouse-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 32px;
  color: rgba(100, 150, 200, 0.4);
  font-weight: bold;
  letter-spacing: 8px;
}

.background-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: 8px;
}

.node-icon {
  position: absolute;
  width: 80px;
  cursor: pointer;
  user-select: none;
  z-index: 10;
  transition: transform 0.15s;
}

.node-icon:hover {
  transform: translateY(-2px);
  z-index: 20;
}

.node-icon.dragging {
  z-index: 100;
  transform: scale(1.1);
}

.node-icon-inner {
  width: 52px;
  height: 52px;
  margin: 0 auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 3px solid #909399;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.2s;
}

.node-emoji {
  font-size: 24px;
  line-height: 1;
}

.sensor-node.status-normal .node-icon-inner {
  border-color: #67c23a;
  box-shadow: 0 0 0 3px rgba(103, 194, 58, 0.2);
}

.sensor-node.status-warning .node-icon-inner {
  border-color: #f56c6c;
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.2);
  animation: warning-blink 1s infinite;
}

.sensor-node.status-offline .node-icon-inner {
  border-color: #c0c4cc;
  opacity: 0.6;
}

.actuator-node.status-on .node-icon-inner {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
  background: #ecf5ff;
}

.actuator-node.status-off .node-icon-inner {
  border-color: #c0c4cc;
  opacity: 0.7;
}

.overview-device-node {
  width: 100px;
}

.overview-device-icon {
  width: 60px;
  height: 60px;
  border-width: 4px;
}

.overview-device-node.status-online .overview-device-icon {
  border-color: #67c23a;
  box-shadow: 0 0 0 4px rgba(103, 194, 58, 0.3);
  background: #f0f9eb;
}

.overview-device-node.status-offline .overview-device-icon {
  border-color: #c0c4cc;
  opacity: 0.6;
  background: #f5f5f5;
}

.overview-device-name {
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-top: 6px;
  background: rgba(255, 255, 255, 0.95);
  padding: 3px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.overview-device-status {
  text-align: center;
  font-size: 11px;
  margin-top: 4px;
  padding: 2px 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.95);
}

.overview-device-status.status-online {
  color: #67c23a;
  font-weight: 500;
}

.overview-device-status.status-offline {
  color: #909399;
}

.zone-label {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  z-index: 5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.canvas-theme-tech-dark .zone-label {
  background: rgba(13, 31, 60, 0.9);
  color: #e6f0ff;
  border-color: rgba(64, 158, 255, 0.3);
}

.zone-icon {
  font-size: 14px;
}

.zone-count {
  padding: 1px 6px;
  background: rgba(64, 158, 255, 0.2);
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
  color: #409eff;
}

.canvas-theme-tech-dark .zone-count {
  background: rgba(64, 158, 255, 0.3);
}

.zone-east { top: 10px; left: 10px; }
.zone-west { top: 10px; right: 10px; }
.zone-south { bottom: 10px; left: 50%; transform: translateX(-50%); }
.zone-north { top: 50%; right: 10px; transform: translateY(-50%); }

.node-icon-inner.rotating {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes warning-blink {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.2);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(245, 108, 108, 0);
  }
}

.node-value {
  text-align: center;
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  margin-top: 6px;
  background: rgba(255, 255, 255, 0.95);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.canvas-theme-tech-dark .node-value {
  background: rgba(13, 31, 60, 0.9);
  color: #e6f0ff;
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.node-value.no-data {
  color: #c0c4cc;
  font-weight: 400;
}

.node-unit {
  font-size: 11px;
  font-weight: 400;
  color: #909399;
  margin-left: 1px;
}

.canvas-theme-tech-dark .node-unit {
  color: #8fa3bf;
}

.node-actuator-status {
  text-align: center;
  font-size: 11px;
  margin-top: 6px;
  padding: 1px 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.95);
  font-weight: 500;
}

.canvas-theme-tech-dark .node-actuator-status {
  background: rgba(13, 31, 60, 0.9);
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.actuator-node.status-on .node-actuator-status {
  color: #409eff;
  background: #ecf5ff;
}

.canvas-theme-tech-dark .actuator-node.status-on .node-actuator-status {
  background: rgba(64, 158, 255, 0.2);
  border-color: rgba(64, 158, 255, 0.5);
}

.actuator-node.status-off .node-actuator-status {
  color: #909399;
}

.node-label {
  text-align: center;
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.9);
  padding: 1px 6px;
  border-radius: 3px;
}

.canvas-theme-tech-dark .node-label {
  background: rgba(13, 31, 60, 0.9);
  color: #b8c7db;
  border: 1px solid rgba(64, 158, 255, 0.2);
}

.legend-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 20px;
  background: white;
  border-top: 1px solid #e4e7ed;
  font-size: 12px;
  color: #606266;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid;
}

.legend-dot.normal {
  border-color: #67c23a;
  background: #67c23a33;
}

.legend-dot.warning {
  border-color: #f56c6c;
  background: #f56c6c33;
}

.legend-dot.offline {
  border-color: #c0c4cc;
  background: #c0c4cc33;
}

.legend-dot.actuator-on {
  border-color: #409eff;
  background: #409eff33;
}

.legend-dot.actuator-off {
  border-color: #c0c4cc;
  background: #c0c4cc33;
}

.update-time {
  margin-left: auto;
  color: #909399;
}

.bg-uploader {
  text-align: center;
}

.bg-preview {
  width: 100%;
  max-height: 300px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.bg-preview img {
  width: 100%;
  height: auto;
  display: block;
}

.bg-uploader-text {
  padding: 40px 0;
  color: #666;
}

.bg-uploader-text p {
  margin-top: 12px;
}

.bg-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.sensor-detail .detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f0f9eb;
  border-radius: 8px;
}

.sensor-detail .detail-header.warning {
  background: #fef0f0;
}

.detail-icon {
  font-size: 48px;
}

.detail-info {
  flex: 1;
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 32px;
  font-weight: 700;
  color: #67c23a;
  font-family: 'Courier New', monospace;
}

.detail-header.warning .detail-value {
  color: #f56c6c;
}

.detail-unit {
  font-size: 16px;
  font-weight: 400;
  color: #909399;
  margin-left: 4px;
}

.actuator-confirm .confirm-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #ecf5ff;
  border-radius: 8px;
}

.confirm-icon {
  font-size: 48px;
}

.confirm-info {
  flex: 1;
}

.confirm-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.confirm-action {
  margin-top: 20px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}
</style>
