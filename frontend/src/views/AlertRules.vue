<template>
  <div class="alert-rules-page">
    <el-card>
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
        <el-table-column prop="name" :label="$t('alertRules.name')" />
        <el-table-column :label="$t('alertRules.alertType')" width="150">
          <template #default="{ row }">
            {{ row.alert_type === 'threshold' ? $t('alertRules.threshold') : $t('alertRules.deviceStatus') }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('alertRules.device')" width="120">
          <template #default="{ row }">
            {{ row.device_id ? `ID: ${row.device_id}` : $t('alertRules.allDevices') }}
          </template>
        </el-table-column>
        <el-table-column prop="property_identifier" :label="$t('alertRules.property')" width="120" />
        <el-table-column :label="$t('alertRules.thresholdValue')" width="150">
          <template #default="{ row }">
            {{ row.operator }} {{ row.threshold_value }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('alertRules.severity')" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('alertRules.enabled')" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="150">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="$t('alertRules.addRule')" width="600px">
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item :label="$t('alertRules.name')">
          <el-input v-model="ruleForm.name" />
        </el-form-item>
        <el-form-item :label="$t('alertRules.alertType')">
          <el-select v-model="ruleForm.alert_type">
            <el-option value="threshold" :label="$t('alertRules.threshold')" />
            <el-option value="device_status" :label="$t('alertRules.deviceStatus')" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertRules.device')">
          <el-select v-model="ruleForm.device_id" clearable>
            <el-option :value="null" :label="$t('alertRules.allDevices')" />
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertRules.property')" v-if="ruleForm.alert_type === 'threshold'">
          <el-input v-model="ruleForm.property_identifier" />
        </el-form-item>
        <el-form-item :label="$t('alertRules.operator')" v-if="ruleForm.alert_type === 'threshold'">
          <el-select v-model="ruleForm.operator">
            <el-option value=">" label=">" />
            <el-option value="<" label="<" />
            <el-option value=">=" label=">=" />
            <el-option value="<=" label="<=" />
            <el-option value="==" label="==" />
            <el-option value="!=" label="!=" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertRules.thresholdValue')" v-if="ruleForm.alert_type === 'threshold'">
          <el-input v-model="ruleForm.threshold_value" />
        </el-form-item>
        <el-form-item :label="$t('alertRules.severity')">
          <el-select v-model="ruleForm.severity">
            <el-option value="info" :label="$t('alertRules.info')" />
            <el-option value="warning" :label="$t('alertRules.warning')" />
            <el-option value="error" :label="$t('alertRules.error')" />
            <el-option value="critical" :label="$t('alertRules.critical')" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAdd" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const deviceStore = useDeviceStore()

const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)

const ruleForm = reactive({
  name: '',
  alert_type: 'threshold',
  device_id: null,
  property_identifier: '',
  operator: '>',
  threshold_value: '',
  severity: 'warning'
})

function getSeverityType(severity) {
  const types = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return types[severity] || 'info'
}

async function loadRules() {
  loading.value = true
  try {
    await Promise.all([
      deviceStore.fetchAlertRules(),
      deviceStore.fetchDevices()
    ])
  } catch (error) {
    ElMessage.error('Failed to load alert rules')
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  saving.value = true
  try {
    await deviceStore.createAlertRule(ruleForm)
    ElMessage.success('Alert rule created')
    showAddDialog.value = false
    Object.keys(ruleForm).forEach(k => {
      if (k === 'alert_type') ruleForm[k] = 'threshold'
      else if (k === 'device_id') ruleForm[k] = null
      else if (k === 'severity') ruleForm[k] = 'warning'
      else ruleForm[k] = ''
    })
    await loadRules()
  } catch (error) {
    ElMessage.error('Failed to create alert rule')
  } finally {
    saving.value = false
  }
}

async function handleToggle(rule) {
  try {
    await deviceStore.updateAlertRule(rule.id, { enabled: rule.enabled })
    ElMessage.success('Rule updated')
  } catch (error) {
    ElMessage.error('Failed to update rule')
  }
}

async function handleDelete(rule) {
  try {
    await ElMessageBox.confirm('Delete this rule?', 'Warning', { type: 'warning' })
    await deviceStore.deleteAlertRule(rule.id)
    ElMessage.success('Rule deleted')
    await loadRules()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('Failed to delete rule')
  }
}

onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
