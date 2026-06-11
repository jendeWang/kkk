<template>
  <div class="commands-page">
    <el-card>
      <template #header>
        <span>{{ $t('commands.title') }}</span>
      </template>

      <el-form :inline="true" :model="commandForm" class="command-form">
        <el-form-item :label="$t('commands.selectDevice')">
          <el-select v-model="commandForm.device_id" @change="loadServices" placeholder="Select device" style="width: 200px">
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('commands.selectService')">
          <el-select v-model="commandForm.service_identifier" @change="loadServiceParams" placeholder="Select service" style="width: 200px" :disabled="!services.length">
            <el-option v-for="s in services" :key="s.identifier" :label="s.name" :value="s.identifier" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="sendCommand" :loading="sending" :disabled="!canSend">{{ $t('commands.sendCommand') }}</el-button>
        </el-form-item>
      </el-form>

      <div v-if="commandForm.service_identifier" class="params-section">
        <div class="params-header">
          <h4>Input Parameters</h4>
          <div v-if="currentServiceParams.length > 0">
            <el-button size="small" @click="switchMode">
              {{ advancedMode ? 'Switch to Form Mode' : 'Switch to Advanced Mode' }}
            </el-button>
          </div>
        </div>

        <!-- Form Mode: Auto-generated inputs from service definition -->
        <div v-if="!advancedMode && currentServiceParams.length > 0" class="params-form-container">
          <el-form :model="paramForm" label-width="120px" class="params-form">
            <el-form-item v-for="param in currentServiceParams" :key="param.name" :label="param.name" :required="param.required">
              <el-input v-if="param.type === 'string'" v-model="paramForm[param.name]" :placeholder="`Enter ${param.name} (string)`" style="width: 300px;" />
              <el-input v-else-if="param.type === 'int'" type="number" v-model.number="paramForm[param.name]" :placeholder="`Enter ${param.name} (integer)`" style="width: 300px;" />
              <el-input v-else-if="param.type === 'float'" type="number" step="0.01" v-model.number="paramForm[param.name]" :placeholder="`Enter ${param.name} (float)`" style="width: 300px;" />
              <el-switch v-else-if="param.type === 'bool'" v-model="paramForm[param.name]" />
              <span v-if="param.description" class="param-desc">{{ param.description }}</span>
            </el-form-item>
          </el-form>
        </div>

        <!-- Advanced Mode: Manual JSON input -->
        <div v-else class="advanced-mode">
          <el-input
            v-model="jsonParams"
            type="textarea"
            :rows="6"
            :placeholder="getJsonPlaceholder()"
            class="json-input"
            @blur="validateJson"
          />
          <div class="json-hint">
            <span class="hint-icon">💡</span>
            <span>Enter parameters as JSON object, e.g. <code>{"brightness": 50, "power": true}</code></span>
          </div>
          <div v-if="jsonError" class="json-error">{{ jsonError }}</div>
        </div>
      </div>

      <el-table :data="deviceStore.commands" style="width: 100%">
        <el-table-column prop="command_id" label="Command ID" width="250">
          <template #default="{ row }">
            <el-tooltip :content="row.command_id" placement="top">
              <span>{{ row.command_id.substring(0, 30) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="service_identifier" :label="$t('commands.selectService')" />
        <el-table-column prop="parameters" :label="$t('commands.parameters')">
          <template #default="{ row }">
            {{ JSON.stringify(row.parameters) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('commands.status')" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('commands.issuedAt')" width="180">
          <template #default="{ row }">
            {{ formatTime(row.issued_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('commands.executedAt')" width="180">
          <template #default="{ row }">
            {{ formatTime(row.executed_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { useProductStore } from '../stores/product.js'
import { ElMessage } from 'element-plus'

const deviceStore = useDeviceStore()
const productStore = useProductStore()

const sending = ref(false)
const services = ref([])
const currentServiceParams = ref([])
const advancedMode = ref(false)
const jsonParams = ref('')
const jsonError = ref('')

const commandForm = reactive({
  device_id: null,
  service_identifier: ''
})

const paramForm = reactive({})

function getJsonPlaceholder() {
  const params = {}
  currentServiceParams.value.forEach(p => {
    if (p.type === 'string') params[p.name] = p.default || ''
    else if (p.type === 'int' || p.type === 'float') params[p.name] = p.default !== '' ? Number(p.default) : 0
    else if (p.type === 'bool') params[p.name] = p.default === 'true' || p.default === true
  })
  return JSON.stringify(params, null, 2)
}

function validateJson() {
  if (!jsonParams.value.trim()) {
    jsonError.value = ''
    return true
  }
  try {
    JSON.parse(jsonParams.value)
    jsonError.value = ''
    return true
  } catch (e) {
    jsonError.value = 'Invalid JSON format: ' + e.message
    return false
  }
}

function switchMode() {
  advancedMode.value = !advancedMode.value
  if (advancedMode.value) {
    // Sync form values to JSON before switching
    const params = {}
    Object.keys(paramForm).forEach(key => {
      if (paramForm[key] !== undefined && paramForm[key] !== '') {
        params[key] = paramForm[key]
      }
    })
    jsonParams.value = JSON.stringify(params, null, 2)
  } else {
    // Sync JSON to form values before switching back
    if (jsonParams.value.trim()) {
      try {
        const parsed = JSON.parse(jsonParams.value)
        Object.assign(paramForm, parsed)
      } catch (e) {
        // Ignore parse errors, keep current form values
      }
    }
  }
}

const canSend = computed(() => {
  return commandForm.device_id && commandForm.service_identifier
})

function getStatusType(status) {
  const types = { pending: 'warning', executing: '', executed: 'success', failed: 'danger' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { pending: 'Pending', executing: 'Executing', executed: 'Executed', failed: 'Failed' }
  return texts[status] || status
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

async function loadServices() {
  if (!commandForm.device_id) {
    services.value = []
    currentServiceParams.value = []
    commandForm.service_identifier = ''
    Object.keys(paramForm).forEach(k => delete paramForm[k])
    return
  }
  try {
    const device = deviceStore.devices.find(d => d.id === commandForm.device_id)
    if (device) {
      const products = await productStore.fetchProducts()
      const product = products.find(p => p.id === device.product_id)
      if (product) {
        const productDetail = await productStore.fetchProduct(product.product_key)
        services.value = productDetail.services || []
      }
    }
  } catch (error) {
    ElMessage.error('Failed to load services')
  }
}

function loadServiceParams() {
  currentServiceParams.value = []
  Object.keys(paramForm).forEach(k => delete paramForm[k])
  advancedMode.value = false
  jsonParams.value = ''
  jsonError.value = ''
  
  if (!commandForm.service_identifier) return
  
  const service = services.value.find(s => s.identifier === commandForm.service_identifier)
  if (!service || !service.input_params) return
  
  // Support both formats: Array of param objects (new) or Dict (legacy)
  if (Array.isArray(service.input_params)) {
    // New format: [{name, type, required, default, description}, ...]
    currentServiceParams.value = service.input_params
    service.input_params.forEach(param => {
      if (param.default !== undefined && param.default !== '') {
        paramForm[param.name] = param.type === 'bool' ? (param.default === true || param.default === 'true') : param.default
      } else {
        paramForm[param.name] = param.type === 'bool' ? false : ''
      }
    })
  } else if (typeof service.input_params === 'object') {
    // Legacy format: {"key": {type, description, ...}}
    const params = []
    Object.keys(service.input_params).forEach(key => {
      const def = service.input_params[key]
      const param = {
        name: key,
        type: typeof def === 'object' && def.type ? def.type : 'string',
        required: false,
        default: typeof def === 'object' && def.default !== undefined ? def.default : '',
        description: typeof def === 'object' && def.description ? def.description : key
      }
      params.push(param)
      paramForm[param.name] = param.type === 'bool' ? false : ''
    })
    currentServiceParams.value = params
  }
}

async function sendCommand() {
  if (!canSend.value) return
  
  let params = {}
  
  if (advancedMode.value || currentServiceParams.value.length === 0) {
    // JSON mode or no defined params - use JSON input
    if (!jsonParams.value.trim()) {
      // Empty JSON is allowed, just send empty params
      params = {}
    } else {
      if (!validateJson()) {
        ElMessage.error('Please fix JSON format errors')
        return
      }
      try {
        params = JSON.parse(jsonParams.value)
      } catch (e) {
        ElMessage.error('Invalid JSON: ' + e.message)
        return
      }
    }
  } else {
    // Form mode with defined params - validate required fields
    for (const param of currentServiceParams.value) {
      if (param.required && (paramForm[param.name] === undefined || paramForm[param.name] === '' || paramForm[param.name] === null)) {
        ElMessage.error(`${param.name} is required`)
        return
      }
    }
    // Build params from form
    Object.keys(paramForm).forEach(key => {
      if (paramForm[key] !== undefined && paramForm[key] !== '') {
        params[key] = paramForm[key]
      }
    })
  }
  
  sending.value = true
  try {
    await deviceStore.createCommand({
      device_id: commandForm.device_id,
      service_identifier: commandForm.service_identifier,
      input_params: params
    })
    ElMessage.success('Command sent')
  } catch (error) {
    ElMessage.error('Failed to send command')
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  loadDevices()
  deviceStore.fetchCommands()
})
</script>

<style scoped>
.command-form {
  margin-bottom: 20px;
}

.params-section {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.params-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.params-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.params-form-container {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}

.params-form {
  max-width: 600px;
}

.params-form .el-form-item {
  margin-bottom: 12px;
}

.param-desc {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}

.advanced-mode {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}

.json-input {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.json-hint {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.json-hint .hint-icon {
  margin-right: 4px;
}

.json-hint code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.json-error {
  margin-top: 8px;
  color: #f56c6c;
  font-size: 12px;
}
</style>
