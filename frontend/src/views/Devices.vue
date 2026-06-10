<template>
  <div class="devices-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('devices.title') }}</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            {{ $t('devices.addDevice') }}
          </el-button>
        </div>
      </template>

      <el-table :data="deviceStore.devices" style="width: 100%" v-loading="loading">
        <el-table-column prop="device_key" :label="$t('devices.deviceKey')" width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.device_key" placement="top">
              <span>{{ row.device_key.substring(0, 20) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="device_name" :label="$t('devices.deviceName')" />
        <el-table-column prop="product_id" :label="$t('devices.product')" />
        <el-table-column :label="$t('devices.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('devices.lastSeen')" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_seen) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="300">
          <template #default="{ row }">
            <el-button size="small" @click="copySecret(row.device_secret)">{{ $t('devices.copySecret') }}</el-button>
            <el-button size="small" @click="handleRegenerateSecret(row)">{{ $t('devices.regenerateSecret') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="$t('devices.addDevice')" width="500px">
      <el-form :model="deviceForm" label-width="120px">
        <el-form-item :label="$t('devices.deviceName')">
          <el-input v-model="deviceForm.device_name" />
        </el-form-item>
        <el-form-item :label="$t('devices.product')">
          <el-select v-model="deviceForm.product_id" placeholder="Select product">
            <el-option v-for="p in productStore.products" :key="p.id" :label="p.name" :value="p.id" />
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
import { useProductStore } from '../stores/product.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const deviceStore = useDeviceStore()
const productStore = useProductStore()

const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)

const deviceForm = reactive({
  device_name: '',
  product_id: null
})

function getStatusType(status) {
  const types = { online: 'success', offline: 'info', error: 'danger' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { online: 'Online', offline: 'Offline', error: 'Error' }
  return texts[status] || status
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

async function loadDevices() {
  loading.value = true
  try {
    await Promise.all([
      deviceStore.fetchDevices(),
      productStore.fetchProducts()
    ])
  } catch (error) {
    ElMessage.error('Failed to load devices')
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  saving.value = true
  try {
    const device = await deviceStore.createDevice(deviceForm)
    ElMessage.success('Device created')
    ElMessage.info(`Device Secret: ${device.device_secret} (Save it!)`)
    showAddDialog.value = false
    deviceForm.device_name = ''
    deviceForm.product_id = null
    await loadDevices()
  } catch (error) {
    ElMessage.error('Failed to create device')
  } finally {
    saving.value = false
  }
}

async function handleRegenerateSecret(device) {
  try {
    await ElMessageBox.confirm('Regenerate device secret?', 'Warning', { type: 'warning' })
    const updated = await deviceStore.regenerateSecret(device.id)
    ElMessage.success('Secret regenerated')
    ElMessage.info(`New Secret: ${updated.device_secret}`)
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('Failed to regenerate secret')
  }
}

async function handleDelete(device) {
  try {
    await ElMessageBox.confirm('Delete this device?', 'Warning', { type: 'warning' })
    await deviceStore.deleteDevice(device.id)
    ElMessage.success('Device deleted')
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('Failed to delete device')
  }
}

function copySecret(secret) {
  navigator.clipboard.writeText(secret)
  ElMessage.success('Secret copied')
}

onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
