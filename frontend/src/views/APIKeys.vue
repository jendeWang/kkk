<template>
  <div class="api-keys-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('apiKeys.title') }}</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            {{ $t('apiKeys.addKey') }}
          </el-button>
        </div>
      </template>

      <el-table :data="apiKeys" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" :label="$t('apiKeys.name')" />
        <el-table-column :label="$t('apiKeys.permission')" width="120">
          <template #default="{ row }">
            {{ getPermissionText(row.permission_level) }}
          </template>
        </el-table-column>
        <el-table-column prop="key" :label="$t('apiKeys.key')">
          <template #default="{ row }">
            <span class="key-display">{{ row.key.substring(0, 20) }}...</span>
            <el-button size="small" @click="copyKey(row.key)">{{ $t('apiKeys.copy') }}</el-button>
          </template>
        </el-table-column>
        <el-table-column :label="$t('apiKeys.lastUsed')" width="180">
          <template #default="{ row }">
            {{ row.last_used_at ? formatTime(row.last_used_at) : $t('apiKeys.never') }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="$t('apiKeys.addKey')" width="500px">
      <el-form :model="keyForm" label-width="100px">
        <el-form-item :label="$t('apiKeys.name')">
          <el-input v-model="keyForm.name" />
        </el-form-item>
        <el-form-item :label="$t('apiKeys.permission')">
          <el-select v-model="keyForm.permission_level">
            <el-option value="read" :label="$t('apiKeys.read')" />
            <el-option value="write" :label="$t('apiKeys.write')" />
            <el-option value="admin" :label="$t('apiKeys.admin')" />
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
import api from '../services/api.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const apiKeys = ref([])
const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)

const keyForm = reactive({
  name: '',
  permission_level: 'read'
})

function getPermissionText(level) {
  const texts = { read: 'Read', write: 'Write', admin: 'Admin' }
  return texts[level] || level
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

async function loadApiKeys() {
  loading.value = true
  try {
    const response = await api.get('/api-keys')
    apiKeys.value = response.data
  } catch (error) {
    ElMessage.error('Failed to load API keys')
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  saving.value = true
  try {
    const response = await api.post('/api-keys', keyForm)
    ElMessage.success('API Key created')
    ElMessage.info(`Key: ${response.data.key} (Save it!)`)
    showAddDialog.value = false
    keyForm.name = ''
    keyForm.permission_level = 'read'
    await loadApiKeys()
  } catch (error) {
    ElMessage.error('Failed to create API key')
  } finally {
    saving.value = false
  }
}

async function handleDelete(key) {
  try {
    await ElMessageBox.confirm('Delete this API key?', 'Warning', { type: 'warning' })
    await api.delete(`/api-keys/${key.id}`)
    ElMessage.success('API key deleted')
    await loadApiKeys()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('Failed to delete API key')
  }
}

function copyKey(key) {
  navigator.clipboard.writeText(key)
  ElMessage.success('Key copied')
}

onMounted(() => {
  loadApiKeys()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.key-display {
  margin-right: 8px;
  font-family: monospace;
}
</style>
