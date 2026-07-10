<template>
  <div class="actuators-page">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>执行器控制</span>
          <div class="header-actions">
            <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 200px" @change="handleDeviceChange">
              <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
            </el-select>
            <el-button @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新状态
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="actuators.length === 0 && !loading" class="empty-state">
        <el-empty description="当前设备暂无执行器，请先在物模型中配置读写类型的属性">
          <template #image>
            <el-icon :size="80" color="#c0c4cc"><Operation /></el-icon>
          </template>
        </el-empty>
      </div>
      <el-row v-else :gutter="16">
        <el-col :span="8" v-for="actuator in actuators" :key="actuator.identifier">
          <div class="actuator-card" :class="{ 'actuator-active': actuator.value }">
            <div class="actuator-header">
              <span class="actuator-icon"><SvgIcon :name="actuator.icon" :size="24" /></span>
              <span class="actuator-name">{{ actuator.name }}</span>
            </div>
            <div class="actuator-status">
              <span :class="actuator.value ? 'status-active' : 'status-inactive'">
                {{ actuator.value ? '运行中' : '已关闭' }}
              </span>
            </div>
            <div class="actuator-control">
              <el-switch v-model="actuator.value" @change="(val) => handleToggle(actuator, val)" />
            </div>
            <div v-if="actuator.type === 'slider'" class="actuator-slider">
              <el-slider v-model="actuator.level" :min="0" :max="100" @change="(val) => handleLevelChange(actuator, val)" />
              <span class="level-value">{{ actuator.level }}%</span>
            </div>
            <div class="actuator-info">
              <span>最后更新: {{ formatTime(actuator.last_updated) }}</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>定时任务</span>
          <el-button type="primary" @click="showAddTaskDialog = true">
            <el-icon><Plus /></el-icon>
            添加任务
          </el-button>
        </div>
      </template>

      <el-table :data="timedTasks" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="任务名称" width="180" />
        <el-table-column prop="device_name" label="设备" width="150" />
        <el-table-column label="执行器" width="120">
          <template #default="{ row }">
            {{ getActuatorName(row.property_identifier) }}
          </template>
        </el-table-column>
        <el-table-column label="目标值" width="100">
          <template #default="{ row }">
            {{ row.target_value === true ? '开启' : row.target_value === false ? '关闭' : row.target_value }}
          </template>
        </el-table-column>
        <el-table-column prop="cron_expression" label="执行时间" width="180" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次执行" width="180">
          <template #default="{ row }">
            {{ row.last_run_at ? formatTime(row.last_run_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleToggleTask(row)">{{ row.enabled ? '禁用' : '启用' }}</el-button>
            <el-button size="small" @click="handleRunTask(row)">立即执行</el-button>
            <el-button size="small" type="danger" @click="handleDeleteTask(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddTaskDialog" title="添加定时任务" width="600px">
      <el-form :model="taskForm" label-width="120px">
        <el-form-item label="任务名称">
          <el-input v-model="taskForm.name" placeholder="输入任务名称" />
        </el-form-item>
        <el-form-item label="选择设备">
          <el-select v-model="taskForm.device_id" placeholder="选择设备">
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行器">
          <el-select v-model="taskForm.property_identifier" placeholder="选择执行器">
            <el-option v-for="a in availableActuators" :key="a.identifier" :label="a.name" :value="a.identifier" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标值">
          <el-radio-group v-model="taskForm.target_value" v-if="taskForm.property_identifier">
            <el-radio :value="true">开启</el-radio>
            <el-radio :value="false">关闭</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="执行时间">
          <el-select v-model="taskForm.cron_expression" placeholder="选择执行时间">
            <el-option label="每天 08:00" value="0 8 * * *" />
            <el-option label="每天 12:00" value="0 12 * * *" />
            <el-option label="每天 18:00" value="0 18 * * *" />
            <el-option label="每天 22:00" value="0 22 * * *" />
            <el-option label="每小时" value="0 * * * *" />
            <el-option label="每3小时" value="0 */3 * * *" />
            <el-option label="每6小时" value="0 */6 * * *" />
            <el-option label="每周一 08:00" value="0 8 * * 1" />
            <el-option label="每周日 22:00" value="0 22 * * 0" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="taskForm.description" type="textarea" placeholder="输入任务描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddTaskDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddTask" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { useProductStore } from '../stores/product.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Operation } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const productStore = useProductStore()

const loading = ref(false)
const saving = ref(false)
const selectedDevice = ref(null)
const showAddTaskDialog = ref(false)

const actuators = ref([])
const timedTasks = ref([])

const inferredActuatorIdentifiers = [
  'fan_status', 'light_status', 'pump_status', 'heater_status',
  'cooler_status', 'curtain_status', 'valve_status', 'water_valve_status',
  'fan_switch', 'light_switch', 'pump_switch', 'heater_switch',
  'cooler_switch', 'curtain_switch', 'valve_switch', 'water_valve_switch',
]

const actuatorNameMap = {
  fan_status: '通风扇',
  light_status: '补光灯',
  pump_status: '灌溉水泵',
  heater_status: '加热器',
  cooler_status: '制冷器',
  curtain_status: '卷帘',
  valve_status: '阀门',
  water_valve_status: '水阀',
  fan_switch: '通风扇',
  light_switch: '补光灯',
  pump_switch: '灌溉水泵',
  heater_switch: '加热器',
  cooler_switch: '制冷器',
  curtain_switch: '卷帘',
  valve_switch: '阀门',
  water_valve_switch: '水阀',
}

const availableActuators = computed(() => {
  if (!selectedDevice.value) return []
  const device = deviceStore.devices.find(d => d.id === selectedDevice.value)
  if (!device) return []
  const product = productStore.products.find(p => p.id === device.product_id)
  const writeableProps = product ? (product.properties || []).filter(p => p.access_type === 'read_write') : []
  if (writeableProps.length > 0) {
    return writeableProps
  }
  return inferredActuatorIdentifiers.map(identifier => ({
    identifier,
    name: actuatorNameMap[identifier] || identifier,
    access_type: 'read_write',
    data_type: 'bool',
  }))
})

const actuatorIcons = {
  fan: 'fan',
  light: 'bulb',
  pump: 'shower',
  curtain: 'gear',
  heater: 'fire',
  cooler: 'snowflake',
}

function getActuatorIcon(identifier) {
  for (const key in actuatorIcons) {
    if (identifier.includes(key)) {
      return actuatorIcons[key]
    }
  }
  return 'bolt'
}

function getActuatorName(identifier) {
  const props = availableActuators.value
  const prop = props.find(p => p.identifier === identifier)
  return prop ? prop.name : identifier
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

async function refreshData() {
  loading.value = true
  try {
    await loadActuators()
    await loadTimedTasks()
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新数据失败')
  } finally {
    loading.value = false
  }
}

async function loadActuators() {
  if (!selectedDevice.value) return

  try {
    const result = await deviceStore.getLatestTelemetry({ device_id: selectedDevice.value })
    const latestValues = result.latest_values || []

    const device = deviceStore.devices.find(d => d.id === selectedDevice.value)
    const product = productStore.products.find(p => device && p.id === device.product_id)

    const writeableProps = product ? (product.properties || []).filter(p => p.access_type === 'read_write') : []

    let actuatorProps = []
    if (writeableProps.length > 0) {
      actuatorProps = writeableProps
    } else {
      const foundInTelemetry = latestValues.filter(t =>
        inferredActuatorIdentifiers.includes(t.property_identifier)
      )
      if (foundInTelemetry.length > 0) {
        actuatorProps = foundInTelemetry.map(t => ({
          identifier: t.property_identifier,
          name: actuatorNameMap[t.property_identifier] || t.property_identifier,
          data_type: typeof t.value === 'number' ? 'int' : 'bool',
        }))
      } else {
        actuatorProps = inferredActuatorIdentifiers.map(identifier => ({
          identifier,
          name: actuatorNameMap[identifier] || identifier,
          data_type: 'bool',
        }))
      }
    }

    actuators.value = actuatorProps.map(prop => {
      const telemetry = latestValues.find(t => t.property_identifier === prop.identifier)
      const isNumeric = prop.data_type === 'int' || prop.data_type === 'float' || prop.data_type === 'double'
      let value = false
      let level = 0
      if (telemetry) {
        if (isNumeric) {
          value = telemetry.value > 0
          level = Math.min(100, Math.max(0, Math.round(telemetry.value * 100)))
        } else {
          value = telemetry.value === true || telemetry.value === 1 || telemetry.value === '1' || telemetry.value === 'on'
        }
      }
      return {
        identifier: prop.identifier,
        name: prop.name,
        icon: getActuatorIcon(prop.identifier),
        type: isNumeric ? 'slider' : 'switch',
        value,
        level,
        last_updated: telemetry?.timestamp,
      }
    }).filter(a => {
      if (writeableProps.length > 0) return true
      return latestValues.some(t => t.property_identifier === a.identifier)
    })
  } catch (e) {
    console.error('Failed to load actuators:', e)
  }
}

async function loadTimedTasks() {
  try {
    const response = await api.get('/tasks')
    timedTasks.value = response.data || []
  } catch (e) {
    console.error('Failed to load tasks:', e)
  }
}

async function handleToggle(actuator, value) {
  try {
    await deviceStore.createCommand({
      device_id: selectedDevice.value,
      service_identifier: `set_${actuator.identifier}`,
      input_params: { status: value },
    })
    ElMessage.success(`${actuator.name}已${value ? '开启' : '关闭'}`)
    actuator.last_updated = new Date().toISOString()
  } catch (error) {
    ElMessage.error('操作失败')
    actuator.value = !value
  }
}

async function handleLevelChange(actuator, level) {
  try {
    await deviceStore.createCommand({
      device_id: selectedDevice.value,
      service_identifier: `set_${actuator.identifier}`,
      input_params: { level: level / 100 },
    })
    ElMessage.success(`${actuator.name}亮度已设置为${level}%`)
    actuator.last_updated = new Date().toISOString()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function handleDeviceChange() {
  loadActuators()
}

watch(selectedDevice, () => {
  if (selectedDevice.value) {
    loadActuators()
  } else {
    actuators.value = []
  }
})

const taskForm = reactive({
  name: '',
  device_id: null,
  property_identifier: '',
  target_value: true,
  cron_expression: '0 8 * * *',
  description: '',
})

async function handleAddTask() {
  if (!taskForm.name || !taskForm.device_id || !taskForm.property_identifier) {
    ElMessage.warning('请填写完整信息')
    return
  }

  saving.value = true
  try {
    await api.post('/tasks', {
      name: taskForm.name,
      device_id: taskForm.device_id,
      property_identifier: taskForm.property_identifier,
      target_value: taskForm.target_value,
      cron_expression: taskForm.cron_expression,
      description: taskForm.description,
      enabled: true,
    })
    ElMessage.success('定时任务已创建')
    showAddTaskDialog.value = false
    Object.assign(taskForm, {
      name: '',
      device_id: null,
      property_identifier: '',
      target_value: true,
      cron_expression: '0 8 * * *',
      description: '',
    })
    await loadTimedTasks()
  } catch (error) {
    ElMessage.error('创建任务失败')
  } finally {
    saving.value = false
  }
}

async function handleToggleTask(task) {
  try {
    const response = await api.post(`/tasks/${task.id}/toggle`)
    task.enabled = response.data.enabled
    ElMessage.success(`任务已${task.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function handleRunTask(task) {
  try {
    await api.post(`/tasks/${task.id}/run`)
    ElMessage.success('任务已执行')
    task.last_run_at = new Date().toISOString()
  } catch (error) {
    ElMessage.error('执行失败')
  }
}

async function handleDeleteTask(task) {
  try {
    await ElMessageBox.confirm('确定要删除此定时任务吗？', '警告', { type: 'warning' })
    await api.delete(`/tasks/${task.id}`)
    timedTasks.value = timedTasks.value.filter(t => t.id !== task.id)
    ElMessage.success('任务已删除')
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  await deviceStore.fetchDevices()
  await productStore.fetchProducts()

  if (deviceStore.devices.length > 0) {
    selectedDevice.value = deviceStore.devices[0].id
  }

  await refreshData()
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
  gap: 10px;
}

.actuator-card {
  padding: 20px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #ebeef5;
  transition: all 0.3s;
  text-align: center;
}

.actuator-card.actuator-active {
  border-left: 4px solid #409eff;
  background: #f0f5ff;
}

.actuator-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 15px;
}

.actuator-icon {
  font-size: 28px;
}

.actuator-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.actuator-status {
  margin-bottom: 15px;
}

.status-active {
  color: #67c23a;
  font-weight: bold;
}

.status-inactive {
  color: #909399;
}

.actuator-control {
  margin-bottom: 15px;
}

.actuator-slider {
  padding: 0 10px;
  margin-bottom: 15px;
}

.level-value {
  display: block;
  text-align: right;
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.actuator-info {
  font-size: 12px;
  color: #909399;
}

.empty-state {
  padding: 60px 0;
}
</style>