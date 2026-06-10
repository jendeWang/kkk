<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409eff"><Goods /></el-icon>
            <div>
              <p class="stat-label">{{ $t('dashboard.totalProducts') }}</p>
              <p class="stat-value">{{ stats.totalProducts }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67c23a"><Monitor /></el-icon>
            <div>
              <p class="stat-label">{{ $t('dashboard.totalDevices') }}</p>
              <p class="stat-value">{{ stats.totalDevices }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#e6a23c"><Connection /></el-icon>
            <div>
              <p class="stat-label">{{ $t('dashboard.onlineDevices') }}</p>
              <p class="stat-value">{{ stats.onlineDevices }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#f56c6c"><Warning /></el-icon>
            <div>
              <p class="stat-label">{{ $t('dashboard.totalAlerts') }}</p>
              <p class="stat-value">{{ stats.totalAlerts }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card>
          <h4>{{ $t('dashboard.deviceStatus') }}</h4>
          <div ref="pieChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <h4>{{ $t('dashboard.recentAlerts') }}</h4>
          <el-table :data="recentAlerts" style="width: 100%">
            <el-table-column prop="message" label="Message" />
            <el-table-column prop="severity" label="Severity" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="Time" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useProductStore } from '../stores/product.js'
import { useDeviceStore } from '../stores/device.js'
import * as echarts from 'echarts'

const productStore = useProductStore()
const deviceStore = useDeviceStore()

const pieChart = ref(null)
let pieChartInstance = null

const stats = reactive({
  totalProducts: 0,
  totalDevices: 0,
  onlineDevices: 0,
  totalAlerts: 0
})

const recentAlerts = ref([])

function getSeverityType(severity) {
  const types = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return types[severity] || 'info'
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

async function loadData() {
  try {
    const [products, devices, alerts] = await Promise.all([
      productStore.fetchProducts(),
      deviceStore.fetchDevices(),
      deviceStore.fetchAlertEvents({ status: 'triggered' })
    ])

    stats.totalProducts = products.length
    stats.totalDevices = devices.length
    stats.onlineDevices = devices.filter(d => d.status === 'online').length
    stats.totalAlerts = alerts.length
    recentAlerts.value = alerts.slice(0, 5)

    updatePieChart(devices)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

function updatePieChart(devices) {
  if (!pieChart.value) return

  const online = devices.filter(d => d.status === 'online').length
  const offline = devices.filter(d => d.status === 'offline').length
  const error = devices.filter(d => d.status === 'error').length

  if (pieChartInstance) {
    pieChartInstance.dispose()
  }

  pieChartInstance = echarts.init(pieChart.value)
  pieChartInstance.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 16 } },
      data: [
        { value: online, name: 'Online', itemStyle: { color: '#67c23a' } },
        { value: offline, name: 'Offline', itemStyle: { color: '#909399' } },
        { value: error, name: 'Error', itemStyle: { color: '#f56c6c' } }
      ]
    }]
  })
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => pieChartInstance?.resize())
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 48px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.charts-row {
  margin-top: 20px;
}

h4 {
  margin-bottom: 16px;
  color: #303133;
}
</style>
