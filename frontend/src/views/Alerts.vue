<template>
  <div class="alerts-page">
    <el-row :gutter="16" class="mb-4">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-icon">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.total }}</div>
            <div class="stats-label">总告警</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card critical">
          <div class="stats-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.severity.critical || 0 }}</div>
            <div class="stats-label">严重</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card warning">
          <div class="stats-icon">
            <el-icon><WarnTriangleFilled /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.severity.warning || 0 }}</div>
            <div class="stats-label">警告</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card pending">
          <div class="stats-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.status.triggered || 0 }}</div>
            <div class="stats-label">待处理</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>告警事件</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索设备名称或告警信息"
              class="search-input"
              :prefix-icon="Search"
            />
            <el-select v-model="filterStatus" placeholder="状态筛选" style="width: 120px; margin-left: 10px">
              <el-option label="全部" value="" />
              <el-option label="待处理" value="triggered" />
              <el-option label="已确认" value="acknowledged" />
              <el-option label="已解决" value="resolved" />
            </el-select>
            <el-select v-model="filterSeverity" placeholder="级别筛选" style="width: 120px; margin-left: 10px">
              <el-option label="全部" value="" />
              <el-option label="严重" value="critical" />
              <el-option label="错误" value="error" />
              <el-option label="警告" value="warning" />
              <el-option label="信息" value="info" />
            </el-select>
            <el-button @click="loadAlerts" size="small" type="primary">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredAlerts" style="width: 100%" v-loading="loading">
        <el-table-column prop="message" label="告警信息" min-width="200" />
        <el-table-column label="设备" width="150">
          <template #default="{ row }">
            <span>{{ getDeviceName(row.device_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="监测指标" width="120">
          <template #default="{ row }">
            <span>{{ getPropertyName(row.property_identifier) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="告警级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityText(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前值" width="100">
          <template #default="{ row }">
            <span>{{ row.current_value }} {{ getPropertyUnit(row.property_identifier) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="阈值" width="100">
          <template #default="{ row }">
            <span>{{ row.threshold_value }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button v-if="row.status === 'triggered'" size="small" @click="handleAcknowledge(row)">
              <el-icon><CircleCheck /></el-icon>
              确认
            </el-button>
            <el-button v-if="row.status !== 'resolved'" size="small" type="success" @click="handleResolve(row)">
              <el-icon><CircleCheck /></el-icon>
              解决
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { useProductStore } from '../stores/product.js'
import { ElMessage } from 'element-plus'
import { Bell, Warning, WarnTriangleFilled, Clock, Search, Refresh, CircleCheck } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const productStore = useProductStore()
const loading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const filterSeverity = ref('')

const stats = ref({
  total: 0,
  severity: {},
  status: {},
})

const filteredAlerts = computed(() => {
  let result = deviceStore.alertEvents || []
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(a => 
      a.message.toLowerCase().includes(query) ||
      getDeviceName(a.device_id).toLowerCase().includes(query)
    )
  }
  if (filterStatus.value) {
    result = result.filter(a => a.status === filterStatus.value)
  }
  if (filterSeverity.value) {
    result = result.filter(a => a.severity === filterSeverity.value)
  }
  return result
})

function getSeverityType(severity) {
  const types = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return types[severity] || 'info'
}

function getSeverityText(severity) {
  const texts = { info: '信息', warning: '警告', error: '错误', critical: '严重' }
  return texts[severity] || severity
}

function getStatusType(status) {
  const types = { triggered: 'danger', acknowledged: 'warning', resolved: 'success' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { triggered: '待处理', acknowledged: '已确认', resolved: '已解决' }
  return texts[status] || status
}

function getDeviceName(deviceId) {
  const device = deviceStore.devices.find(d => d.id === deviceId)
  return device ? device.device_name : `设备#${deviceId}`
}

function getPropertyName(identifier) {
  const props = productStore.products[0]?.properties || []
  const prop = props.find(p => p.identifier === identifier)
  return prop ? prop.name : identifier
}

function getPropertyUnit(identifier) {
  const props = productStore.products[0]?.properties || []
  const prop = props.find(p => p.identifier === identifier)
  return prop ? prop.unit : ''
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function loadAlerts() {
  loading.value = true
  try {
    await Promise.all([
      deviceStore.fetchAlertEvents(),
      deviceStore.fetchDevices(),
      productStore.fetchProducts(),
    ])
    await loadStats()
  } catch (error) {
    ElMessage.error('加载告警失败')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const response = await fetch('/api/v1/alerts/stats?days=7', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    stats.value = await response.json()
  } catch (e) {}
}

async function handleAcknowledge(alert) {
  try {
    await deviceStore.updateAlertEventStatus(alert.id, 'acknowledged')
    ElMessage.success('告警已确认')
    await loadAlerts()
  } catch (error) {
    ElMessage.error('确认告警失败')
  }
}

async function handleResolve(alert) {
  try {
    await deviceStore.updateAlertEventStatus(alert.id, 'resolved')
    ElMessage.success('告警已解决')
    await loadAlerts()
  } catch (error) {
    ElMessage.error('解决告警失败')
  }
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alerts-page {
  padding: 0;
}

.stats-card {
  display: flex;
  align-items: center;
  gap: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stats-card .stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #409eff;
  background: #ecf5ff;
}

.stats-card.critical .stats-icon {
  color: #f56c6c;
  background: #fef0f0;
}

.stats-card.warning .stats-icon {
  color: #e6a23c;
  background: #fdf6ec;
}

.stats-card.pending .stats-icon {
  color: #909399;
  background: #f4f4f5;
}

.stats-card .stats-info {
  flex: 1;
}

.stats-card .stats-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stats-card .stats-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-actions {
  display: flex;
  align-items: center;
}

.search-input {
  width: 200px;
}
</style>