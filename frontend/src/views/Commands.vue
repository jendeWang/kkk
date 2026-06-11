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
          <el-select v-model="commandForm.service_identifier" placeholder="Select service" style="width: 200px" :disabled="!services.length">
            <el-option v-for="s in services" :key="s.identifier" :label="s.name" :value="s.identifier" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('commands.parameters')">
          <el-input v-model="commandForm.input_params" placeholder='{"key": "value"}' style="width: 250px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="sendCommand" :loading="sending" :disabled="!canSend">{{ $t('commands.sendCommand') }}</el-button>
        </el-form-item>
      </el-form>

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

const commandForm = reactive({
  device_id: null,
  service_identifier: '',
  input_params: '{}'
})

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
    return
  }
  try {
    const device = deviceStore.devices.find(d => d.id === commandForm.device_id)
    if (device) {
      const product = await productStore.fetchProduct(device.product_id)
      services.value = product.services || []
    }
  } catch (error) {
    ElMessage.error('Failed to load services')
  }
}

async function sendCommand() {
  if (!canSend.value) return
  sending.value = true
  try {
    let params = {}
    try {
      params = JSON.parse(commandForm.input_params)
    } catch (e) {
      params = {}
    }
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
</style>
