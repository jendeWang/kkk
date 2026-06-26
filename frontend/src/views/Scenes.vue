<template>
  <div class="scenes-page">
    <div class="page-header">
      <h2 class="page-title">场景联动</h2>
      <el-button type="primary" @click="showTemplatesDialog = true">
        <el-icon><MagicStick /></el-icon>
        使用模板
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <el-card class="stat-card">
        <div class="stat-inner">
          <div class="stat-icon-wrap stat-blue">
            <el-icon :size="28"><Collection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">场景总数</div>
            <div class="stat-value">{{ scenes.length }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-inner">
          <div class="stat-icon-wrap stat-green">
            <el-icon :size="28"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">已启用</div>
            <div class="stat-value">{{ enabledCount }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-inner">
          <div class="stat-icon-wrap stat-orange">
            <el-icon :size="28"><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">今日执行</div>
            <div class="stat-value">{{ todayExecutions }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 主内容区 -->
    <el-row :gutter="20">
      <!-- 场景列表 -->
      <el-col :span="14">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">📋 我的场景</span>
              <el-button type="primary" size="small" @click="openCreateDialog">
                <el-icon><Plus /></el-icon>
                新建场景
              </el-button>
            </div>
          </template>

          <div v-if="scenes.length === 0" class="empty-state">
            <el-icon :size="64" color="#dcdfe6"><Files /></el-icon>
            <p>还没有创建任何场景</p>
            <p class="tip">点击右上角"新建场景"或"使用模板"开始</p>
          </div>

          <div v-else class="scene-list">
            <div
              v-for="scene in scenes"
              :key="scene.id"
              class="scene-card"
              :class="{ active: selectedScene?.id === scene.id, disabled: !scene.enabled }"
              @click="selectScene(scene)"
            >
              <div class="scene-header">
                <span class="scene-icon">{{ getSceneIcon(scene.trigger_type) }}</span>
                <span class="scene-name">{{ scene.name }}</span>
                <el-tag size="small" :type="scene.enabled ? 'success' : 'info'">
                  {{ scene.enabled ? '已启用' : '已禁用' }}
                </el-tag>
              </div>
              <div class="scene-desc">{{ scene.description || '暂无描述' }}</div>
              <div class="scene-meta">
                <span class="meta-item">
                  <el-icon><Clock /></el-icon>
                  {{ formatTime(scene.last_triggered_at) }}
                </span>
                <div class="scene-actions">
                  <el-button
                    size="small"
                    :icon="scene.enabled ? 'Close' : 'Check'"
                    @click.stop="toggleScene(scene)"
                    :type="scene.enabled ? 'danger' : 'success'"
                    circle
                  />
                  <el-button
                    size="small"
                    icon="VideoPlay"
                    @click.stop="triggerScene(scene)"
                    circle
                  />
                  <el-button
                    size="small"
                    icon="Delete"
                    @click.stop="deleteScene(scene)"
                    type="danger"
                    circle
                  />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 场景详情/配置 -->
      <el-col :span="10">
        <!-- 未选择场景 -->
        <el-card v-if="!selectedScene" class="section-card">
          <div class="empty-state">
            <el-icon :size="64" color="#dcdfe6"><Pointer /></el-icon>
            <p>点击左侧场景查看详情</p>
            <p class="tip">或使用模板快速创建</p>
          </div>
        </el-card>

        <!-- 场景详情 -->
        <el-card v-else class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ selectedScene.name }}</span>
              <el-button size="small" @click="openEditDialog">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
            </div>
          </template>

          <div class="scene-detail">
            <div class="detail-section">
              <h4 class="section-title">📌 触发条件</h4>
              <div class="condition-box">
                <template v-if="selectedScene.trigger_type === 'threshold'">
                  <div class="condition-text">
                    当 <strong>{{ getPropertyLabel(selectedScene.trigger_config?.property_identifier) }}</strong>
                    <strong>{{ getOperatorLabel(selectedScene.trigger_config?.operator) }}</strong>
                    <strong>{{ selectedScene.trigger_config?.threshold_value }}</strong>
                    {{ getPropertyUnit(selectedScene.trigger_config?.property_identifier) }}
                    时触发
                  </div>
                </template>
                <template v-else-if="selectedScene.trigger_type === 'schedule'">
                  <div class="condition-text">
                    定时执行：{{ selectedScene.trigger_config?.cron || '未配置' }}
                  </div>
                </template>
                <template v-else>
                  <div class="condition-text">
                    {{ selectedScene.trigger_type }}
                  </div>
                </template>
              </div>
            </div>

            <div class="detail-section">
              <h4 class="section-title">⚡ 执行动作</h4>
              <div class="action-box">
                <template v-if="selectedScene.action_type === 'command'">
                  <div class="action-text">
                    控制 <strong>{{ getServiceLabel(selectedScene.action_config?.service_identifier) }}</strong>
                    <span v-if="selectedScene.action_config?.input_params?.status !== undefined">
                      {{ selectedScene.action_config.input_params.status ? '开启' : '关闭' }}
                    </span>
                  </div>
                </template>
                <template v-else-if="selectedScene.action_type === 'alert'">
                  <div class="action-text">发送告警通知</div>
                </template>
                <template v-else>
                  <div class="action-text">{{ selectedScene.action_type }}</div>
                </template>
              </div>
            </div>

            <div class="detail-section">
              <h4 class="section-title">⚙️ 设置</h4>
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="触发间隔">
                  至少{{ selectedScene.cooldown_seconds || 60 }}秒执行一次
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="selectedScene.enabled ? 'success' : 'info'" size="small">
                    {{ selectedScene.enabled ? '已启用' : '已禁用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="最后执行">
                  {{ formatTime(selectedScene.last_triggered_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="detail-actions">
              <el-button type="primary" @click="triggerScene(selectedScene)">
                <el-icon><VideoPlay /></el-icon>
                立即执行
              </el-button>
              <el-button @click="toggleScene(selectedScene)">
                {{ selectedScene.enabled ? '暂停场景' : '启用场景' }}
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 执行日志 -->
        <el-card class="section-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">📜 执行日志</span>
              <el-button size="small" @click="loadExecutionLogs" :icon="Refresh">
                刷新
              </el-button>
            </div>
          </template>

          <div v-if="executionLogs.length === 0" class="empty-state small">
            <p>暂无执行记录</p>
          </div>

          <div v-else class="log-list">
            <div v-for="log in executionLogs" :key="log.id" class="log-item">
              <div class="log-header">
                <el-tag size="small" :type="getStatusType(log.status)">
                  {{ getStatusLabel(log.status) }}
                </el-tag>
                <span class="log-time">{{ formatTime(log.created_at) }}</span>
              </div>
              <div v-if="log.error_message" class="log-error">
                {{ log.error_message }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建/编辑场景对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="isEditing ? '编辑场景' : '新建场景'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="场景名称" prop="name">
          <el-input v-model="form.name" placeholder="给场景起个名字，如：高温自动通风" />
        </el-form-item>

        <el-form-item label="场景描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="简单描述这个场景的作用"
          />
        </el-form-item>

        <el-divider content-position="left">触发条件</el-divider>

        <el-form-item label="触发方式" prop="trigger_type">
          <el-radio-group v-model="form.trigger_type" @change="handleTriggerTypeChange">
            <el-radio label="threshold">阈值触发</el-radio>
            <el-radio label="schedule">定时触发</el-radio>
            <el-radio label="manual">手动触发</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 阈值触发配置 -->
        <template v-if="form.trigger_type === 'threshold'">
          <el-form-item label="监测指标" prop="trigger_config.property_identifier">
            <el-select v-model="form.trigger_config.property_identifier" placeholder="选择要监测的指标">
              <el-option label="🌡️ 空气温度" value="temperature" />
              <el-option label="💧 空气湿度" value="humidity" />
              <el-option label="🌱 土壤湿度" value="soil_moisture" />
              <el-option label="☀️ 光照强度" value="light_intensity" />
              <el-option label="💨 CO₂浓度" value="co2" />
              <el-option label="🪴 土壤温度" value="soil_temperature" />
            </el-select>
          </el-form-item>

          <el-form-item label="条件" prop="trigger_config.operator">
            <el-select v-model="form.trigger_config.operator" placeholder="选择条件">
              <el-option label="大于" value="gt" />
              <el-option label="小于" value="lt" />
              <el-option label="等于" value="eq" />
            </el-select>
          </el-form-item>

          <el-form-item label="阈值" prop="trigger_config.threshold_value">
            <el-input-number
              v-model="form.trigger_config.threshold_value"
              :precision="1"
              :step="1"
            />
            <span class="unit-label">{{ getPropertyUnit(form.trigger_config.property_identifier) }}</span>
          </el-form-item>
        </template>

        <!-- 定时触发配置 -->
        <template v-else-if="form.trigger_type === 'schedule'">
          <el-form-item label="执行时间" prop="trigger_config.cron">
            <el-input v-model="form.trigger_config.cron" placeholder="如：0 8 * * * 表示每天8点" />
            <div class="form-tip">
              格式：分 时 日 月 周（如：0 8 * * * = 每天8点，30 18 * * * = 每天18:30）
            </div>
          </el-form-item>
        </template>

        <el-divider content-position="left">执行动作</el-divider>

        <el-form-item label="动作类型" prop="action_type">
          <el-radio-group v-model="form.action_type">
            <el-radio label="command">下发命令</el-radio>
            <el-radio label="alert">发送告警</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 命令动作配置 -->
        <template v-if="form.action_type === 'command'">
          <el-form-item label="选择设备" prop="action_config.device_id">
            <el-select v-model="form.action_config.device_id" placeholder="选择要控制的设备">
              <el-option
                v-for="device in devices"
                :key="device.id"
                :label="device.name"
                :value="device.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="控制设备" prop="action_config.service_identifier">
            <el-select v-model="form.action_config.service_identifier" placeholder="选择要控制的设备">
              <el-option label="🌀 通风扇" value="set_fan" />
              <el-option label="💡 补光灯" value="set_light" />
              <el-option label="🚿 灌溉水泵" value="set_pump" />
            </el-select>
          </el-form-item>

          <el-form-item label="操作" prop="action_config.input_params.status">
            <el-radio-group v-model="form.action_config.input_params.status">
              <el-radio :label="true">开启</el-radio>
              <el-radio :label="false">关闭</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item v-if="form.action_config.service_identifier === 'set_light'" label="亮度">
            <el-slider
              v-model="form.action_config.input_params.brightness"
              :min="10"
              :max="100"
              :step="10"
              show-stops
            />
          </el-form-item>
        </template>

        <!-- 告警动作配置 -->
        <template v-else-if="form.action_type === 'alert'">
          <el-form-item label="告警级别">
            <el-select v-model="form.action_config.level" placeholder="选择告警级别">
              <el-option label="提示" value="info" />
              <el-option label="警告" value="warning" />
              <el-option label="严重" value="error" />
            </el-select>
          </el-form-item>
        </template>

        <el-divider content-position="left">高级设置</el-divider>

        <el-form-item label="触发间隔">
          <el-input-number v-model="form.cooldown_seconds" :min="10" :max="3600" :step="10" />
          <span class="unit-label">秒</span>
          <div class="form-tip">
            场景触发后，间隔多少秒才能再次执行（防止频繁触发）
          </div>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '保存修改' : '创建场景' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <el-dialog v-model="showTemplatesDialog" title="📦 快速使用模板" width="700px">
      <div class="template-grid">
        <div
          v-for="template in sceneTemplates"
          :key="template.id"
          class="template-card"
          @click="useTemplate(template)"
        >
          <div class="template-icon">{{ template.name.split(' ')[0] }}</div>
          <div class="template-name">{{ template.name.split(' ').slice(1).join(' ') }}</div>
          <div class="template-desc">{{ template.description }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Collection, CircleCheck, Timer, Plus, Clock, Delete,
  Edit, VideoPlay, Pointer, Files, Refresh, MagicStick
} from '@element-plus/icons-vue'
import { sceneService, sceneTemplates, propertyLabels, operatorLabels, serviceLabels } from '../services/scene.js'
import api from '../services/api.js'

const scenes = ref([])
const selectedScene = ref(null)
const devices = ref([])
const executionLogs = ref([])
const showDialog = ref(false)
const showTemplatesDialog = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  description: '',
  trigger_type: 'threshold',
  trigger_config: {
    property_identifier: '',
    operator: 'gt',
    threshold_value: 30,
    cron: ''
  },
  action_type: 'command',
  action_config: {
    device_id: null,
    service_identifier: '',
    input_params: {
      status: true,
      brightness: 80
    },
    level: 'warning'
  },
  enabled: true,
  cooldown_seconds: 60
})

const rules = {
  name: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
  trigger_type: [{ required: true, message: '请选择触发方式', trigger: 'change' }],
  action_type: [{ required: true, message: '请选择动作类型', trigger: 'change' }],
  'trigger_config.property_identifier': [{ required: true, message: '请选择监测指标', trigger: 'change' }],
  'trigger_config.operator': [{ required: true, message: '请选择条件', trigger: 'change' }],
  'trigger_config.threshold_value': [{ required: true, message: '请输入阈值', trigger: 'blur' }],
  'action_config.service_identifier': [{ required: true, message: '请选择要控制的设备', trigger: 'change' }]
}

const enabledCount = computed(() => scenes.value.filter(s => s.enabled).length)
const todayExecutions = computed(() => {
  const today = new Date().toDateString()
  return executionLogs.value.filter(log => new Date(log.created_at).toDateString() === today).length
})

async function loadScenes() {
  try {
    scenes.value = await sceneService.getScenes()
  } catch (e) {
    console.error('Failed to load scenes:', e)
  }
}

async function loadDevices() {
  try {
    const resp = await api.get('/devices/')
    devices.value = resp.data
  } catch (e) {
    console.error('Failed to load devices:', e)
  }
}

async function loadExecutionLogs() {
  if (!selectedScene.value) return
  try {
    executionLogs.value = await sceneService.getExecutionLogs(selectedScene.value.id, { limit: 20 })
  } catch (e) {
    console.error('Failed to load execution logs:', e)
  }
}

function selectScene(scene) {
  selectedScene.value = scene
  loadExecutionLogs()
}

function openCreateDialog() {
  isEditing.value = false
  showDialog.value = true
}

function openEditDialog() {
  if (!selectedScene.value) return
  isEditing.value = true
  form.name = selectedScene.value.name
  form.description = selectedScene.value.description
  form.trigger_type = selectedScene.value.trigger_type
  form.trigger_config = { ...selectedScene.value.trigger_config }
  form.action_type = selectedScene.value.action_type
  form.action_config = { ...selectedScene.value.action_config }
  if (!form.action_config.input_params) {
    form.action_config.input_params = { status: true, brightness: 80 }
  }
  form.enabled = selectedScene.value.enabled
  form.cooldown_seconds = selectedScene.value.cooldown_seconds
  showDialog.value = true
}

function resetForm() {
  form.name = ''
  form.description = ''
  form.trigger_type = 'threshold'
  form.trigger_config = { property_identifier: '', operator: 'gt', threshold_value: 30, cron: '' }
  form.action_type = 'command'
  form.action_config = { device_id: null, service_identifier: '', input_params: { status: true, brightness: 80 }, level: 'warning' }
  form.enabled = true
  form.cooldown_seconds = 60
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = {
      name: form.name,
      description: form.description,
      trigger_type: form.trigger_type,
      trigger_config: form.trigger_config,
      action_type: form.action_type,
      action_config: form.action_config,
      enabled: form.enabled,
      cooldown_seconds: form.cooldown_seconds
    }

    if (isEditing.value) {
      await sceneService.updateScene(selectedScene.value.id, data)
      ElMessage.success('场景已更新')
    } else {
      await sceneService.createScene(data)
      ElMessage.success('场景已创建')
    }

    showDialog.value = false
    await loadScenes()
  } catch (e) {
    ElMessage.error('操作失败：' + (e.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

async function toggleScene(scene) {
  try {
    const updated = await sceneService.toggleScene(scene.id)
    scene.enabled = updated.enabled
    ElMessage.success(updated.enabled ? '场景已启用' : '场景已禁用')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function triggerScene(scene) {
  try {
    await sceneService.triggerScene(scene.id)
    ElMessage.success('场景已触发执行')
    await loadExecutionLogs()
    await loadScenes()
  } catch (e) {
    ElMessage.error('触发失败：' + (e.message || '未知错误'))
  }
}

async function deleteScene(scene) {
  try {
    await ElMessageBox.confirm(
      `确定要删除场景"${scene.name}"吗？删除后无法恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await sceneService.deleteScene(scene.id)
    ElMessage.success('场景已删除')
    if (selectedScene.value?.id === scene.id) {
      selectedScene.value = null
    }
    await loadScenes()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function useTemplate(template) {
  showTemplatesDialog.value = false
  form.name = template.name.split(' ').slice(1).join(' ')
  form.description = template.description
  form.trigger_type = template.trigger_type
  form.trigger_config = { ...template.trigger_config }
  form.action_type = template.action_type
  form.action_config = { ...template.action_config }
  if (!form.action_config.input_params) {
    form.action_config.input_params = { status: true, brightness: 80 }
  }
  isEditing.value = false
  showDialog.value = true
}

function handleTriggerTypeChange() {
  if (form.trigger_type !== 'threshold') {
    form.trigger_config.threshold_value = null
    form.trigger_config.property_identifier = ''
  }
}

function getSceneIcon(triggerType) {
  const icons = {
    threshold: '🎯',
    schedule: '⏰',
    manual: '👆',
    device_status: '📡'
  }
  return icons[triggerType] || '📋'
}

function getPropertyLabel(prop) {
  return propertyLabels[prop] || prop
}

function getOperatorLabel(op) {
  return operatorLabels[op] || op
}

function getServiceLabel(service) {
  return serviceLabels[service] || service
}

function getPropertyUnit(prop) {
  const units = {
    temperature: '°C',
    humidity: '%',
    soil_moisture: '%',
    soil_temperature: '°C',
    light_intensity: ' lux',
    co2: ' ppm'
  }
  return units[prop] || ''
}

function getStatusType(status) {
  const types = { success: 'success', failed: 'danger', executing: 'warning' }
  return types[status] || 'info'
}

function getStatusLabel(status) {
  const labels = { success: '成功', failed: '失败', executing: '执行中' }
  return labels[status] || status
}

function formatTime(time) {
  if (!time) return '从未'
  const d = new Date(time)
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  await Promise.all([loadScenes(), loadDevices()])
})
</script>

<style scoped>
.scenes-page {
  padding: 0;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  border: none;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-blue { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-green { background: linear-gradient(135deg, #11998e, #38ef7d); }
.stat-orange { background: linear-gradient(135deg, #f093fb, #f5576c); }

.stat-info { flex: 1; }

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
}

.section-card {
  border-radius: 12px;
  height: fit-content;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state.small {
  padding: 30px 20px;
  font-size: 13px;
}

.empty-state p {
  margin: 10px 0 0;
}

.empty-state .tip {
  font-size: 12px;
  color: #c0c4cc;
}

.scene-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scene-card {
  padding: 16px;
  border-radius: 10px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.scene-card:hover {
  background: #f0f9eb;
}

.scene-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.scene-card.disabled {
  opacity: 0.6;
}

.scene-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.scene-icon {
  font-size: 20px;
}

.scene-name {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.scene-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
}

.scene-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.scene-actions {
  display: flex;
  gap: 6px;
}

.scene-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.condition-box,
.action-box {
  padding: 14px;
  border-radius: 8px;
  background: #f4f4f5;
  font-size: 14px;
  color: #606266;
}

.condition-box strong,
.action-box strong {
  color: #409eff;
  font-weight: 600;
}

.detail-actions {
  display: flex;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.log-item {
  padding: 10px;
  border-radius: 6px;
  background: #fafafa;
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-error {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.template-card {
  padding: 20px;
  border-radius: 10px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.template-card:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.template-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.template-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.template-desc {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
}

.unit-label {
  margin-left: 8px;
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
