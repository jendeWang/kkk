<template>
  <div class="telemetry-page">
    <el-card>
      <template #header>
        <span>{{ $t('telemetry.title') }}</span>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item :label="$t('telemetry.selectDevice')">
          <el-select v-model="queryForm.device_id" @change="loadTelemetry" :placeholder="$t('telemetry.selectDevice')" style="width: 200px">
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('telemetry.selectProperty')">
          <el-select v-model="queryForm.property_identifier" @change="loadTelemetry" :placeholder="$t('telemetry.allProperties')" style="width: 150px" clearable>
            <el-option v-for="p in properties" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetQuery">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="telemetryData" style="width: 100%" v-loading="loading">
        <el-table-column prop="property_identifier" :label="$t('telemetry.selectProperty')" />
        <el-table-column prop="value" :label="$t('telemetry.value')" />
        <el-table-column prop="quality" :label="$t('telemetry.quality')">
          <template #default="{ row }">
            <el-tag :type="getQualityType(row.quality)">{{ row.quality }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" :label="$t('telemetry.timestamp')">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { ElMessage } from 'element-plus'

const deviceStore = useDeviceStore()

const loading = ref(false)
const telemetryData = ref([])
const properties = ref([])

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
  return new Date(time).toLocaleString()
}

async function loadDevices() {
  try {
    await deviceStore.fetchDevices()
  } catch (error) {
    ElMessage.error('Failed to load devices')
  }
}

async function loadTelemetry() {
  if (!queryForm.device_id) return
  loading.value = true
  try {
    const response = await deviceStore.fetchTelemetry({
      device_id: queryForm.device_id,
      property_identifier: queryForm.property_identifier || undefined,
      limit: 100
    })
    const data = response.items || response
    telemetryData.value = Array.isArray(data) ? data : []
    properties.value = [...new Set(telemetryData.value.map(t => t.property_identifier))]
  } catch (error) {
    ElMessage.error('Failed to load telemetry data')
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  queryForm.device_id = null
  queryForm.property_identifier = ''
  telemetryData.value = []
  properties.value = []
}

let eventSource = null

function connectSSE() {
  const token = localStorage.getItem('token')
  eventSource = new EventSource(`/api/v1/sse/devices?token=${token}`)
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'device_status' && queryForm.device_id) {
        loadTelemetry()
        loadDevices()
      }
    } catch (e) {}
  }
  eventSource.onerror = () => {
    eventSource.close()
    setTimeout(connectSSE, 5000)
  }
}

onMounted(() => {
  loadDevices()
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>

<style scoped>
.query-form {
  margin-bottom: 20px;
}
</style>
