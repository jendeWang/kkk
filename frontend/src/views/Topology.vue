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
        </div>
        <div class="toolbar-right">
          <el-button @click="showBgUpload = true">
            <el-icon><Picture /></el-icon>
            背景图设置
          </el-button>
        </div>
      </div>

      <div
        ref="canvasContainer"
        class="canvas-container"
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
            class="background-grid"
          ></div>

          <div
            v-for="device in devicesWithPosition"
            :key="device.id"
            class="device-icon"
            :class="['status-' + device.status, { dragging: draggingDevice?.id === device.id }]"
            :style="getDeviceStyle(device)"
            @mousedown.stop="handleDeviceMouseDown($event, device)"
            @click.stop="handleDeviceClick(device)"
          >
            <div class="device-icon-inner">
              <el-icon :size="24"><Monitor /></el-icon>
            </div>
            <div class="device-label">{{ device.device_name }}</div>
          </div>
        </div>
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
          <p>点击上传背景图片</p>
        </div>
      </el-upload>
      <div class="bg-actions">
        <el-button @click="clearBackground" :disabled="!config.background_image">清除背景</el-button>
      </div>
      <template #footer>
        <el-button @click="showBgUpload = false">取消</el-button>
        <el-button type="primary" @click="saveBackground" :loading="savingBg">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDeviceDetail" title="设备详情" width="420px">
      <div v-if="selectedDevice" class="device-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="设备名称">
            {{ selectedDevice.device_name }}
          </el-descriptions-item>
          <el-descriptions-item label="设备状态">
            <el-tag :type="getStatusType(selectedDevice.status)">
              {{ getStatusText(selectedDevice.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="设备Key">
            {{ selectedDevice.device_key }}
          </el-descriptions-item>
          <el-descriptions-item label="最后在线">
            {{ formatTime(selectedDevice.last_seen) }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="device-latest-data" v-if="deviceLatestData">
          <h4>最新数据</h4>
          <div v-for="(value, key) in deviceLatestData" :key="key" class="data-item">
            <span class="data-key">{{ key }}:</span>
            <span class="data-value">{{ value }}</span>
          </div>
        </div>

        <div class="device-quick-actions">
          <el-button type="primary" @click="goToDeviceDetail">查看详情</el-button>
          <el-button @click="showDeviceDetail = false">关闭</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Monitor, ZoomIn, ZoomOut, Refresh, Picture, UploadFilled } from '@element-plus/icons-vue'
import api from '../services/api.js'

const router = useRouter()

const canvasContainer = ref(null)
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const devices = ref([])
const config = reactive({
  id: null,
  background_image: null,
  canvas_width: 1200,
  canvas_height: 800
})

const showBgUpload = ref(false)
const tempBgImage = ref('')
const savingBg = ref(false)

const draggingDevice = ref(null)
const dragOffset = reactive({ x: 0, y: 0 })

const isPanning = ref(false)
const panStart = reactive({ x: 0, y: 0 })

const showDeviceDetail = ref(false)
const selectedDevice = ref(null)
const deviceLatestData = ref(null)

const canvasStyle = computed(() => ({
  width: config.canvas_width + 'px',
  height: config.canvas_height + 'px',
  transform: `translate(${panX.value}px, ${panY.value}px) scale(${scale.value})`,
  transformOrigin: '0 0'
}))

const devicesWithPosition = computed(() => {
  return devices.value.map((device, index) => {
    let x = 100 + (index % 5) * 150
    let y = 100 + Math.floor(index / 5) * 120
    if (device.extra?.topology) {
      x = device.extra.topology.x ?? x
      y = device.extra.topology.y ?? y
    }
    return { ...device, topologyX: x, topologyY: y }
  })
})

function getDeviceStyle(device) {
  return {
    left: device.topologyX + 'px',
    top: device.topologyY + 'px'
  }
}

function getStatusType(status) {
  const types = { online: 'success', offline: 'info', error: 'danger' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { online: '在线', offline: '离线', error: '告警' }
  return texts[status] || status
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
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
  if (e.target.closest('.device-icon')) return
  isPanning.value = true
  panStart.x = e.clientX - panX.value
  panStart.y = e.clientY - panY.value
}

function handleCanvasMouseMove(e) {
  if (isPanning.value) {
    panX.value = e.clientX - panStart.x
    panY.value = e.clientY - panStart.y
  }
  if (draggingDevice.value) {
    const rect = canvasContainer.value.getBoundingClientRect()
    const x = (e.clientX - rect.left - panX.value - dragOffset.x) / scale.value
    const y = (e.clientY - rect.top - panY.value - dragOffset.y) / scale.value
    draggingDevice.value.topologyX = Math.max(0, Math.min(config.canvas_width - 60, x))
    draggingDevice.value.topologyY = Math.max(0, Math.min(config.canvas_height - 60, y))
  }
}

function handleCanvasMouseUp() {
  if (isPanning.value) {
    isPanning.value = false
  }
  if (draggingDevice.value) {
    saveDevicePosition(draggingDevice.value)
    draggingDevice.value = null
  }
}

function handleDeviceMouseDown(e, device) {
  draggingDevice.value = device
  const rect = e.currentTarget.getBoundingClientRect()
  dragOffset.x = e.clientX - rect.left
  dragOffset.y = e.clientY - rect.top
}

async function saveDevicePosition(device) {
  try {
    const res = await api.put(`/devices/${device.id}/topology`, {
      x: device.topologyX,
      y: device.topologyY
    })
    const idx = devices.value.findIndex(d => d.id === device.id)
    if (idx !== -1) {
      devices.value[idx] = res.data
    }
  } catch (error) {
    ElMessage.error('保存位置失败')
  }
}

async function handleDeviceClick(device) {
  if (draggingDevice.value) return
  selectedDevice.value = device
  deviceLatestData.value = null
  showDeviceDetail.value = true
  try {
    const res = await api.get(`/devices/${device.id}/properties`)
    const data = {}
    res.data.forEach(p => {
      data[p.name] = p.current_value ?? '-'
    })
    deviceLatestData.value = data
  } catch (e) {
  }
}

function goToDeviceDetail() {
  showDeviceDetail.value = false
  router.push('/devices')
}

function handleBgFileChange(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    tempBgImage.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

async function saveBackground() {
  if (!tempBgImage.value && !config.background_image) {
    ElMessage.warning('请先选择图片')
    return
  }
  savingBg.value = true
  try {
    const res = await api.put('/topology/config', {
      background_image: tempBgImage.value || config.background_image
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

async function loadDevices() {
  try {
    const res = await api.get('/devices/', { params: { page_size: 100 } })
    devices.value = res.data
  } catch (error) {
    ElMessage.error('加载设备失败')
  }
}

async function loadConfig() {
  try {
    const res = await api.get('/topology/config')
    config.id = res.data.id
    config.background_image = res.data.background_image
    config.canvas_width = res.data.canvas_width
    config.canvas_height = res.data.canvas_height
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

onMounted(async () => {
  await Promise.all([loadDevices(), loadConfig()])
})
</script>

<style scoped>
.topology-page {
  height: 100%;
}

.topology-container {
  height: calc(100vh - 140px);
  background: white;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e6e6e6;
  background: #fafafa;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scale-text {
  color: #666;
  font-size: 14px;
  min-width: 50px;
}

.canvas-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  background: #f0f2f5;
  cursor: grab;
}

.canvas-container:active {
  cursor: grabbing;
}

.canvas {
  position: absolute;
  left: 0;
  top: 0;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
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
  opacity: 0.9;
}

.background-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}

.device-icon {
  position: absolute;
  width: 60px;
  cursor: move;
  user-select: none;
  transition: box-shadow 0.2s;
  z-index: 10;
}

.device-icon-inner {
  width: 48px;
  height: 48px;
  margin: 0 auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 3px solid #909399;
  color: #909399;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.2s;
}

.device-icon.status-online .device-icon-inner {
  border-color: #67c23a;
  color: #67c23a;
}

.device-icon.status-error .device-icon-inner {
  border-color: #f56c6c;
  color: #f56c6c;
  animation: blink 1s infinite;
}

.device-icon.dragging .device-icon-inner {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  transform: scale(1.1);
}

.device-icon:hover .device-icon-inner {
  transform: scale(1.05);
}

.device-label {
  text-align: center;
  font-size: 12px;
  color: #333;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 4px;
}

@keyframes blink {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.7);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(245, 108, 108, 0);
  }
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
  text-align: center;
}

.device-detail {
  padding: 10px 0;
}

.device-latest-data {
  margin-top: 20px;
}

.device-latest-data h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
}

.data-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 6px;
}

.data-key {
  color: #666;
}

.data-value {
  color: #333;
  font-weight: 500;
}

.device-quick-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
