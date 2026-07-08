<template>
  <div class="operation-logs-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>操作日志</span>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="操作类型">
          <el-select v-model="queryForm.action" clearable placeholder="全部" style="width: 150px">
            <el-option label="登录" value="login" />
            <el-option label="登出" value="logout" />
            <el-option label="创建设备" value="create_device" />
            <el-option label="删除设备" value="delete_device" />
            <el-option label="创建产品" value="create_product" />
            <el-option label="删除产品" value="delete_product" />
            <el-option label="命令下发" value="send_command" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" clearable placeholder="全部" style="width: 120px">
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadLogs">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="logs" style="width: 100%" v-loading="loading">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)" size="small">
              {{ getActionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="操作描述" min-width="200" />
        <el-table-column prop="resource_type" label="资源类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="140" />
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadLogs"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api.js'

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const queryForm = reactive({
  action: '',
  status: '',
})

function formatTime(time) {
  if (!time) return '--'
  const d = new Date(time)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getActionLabel(action) {
  const labels = {
    login: '登录',
    logout: '登出',
    create_device: '创建设备',
    delete_device: '删除设备',
    create_product: '创建产品',
    delete_product: '删除产品',
    send_command: '命令下发',
    create_alert_rule: '创建告警规则',
    delete_alert_rule: '删除告警规则',
    create_scene: '创建场景',
    delete_scene: '删除场景',
  }
  return labels[action] || action
}

function getActionTagType(action) {
  if (action?.includes('create') || action === 'login') return 'success'
  if (action?.includes('delete')) return 'danger'
  if (action?.includes('update')) return 'warning'
  return 'info'
}

async function loadLogs() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (queryForm.action) params.action = queryForm.action
    if (queryForm.status) params.status = queryForm.status

    const resp = await api.get('/operation-logs/', { params })
    logs.value = resp.data.items || []
    total.value = resp.data.total || 0
  } catch (e) {
    ElMessage.error('加载操作日志失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  queryForm.action = ''
  queryForm.status = ''
  currentPage.value = 1
  loadLogs()
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.query-form {
  margin-bottom: 16px;
}

.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
