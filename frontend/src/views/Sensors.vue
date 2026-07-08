<template>
  <div class="sensors-page">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>传感器监控</span>
          <div class="header-actions">
            <el-select v-model="selectedDevice" placeholder="选择设备" clearable style="width: 200px" @change="handleDeviceChange">
              <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
            </el-select>
            <el-select v-model="selectedProperty" placeholder="选择属性" clearable style="width: 150px; margin-left: 10px" @change="handlePropertyChange">
              <el-option v-for="p in availableProperties" :key="p.identifier" :label="p.name" :value="p.identifier" />
            </el-select>
            <el-select v-model="timeRange" placeholder="时间范围" style="width: 150px; margin-left: 10px">
              <el-option label="1小时" value="1h" />
              <el-option label="6小时" value="6h" />
              <el-option label="24小时" value="24h" />
              <el-option label="7天" value="7d" />
            </el-select>
            <el-button @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="16">
        <el-col :span="6" v-for="item in latestData" :key="item.property_identifier">
          <div class="sensor-card" :class="getStatusClass(item)">
            <div class="sensor-header">
              <span class="sensor-name">{{ getPropertyName(item.property_identifier) }}</span>
              <span class="sensor-unit">{{ getPropertyUnit(item.property_identifier) }}</span>
            </div>
            <div class="sensor-value">{{ formatValue(item.value) }}</div>
            <div class="sensor-time">更新于 {{ formatTime(item.timestamp) }}</div>
            <div class="sensor-trend" v-if="getTrend(item.property_identifier)">
              <el-icon :class="getTrendClass(item.property_identifier)">
                <ArrowUp v-if="getTrend(item.property_identifier) > 0" />
                <ArrowDown v-else />
              </el-icon>
              <span>{{ Math.abs(getTrend(item.property_identifier)).toFixed(2) }}%</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-if="selectedProperty">
      <template #header>
        <div class="card-header">
          <span>{{ getPropertyName(selectedProperty) }} 趋势图表</span>
          <div class="chart-actions">
            <el-select v-model="chartType" placeholder="图表类型" style="width: 120px">
              <el-option label="折线图" value="line" />
              <el-option label="柱状图" value="bar" />
            </el-select>
          </div>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>

    <el-row :gutter="16" v-if="aggregationData.length > 0">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-title">数据统计</div>
          <div class="stats-content">
            <div v-for="item in aggregationData" :key="item.property_identifier" class="stat-item">
              <div class="stat-label">{{ getPropertyName(item.property_identifier) }}</div>
              <div class="stat-values">
                <span class="stat-min">最小: {{ formatValue(item.min_value) }}</span>
                <span class="stat-max">最大: {{ formatValue(item.max_value) }}</span>
                <span class="stat-avg">平均: {{ formatValue(item.avg_value) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="18">
        <el-card>
          <template #header>
            <span>实时数据列表</span>
          </template>
          <el-table :data="telemetryList" style="width: 100%" v-loading="loading">
            <el-table-column prop="device_name" label="设备" width="150" />
            <el-table-column prop="property_identifier" label="属性" width="150">
              <template #default="{ row }">
                {{ getPropertyName(row.property_identifier) }}
              </template>
            </el-table-column>
            <el-table-column prop="value" label="数值" width="120" />
            <el-table-column prop="data_type" label="类型" width="80" />
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="quality" label="质量" width="80">
              <template #default="{ row }">
                <el-tag :type="row.quality === 'good' ? 'success' : 'warning'" size="small">
                  {{ row.quality === 'good' ? '良好' : '异常' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { useProductStore } from '../stores/product.js'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Refresh, ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const productStore = useProductStore()

const loading = ref(false)
const selectedDevice = ref(null)
const selectedProperty = ref('temperature')
const timeRange = ref('24h')
const chartType = ref('line')
const chartRef = ref(null)
let chartInstance = null

const latestData = ref([])
const telemetryList = ref([])
const aggregationData = ref([])
const trendData = ref({})
const previousValues = ref({})

const availableProperties = computed(() => {
  if (!selectedDevice.value) {
    const product = productStore.products[0]
    return product ? product.properties || [] : []
  }
  const device = deviceStore.devices.find(d => d.id === selectedDevice.value)
  if (!device) return []
  const product = productStore.products.find(p => p.id === device.product_id)
  return product ? product.properties || [] : []
})

function getPropertyName(identifier) {
  const props = availableProperties.value
  const prop = props.find(p => p.identifier === identifier)
  return prop ? prop.name : identifier
}

function getPropertyUnit(identifier) {
  const props = availableProperties.value
  const prop = props.find(p => p.identifier === identifier)
  return prop ? prop.unit || '' : ''
}

function formatValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    return value.toFixed(2)
  }
  return String(value)
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

function getStatusClass(item) {
  const props = availableProperties.value
  const prop = props.find(p => p.identifier === item.property_identifier)
  if (!prop || !prop.min_value || !prop.max_value) return ''
  
  const min = parseFloat(prop.min_value)
  const max = parseFloat(prop.max_value)
  const val = parseFloat(item.value)
  
  if (val < min || val > max) return 'status-error'
  const range = max - min
  if (val < min + range * 0.2 || val > max - range * 0.2) return 'status-warning'
  return 'status-normal'
}

function getTrend(identifier) {
  return trendData.value[identifier] || 0
}

function getTrendClass(identifier) {
  return getTrend(identifier) > 0 ? 'trend-up' : 'trend-down'
}

async function refreshData() {
  loading.value = true
  try {
    await Promise.all([
      loadLatestData(),
      loadAggregationData(),
      loadTelemetryList(),
      loadTrendData()
    ])
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

async function loadLatestData() {
  const params = {}
  if (selectedDevice.value) {
    params.device_id = selectedDevice.value
  }
  const result = await deviceStore.getLatestTelemetry(params)
  latestData.value = result.latest_values || []
  
  latestData.value.forEach(item => {
    const prev = previousValues.value[item.property_identifier]
    if (prev !== undefined && prev !== null && item.value !== null) {
      const diff = ((item.value - prev) / prev * 100)
      trendData.value[item.property_identifier] = diff
    }
    previousValues.value[item.property_identifier] = item.value
  })
}

async function loadAggregationData() {
  const params = {}
  if (selectedDevice.value) {
    params.device_id = selectedDevice.value
  }
  if (selectedProperty.value) {
    params.property_identifier = selectedProperty.value
  }
  
  const hours = { '1h': 1, '6h': 6, '24h': 24, '7d': 168 }[timeRange.value] || 24
  params.end_time = new Date().toISOString()
  params.start_time = new Date(Date.now() - hours * 3600 * 1000).toISOString()
  
  const result = await deviceStore.getTelemetryAggregation(params)
  aggregationData.value = result.aggregations || []
}

async function loadTelemetryList() {
  const params = { limit: 20 }
  if (selectedDevice.value) {
    params.device_id = selectedDevice.value
  }
  const result = await deviceStore.fetchTelemetry(params)
  telemetryList.value = result.items || []
}

async function loadTrendData() {
  const params = { property_identifier: selectedProperty.value }
  if (selectedDevice.value) {
    params.device_id = selectedDevice.value
  }
  
  const hours = { '1h': 1, '6h': 6, '24h': 24, '7d': 168 }[timeRange.value] || 24
  params.end_time = new Date().toISOString()
  params.start_time = new Date(Date.now() - hours * 3600 * 1000).toISOString()
  
  const interval = hours <= 6 ? '15m' : hours <= 24 ? '1h' : '6h'
  params.interval = interval
  
  const result = await deviceStore.getTelemetryTrend(params)
  updateChart(result.trends || {})
}

function updateChart(trends) {
  if (!chartInstance) return
  
  const data = trends[selectedProperty.value] || []
  const xAxis = data.map(item => {
    const dt = new Date(item.timestamp)
    return `${dt.getHours().toString().padStart(2, '0')}:${dt.getMinutes().toString().padStart(2, '0')}`
  })
  const yAxis = data.map(item => item.avg_value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>{c} ' + getPropertyUnit(selectedProperty.value)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxis
    },
    yAxis: {
      type: 'value',
      name: getPropertyUnit(selectedProperty.value)
    },
    series: [{
      name: getPropertyName(selectedProperty.value),
      type: chartType.value,
      data: yAxis,
      smooth: true,
      areaStyle: chartType.value === 'line' ? { opacity: 0.3 } : {},
      itemStyle: {
        color: '#409eff'
      }
    }]
  }
  
  chartInstance.setOption(option, true)
}

function initChart() {
  if (chartRef.value && !chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
}

function handleDeviceChange() {
  selectedProperty.value = availableProperties.value[0]?.identifier || 'temperature'
  refreshData()
}

function handlePropertyChange() {
  loadTrendData()
}

watch(timeRange, () => {
  refreshData()
})

watch(chartType, () => {
  loadTrendData()
})

onMounted(async () => {
  await deviceStore.fetchDevices()
  await productStore.fetchProducts()
  
  if (deviceStore.devices.length > 0) {
    selectedDevice.value = deviceStore.devices[0].id
  }
  
  await refreshData()
  await nextTick()
  initChart()
  
  window.addEventListener('resize', () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.chart-actions {
  display: flex;
  align-items: center;
}

.chart-container {
  height: 400px;
}

.sensor-card {
  padding: 20px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #ebeef5;
  transition: all 0.3s;
}

.sensor-card.status-normal {
  border-left: 4px solid #67c23a;
}

.sensor-card.status-warning {
  border-left: 4px solid #e6a23c;
}

.sensor-card.status-error {
  border-left: 4px solid #f56c6c;
}

.sensor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.sensor-name {
  font-size: 14px;
  color: #606266;
}

.sensor-unit {
  font-size: 12px;
  color: #909399;
}

.sensor-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.sensor-time {
  font-size: 12px;
  color: #909399;
}

.sensor-trend {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 10px;
  font-size: 12px;
}

.trend-up {
  color: #f56c6c;
}

.trend-down {
  color: #67c23a;
}

.stats-card {
  padding: 15px;
}

.stats-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.stat-item {
  margin-bottom: 15px;
}

.stat-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 5px;
}

.stat-values {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-min, .stat-max, .stat-avg {
  font-size: 12px;
  color: #909399;
}

.stat-min {
  color: #409eff;
}

.stat-max {
  color: #f56c6c;
}

.stat-avg {
  color: #67c23a;
}
</style>