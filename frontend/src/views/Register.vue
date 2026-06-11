<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">{{ $t('login.register') || 'Register' }}</h1>
      <el-form @submit.prevent="handleRegister" :model="form" class="login-form">
        <el-form-item>
          <el-input v-model="form.username" :placeholder="$t('login.username')" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.email" :placeholder="$t('login.email')" size="large" prefix-icon="Message" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.full_name" :placeholder="$t('login.fullName')" size="large" prefix-icon="UserFilled" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" :placeholder="$t('login.password')" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.confirmPassword" type="password" :placeholder="$t('login.confirmPassword')" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" native-type="submit">
            {{ $t('login.register') || 'Register' }}
          </el-button>
        </el-form-item>
      </el-form>
      <p class="hint">
        <router-link to="/login">{{ $t('login.backToLogin') }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)

async function handleRegister() {
  if (!form.username || !form.password) return
  if (form.password !== form.confirmPassword) {
    ElMessage.error('Passwords do not match')
    return
  }
  loading.value = true
  try {
    await authStore.register(form.username, form.password, form.email || null, form.full_name || null)
    ElMessage.success('Registration successful')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'Registration failed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 400px;
}

.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
}

.hint {
  text-align: center;
  color: #999;
  font-size: 12px;
  margin-top: 16px;
}

.hint a {
  color: #667eea;
  text-decoration: none;
}

.hint a:hover {
  text-decoration: underline;
}
</style>
