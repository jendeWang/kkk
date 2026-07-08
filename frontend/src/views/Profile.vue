<template>
  <div class="profile-page">
    <el-card>
      <template #header>
        <span>个人中心</span>
      </template>

      <el-tabs v-model="activeTab" class="mt-4">
        <el-tab-pane label="个人信息" name="info">
          <el-form :model="profileForm" label-width="100px" class="mt-4">
            <el-form-item label="用户名">
              <el-input :value="profileForm.username" disabled />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="profileForm.full_name" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" />
            </el-form-item>
            <el-form-item label="状态">
              <el-tag :type="profileForm.is_active ? 'success' : 'danger'" size="small">
                {{ profileForm.is_active ? '正常' : '禁用' }}
              </el-tag>
            </el-form-item>
            <el-form-item label="权限">
              <el-tag :type="profileForm.is_superuser ? 'warning' : 'info'" size="small">
                {{ profileForm.is_superuser ? '管理员' : '普通用户' }}
              </el-tag>
            </el-form-item>
            <el-form-item label="创建时间">
              <span>{{ formatTime(profileForm.created_at) }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProfile">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="修改密码" name="password">
          <el-form :model="passwordForm" label-width="120px" class="mt-4" :rules="passwordRules">
            <el-form-item label="当前密码" prop="currentPassword">
              <el-input v-model="passwordForm.currentPassword" type="password" />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="passwordForm.newPassword" type="password" placeholder="至少6位" />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="passwordForm.confirmPassword" type="password" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword">修改密码</el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api.js'

const activeTab = ref('info')
const profileForm = reactive({
  username: '',
  full_name: '',
  email: '',
  is_active: true,
  is_superuser: false,
  created_at: '',
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function loadProfile() {
  try {
    const response = await api.get('/auth/me')
    const user = response.data
    profileForm.username = user.username
    profileForm.full_name = user.full_name || ''
    profileForm.email = user.email || ''
    profileForm.is_active = user.is_active
    profileForm.is_superuser = user.is_superuser
    profileForm.created_at = user.created_at
  } catch (error) {
    ElMessage.error('加载个人信息失败')
  }
}

async function saveProfile() {
  try {
    await api.put('/users/me/profile', {
      email: profileForm.email,
      full_name: profileForm.full_name,
    })
    ElMessage.success('个人信息更新成功')
    await loadProfile()
  } catch (error) {
    ElMessage.error(error.userMessage || '更新失败')
  }
}

async function changePassword() {
  if (passwordForm.currentPassword === passwordForm.newPassword) {
    ElMessage.warning('新密码不能与当前密码相同')
    return
  }

  try {
    await api.put('/users/me/password', {
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword,
    })
    ElMessage.success('密码修改成功，请重新登录')
    resetPasswordForm()
    setTimeout(() => {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }, 1000)
  } catch (error) {
    ElMessage.error(error.userMessage || '密码修改失败')
  }
}

function resetPasswordForm() {
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  padding: 0;
}
</style>