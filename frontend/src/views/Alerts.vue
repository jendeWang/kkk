<template>
  <div class="alerts-page">
    <el-card>
      <template #header>
        <span>{{ $t('alerts.title') }}</span>
      </template>

      <el-table :data="deviceStore.alertEvents" style="width: 100%" v-loading="loading">
        <el-table-column prop="message" :label="$t('alerts.message')" />
        <el-table-column :label="$t('alerts.device')" width="100">
          <template #default="{ row }">
            {{ getDeviceName(row.device_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('alerts.severity')" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('alerts.status')" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_value" :label="$t('alerts.currentValue')" width="120" />
        <el-table-column prop="threshold_value" :label="$t('alerts.thresholdValue')" width="120" />
        <el-table-column :label="$t('alerts.createdAt')" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="180">
          <template #default="{ row }">
            <el-button v-if="row.status === 'triggered'" size="small" @click="acknowledge(row)">{{ $t('alerts.acknowledge') }}</el-button>
            <el-button v-if="row.status !== 'resolved'" size="small" type="success" @click="resolve(row)">{{ $t('alerts.resolve') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { ElMessage } from 'element-plus'

const deviceStore = useDeviceStore()
const loading = ref(false)

function getSeverityType(severity) {
  const types = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return types[severity] || 'info'
}

function getStatusType(status) {
  const types = { triggered: 'danger', acknowledged: 'warning', resolved: 'success' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { triggered: 'Triggered', acknowledged: 'Acknowledged', resolved: 'Resolved' }
  return texts[status] || status
}

function getDeviceName(deviceId) {
  const device = deviceStore.devices.find(d => d.id === deviceId)
  return device ? device.device_name : `Device ${deviceId}`
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

async function loadAlerts() {
  loading.value = true
  try {
    await Promise.all([
      deviceStore.fetchAlertEvents(),
      deviceStore.fetchDevices()
    ])
  } catch (error) {
    ElMessage.error('Failed to load alerts')
  } finally {
    loading.value = false
  }
}

async function acknowledge(alert) {
  try {
    await deviceStore.updateAlertEventStatus(alert.id, 'acknowledged')
    ElMessage.success('Alert acknowledged')
    await loadAlerts()
  } catch (error) {
    ElMessage.error('Failed to acknowledge alert')
  }
}

async function resolve(alert) {
  try {
    await deviceStore.updateAlertEventStatus(alert.id, 'resolved')
    ElMessage.success('Alert resolved')
    await loadAlerts()
  } catch (error) {
    ElMessage.error('Failed to resolve alert')
  }
}

let eventSource = null
let sseEnabled = true

function isProxyEnvironment() {
  // 检测是否在代理环境下（内置预览使用代理域名）
  const hostname = window.location.hostname
  return hostname.includes('agent-sandbox') || hostname.includes('preview.agent')
}

function connectSSE() {
  // SSE在代理环境下不可用（代理不支持长连接），完全禁用
  if (isProxyEnvironment() || !sseEnabled) return
  
  const token = localStorage.getItem('token')
  if (!token) return
  
  eventSource = new EventSource(`/api/v1/sse/alerts?token=${token}`)
  eventSource.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'new_alert') {
        ElMessage.warning({
          message: data.data.message,
          duration: 5000
        })
        await loadAlerts()
      }
    } catch (e) {}
  }
  eventSource.onerror = () => {
    sseEnabled = false
    eventSource.close()
  }
}

onMounted(() => {
  loadAlerts()
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>
