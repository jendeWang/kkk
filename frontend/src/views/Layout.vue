<template>
  <div class="layout">
    <el-container>
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <h2>IOTPlatform</h2>
        </div>
        <el-menu :default-active="activeMenu" router class="sidebar-menu">
          <el-menu-item index="/dashboard">
            <el-icon><DataBoard /></el-icon>
            <span>{{ $t('menu.dashboard') }}</span>
          </el-menu-item>
          <el-menu-item index="/big-screen" @click="openBigScreen">
            <el-icon><DataLine /></el-icon>
            <span>数据大屏</span>
          </el-menu-item>
          <el-menu-item index="/greenhouse-3d" @click="openGreenhouse3D">
            <el-icon><Grid /></el-icon>
            <span>数字孪生</span>
          </el-menu-item>
          <el-menu-item index="/devices">
            <el-icon><Monitor /></el-icon>
            <span>{{ $t('menu.devices') }}</span>
          </el-menu-item>
          <el-menu-item index="/alerts">
            <el-icon><Bell /></el-icon>
            <span>{{ $t('menu.alerts') }}</span>
          </el-menu-item>
          <el-menu-item index="/scenes">
            <el-icon><Timer /></el-icon>
            <span>场景联动</span>
          </el-menu-item>
          
          <template v-if="settingsStore.uiMode === 'advanced'">
            <el-menu-item index="/products">
              <el-icon><Goods /></el-icon>
              <span>{{ $t('menu.products') }}</span>
            </el-menu-item>
            <el-menu-item index="/thing-model">
              <el-icon><Edit /></el-icon>
              <span>物模型编辑器</span>
            </el-menu-item>
            <el-menu-item index="/template-market">
              <el-icon><Box /></el-icon>
              <span>模板市场</span>
            </el-menu-item>
            <el-menu-item index="/telemetry">
            <el-icon><DataLine /></el-icon>
            <span>{{ $t('menu.telemetry') }}</span>
          </el-menu-item>
          <el-menu-item index="/sensors">
            <el-icon><DataAnalysis /></el-icon>
            <span>传感器监控</span>
          </el-menu-item>
          <el-menu-item index="/actuators">
            <el-icon><SwitchButton /></el-icon>
            <span>执行器控制</span>
          </el-menu-item>
          <el-menu-item index="/rule-editor">
            <el-icon><Filter /></el-icon>
            <span>规则编辑器</span>
          </el-menu-item>
            <el-menu-item index="/commands">
              <el-icon><MessageBox /></el-icon>
              <span>{{ $t('menu.commands') }}</span>
            </el-menu-item>
            <el-menu-item index="/alert-rules">
              <el-icon><Warning /></el-icon>
              <span>{{ $t('menu.alertRules') }}</span>
            </el-menu-item>
            <el-menu-item index="/groups">
              <el-icon><Folder /></el-icon>
              <span>设备分组</span>
            </el-menu-item>
            <el-menu-item index="/api-keys">
              <el-icon><Key /></el-icon>
              <span>{{ $t('menu.apiKeys') }}</span>
            </el-menu-item>
            <el-menu-item index="/topology">
              <el-icon><Grid /></el-icon>
              <span>沙盘拓扑</span>
            </el-menu-item>
            <el-menu-item index="/api-playground">
              <el-icon><Tools /></el-icon>
              <span>API测试台</span>
            </el-menu-item>
            <el-menu-item index="/operation-logs">
              <el-icon><Document /></el-icon>
              <span>操作日志</span>
            </el-menu-item>
            <el-menu-item index="/users" v-if="can('user:write')">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
          </template>
        </el-menu>
        
        <div class="mode-switch">
          <el-switch
            v-model="isAdvanced"
            @change="handleModeChange"
            active-text="高级"
            inactive-text="简化"
            inline-prompt
          />
        </div>
      </el-aside>
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <h3>{{ pageTitle }}</h3>
          </div>
          <div class="header-right">
            <el-tooltip content="切换语言" placement="bottom">
              <el-button :icon="SwitchButton" text @click="toggleLanguage" class="lang-btn">
                {{ currentLangLabel }}
              </el-button>
            </el-tooltip>
            <el-tooltip :content="settingsStore.uiMode === 'simple' ? '当前为简化模式，点击切换到高级模式可查看更多功能' : '当前为高级模式，点击切换到简化模式可隐藏高级功能'" placement="bottom">
              <el-button :icon="settingsStore.uiMode === 'simple' ? MagicStick : Setting" text @click="settingsStore.toggleUiMode()" class="mode-toggle-btn">
                {{ settingsStore.uiMode === 'simple' ? '简化模式' : '高级模式' }}
              </el-button>
            </el-tooltip>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                <span class="user-name">{{ authStore.user?.username || 'Admin' }}</span>
                <el-tag v-if="authStore.user?.role" :type="roleTagType(authStore.user.role)" size="small" class="role-tag">
                  {{ roleName(authStore.user.role) }}
                </el-tag>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useSettingsStore } from '../stores/settings.js'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { loadPropertyMappings } from '../services/propertyMapper.js'
import { MagicStick, Setting, SwitchButton, DataAnalysis, Filter, Edit, Box } from '@element-plus/icons-vue'
import { hasPermission } from '../utils/permission.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const { locale, t } = useI18n()

const savedLang = localStorage.getItem('lang')
if (savedLang) {
  locale.value = savedLang
}

const currentLangLabel = computed(() => {
  return locale.value === 'zh' ? '中文' : 'EN'
})

function toggleLanguage() {
  locale.value = locale.value === 'zh' ? 'en' : 'zh'
  localStorage.setItem('lang', locale.value)
  ElMessage.success(locale.value === 'zh' ? '已切换到中文' : 'Switched to English')
}

const isAdvanced = computed({
  get: () => settingsStore.uiMode === 'advanced',
  set: (val) => settingsStore.setUiMode(val ? 'advanced' : 'simple')
})

const currentUser = computed(() => authStore.user)

function can(permission) {
  return hasPermission(currentUser.value, permission)
}

function roleName(role) {
  const names = { admin: '管理员', operator: '操作员', viewer: '查看员' }
  return names[role] || role || '查看员'
}

function roleTagType(role) {
  if (role === 'admin') return 'danger'
  if (role === 'operator') return 'warning'
  return 'info'
}

function handleModeChange() {
  ElMessage.success(`已切换到${settingsStore.uiMode === 'simple' ? '简化' : '高级'}模式`)
}

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await loadPropertyMappings()
  }
})

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  const titles = {
    '/dashboard': '仪表盘',
    '/products': '产品管理',
    '/thing-model': '物模型编辑器',
    '/template-market': '模板市场',
    '/devices': '设备管理',
    '/telemetry': '遥测数据',
    '/sensors': '传感器监控',
    '/actuators': '执行器控制',
    '/rule-editor': '规则编辑器',
    '/commands': '命令下发',
    '/alert-rules': '告警规则',
    '/alerts': '告警事件',
    '/scenes': '场景联动',
    '/groups': '设备分组',
    '/api-keys': 'API密钥',
    '/api-playground': 'API测试台',
    '/topology': '沙盘拓扑',
    '/operation-logs': '操作日志',
    '/users': '用户管理',
    '/profile': '个人中心'
  }
  return titles[route.path] || ''
})

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('Logged out')
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

function openBigScreen() {
  router.push('/big-screen')
}

function openGreenhouse3D() {
  router.push('/greenhouse-3d')
}
</script>

<style scoped>
.layout {
  height: 100vh;
}

.sidebar {
  background: #304156;
  color: white;
  display: flex;
  flex-direction: column;
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
  flex: 1;
}

.mode-switch {
  padding: 16px;
  border-top: 1px solid #3d4a5c;
  text-align: center;
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

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mode-toggle-btn {
  font-size: 13px;
}

.lang-btn {
  font-size: 13px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.user-name {
  font-size: 14px;
}

.role-tag {
  margin-left: 4px;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
}
</style>
