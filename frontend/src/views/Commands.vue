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

      <div v-if="currentServiceParams.length > 0" class="params-section">
        <h4>Input Parameters</h4>
        <el-form :model="paramForm" label-width="120px" class="params-form">
          <el-form-item v-for="param in currentServiceParams" :key="param.name" :label="param.name" :required="param.required">
            <el-input v-if="param.type === 'string'" v-model="paramForm[param.name]" :placeholder="`Enter ${param.name}`" />
            <el-input v-else-if="param.type === 'int'" type="number" v-model.number="paramForm[param.name]" :placeholder="`Enter ${param.name}`" />
            <el-input v-else-if="param.type === 'float'" type="number" step="0.1" v-model.number="paramForm[param.name]" :placeholder="`Enter ${param.name}`" />
            <el-switch v-else-if="param.type === 'bool'" v-model="paramForm[param.name]" />
          </el-form-item>
        </el-form>
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

const commandForm = reactive({
  device_id: null,
  service_identifier: ''
})

const paramForm = reactive({})

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
  
  if (!commandForm.service_identifier) return
  
  const service = services.value.find(s => s.identifier === commandForm.service_identifier)
  if (service && service.input_params && Array.isArray(service.input_params)) {
    currentServiceParams.value = service.input_params
    service.input_params.forEach(param => {
      if (param.default !== undefined) {
        paramForm[param.name] = param.default
      } else {
        paramForm[param.name] = param.type === 'bool' ? false : ''
      }
    })
  }
}

async function sendCommand() {
  if (!canSend.value) return
  
  for (const param of currentServiceParams.value) {
    if (param.required && (paramForm[param.name] === undefined || paramForm[param.name] === '' || paramForm[param.name] === null)) {
      ElMessage.error(`${param.name} is required`)
      return
    }
  }
  
  sending.value = true
  try {
    const params = {}
    Object.keys(paramForm).forEach(key => {
      if (paramForm[key] !== undefined && paramForm[key] !== '') {
        params[key] = paramForm[key]
      }
    })
    
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
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}

.params-section h4 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
}

.params-form {
  max-width: 600px;
}

.params-form .el-form-item {
  margin-bottom: 12px;
}
</style>
