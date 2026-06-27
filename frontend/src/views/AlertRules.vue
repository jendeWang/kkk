<template>
  <div class="alert-rules-page">
    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="page-intro"
    >
      <template #title>📢 告警规则 = 监测 + 通知</template>
      <template #default>
        告警规则负责<strong>发现异常并通知您</strong>（如温度过高、设备离线等）。
        如果需要<strong>自动控制设备</strong>（如高温自动开风扇），请使用「场景联动」。
        告警触发时也可以选择自动执行某个场景进行联动处置。
        <router-link to="/scenes" style="margin-left: 8px;">去配置场景联动 →</router-link>
      </template>
    </el-alert>

    <el-card style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <span>{{ $t('alertRules.title') }}</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            {{ $t('alertRules.addRule') }}
          </el-button>
        </div>
      </template>

      <el-table :data="deviceStore.alertRules" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" :label="$t('alertRules.name')" min-width="140" />
        <el-table-column :label="$t('alertRules.alertType')" width="120">
          <template #default="{ row }">
            {{ getAlertTypeLabel(row.alert_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="property_identifier" :label="$t('alertRules.property')" width="120" />
        <el-table-column :label="阈值" width="140">
          <template #default="{ row }">
            <span v-if="row.alert_type === 'threshold'">
              {{ getOperatorSymbol(row.operator) }} {{ row.threshold_value }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('alertRules.severity')" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">{{ getSeverityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="联动场景" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.linked_scene_name" type="success" effect="plain" size="small">
              {{ row.linked_scene_name }}
            </el-tag>
            <span v-else class="text-muted">未关联</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('alertRules.enabled')" width="90">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="isEditing ? '编辑告警规则' : $t('alertRules.addRule')" width="650px">
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item :label="$t('alertRules.name')">
          <el-input v-model="ruleForm.name" placeholder="如：高温告警" />
        </el-form-item>
        <el-form-item :label="$t('alertRules.alertType')">
          <el-select v-model="ruleForm.alert_type" style="width: 100%">
            <el-option value="threshold" :label="$t('alertRules.threshold')" />
            <el-option value="device_offline" :label="$t('alertRules.deviceOffline')" />
            <el-option value="device_online" :label="$t('alertRules.deviceOnline')" />
          </el-select>
        </el-form-item>
        <el-form-item :label="监测设备">
          <el-select v-model="ruleForm.device_id" clearable placeholder="选择设备（不选则全部设备）" style="width: 100%">
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertRules.property')" v-if="ruleForm.alert_type === 'threshold'">
          <el-select v-model="ruleForm.property_identifier" filterable allow-create placeholder="选择或输入属性标识符" style="width: 100%">
            <el-option label="空气温度" value="temperature" />
            <el-option label="空气湿度" value="humidity" />
            <el-option label="土壤湿度" value="soil_moisture" />
            <el-option label="光照强度" value="light_intensity" />
            <el-option label="CO₂浓度" value="co2" />
            <el-option label="土壤温度" value="soil_temperature" />
            <el-option label="氨气浓度" value="ammonia" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertRules.operator')" v-if="ruleForm.alert_type === 'threshold'">
          <el-select v-model="ruleForm.operator" style="width: 100%">
            <el-option value="gt" label="大于 ( > )" />
            <el-option value="lt" label="小于 ( < )" />
            <el-option value="gte" label="大于等于 ( >= )" />
            <el-option value="lte" label="小于等于 ( <= )" />
            <el-option value="eq" label="等于 ( == )" />
            <el-option value="neq" label="不等于 ( != )" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertRules.thresholdValue')" v-if="ruleForm.alert_type === 'threshold'">
          <el-input-number v-model="ruleForm.threshold_value" :precision="1" :step="0.5" style="width: 200px" />
        </el-form-item>
        <el-form-item :label="$t('alertRules.severity')">
          <el-radio-group v-model="ruleForm.severity">
            <el-radio value="info">提示</el-radio>
            <el-radio value="warning">警告</el-radio>
            <el-radio value="error">严重</el-radio>
            <el-radio value="critical">紧急</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider content-position="left">联动处置（可选）</el-divider>

        <el-form-item label="关联场景">
          <el-select v-model="ruleForm.linked_scene_id" clearable placeholder="选择告警触发时自动执行的场景" style="width: 100%">
            <el-option
              v-for="scene in sceneList"
              :key="scene.id"
              :label="scene.name"
              :value="scene.id"
            />
          </el-select>
          <div class="form-tip">选择后，告警触发时会自动执行该场景（如自动开通风扇降温）</div>
        </el-form-item>
        <el-form-item label="自动执行" v-if="ruleForm.linked_scene_id">
          <el-switch v-model="ruleForm.auto_execute_scene" />
          <span class="form-tip-inline">开启后告警触发时自动执行关联场景</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '../services/api.js'

const { t } = useI18n()
const deviceStore = useDeviceStore()

const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)
const isEditing = ref(false)
const editingRuleId = ref(null)
const sceneList = ref([])

const ruleForm = reactive({
  name: '',
  alert_type: 'threshold',
  device_id: null,
  property_identifier: '',
  operator: 'gt',
  threshold_value: 30,
  severity: 'warning',
  linked_scene_id: null,
  auto_execute_scene: false
})

function getSeverityType(severity) {
  const types = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return types[severity] || 'info'
}

function getSeverityLabel(severity) {
  const labels = { info: '提示', warning: '警告', error: '严重', critical: '紧急' }
  return labels[severity] || severity
}

function getOperatorSymbol(operator) {
  const symbols = { gt: '>', gte: '>=', lt: '<', lte: '<=', eq: '==', neq: '!=' }
  return symbols[operator] || operator
}

function getAlertTypeLabel(alertType) {
  const labels = {
    threshold: '阈值告警',
    device_offline: '设备离线',
    device_online: '设备上线'
  }
  return labels[alertType] || alertType
}

function resetForm() {
  ruleForm.name = ''
  ruleForm.alert_type = 'threshold'
  ruleForm.device_id = null
  ruleForm.property_identifier = ''
  ruleForm.operator = 'gt'
  ruleForm.threshold_value = 30
  ruleForm.severity = 'warning'
  ruleForm.linked_scene_id = null
  ruleForm.auto_execute_scene = false
  isEditing.value = false
  editingRuleId.value = null
}

async function loadScenes() {
  try {
    const resp = await api.get('/scenes/')
    sceneList.value = resp.data || []
  } catch (e) {
    console.error('Failed to load scenes:', e)
  }
}

async function loadRules() {
  loading.value = true
  try {
    await Promise.all([
      deviceStore.fetchAlertRules(),
      deviceStore.fetchDevices(),
      loadScenes()
    ])
  } catch (error) {
    ElMessage.error('Failed to load alert rules')
  } finally {
    loading.value = false
  }
}

function handleEdit(rule) {
  isEditing.value = true
  editingRuleId.value = rule.id
  ruleForm.name = rule.name
  ruleForm.alert_type = rule.alert_type
  ruleForm.device_id = rule.device_id
  ruleForm.property_identifier = rule.property_identifier || ''
  ruleForm.operator = rule.operator || 'gt'
  ruleForm.threshold_value = rule.threshold_value ? parseFloat(rule.threshold_value) : 30
  ruleForm.severity = rule.severity
  ruleForm.linked_scene_id = rule.linked_scene_id || null
  ruleForm.auto_execute_scene = rule.auto_execute_scene || false
  showAddDialog.value = true
}

async function handleSave() {
  if (!ruleForm.name) {
    ElMessage.warning('请输入规则名称')
    return
  }
  if (ruleForm.alert_type === 'threshold' && !ruleForm.property_identifier) {
    ElMessage.warning('请选择监测属性')
    return
  }

  saving.value = true
  try {
    const payload = { ...ruleForm }
    if (isEditing.value) {
      await deviceStore.updateAlertRule(editingRuleId.value, payload)
      ElMessage.success('告警规则已更新')
    } else {
      await deviceStore.createAlertRule(payload)
      ElMessage.success('告警规则创建成功')
    }
    showAddDialog.value = false
    resetForm()
    await loadRules()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleToggle(rule) {
  try {
    await deviceStore.updateAlertRule(rule.id, { enabled: rule.enabled })
    ElMessage.success(rule.enabled ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('操作失败')
    rule.enabled = !rule.enabled
  }
}

async function handleDelete(rule) {
  try {
    await ElMessageBox.confirm(`确定要删除告警规则"${rule.name}"吗？`, '删除确认', { type: 'warning' })
    await deviceStore.deleteAlertRule(rule.id)
    ElMessage.success('删除成功')
    await loadRules()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.page-intro {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-muted {
  color: #c0c4cc;
  font-size: 13px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.form-tip-inline {
  margin-left: 8px;
  font-size: 13px;
  color: #606266;
}
</style>
