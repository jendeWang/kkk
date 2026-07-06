<template>
  <div class="devices-page">
    <el-row :gutter="16" class="mb-4">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-icon">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ statusSummary.total }}</div>
            <div class="stats-label">总设备</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card online">
          <div class="stats-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ statusSummary.online }}</div>
            <div class="stats-label">在线</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card offline">
          <div class="stats-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ statusSummary.offline }}</div>
            <div class="stats-label">离线</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card error">
          <div class="stats-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ statusSummary.error }}</div>
            <div class="stats-label">异常</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('devices.title') }}</span>
          <div class="header-actions">
            <el-button-group v-if="selectedIds.length > 0">
              <el-button size="small" type="primary" @click="showBatchCommandDialog = true">
                <el-icon><Setting /></el-icon>
                批量命令
              </el-button>
              <el-button size="small" @click="showBatchUpdateDialog = true">
                <el-icon><Edit /></el-icon>
                批量修改
              </el-button>
              <el-button size="small" type="danger" @click="handleBatchDelete">
                <el-icon><Delete /></el-icon>
                批量删除
              </el-button>
            </el-button-group>
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              {{ $t('devices.addDevice') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="search-bar mb-4">
        <el-input v-model="searchKeyword" placeholder="搜索设备名称或设备密钥" prefix-icon="Search" style="width: 300px" @keyup.enter="handleSearch" />
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px; margin-left: 10px">
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
          <el-option label="异常" value="error" />
        </el-select>
        <el-select v-model="filterProduct" placeholder="产品筛选" clearable style="width: 150px; margin-left: 10px">
          <el-option v-for="p in productStore.products" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button @click="handleSearch">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>

      <el-table :data="filteredDevices" style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="device_name" :label="$t('devices.deviceName')" min-width="150" />
        <el-table-column prop="device_key" :label="$t('devices.deviceKey')" width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.device_key" placement="top">
              <span>{{ row.device_key.substring(0, 16) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('devices.product')" width="120">
          <template #default="{ row }">
            {{ getProductName(row.product_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('devices.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('devices.lastSeen')" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_seen) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="copySecret(row.device_secret)">复制密钥</el-button>
            <el-button size="small" @click="handleRegenerateSecret(row)">重新生成</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > 0"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
        style="margin-top: 20px; text-align: right"
      />
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

    <el-dialog v-model="showBatchCommandDialog" title="批量发送命令" width="500px">
      <el-form :model="batchCommandForm" label-width="120px">
        <el-form-item label="命令类型">
          <el-select v-model="batchCommandForm.service_identifier" placeholder="选择命令类型">
            <el-option label="设置风扇" value="set_fan" />
            <el-option label="设置灯光" value="set_light" />
            <el-option label="设置水泵" value="set_pump" />
            <el-option label="设置模式" value="set_mode" />
          </el-select>
        </el-form-item>
        <el-form-item label="参数">
          <el-input v-model="batchCommandForm.input_params_json" type="textarea" placeholder='{"status": true}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchCommandDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchCommand" :loading="batchCommandLoading">发送</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showBatchUpdateDialog" title="批量修改设备" width="500px">
      <el-form :model="batchUpdateForm" label-width="120px">
        <el-form-item label="设备名称">
          <el-input v-model="batchUpdateForm.device_name" placeholder="新的设备名称（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchUpdateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchUpdate" :loading="batchUpdateLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useDeviceStore } from '../stores/device.js'
import { useProductStore } from '../stores/product.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { groupService } from '../services/group.js'
import { Monitor, CircleCheck, Clock, Warning, Plus, Setting, Edit, Delete, Search } from '@element-plus/icons-vue'

const deviceStore = useDeviceStore()
const productStore = useProductStore()

const loading = ref(false)
const saving = ref(false)
const batchCommandLoading = ref(false)
const batchUpdateLoading = ref(false)

const showAddDialog = ref(false)
const showBatchCommandDialog = ref(false)
const showBatchUpdateDialog = ref(false)

const groups = ref([])
const selectedIds = ref([])

const searchKeyword = ref('')
const filterStatus = ref('')
const filterProduct = ref(null)

const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const statusSummary = ref({ total: 0, online: 0, offline: 0, error: 0 })

const deviceForm = reactive({
  device_name: '',
  product_id: null,
  group_id: null
})

const batchCommandForm = reactive({
  service_identifier: '',
  input_params_json: '{"status": true}'
})

const batchUpdateForm = reactive({
  device_name: ''
})

const filteredDevices = computed(() => {
  let result = deviceStore.devices
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(d => 
      d.device_name.toLowerCase().includes(keyword) || 
      d.device_key.toLowerCase().includes(keyword)
    )
  }
  
  if (filterStatus.value) {
    result = result.filter(d => d.status === filterStatus.value)
  }
  
  if (filterProduct.value) {
    result = result.filter(d => d.product_id === filterProduct.value)
  }
  
  total.value = result.length
  return result
})

async function loadGroups() {
  try {
    groups.value = await groupService.getGroups()
  } catch (e) {
    console.error('Failed to load groups:', e)
  }
}

async function loadStatusSummary() {
  try {
    statusSummary.value = await deviceStore.getDeviceStatusSummary()
  } catch (e) {
    console.error('Failed to load status summary:', e)
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
      productStore.fetchProducts(),
      loadStatusSummary()
    ])
  } catch (error) {
    ElMessage.error('加载设备列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
}

function resetFilters() {
  searchKeyword.value = ''
  filterStatus.value = ''
  filterProduct.value = null
  currentPage.value = 1
}

function handlePageChange(page) {
  currentPage.value = page
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
}

async function handleAdd() {
  saving.value = true
  try {
    const device = await deviceStore.createDevice(deviceForm)
    
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
    await ElMessageBox.confirm('确定要重新生成设备密钥吗？', '警告', { type: 'warning' })
    const updated = await deviceStore.regenerateSecret(device.id)
    ElMessage.success('密钥已重新生成')
    ElMessage.info(`新密钥: ${updated.device_secret}`)
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('重新生成密钥失败')
  }
}

async function handleDelete(device) {
  try {
    await ElMessageBox.confirm('确定要删除此设备吗？', '警告', { type: 'warning' })
    await deviceStore.deleteDevice(device.id)
    ElMessage.success('设备已删除')
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除设备失败')
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个设备吗？`, '警告', { type: 'warning' })
    await deviceStore.batchDeleteDevices(selectedIds.value)
    ElMessage.success(`已删除 ${selectedIds.value.length} 个设备`)
    selectedIds.value = []
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('批量删除失败')
  }
}

async function handleBatchCommand() {
  if (!batchCommandForm.service_identifier) {
    ElMessage.warning('请选择命令类型')
    return
  }
  
  let inputParams
  try {
    inputParams = JSON.parse(batchCommandForm.input_params_json)
  } catch (e) {
    ElMessage.error('参数格式不正确，请输入有效的JSON')
    return
  }
  
  batchCommandLoading.value = true
  try {
    const result = await deviceStore.batchSendCommands(selectedIds.value, {
      service_identifier: batchCommandForm.service_identifier,
      input_params: inputParams
    })
    ElMessage.success(`成功发送 ${result.sent} 条命令，失败 ${result.failed} 条`)
    showBatchCommandDialog.value = false
    selectedIds.value = []
    await loadDevices()
  } catch (error) {
    ElMessage.error('批量发送命令失败')
  } finally {
    batchCommandLoading.value = false
  }
}

async function handleBatchUpdate() {
  if (!batchUpdateForm.device_name.trim()) {
    ElMessage.warning('请输入设备名称')
    return
  }
  
  batchUpdateLoading.value = true
  try {
    await deviceStore.batchUpdateDevices(selectedIds.value, { device_name: batchUpdateForm.device_name })
    ElMessage.success(`已更新 ${selectedIds.value.length} 个设备`)
    showBatchUpdateDialog.value = false
    selectedIds.value = []
    await loadDevices()
  } catch (error) {
    ElMessage.error('批量更新失败')
  } finally {
    batchUpdateLoading.value = false
  }
}

function copySecret(secret) {
  navigator.clipboard.writeText(secret)
  ElMessage.success('密钥已复制')
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-bar {
  display: flex;
  align-items: center;
}

.stats-card {
  display: flex;
  align-items: center;
  padding: 15px;
}

.stats-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #606266;
  background: #f5f7fa;
  margin-right: 15px;
}

.stats-card.online .stats-icon {
  background: #f0f9eb;
  color: #67c23a;
}

.stats-card.offline .stats-icon {
  background: #ecf5ff;
  color: #409eff;
}

.stats-card.error .stats-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.stats-info {
  flex: 1;
}

.stats-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stats-label {
  font-size: 12px;
  color: #909399;
}
</style>