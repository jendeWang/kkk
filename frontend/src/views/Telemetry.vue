<template>
  <div class="telemetry-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>遥测数据</span>
          <el-button type="primary" :icon="Download" @click="exportCSV" :disabled="!queryForm.device_id">
            导出CSV
          </el-button>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="选择设备">
          <el-select v-model="queryForm.device_id" @change="onDeviceChange" placeholder="选择设备" style="width: 200px">
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="属性">
          <el-select v-model="queryForm.property_identifier" @change="loadTelemetry" placeholder="全部属性" style="width: 150px" clearable>
            <el-option v-for="p in properties" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="x"
            style="width: 360px"
            @change="loadTelemetry"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="telemetryData" style="width: 100%" v-loading="loading">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="property_identifier" label="属性" width="160" />
        <el-table-column prop="value" label="值" />
        <el-table-column prop="quality" label="质量" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getQualityType(row.quality)">{{ row.quality }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadTelemetry"
          @current-change="loadTelemetry"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, onUnmounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import api from '../services/api.js'

const deviceStore = useDeviceStore()

const loading = ref(false)
const telemetryData = ref([])
const properties = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const dateRange = ref(null)

const queryForm = reactive({
  device_id: null,
  property_identifier: ''
})

function getQualityType(quality) {
  const types = { good: 'success', bad: 'danger', uncertain: 'warning' }
  return types[quality] || 'info'
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function loadDevices() {
  try {
    await deviceStore.fetchDevices()
  } catch (error) {
    ElMessage.error('Failed to load devices')
  }
}

function getQueryParams() {
  const params = {
    device_id: queryForm.device_id || undefined,
    property_identifier: queryForm.property_identifier || undefined,
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value,
  }
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_time = new Date(dateRange.value[0]).toISOString()
    params.end_time = new Date(dateRange.value[1]).toISOString()
  }
  return params
}

async function loadTelemetry() {
  if (!queryForm.device_id) return
  loading.value = true
  try {
    const params = getQueryParams()
    const response = await api.get('/telemetry/', { params })
    const data = response.data
    telemetryData.value = data.items || []
    total.value = data.total || 0
    if (!queryForm.property_identifier) {
      properties.value = [...new Set(telemetryData.value.map(t => t.property_identifier))]
    }
  } catch (error) {
    ElMessage.error('Failed to load telemetry data')
  } finally {
    loading.value = false
  }
}

function onDeviceChange() {
  currentPage.value = 1
  properties.value = []
  loadTelemetry()
}

function resetQuery() {
  queryForm.device_id = null
  queryForm.property_identifier = ''
  dateRange.value = null
  telemetryData.value = []
  properties.value = []
  total.value = 0
  currentPage.value = 1
}

async function exportCSV() {
  if (!queryForm.device_id) {
    ElMessage.warning('请先选择设备')
    return
  }
  try {
    const params = getQueryParams()
    const response = await api.get('/telemetry/export/csv', {
      params,
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `telemetry_${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

let eventSource = null
let sseEnabled = true
let pollingTimer = null

function isProxyEnvironment() {
  const hostname = window.location.hostname
  return hostname.includes('agent-sandbox') || hostname.includes('preview.agent')
}

function startPolling() {
  if (pollingTimer) return
  pollingTimer = setInterval(() => {
    if (queryForm.device_id) {
      loadTelemetry()
    }
  }, 10000)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

function connectSSE() {
  if (isProxyEnvironment()) {
    startPolling()
    return
  }
  
  if (!sseEnabled) return
  
  const token = localStorage.getItem('token')
  if (!token) return
  
  eventSource = new EventSource(`/api/v1/sse/devices?token=${token}`)
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'device_status' && queryForm.device_id) {
        loadTelemetry()
      }
    } catch (e) {}
  }
  eventSource.onerror = () => {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (sseEnabled) {
      sseEnabled = false
      startPolling()
    }
  }
}

onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  stopPolling()
})

onMounted(() => {
  loadDevices()
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.query-form {
  margin-bottom: 20px;
}

.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
