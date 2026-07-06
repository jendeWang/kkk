<template>
  <div class="rule-editor-page">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>规则编辑器</span>
          <div class="header-actions">
            <el-button type="primary" @click="showAddRuleDialog = true">
              <el-icon><Plus /></el-icon>
              创建规则
            </el-button>
            <el-select v-model="ruleType" placeholder="规则类型" style="width: 150px; margin-left: 10px">
              <el-option label="告警规则" value="alert" />
              <el-option label="场景联动" value="scene" />
            </el-select>
          </div>
        </div>
      </template>

      <div class="rules-grid">
        <div class="rule-card" v-for="rule in rules" :key="rule.id">
          <div class="rule-header" :class="rule.enabled ? '' : 'disabled'">
            <div class="rule-icon">
              <el-icon><AlertTriangle v-if="ruleType === 'alert'" /><Timer v-else /></el-icon>
            </div>
            <div class="rule-info">
              <div class="rule-name">{{ rule.name }}</div>
              <div class="rule-desc">{{ rule.description }}</div>
            </div>
            <div class="rule-controls">
              <el-switch v-model="rule.enabled" @change="(val) => handleToggleRule(rule, val)" />
            </div>
          </div>

          <div class="rule-body">
            <div class="condition-section">
              <div class="section-title">触发条件</div>
              <div class="condition-content">
                <span class="device-tag">{{ getDeviceName(rule.device_id) }}</span>
                <span class="property-tag">{{ getPropertyName(rule.property_identifier) }}</span>
                <span class="operator-tag">{{ getOperatorText(rule.operator) }}</span>
                <span class="value-tag">{{ rule.threshold_value }}</span>
              </div>
            </div>

            <div class="action-section" v-if="rule.linked_scene_id">
              <div class="section-title">执行动作</div>
              <div class="action-content">
                <span>自动执行场景: {{ rule.linked_scene_name }}</span>
              </div>
            </div>

            <div class="rule-meta">
              <span class="meta-item">级别: {{ getSeverityText(rule.severity) }}</span>
              <span class="meta-item">冷却: {{ rule.cooldown_seconds }}s</span>
              <span class="meta-item">持续: {{ rule.duration_seconds }}s</span>
            </div>
          </div>

          <div class="rule-footer">
            <el-button size="small" @click="handleEditRule(rule)">编辑</el-button>
            <el-button size="small" @click="handleTestRule(rule)">测试</el-button>
            <el-button size="small" type="danger" @click="handleDeleteRule(rule)">删除</el-button>
          </div>
        </div>
      </div>

      <div v-if="rules.length === 0" class="empty-state">
        <el-icon><FolderOpened /></el-icon>
        <div>暂无规则，点击上方按钮创建</div>
      </div>
    </el-card>

    <el-dialog v-model="showAddRuleDialog" :title="editingRule ? '编辑规则' : '创建规则'" width="700px">
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item label="规则名称" required>
          <el-input v-model="ruleForm.name" placeholder="输入规则名称" />
        </el-form-item>
        <el-form-item label="规则描述">
          <el-input v-model="ruleForm.description" type="textarea" placeholder="输入规则描述" />
        </el-form-item>

        <el-divider content-position="left">触发条件</el-divider>

        <el-form-item label="告警类型">
          <el-select v-model="ruleForm.alert_type" placeholder="选择告警类型">
            <el-option label="阈值告警" value="threshold" />
            <el-option label="设备离线" value="device_offline" />
            <el-option label="自定义事件" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="关联设备">
          <el-select v-model="ruleForm.device_id" placeholder="选择设备（可选，为空则应用于所有设备）" clearable>
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="监控属性">
          <el-select v-model="ruleForm.property_identifier" placeholder="选择监控属性">
            <el-option v-for="p in availableProperties" :key="p.identifier" :label="p.name" :value="p.identifier" />
          </el-select>
        </el-form-item>

        <el-form-item label="比较操作">
          <el-select v-model="ruleForm.operator" placeholder="选择比较操作">
            <el-option label="大于" value="gt" />
            <el-option label="大于等于" value="gte" />
            <el-option label="小于" value="lt" />
            <el-option label="小于等于" value="lte" />
            <el-option label="等于" value="eq" />
            <el-option label="不等于" value="neq" />
            <el-option label="上升速率" value="increase_rate" />
            <el-option label="下降速率" value="decrease_rate" />
          </el-select>
        </el-form-item>

        <el-form-item label="阈值">
          <el-input v-model="ruleForm.threshold_value" placeholder="输入阈值" />
        </el-form-item>

        <el-form-item label="持续时间(秒)">
          <el-input-number v-model="ruleForm.duration_seconds" :min="0" :max="3600" />
        </el-form-item>

        <el-divider content-position="left">告警配置</el-divider>

        <el-form-item label="告警级别">
          <el-radio-group v-model="ruleForm.severity">
            <el-radio label="info">信息</el-radio>
            <el-radio label="warning">警告</el-radio>
            <el-radio label="error">错误</el-radio>
            <el-radio label="critical">严重</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="冷却时间(秒)">
          <el-input-number v-model="ruleForm.cooldown_seconds" :min="0" :max="86400" />
        </el-form-item>

        <el-form-item label="静默时段">
          <div class="silent-time">
            <el-input-number v-model="ruleForm.silent_from_hour" :min="0" :max="23" />
            <span>至</span>
            <el-input-number v-model="ruleForm.silent_to_hour" :min="0" :max="23" />
          </div>
        </el-form-item>

        <el-divider content-position="left">联动配置</el-divider>

        <el-form-item label="关联场景">
          <el-select v-model="ruleForm.linked_scene_id" placeholder="选择关联场景（可选）" clearable>
            <el-option v-for="s in scenes" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="自动执行场景">
          <el-switch v-model="ruleForm.auto_execute_scene" />
        </el-form-item>

        <el-form-item label="启用规则">
          <el-switch v-model="ruleForm.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveRule" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTestDialog" title="测试规则" width="500px">
      <el-form :model="testForm" label-width="120px">
        <el-form-item label="测试值">
          <el-input v-model="testForm.value" placeholder="输入测试值" />
        </el-form-item>
        <el-form-item label="设备ID">
          <el-input v-model="testForm.device_id" :disabled="true" />
        </el-form-item>
        <el-form-item label="属性">
          <el-input v-model="testForm.property_identifier" :disabled="true" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTestDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExecuteTest" :loading="testing">执行测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { useProductStore } from '../stores/product.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, AlertTriangle, Timer, FolderOpened } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const productStore = useProductStore()

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const ruleType = ref('alert')
const showAddRuleDialog = ref(false)
const showTestDialog = ref(false)
const editingRule = ref(null)

const rules = ref([])
const scenes = ref([])

const availableProperties = computed(() => {
  const product = productStore.products[0]
  return product ? (product.properties || []).filter(p => p.access_type === 'read_only') : []
})

const ruleForm = reactive({
  name: '',
  description: '',
  alert_type: 'threshold',
  device_id: null,
  property_identifier: '',
  operator: 'gt',
  threshold_value: '',
  duration_seconds: 0,
  severity: 'warning',
  cooldown_seconds: 300,
  silent_from_hour: null,
  silent_to_hour: null,
  linked_scene_id: null,
  auto_execute_scene: false,
  enabled: true,
})

const testForm = reactive({
  value: '',
  device_id: '',
  property_identifier: '',
})

const operatorText = {
  gt: '>',
  gte: '>=',
  lt: '<',
  lte: '<=',
  eq: '=',
  neq: '!=',
  increase_rate: '↑速率',
  decrease_rate: '↓速率',
}

const severityText = {
  info: '信息',
  warning: '警告',
  error: '错误',
  critical: '严重',
}

function getOperatorText(operator) {
  return operatorText[operator] || operator
}

function getSeverityText(severity) {
  return severityText[severity] || severity
}

function getDeviceName(device_id) {
  if (!device_id) return '所有设备'
  const device = deviceStore.devices.find(d => d.id === device_id)
  return device ? device.device_name : `设备#${device_id}`
}

function getPropertyName(identifier) {
  const props = availableProperties.value
  const prop = props.find(p => p.identifier === identifier)
  return prop ? prop.name : identifier
}

async function loadRules() {
  try {
    const result = await deviceStore.fetchAlertRules()
    rules.value = result
  } catch (e) {
    console.error('Failed to load rules:', e)
  }
}

async function loadScenes() {
  try {
    const response = await fetch('/api/v1/scenes/')
    const data = await response.json()
    scenes.value = data
  } catch (e) {
    console.error('Failed to load scenes:', e)
  }
}

async function handleToggleRule(rule, enabled) {
  try {
    await deviceStore.updateAlertRule(rule.id, { enabled })
    ElMessage.success(`规则已${enabled ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('操作失败')
    rule.enabled = !enabled
  }
}

function handleEditRule(rule) {
  editingRule.value = rule
  Object.assign(ruleForm, {
    name: rule.name,
    description: rule.description || '',
    alert_type: rule.alert_type,
    device_id: rule.device_id,
    property_identifier: rule.property_identifier,
    operator: rule.operator,
    threshold_value: rule.threshold_value,
    duration_seconds: rule.duration_seconds || 0,
    severity: rule.severity,
    cooldown_seconds: rule.cooldown_seconds || 300,
    silent_from_hour: rule.silent_from_hour,
    silent_to_hour: rule.silent_to_hour,
    linked_scene_id: rule.linked_scene_id,
    auto_execute_scene: rule.auto_execute_scene || false,
    enabled: rule.enabled,
  })
  showAddRuleDialog.value = true
}

function handleTestRule(rule) {
  testForm.value = ''
  testForm.device_id = rule.device_id || ''
  testForm.property_identifier = rule.property_identifier || ''
  showTestDialog.value = true
}

async function handleExecuteTest() {
  if (!testing.value && editingRule.value) {
    testing.value = true
    try {
      const response = await fetch(`/api/v1/alerts/rules/${editingRule.value.id}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(testForm),
      })
      const data = await response.json()
      if (data.triggered) {
        ElMessage.success(`规则已触发！事件ID: ${data.event_id}`)
      } else {
        ElMessage.info('规则未触发')
      }
    } catch (error) {
      ElMessage.error('测试失败')
    } finally {
      testing.value = false
      showTestDialog.value = false
    }
  }
}

async function handleDeleteRule(rule) {
  try {
    await ElMessageBox.confirm('确定要删除此规则吗？', '警告', { type: 'warning' })
    await deviceStore.deleteAlertRule(rule.id)
    rules.value = rules.value.filter(r => r.id !== rule.id)
    ElMessage.success('规则已删除')
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleSaveRule() {
  if (!ruleForm.name || !ruleForm.property_identifier || !ruleForm.operator || !ruleForm.threshold_value) {
    ElMessage.warning('请填写必填项')
    return
  }

  saving.value = true
  try {
    if (editingRule.value) {
      await deviceStore.updateAlertRule(editingRule.value.id, ruleForm)
      ElMessage.success('规则已更新')
    } else {
      await deviceStore.createAlertRule(ruleForm)
      ElMessage.success('规则已创建')
    }
    showAddRuleDialog.value = false
    editingRule.value = null
    Object.assign(ruleForm, {
      name: '',
      description: '',
      alert_type: 'threshold',
      device_id: null,
      property_identifier: '',
      operator: 'gt',
      threshold_value: '',
      duration_seconds: 0,
      severity: 'warning',
      cooldown_seconds: 300,
      silent_from_hour: null,
      silent_to_hour: null,
      linked_scene_id: null,
      auto_execute_scene: false,
      enabled: true,
    })
    await loadRules()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await deviceStore.fetchDevices()
  await productStore.fetchProducts()
  await loadRules()
  await loadScenes()
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

.rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.rule-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  overflow: hidden;
  transition: all 0.3s;
}

.rule-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.rule-header {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.rule-header.disabled {
  opacity: 0.6;
}

.rule-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #e6f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 20px;
}

.rule-info {
  flex: 1;
}

.rule-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.rule-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.rule-controls {
  margin-left: 10px;
}

.rule-body {
  padding: 15px;
}

.section-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.condition-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.device-tag, .property-tag, .operator-tag, .value-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
}

.device-tag {
  background: #f0f5ff;
  color: #409eff;
}

.property-tag {
  background: #f6ffed;
  color: #67c23a;
}

.operator-tag {
  background: #fff7e6;
  color: #e6a23c;
}

.value-tag {
  background: #fef0f0;
  color: #f56c6c;
}

.action-section {
  margin-top: 15px;
}

.action-content {
  font-size: 13px;
  color: #606266;
}

.rule-meta {
  margin-top: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.meta-item {
  font-size: 12px;
  color: #909399;
}

.rule-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px;
  border-top: 1px solid #ebeef5;
  background: #fafafa;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #909399;
}

.empty-state el-icon {
  font-size: 48px;
  margin-bottom: 15px;
  color: #c0c4cc;
}

.silent-time {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>