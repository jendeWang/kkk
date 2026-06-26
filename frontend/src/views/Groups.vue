<template>
  <div class="groups-page">
    <div class="page-header">
      <h2 class="page-title">设备分组</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新建分组
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <el-card class="stat-card">
        <div class="stat-inner">
          <div class="stat-icon-wrap stat-blue">
            <el-icon :size="28"><Folder /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">分组总数</div>
            <div class="stat-value">{{ groups.length }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-inner">
          <div class="stat-icon-wrap stat-green">
            <el-icon :size="28"><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">设备总数</div>
            <div class="stat-value">{{ totalDevices }}</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-inner">
          <div class="stat-icon-wrap stat-orange">
            <el-icon :size="28"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">在线设备</div>
            <div class="stat-value">{{ onlineDevices }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 主内容区 -->
    <el-row :gutter="20">
      <!-- 分组列表 -->
      <el-col :span="8">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">🏷️ 我的分组</span>
            </div>
          </template>

          <div v-if="groups.length === 0" class="empty-state">
            <el-icon :size="64" color="#dcdfe6"><FolderOpened /></el-icon>
            <p>还没有创建任何分组</p>
            <p class="tip">点击右上角"新建分组"开始</p>
          </div>

          <div v-else class="group-list">
            <div
              v-for="group in groups"
              :key="group.id"
              class="group-card"
              :class="{ active: selectedGroup?.id === group.id }"
              @click="selectGroup(group)"
            >
              <div class="group-header">
                <span class="group-icon">🏠</span>
                <div class="group-info">
                  <span class="group-name">{{ group.name }}</span>
                  <span class="group-count">{{ group.device_count || 0 }} 个设备</span>
                </div>
                <el-tag size="small" type="info">{{ formatDate(group.created_at) }}</el-tag>
              </div>
              <div class="group-desc">{{ group.description || '暂无描述' }}</div>
              <div class="group-actions">
                <el-button size="small" @click.stop="editGroup(group)" circle>
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" @click.stop="deleteGroup(group)" type="danger" circle>
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 分组详情/设备列表 -->
      <el-col :span="16">
        <!-- 未选择分组 -->
        <el-card v-if="!selectedGroup" class="section-card">
          <div class="empty-state">
            <el-icon :size="64" color="#dcdfe6"><Pointer /></el-icon>
            <p>点击左侧分组查看设备</p>
            <p class="tip">或拖动设备到不同分组</p>
          </div>
        </el-card>

        <!-- 分组详情 -->
        <el-card v-else class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">🏠 {{ selectedGroup.name }}</span>
              <el-button size="small" type="primary" @click="showAddDeviceDialog = true">
                <el-icon><Plus /></el-icon>
                添加设备
              </el-button>
            </div>
          </template>

          <div class="group-detail">
            <div class="detail-info">
              <p>{{ selectedGroup.description || '暂无描述' }}</p>
              <p class="meta">共 {{ groupDevices.length }} 个设备，{{ onlineCount }} 个在线</p>
            </div>

            <el-divider content-position="left">分组内设备</el-divider>

            <div v-if="groupDevices.length === 0" class="empty-device">
              <p>该分组还没有设备</p>
              <el-button type="primary" @click="showAddDeviceDialog = true">
                <el-icon><Plus /></el-icon>
                添加设备
              </el-button>
            </div>

            <div v-else class="device-grid">
              <div
                v-for="device in groupDevices"
                :key="device.id"
                class="device-card"
                :class="{ offline: !device.is_online }"
              >
                <div class="device-status">
                  <span class="status-dot" :class="{ online: device.is_online }"></span>
                  <span class="status-text">{{ device.is_online ? '在线' : '离线' }}</span>
                </div>
                <div class="device-name">{{ device.device_name }}</div>
                <div class="device-product">{{ device.product_name || `产品ID: ${device.product_id}` }}</div>
                <div class="device-actions">
                  <el-button size="small" @click="removeFromGroup(device)" type="danger" plain>
                    移出分组
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 未分组设备 -->
        <el-card class="section-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">📦 未分组设备</span>
              <span class="tip-text">拖动设备到左侧分组，或点击添加</span>
            </div>
          </template>

          <div v-if="ungroupedDevices.length === 0" class="empty-device">
            <el-icon :size="32" color="#67c23a"><CircleCheck /></el-icon>
            <p>所有设备都已分配到分组</p>
          </div>

          <div v-else class="device-grid">
            <div
              v-for="device in ungroupedDevices"
              :key="device.id"
              class="device-card"
              :class="{ offline: !device.is_online }"
            >
              <div class="device-status">
                <span class="status-dot" :class="{ online: device.is_online }"></span>
                <span class="status-text">{{ device.is_online ? '在线' : '离线' }}</span>
              </div>
              <div class="device-name">{{ device.device_name }}</div>
              <div class="device-product">{{ device.product_name || `产品ID: ${device.product_id}` }}</div>
              <div class="device-actions">
                <el-dropdown @command="(cmd) => addToGroup(device, cmd)">
                  <el-button size="small" type="primary" plain>
                    添加到分组 <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-for="g in groups" :key="g.id" :command="g.id">
                        {{ g.name }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建/编辑分组对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingGroup ? '编辑分组' : '新建分组'"
      width="500px"
    >
      <el-form :model="groupForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="如：1号大棚、草莓种植区" />
        </el-form-item>
        <el-form-item label="分组描述" prop="description">
          <el-input
            v-model="groupForm.description"
            type="textarea"
            :rows="2"
            placeholder="简单描述这个分组"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingGroup ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加设备到分组对话框 -->
    <el-dialog v-model="showAddDeviceDialog" title="添加设备到分组" width="600px">
      <el-table
        :data="availableDevices"
        @selection-change="handleSelectionChange"
        style="width: 100%"
        max-height="400"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="device_name" label="设备名称" />
        <el-table-column prop="product_name" label="所属产品">
          <template #default="{ row }">
            {{ row.product_name || `产品ID: ${row.product_id}` }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_online ? 'success' : 'info'">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showAddDeviceDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddDevices" :loading="submitting">
          添加到 {{ selectedGroup?.name }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Folder, FolderOpened, Plus, Edit, Delete, Monitor, Clock,
  Pointer, CircleCheck, ArrowDown
} from '@element-plus/icons-vue'
import { groupService } from '../services/group.js'
import { useDeviceStore } from '../stores/device.js'
import api from '../services/api.js'

const deviceStore = useDeviceStore()

const groups = ref([])
const selectedGroup = ref(null)
const groupDevices = ref([])
const allDevices = ref([])
const showAddDialog = ref(false)
const showAddDeviceDialog = ref(false)
const editingGroup = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const selectedDevices = ref([])

const groupForm = reactive({
  name: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }]
}

const totalDevices = computed(() => allDevices.value.length)
const onlineDevices = computed(() => allDevices.value.filter(d => d.is_online).length)
const onlineCount = computed(() => groupDevices.value.filter(d => d.is_online).length)
const ungroupedDevices = computed(() => {
  const groupedIds = new Set(groupDevices.value.map(d => d.id))
  return allDevices.value.filter(d => !groupedIds.has(d.id))
})
const availableDevices = computed(() => {
  const inGroupIds = new Set(groupDevices.value.map(d => d.id))
  return allDevices.value.filter(d => !inGroupIds.has(d.id))
})

async function loadGroups() {
  try {
    groups.value = await groupService.getGroups()
  } catch (e) {
    console.error('Failed to load groups:', e)
  }
}

async function loadAllDevices() {
  try {
    const resp = await api.get('/devices/')
    allDevices.value = resp.data || []
  } catch (e) {
    console.error('Failed to load devices:', e)
  }
}

async function loadGroupDevices() {
  if (!selectedGroup.value) return
  try {
    groupDevices.value = await groupService.getGroupDevices(selectedGroup.value.id)
  } catch (e) {
    console.error('Failed to load group devices:', e)
  }
}

function selectGroup(group) {
  selectedGroup.value = group
  loadGroupDevices()
}

function editGroup(group) {
  editingGroup.value = group
  groupForm.name = group.name
  groupForm.description = group.description || ''
  showAddDialog.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = {
      name: groupForm.name,
      description: groupForm.description
    }

    if (editingGroup.value) {
      await groupService.updateGroup(editingGroup.value.id, data)
      ElMessage.success('分组已更新')
    } else {
      await groupService.createGroup(data)
      ElMessage.success('分组已创建')
    }

    showAddDialog.value = false
    editingGroup.value = null
    groupForm.name = ''
    groupForm.description = ''
    await loadGroups()

    if (selectedGroup.value) {
      const updated = groups.value.find(g => g.id === selectedGroup.value.id)
      if (updated) selectedGroup.value = updated
    }
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function deleteGroup(group) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分组"${group.name}"吗？分组内的设备不会被删除。`,
      '删除确认',
      { type: 'warning' }
    )
    await groupService.deleteGroup(group.id)
    ElMessage.success('分组已删除')
    if (selectedGroup.value?.id === group.id) {
      selectedGroup.value = null
      groupDevices.value = []
    }
    await loadGroups()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function handleSelectionChange(devices) {
  selectedDevices.value = devices
}

async function handleAddDevices() {
  if (!selectedGroup.value || selectedDevices.value.length === 0) {
    ElMessage.warning('请选择要添加的设备')
    return
  }

  try {
    const deviceIds = selectedDevices.value.map(d => d.id)
    await groupService.addDevicesToGroup(selectedGroup.value.id, deviceIds)
    ElMessage.success(`已添加 ${deviceIds.length} 个设备到 ${selectedGroup.value.name}`)
    showAddDeviceDialog.value = false
    selectedDevices.value = []
    await loadGroupDevices()
    await loadGroups()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function addToGroup(device, groupId) {
  const group = groups.value.find(g => g.id === groupId)
  if (!group) return

  try {
    await groupService.addDevicesToGroup(groupId, [device.id])
    ElMessage.success(`已将 ${device.device_name} 添加到 ${group.name}`)
    await loadGroupDevices()
    await loadGroups()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeFromGroup(device) {
  if (!selectedGroup.value) return

  try {
    await groupService.removeDevicesFromGroup(selectedGroup.value.id, [device.id])
    ElMessage.success(`已将 ${device.device_name} 移出分组`)
    await loadGroupDevices()
    await loadGroups()
  } catch (e) {
    ElMessage.error('移除失败')
  }
}

function formatDate(date) {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

onMounted(async () => {
  await Promise.all([loadGroups(), loadAllDevices()])
  if (groups.value.length > 0) {
    selectGroup(groups.value[0])
  }
})
</script>

<style scoped>
.groups-page {
  padding: 0;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  border: none;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-blue { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-green { background: linear-gradient(135deg, #11998e, #38ef7d); }
.stat-orange { background: linear-gradient(135deg, #f093fb, #f5576c); }

.stat-info { flex: 1; }

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
}

.section-card {
  border-radius: 12px;
  height: fit-content;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state p {
  margin: 10px 0 0;
}

.empty-state .tip {
  font-size: 12px;
  color: #c0c4cc;
}

.group-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-card {
  padding: 16px;
  border-radius: 10px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.group-card:hover {
  background: #f0f9eb;
}

.group-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.group-icon {
  font-size: 24px;
}

.group-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.group-name {
  font-weight: 600;
  color: #303133;
  font-size: 15px;
}

.group-count {
  font-size: 12px;
  color: #909399;
}

.group-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
}

.group-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.group-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-info {
  font-size: 14px;
  color: #606266;
}

.detail-info .meta {
  font-size: 13px;
  color: #909399;
  margin-top: 8px;
}

.empty-device {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px;
  color: #909399;
  gap: 10px;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.device-card {
  padding: 16px;
  border-radius: 10px;
  background: #fafafa;
  transition: all 0.3s;
  border: 1px solid #ebeef5;
}

.device-card:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.device-card.offline {
  opacity: 0.6;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #909399;
}

.status-dot.online {
  background: #67c23a;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 12px;
  color: #909399;
}

.device-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.device-product {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.device-actions {
  display: flex;
  gap: 8px;
}

.tip-text {
  font-size: 12px;
  color: #909399;
}
</style>
