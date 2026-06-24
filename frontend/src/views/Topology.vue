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
          <span class="device-name">🏠 {{ deviceInfo.device_name || '智慧大棚' }}</span>
          <el-tag :type="deviceStatusType" size="small">{{ deviceStatusText }}</el-tag>
        </div>
        <div class="toolbar-right">
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
        :class="{ 'edit-mode': editMode }"
        @mousedown="handleCanvasMouseDown"
        @mousemove="handleCanvasMouseMove"
        @mouseup="handleCanvasMouseUp"
        @mouseleave="handleCanvasMouseUp"
        @wheel="handleWheel"
      >
        <div
          class="canvas"
          :style="canvasStyle"
        >
          <div
            v-if="config.background_image"
            class="background-image"
            :style="{ backgroundImage: 'url(' + config.background_image + ')' }"
          ></div>
          <div
            v-else
            class="background-greenhouse"
          >
            <div class="greenhouse-outline">
              <div class="greenhouse-roof"></div>
              <div class="greenhouse-body">
                <div class="greenhouse-label">智慧大棚</div>
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
            <div class="node-icon-inner">
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
            <div class="node-icon-inner" :class="{ 'rotating': node.id === 'fan_status' && node.isOn }">
              <span class="node-emoji">{{ node.icon }}</span>
            </div>
            <div class="node-actuator-status">{{ node.isOn ? '运行中' : '已关闭' }}</div>
            <div class="node-label">{{ node.name }}</div>
          </div>
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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ZoomIn, ZoomOut, Refresh, Picture, UploadFilled } from '@element-plus/icons-vue'
import api from '../services/api.js'

const canvasContainer = ref(null)
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const editMode = ref(false)

const deviceInfo = reactive({
  id: null,
  device_name: '',
  status: 'offline'
})

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

const showSensorDetail = ref(false)
const selectedSensor = ref(null)
const showActuatorConfirm = ref(false)
const selectedActuator = ref(null)
const sendingCommand = ref(false)

let refreshTimer = null
let nodePositions = {}

const sensorConfigs = [
  { id: 'temperature', name: '温度传感器', icon: '🌡️', unit: '°C', decimals: 1, min: 15, max: 30, color: '#f56c6c' },
  { id: 'humidity', name: '空气湿度', icon: '💧', unit: '%', decimals: 1, min: 40, max: 70, color: '#409eff' },
  { id: 'light_intensity', name: '光照传感器', icon: '☀️', unit: 'lux', decimals: 0, min: 1000, max: 50000, color: '#e6a23c' },
  { id: 'soil_moisture', name: '土壤湿度', icon: '🌱', unit: '%', decimals: 1, min: 30, max: 80, color: '#67c23a' },
  { id: 'co2', name: 'CO₂浓度', icon: '💨', unit: 'ppm', decimals: 0, min: 400, max: 1500, color: '#909399' },
  { id: 'soil_temperature', name: '土壤温度', icon: '🪴', unit: '°C', decimals: 1, min: 15, max: 28, color: '#8e44ad' }
]

const actuatorConfigs = [
  { id: 'fan_status', name: '通风扇', icon: '🌀', service: 'set_fan', param: 'fan_status' },
  { id: 'light_status', name: '补光灯', icon: '💡', service: 'set_light', param: 'light_status' },
  { id: 'pump_status', name: '灌溉水泵', icon: '🚿', service: 'set_pump', param: 'pump_status' }
]

const defaultPositions = {
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

const sensorNodes = computed(() => {
  return sensorConfigs.map(cfg => {
    const value = shadowData[cfg.id]
    const isWarning = value !== undefined && (value < cfg.min || value > cfg.max)
    const pos = nodePositions[cfg.id] || defaultPositions[cfg.id] || { x: 100, y: 100 }
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
  return actuatorConfigs.map(cfg => {
    const isOn = !!shadowData[cfg.id]
    const pos = nodePositions[cfg.id] || defaultPositions[cfg.id] || { x: 100, y: 100 }
    return {
      ...cfg,
      isOn,
      x: pos.x,
      y: pos.y
    }
  })
})

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

function formatValue(val, decimals) {
  if (val === null || val === undefined || isNaN(val)) return '--'
  return Number(val).toFixed(decimals)
}

function loadPositions() {
  try {
    const saved = localStorage.getItem('topology_positions')
    if (saved) {
      nodePositions = JSON.parse(saved)
    }
  } catch (e) {
    nodePositions = {}
  }
}

function savePositions() {
  try {
    localStorage.setItem('topology_positions', JSON.stringify(nodePositions))
  } catch (e) {}
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
    draggingNode.value.x = Math.max(0, Math.min(config.canvas_width - 80, x))
    draggingNode.value.y = Math.max(0, Math.min(config.canvas_height - 80, y))
  }
}

function handleCanvasMouseUp() {
  if (isPanning.value) {
    isPanning.value = false
  }
  if (draggingNode.value) {
    nodePositions[draggingNode.value.id] = {
      x: draggingNode.value.x,
      y: draggingNode.value.y
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

onMounted(async () => {
  loadPositions()
  await Promise.all([loadDevice(), loadConfig()])
  if (deviceInfo.id) {
    await loadDeviceShadow()
  }
  refreshTimer = setInterval(() => {
    loadDeviceShadow()
  }, 3000)
})

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
  background: #e8f5e9;
  cursor: grab;
}

.canvas-container.edit-mode {
  cursor: default;
  background: #fff3e0;
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

.node-actuator-status {
  text-align: center;
  font-size: 11px;
  margin-top: 6px;
  padding: 1px 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.95);
  font-weight: 500;
}

.actuator-node.status-on .node-actuator-status {
  color: #409eff;
  background: #ecf5ff;
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
