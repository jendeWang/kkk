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
        <el-table-column :label="$t('devices.product')">
          <template #default="{ row }">
            {{ getProductName(row.product_id) }}
          </template>
        </el-table-column>
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
          <el-input v-model="deviceForm.device_name" placeholder="给设备起个名字" />
        </el-form-item>
        <el-form-item :label="$t('devices.product')">
          <el-select v-model="deviceForm.product_id" placeholder="选择产品">
            <el-option v-for="p in productStore.products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="归属分组">
          <el-select v-model="deviceForm.group_id" placeholder="选择设备归属的分组（可选）" clearable>
            <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
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
import { groupService } from '../services/group.js'

const deviceStore = useDeviceStore()
const productStore = useProductStore()

const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)
const groups = ref([])

const deviceForm = reactive({
  device_name: '',
  product_id: null,
  group_id: null
})

async function loadGroups() {
  try {
    groups.value = await groupService.getGroups()
  } catch (e) {
    console.error('Failed to load groups:', e)
  }
}

function getStatusType(status) {
  const types = { online: 'success', offline: 'info', error: 'danger' }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = { online: '在线', offline: '离线', error: '异常' }
  return texts[status] || status
}

function getProductName(product_id) {
  const product = productStore.products.find(p => p.id === product_id)
  return product ? product.name : `产品 #${product_id}`
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
    
    // 如果选择了分组，自动添加设备到分组
    if (deviceForm.group_id) {
      try {
        await groupService.addDevicesToGroup(deviceForm.group_id, [device.id])
        const group = groups.value.find(g => g.id === deviceForm.group_id)
        ElMessage.success(`设备已创建并添加到 ${group?.name || '分组'}`)
      } catch (e) {
        console.error('Failed to add device to group:', e)
        ElMessage.warning('设备已创建，但添加到分组失败，请手动添加')
      }
    } else {
      ElMessage.success('设备已创建')
    }
    
    ElMessage.info(`设备密钥: ${device.device_secret}（请妥善保管）`)
    showAddDialog.value = false
    deviceForm.device_name = ''
    deviceForm.product_id = null
    deviceForm.group_id = null
    await loadDevices()
  } catch (error) {
    ElMessage.error('创建设备失败')
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
  loadGroups()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
