<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">{{ $t('login.title') }}</h1>
      <el-form @submit.prevent="handleLogin" :model="form" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.username"
            :placeholder="$t('login.username')"
            size="large"
            prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="$t('login.password')"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" native-type="submit">
            {{ $t('login.loginBtn') }}
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="success" size="large" style="width: 100%" :loading="demoLoading" @click="handleDemoLogin">
            <el-icon><MagicStick /></el-icon>
            一键体验（无需注册）
          </el-button>
        </el-form-item>
      </el-form>
      <p class="hint">
        <router-link to="/register">{{ $t('login.register') || 'Register a new account' }}</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const demoLoading = ref(false)

async function handleLogin() {
  if (!form.username || !form.password) return
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleDemoLogin() {
  demoLoading.value = true
  try {
    await authStore.login('admin', 'admin123')
    ElMessage.success('欢迎体验智慧大棚物联网平台！')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '演示登录失败，请使用管理员账号登录')
  } finally {
    demoLoading.value = false
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
</style>
