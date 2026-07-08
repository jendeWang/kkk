<template>
  <div class="users-page">
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              新增用户
            </el-button>
          </div>
        </div>
      </template>

      <div class="search-bar mb-4">
        <el-input v-model="searchKeyword" placeholder="搜索用户名或姓名" prefix-icon="Search" style="width: 300px" />
      </div>

      <el-table :data="filteredUsers" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="full_name" label="姓名" min-width="120">
          <template #default="{ row }">{{ row.full_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="150">
          <template #default="{ row }">{{ row.email || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">
              {{ roleName(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_superuser ? 'warning' : 'info'" size="small">
              {{ row.is_superuser ? '超级用户' : '普通' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleUserStatus(row)">
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)" v-if="row.id !== currentUserId">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog :title="editingUser ? '编辑用户' : '新增用户'" v-model="showAddDialog" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item label="密码" v-if="!editingUser">
          <el-input v-model="form.password" type="password" placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option v-for="r in roleList" :key="r.key" :label="r.name" :value="r.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="超级用户">
          <el-switch v-model="form.is_superuser" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '../services/api.js'

const loading = ref(false)
const users = ref([])
const searchKeyword = ref('')
const showAddDialog = ref(false)
const editingUser = ref(null)
const currentUserId = ref(null)
const roleList = ref([])

const form = ref({
  username: '',
  password: '',
  full_name: '',
  email: '',
  is_superuser: false,
  role: 'viewer',
})

const ROLE_NAMES = {
  admin: '管理员',
  operator: '操作员',
  viewer: '查看员',
}

function roleName(role) {
  return ROLE_NAMES[role] || role || '查看员'
}

function roleTagType(role) {
  if (role === 'admin') return 'danger'
  if (role === 'operator') return 'warning'
  return 'info'
}

const filteredUsers = computed(() => {
  let result = users.value
  if (searchKeyword.value) {
    const query = searchKeyword.value.toLowerCase()
    result = result.filter(u =>
      u.username.toLowerCase().includes(query) ||
      (u.full_name && u.full_name.toLowerCase().includes(query))
    )
  }
  return result
})

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function loadUsers() {
  loading.value = true
  try {
    const response = await api.get('/users/')
    users.value = response.data
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

async function loadCurrentUser() {
  try {
    const response = await api.get('/auth/me')
    currentUserId.value = response.data.id
  } catch (e) {}
}

function editUser(user) {
  editingUser.value = user
  form.value = {
    username: user.username,
    password: '',
    full_name: user.full_name || '',
    email: user.email || '',
    is_superuser: user.is_superuser || false,
    role: user.role || 'viewer',
  }
  showAddDialog.value = true
}

function toggleUserStatus(user) {
  const statusText = user.is_active ? '禁用' : '启用'
  ElMessageBox.confirm(`确定要${statusText}用户 "${user.username}" 吗？`, '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      await api.put(`/users/${user.id}`, { is_active: !user.is_active })
      ElMessage.success(`用户已${statusText}`)
      await loadUsers()
    } catch (error) {
      ElMessage.error(`${statusText}失败`)
    }
  })
}

function deleteUser(user) {
  ElMessageBox.confirm(`确定要删除用户 "${user.username}" 吗？此操作不可恢复。`, '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await api.delete(`/users/${user.id}`)
      ElMessage.success('删除成功')
      await loadUsers()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

async function saveUser() {
  if (!form.value.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!editingUser.value && !form.value.password) {
    ElMessage.warning('请输入密码')
    return
  }

  try {
    if (editingUser.value) {
      await api.put(`/users/${editingUser.value.id}`, {
        email: form.value.email,
        full_name: form.value.full_name,
        is_superuser: form.value.is_superuser,
        role: form.value.role,
      })
      ElMessage.success('更新成功')
    } else {
      await api.post('/users/', {
        username: form.value.username,
        password: form.value.password,
        full_name: form.value.full_name,
        email: form.value.email,
        role: form.value.role,
      })
      ElMessage.success('创建成功')
    }
    showAddDialog.value = false
    editingUser.value = null
    form.value = { username: '', password: '', full_name: '', email: '', is_superuser: false, role: 'viewer' }
    await loadUsers()
  } catch (error) {
    ElMessage.error(error.userMessage || '操作失败')
  }
}

async function loadRoles() {
  try {
    const response = await api.get('/users/roles')
    roleList.value = response.data
  } catch (e) {
    roleList.value = [
      { key: 'admin', name: '管理员', description: '拥有全部权限' },
      { key: 'operator', name: '操作员', description: '可操作设备、配置规则' },
      { key: 'viewer', name: '查看员', description: '只能查看数据' },
    ]
  }
}

onMounted(() => {
  loadUsers()
  loadCurrentUser()
  loadRoles()
})
</script>

<style scoped>
.users-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.search-bar {
  display: flex;
  align-items: center;
}
</style>