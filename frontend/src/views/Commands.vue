<template>
  <div class="commands-page">
    <el-card>
      <template #header>
        <span>{{ $t('commands.title') }}</span>
      </template>

      <el-form :inline="true" :model="commandForm" class="command-form">
        <el-form-item :label="$t('commands.selectDevice')">
          <el-select v-model="commandForm.device_id" @change="loadServices" :placeholder="$t('commands.selectDevice')" style="width: 200px">
            <el-option v-for="d in deviceStore.devices" :key="d.id" :label="d.device_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('commands.selectService')">
          <el-select v-model="commandForm.service_identifier" @change="loadServiceParams" :placeholder="$t('commands.selectService')" style="width: 200px" :disabled="!services.length">
            <el-option v-for="s in services" :key="s.identifier" :label="s.name" :value="s.identifier" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="sendCommand" :loading="sending" :disabled="!canSend">{{ $t('commands.sendCommand') }}</el-button>
        </el-form-item>
      </el-form>

      <div v-if="commandForm.service_identifier" class="params-section">
        <div class="params-header">
          <h4>{{ $t('commands.inputParams') }}</h4>
          <div v-if="currentServiceParams.length > 0">
            <el-button size="small" @click="switchMode">
              {{ advancedMode ? $t('commands.switchToFormMode') : $t('commands.switchToAdvancedMode') }}
            </el-button>
          </div>
        </div>

        <!-- Form Mode: Auto-generated inputs from service definition -->
        <div v-if="!advancedMode && currentServiceParams.length > 0" class="params-form-container">
          <el-form :model="paramForm" label-width="120px" class="params-form">
            <el-form-item
              v-for="param in currentServiceParams"
              :key="param.name"
              :label="param.name"
              :required="param.required"
            >
              <!-- Boolean -->
              <el-switch
                v-if="param.type === 'bool'"
                v-model="paramForm[param.name]"
              />

              <!-- String: with options or plain input -->
              <template v-else-if="param.type === 'string'">
                <el-select
                  v-if="hasValidOptions(param)"
                  v-model="paramForm[param.name]"
                  :filterable="true"
                  :allow-create="allowCustomInput(param)"
                  default-first-option
                  placeholder="Select or enter a value"
                  style="width: 300px"
                >
                  <el-option
                    v-for="opt in param.options"
                    :key="opt"
                    :value="String(opt)"
                    :label="String(opt)"
                  />
                </el-select>
                <el-input
                  v-else
                  v-model="paramForm[param.name]"
                  :placeholder="param.description || 'Enter string value'"
                  style="width: 300px"
                />
              </template>

              <!-- Integer/Float: with options or input-number -->
              <template v-else-if="param.type === 'int' || param.type === 'float'">
                <el-select
                  v-if="hasValidOptions(param) && !allowCustomInput(param)"
                  v-model="paramForm[param.name]"
                  placeholder="Select a value"
                  style="width: 300px"
                >
                  <el-option
                    v-for="opt in param.options"
                    :key="opt"
                    :value="Number(opt)"
                    :label="String(opt)"
                  />
                </el-select>
                <el-input-number
                  v-else
                  v-model="paramForm[param.name]"
                  :min="getSafeMin(param)"
                  :max="getSafeMax(param)"
                  :step="getSafeStep(param)"
                  :step-strictly="false"
                  :controls="true"
                  :placeholder="param.description || 'Enter a number'"
                />
              </template>

              <!-- Fallback -->
              <el-input
                v-else
                v-model="paramForm[param.name]"
                :placeholder="param.description || 'Enter value'"
                style="width: 300px"
              />

              <span v-if="param.description" class="param-desc">{{ param.description }}</span>
              <div v-if="getParamHint(param)" class="param-hint">{{ getParamHint(param) }}</div>
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
        <el-table-column prop="command_id" :label="$t('commands.commandId')" width="250">
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

const paramForm = ref({})

function hasValidOptions(param) {
  return Array.isArray(param.options) && param.options.length > 0
}

function allowCustomInput(param) {
  return param.allow_custom !== false
}

function getSafeMin(param) {
  if (param.min === '' || param.min === null || param.min === undefined) return undefined
  const v = Number(param.min)
  return isNaN(v) ? undefined : v
}

function getSafeMax(param) {
  if (param.max === '' || param.max === null || param.max === undefined) return undefined
  const v = Number(param.max)
  return isNaN(v) ? undefined : v
}

function getSafeStep(param) {
  if (param.step !== '' && param.step !== null && param.step !== undefined) {
    const v = Number(param.step)
    if (!isNaN(v)) return v
  }
  return param.type === 'int' ? 1 : 0.01
}

function getParamHint(param) {
  const hints = []
  if (param.type === 'int' || param.type === 'float') {
    const mn = getSafeMin(param)
    const mx = getSafeMax(param)
    if (mn !== undefined) hints.push(`min: ${mn}`)
    if (mx !== undefined) hints.push(`max: ${mx}`)
  }
  if (param.type === 'string' && param.pattern) {
    hints.push(`pattern: ${param.pattern}`)
  }
  return hints.length > 0 ? hints.join(' | ') : ''
}

function getJsonPlaceholder() {
  const params = {}
  currentServiceParams.value.forEach(p => {
    if (p.type === 'string') params[p.name] = p.default !== undefined && p.default !== '' ? String(p.default) : ''
    else if (p.type === 'int' || p.type === 'float') params[p.name] = p.default !== '' && p.default !== undefined ? Number(p.default) : 0
    else if (p.type === 'bool') params[p.name] = p.default === true || p.default === 'true'
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
    const params = {}
    Object.keys(paramForm.value).forEach(key => {
      if (paramForm.value[key] !== undefined && paramForm.value[key] !== '') {
        params[key] = paramForm.value[key]
      }
    })
    jsonParams.value = JSON.stringify(params, null, 2)
  } else {
    if (jsonParams.value.trim()) {
      try {
        const parsed = JSON.parse(jsonParams.value)
        paramForm.value = { ...parsed }
      } catch (e) {
        // Ignore parse errors
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
  const texts = { 
    pending: $t('commands.pending'), 
    executing: $t('commands.executing'), 
    executed: $t('commands.executed'), 
    failed: $t('commands.failed'),
    sent: $t('commands.sent')
  }
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
    paramForm.value = {}
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

function parseDefaultValue(param) {
  if (param.type === 'bool') {
    if (param.default === true || param.default === 'true') return true
    if (param.default === false || param.default === 'false') return false
    return false
  }
  if (param.type === 'int' || param.type === 'float') {
    if (param.default === '' || param.default === null || param.default === undefined) return ''
    const v = Number(param.default)
    return isNaN(v) ? '' : v
  }
  return param.default !== undefined && param.default !== null ? String(param.default) : ''
}

function loadServiceParams() {
  currentServiceParams.value = []
  paramForm.value = {}
  advancedMode.value = false
  jsonParams.value = ''
  jsonError.value = ''

  if (!commandForm.service_identifier) return

  const service = services.value.find(s => s.identifier === commandForm.service_identifier)
  if (!service || !service.input_params) return

  const formData = {}

  // Support both formats: Array of param objects (new) or Dict (legacy)
  if (Array.isArray(service.input_params)) {
    currentServiceParams.value = service.input_params
    service.input_params.forEach(param => {
      formData[param.name] = parseDefaultValue(param)
    })
  } else if (typeof service.input_params === 'object') {
    const params = []
    Object.keys(service.input_params).forEach(key => {
      const def = service.input_params[key]
      const param = {
        name: key,
        type: typeof def === 'object' && def.type ? def.type : 'string',
        required: false,
        default: typeof def === 'object' && def.default !== undefined ? def.default : '',
        description: typeof def === 'object' && def.description ? def.description : key,
        options: Array.isArray(def.options) ? def.options : [],
        allow_custom: def.allow_custom !== false,
        min: def.min,
        max: def.max,
        step: def.step,
        pattern: def.pattern
      }
      params.push(param)
      formData[param.name] = parseDefaultValue(param)
    })
    currentServiceParams.value = params
  }

  paramForm.value = formData
}

function validateParam(param, value) {
  if (param.required && (value === '' || value === undefined || value === null)) {
    ElMessage.error(`${param.name} is required`)
    return false
  }

  if (value === '' || value === undefined || value === null) return true

  if (param.type === 'int' || param.type === 'float') {
    const num = Number(value)
    if (isNaN(num)) {
      ElMessage.error(`${param.name} must be a number`)
      return false
    }
    const mn = getSafeMin(param)
    const mx = getSafeMax(param)
    if (mn !== undefined && num < mn) {
      ElMessage.error(`${param.name} must be >= ${mn}`)
      return false
    }
    if (mx !== undefined && num > mx) {
      ElMessage.error(`${param.name} must be <= ${mx}`)
      return false
    }
    if (hasValidOptions(param) && !allowCustomInput(param)) {
      const matched = param.options.some(opt => Number(opt) === num || String(opt) === String(value))
      if (!matched) {
        ElMessage.error(`${param.name} must be one of: ${param.options.join(', ')}`)
        return false
      }
    }
  }

  if (param.type === 'string') {
    if (hasValidOptions(param) && !allowCustomInput(param)) {
      if (!param.options.includes(value)) {
        ElMessage.error(`${param.name} must be one of: ${param.options.join(', ')}`)
        return false
      }
    }
    if (param.pattern) {
      try {
        const regex = new RegExp(param.pattern)
        if (!regex.test(String(value))) {
          ElMessage.error(`${param.name} does not match pattern: ${param.pattern}`)
          return false
        }
      } catch (e) {
        // Invalid regex, skip validation
      }
    }
  }

  return true
}

async function sendCommand() {
  if (!canSend.value) return

  let params = {}

  if (advancedMode.value || currentServiceParams.value.length === 0) {
    if (!jsonParams.value.trim()) {
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
    for (const param of currentServiceParams.value) {
      const value = paramForm.value[param.name]
      if (!validateParam(param, value)) return
    }
    Object.keys(paramForm.value).forEach(key => {
      if (paramForm.value[key] !== undefined && paramForm.value[key] !== '') {
        params[key] = paramForm.value[key]
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

.param-hint {
  margin-top: 4px;
  margin-left: 0;
  color: #909399;
  font-size: 12px;
  font-family: monospace;
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
