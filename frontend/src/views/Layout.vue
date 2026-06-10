<template>
  <div class="layout">
    <el-container>
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <h2>IOTPlatform</h2>
        </div>
        <el-menu :default-active="activeMenu" router class="sidebar-menu">
          <el-menu-item index="/dashboard">
            <el-icon><Odomometer /></el-icon>
            <span>{{ $t('menu.dashboard') }}</span>
          </el-menu-item>
          <el-menu-item index="/products">
            <el-icon><Goods /></el-icon>
            <span>{{ $t('menu.products') }}</span>
          </el-menu-item>
          <el-menu-item index="/devices">
            <el-icon><Monitor /></el-icon>
            <span>{{ $t('menu.devices') }}</span>
          </el-menu-item>
          <el-menu-item index="/telemetry">
            <el-icon><DataLine /></el-icon>
            <span>{{ $t('menu.telemetry') }}</span>
          </el-menu-item>
          <el-menu-item index="/commands">
            <el-icon><MessageBox /></el-icon>
            <span>{{ $t('menu.commands') }}</span>
          </el-menu-item>
          <el-menu-item index="/alert-rules">
            <el-icon><Warning /></el-icon>
            <span>{{ $t('menu.alertRules') }}</span>
          </el-menu-item>
          <el-menu-item index="/alerts">
            <el-icon><Bell /></el-icon>
            <span>{{ $t('menu.alerts') }}</span>
          </el-menu-item>
          <el-menu-item index="/api-keys">
            <el-icon><Key /></el-icon>
            <span>{{ $t('menu.apiKeys') }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <h3>{{ pageTitle }}</h3>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                {{ authStore.user?.username || 'Admin' }}
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">{{ $t('menu.logout') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  const titles = {
    '/dashboard': 'menu.dashboard',
    '/products': 'menu.products',
    '/devices': 'menu.devices',
    '/telemetry': 'menu.telemetry',
    '/commands': 'menu.commands',
    '/alert-rules': 'menu.alertRules',
    '/alerts': 'menu.alerts',
    '/api-keys': 'menu.apiKeys'
  }
  return titles[route.path] ? route.meta?.title || route.path : ''
})

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('Logged out')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.sidebar {
  background: #304156;
  color: white;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #3d4a5c;
}

.logo h2 {
  color: #409eff;
  font-size: 18px;
}

.sidebar-menu {
  border-right: none;
  background: #304156;
}

:deep(.el-menu-item) {
  color: #bfcbd9;
}

:deep(.el-menu-item:hover),
:deep(.el-menu-item.is-active) {
  background: #263445;
  color: #409eff;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left h3 {
  color: #333;
  font-size: 18px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
}
</style>
