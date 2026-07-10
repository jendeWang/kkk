<template>
  <div class="template-market">
    <div class="market-header">
      <div class="header-left">
        <h2 class="page-title">📦 模板市场</h2>
        <p class="page-subtitle">选择预设模板，一键创建完整的物联网解决方案</p>
      </div>
      <div class="header-filters">
        <el-select v-model="categoryFilter" placeholder="选择分类" clearable>
          <el-option label="全部" value="" />
          <el-option label="农业" value="农业" />
          <el-option label="畜牧" value="畜牧" />
        </el-select>
        <el-select v-model="levelFilter" placeholder="选择级别" clearable>
          <el-option label="全部" value="" />
          <el-option label="入门" value="入门" />
          <el-option label="推荐" value="推荐" />
          <el-option label="专业" value="专业" />
        </el-select>
      </div>
    </div>

    <div class="template-stats">
      <div class="stat-item">
        <span class="stat-icon"><SvgIcon name="leaf" :size="20" /></span>
        <span class="stat-text">农业模板</span>
        <span class="stat-num">{{ agricultureCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon"><SvgIcon name="treePine" :size="20" /></span>
        <span class="stat-text">畜牧模板</span>
        <span class="stat-num">{{ livestockCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon"><SvgIcon name="star" :size="20" /></span>
        <span class="stat-text">推荐模板</span>
        <span class="stat-num">{{ recommendedCount }}</span>
      </div>
    </div>

    <div class="template-grid" v-loading="loading">
      <div
        v-for="tpl in filteredTemplates"
        :key="tpl.template_id"
        class="template-card"
        :class="{ 'featured': tpl.level === '推荐' }"
      >
        <div class="card-badge" v-if="tpl.level === '推荐'">
          <el-tag type="danger" effect="dark">推荐</el-tag>
        </div>

        <div class="card-icon-wrap">
          <span class="card-icon">{{ tpl.icon }}</span>
        </div>

        <div class="card-content">
          <h3 class="card-title">{{ tpl.name }}</h3>
          <p class="card-desc">{{ tpl.description }}</p>

          <div class="card-stats">
            <div class="mini-stat">
              <span class="mini-num">{{ tpl.sensor_count }}</span>
              <span class="mini-label">传感器</span>
            </div>
            <div class="mini-stat">
              <span class="mini-num">{{ tpl.actuator_count }}</span>
              <span class="mini-label">执行器</span>
            </div>
            <div class="mini-stat">
              <span class="mini-num">{{ tpl.alert_count }}</span>
              <span class="mini-label">告警规则</span>
            </div>
            <div class="mini-stat">
              <span class="mini-num">{{ tpl.scene_count }}</span>
              <span class="mini-label">自动化场景</span>
            </div>
          </div>

          <div class="card-tags">
            <el-tag v-for="tag in tpl.tags" :key="tag" size="small" type="info" effect="plain">{{ tag }}</el-tag>
          </div>

          <div class="card-footer">
            <el-tag :type="getLevelTagType(tpl.level)" size="small">
              {{ tpl.level }}
            </el-tag>
            <el-button type="primary" @click="useTemplate(tpl)" :loading="usingTemplate === tpl.template_id">
              使用模板
            </el-button>
          </div>
        </div>

        <div class="card-preview" @click="showTemplateDetail(tpl)">
          <div class="preview-title">预览物模型</div>
          <div class="preview-props">
            <div class="prop-chip" v-for="prop in getPreviewProps(tpl)" :key="prop.identifier">
              <SvgIcon :name="prop.icon" :size="14" /> {{ prop.name }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <el-icon :size="64" color="#909399"><Box /></el-icon>
        <p>暂无匹配的模板</p>
      </div>
    </div>

    <el-dialog v-model="showDetailDialog" :title="selectedTemplate?.name" width="800px">
      <div v-if="selectedTemplate" class="detail-content">
        <div class="detail-header">
          <span class="detail-icon">{{ selectedTemplate.icon }}</span>
          <div class="detail-info">
            <h3>{{ selectedTemplate.name }}</h3>
            <p>{{ selectedTemplate.description }}</p>
            <div class="detail-meta">
              <el-tag type="info">{{ selectedTemplate.category }}</el-tag>
              <el-tag :type="getLevelTagType(selectedTemplate.level)">{{ selectedTemplate.level }}</el-tag>
            </div>
          </div>
        </div>

        <div class="detail-sections">
          <div class="detail-section">
            <h4 class="section-title"><SvgIcon name="trendUp" :size="16" /> 传感器 ({{ getTemplateProps(selectedTemplate)?.length || 0 }}个)</h4>
            <div class="prop-list">
              <div v-for="prop in getTemplateProps(selectedTemplate)" :key="prop.identifier" class="prop-item">
                <span class="prop-icon"><SvgIcon :name="getPropIcon(prop.identifier)" :size="16" /></span>
                <div class="prop-info">
                  <span class="prop-name">{{ prop.name }}</span>
                  <span class="prop-unit">{{ prop.unit }}</span>
                </div>
                <el-tag :type="prop.access_type === 'read_write' ? 'success' : 'info'" size="small">
                  {{ prop.access_type === 'read_write' ? '读写' : '只读' }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="section-title"><SvgIcon name="bolt" :size="16" /> 执行器服务 ({{ getTemplateServices(selectedTemplate)?.length || 0 }}个)</h4>
            <div class="service-list">
              <div v-for="svc in getTemplateServices(selectedTemplate)" :key="svc.identifier" class="service-item">
                <span class="service-icon"><SvgIcon name="bolt" :size="18" /></span>
                <div class="service-info">
                  <span class="service-name">{{ svc.name }}</span>
                  <span class="service-desc">{{ svc.description }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="section-title"><SvgIcon name="bell" :size="16" /> 告警规则 ({{ selectedTemplate.alert_count }}个)</h4>
            <div class="alert-list">
              <div v-for="(alert, idx) in getTemplateAlerts(selectedTemplate)" :key="idx" class="alert-item">
                <span class="alert-icon"><SvgIcon :name="getAlertIcon(alert.severity)" :size="16" /></span>
                <span class="alert-name">{{ alert.name }}</span>
                <el-tag :type="getSeverityTag(alert.severity)" size="small">
                  {{ getSeverityText(alert.severity) }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="section-title">🎬 自动化场景 ({{ selectedTemplate.scene_count }}个)</h4>
            <div class="scene-list">
              <div v-for="(scene, idx) in getTemplateScenes(selectedTemplate)" :key="idx" class="scene-item">
                <span class="scene-icon">🎬</span>
                <span class="scene-name">{{ scene.name }}</span>
                <span class="scene-desc">{{ getSceneDesc(scene) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="useTemplate(selectedTemplate)" :loading="usingTemplate === selectedTemplate?.template_id">
          使用此模板
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api.js'
import { ElMessage } from 'element-plus'
import { Box } from '@element-plus/icons-vue'

const router = useRouter()

const templates = ref([])
const loading = ref(false)
const categoryFilter = ref('')
const levelFilter = ref('')
const selectedTemplate = ref(null)
const showDetailDialog = ref(false)
const usingTemplate = ref(null)

const PROP_ICONS = {
  temperature: 'thermometer', humidity: 'droplet', light_intensity: 'sun', soil_moisture: 'leaf',
  co2: 'wind', soil_temperature: 'soil', soil_ph: 'flask', wind_speed: 'cloud',
  rainfall: 'rain', ammonia: 'wind', hydrogen_sulfide: 'cloud', ec_value: 'bolt',
  soil_nitrogen: 'flask', soil_phosphorus: 'star', soil_potassium: 'star', leaf_temperature: 'leaf',
  fan_status: 'fan', light_status: 'bulb', pump_status: 'shower', heater_status: 'fire',
  water_valve_status: 'shower', brightness: 'sun', curtain_status: 'gear', valve_status: 'settings',
}

const agricultureCount = computed(() => templates.value.filter(t => t.category === '农业').length)
const livestockCount = computed(() => templates.value.filter(t => t.category === '畜牧').length)
const recommendedCount = computed(() => templates.value.filter(t => t.level === '推荐').length)

const filteredTemplates = computed(() => {
  let result = templates.value
  if (categoryFilter.value) {
    result = result.filter(t => t.category === categoryFilter.value)
  }
  if (levelFilter.value) {
    result = result.filter(t => t.level === levelFilter.value)
  }
  return result
})

function getLevelTagType(level) {
  const types = { '入门': 'info', '推荐': 'danger', '专业': 'warning' }
  return types[level] || 'info'
}

function getPropIcon(identifier) {
  return PROP_ICONS[identifier] || 'trendUp'
}

function getAlertIcon(severity) {
  const icons = { warning: 'alertTriangle', error: 'xCircle', info: 'alertCircle', critical: 'alertCircle' }
  return icons[severity] || 'bell'
}

function getSeverityTag(severity) {
  const tags = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return tags[severity] || 'info'
}

function getSeverityText(severity) {
  const texts = { info: '提示', warning: '警告', error: '错误', critical: '严重' }
  return texts[severity] || severity
}

function getPreviewProps(tpl) {
  const propMap = {
    greenhouse_basic: [{ identifier: 'temperature', icon: 'thermometer', name: '温度' }, { identifier: 'humidity', icon: 'droplet', name: '湿度' }, { identifier: 'soil_moisture', icon: 'leaf', name: '土壤湿度' }, { identifier: 'light_intensity', icon: 'sun', name: '光照' }],
    greenhouse_standard: [{ identifier: 'temperature', icon: 'thermometer', name: '温度' }, { identifier: 'humidity', icon: 'droplet', name: '湿度' }, { identifier: 'co2', icon: 'wind', name: 'CO₂' }, { identifier: 'soil_temperature', icon: 'soil', name: '地温' }],
    greenhouse_pro: [{ identifier: 'temperature', icon: 'thermometer', name: '温度' }, { identifier: 'soil_ph', icon: 'flask', name: 'pH' }, { identifier: 'soil_nitrogen', icon: 'flask', name: '氮' }, { identifier: 'soil_phosphorus', icon: 'star', name: '磷' }],
    livestock_basic: [{ identifier: 'temperature', icon: 'thermometer', name: '温度' }, { identifier: 'humidity', icon: 'droplet', name: '湿度' }, { identifier: 'ammonia', icon: 'wind', name: '氨气' }, { identifier: 'hydrogen_sulfide', icon: 'cloud', name: '硫化氢' }],
  }
  return propMap[tpl.template_id] || []
}

function getTemplateProps(tpl) {
  const propMaps = {
    greenhouse_basic: [
      { identifier: 'temperature', name: '空气温度', unit: '℃', access_type: 'read_only' },
      { identifier: 'humidity', name: '空气湿度', unit: '%RH', access_type: 'read_only' },
      { identifier: 'soil_moisture', name: '土壤湿度', unit: '%', access_type: 'read_only' },
      { identifier: 'light_intensity', name: '光照强度', unit: 'lux', access_type: 'read_only' },
      { identifier: 'fan_status', name: '通风扇状态', unit: '', access_type: 'read_write' },
      { identifier: 'light_status', name: '补光灯状态', unit: '', access_type: 'read_write' },
      { identifier: 'pump_status', name: '灌溉水泵状态', unit: '', access_type: 'read_write' },
    ],
    greenhouse_standard: [
      { identifier: 'temperature', name: '空气温度', unit: '℃', access_type: 'read_only' },
      { identifier: 'humidity', name: '空气湿度', unit: '%RH', access_type: 'read_only' },
      { identifier: 'soil_moisture', name: '土壤湿度', unit: '%', access_type: 'read_only' },
      { identifier: 'light_intensity', name: '光照强度', unit: 'lux', access_type: 'read_only' },
      { identifier: 'co2', name: 'CO₂浓度', unit: 'ppm', access_type: 'read_only' },
      { identifier: 'soil_temperature', name: '土壤温度', unit: '℃', access_type: 'read_only' },
      { identifier: 'fan_status', name: '通风扇状态', unit: '', access_type: 'read_write' },
      { identifier: 'light_status', name: '补光灯状态', unit: '', access_type: 'read_write' },
      { identifier: 'pump_status', name: '灌溉水泵状态', unit: '', access_type: 'read_write' },
      { identifier: 'brightness', name: '补光灯亮度', unit: '%', access_type: 'read_write' },
    ],
    greenhouse_pro: [
      { identifier: 'temperature', name: '空气温度', unit: '℃', access_type: 'read_only' },
      { identifier: 'humidity', name: '空气湿度', unit: '%RH', access_type: 'read_only' },
      { identifier: 'soil_moisture', name: '土壤湿度', unit: '%', access_type: 'read_only' },
      { identifier: 'light_intensity', name: '光照强度', unit: 'lux', access_type: 'read_only' },
      { identifier: 'co2', name: 'CO₂浓度', unit: 'ppm', access_type: 'read_only' },
      { identifier: 'soil_temperature', name: '土壤温度', unit: '℃', access_type: 'read_only' },
      { identifier: 'soil_ph', name: '土壤pH值', unit: '', access_type: 'read_only' },
      { identifier: 'ec_value', name: '土壤电导率', unit: 'mS/cm', access_type: 'read_only' },
      { identifier: 'soil_nitrogen', name: '土壤氮含量', unit: 'mg/kg', access_type: 'read_only' },
      { identifier: 'soil_phosphorus', name: '土壤磷含量', unit: 'mg/kg', access_type: 'read_only' },
      { identifier: 'soil_potassium', name: '土壤钾含量', unit: 'mg/kg', access_type: 'read_only' },
      { identifier: 'wind_speed', name: '风速', unit: 'm/s', access_type: 'read_only' },
      { identifier: 'fan_status', name: '通风扇状态', unit: '', access_type: 'read_write' },
      { identifier: 'light_status', name: '补光灯状态', unit: '', access_type: 'read_write' },
      { identifier: 'pump_status', name: '灌溉水泵状态', unit: '', access_type: 'read_write' },
      { identifier: 'brightness', name: '补光灯亮度', unit: '%', access_type: 'read_write' },
    ],
    livestock_basic: [
      { identifier: 'temperature', name: '舍内温度', unit: '℃', access_type: 'read_only' },
      { identifier: 'humidity', name: '舍内湿度', unit: '%RH', access_type: 'read_only' },
      { identifier: 'ammonia', name: '氨气浓度', unit: 'ppm', access_type: 'read_only' },
      { identifier: 'hydrogen_sulfide', name: '硫化氢浓度', unit: 'ppm', access_type: 'read_only' },
      { identifier: 'co2', name: 'CO₂浓度', unit: 'ppm', access_type: 'read_only' },
      { identifier: 'fan_status', name: '通风扇状态', unit: '', access_type: 'read_write' },
      { identifier: 'heater_status', name: '加热器状态', unit: '', access_type: 'read_write' },
      { identifier: 'water_valve_status', name: '饮水阀状态', unit: '', access_type: 'read_write' },
    ],
  }
  return propMaps[tpl.template_id] || []
}

function getTemplateServices(tpl) {
  const serviceMaps = {
    greenhouse_basic: [
      { identifier: 'set_fan', name: '设置通风扇', description: '开启或关闭通风扇' },
      { identifier: 'set_light', name: '设置补光灯', description: '控制补光灯开关' },
      { identifier: 'set_pump', name: '设置灌溉泵', description: '控制灌溉水泵' },
      { identifier: 'set_mode', name: '设置工作模式', description: '切换手动/自动模式' },
    ],
    greenhouse_standard: [
      { identifier: 'set_fan', name: '设置通风扇', description: '开启或关闭通风扇' },
      { identifier: 'set_light', name: '设置补光灯', description: '控制补光灯开关' },
      { identifier: 'set_pump', name: '设置灌溉泵', description: '控制灌溉水泵' },
      { identifier: 'set_mode', name: '设置工作模式', description: '切换手动/自动模式' },
      { identifier: 'set_light_brightness', name: '调节补光亮度', description: '设置补光灯亮度百分比' },
    ],
    greenhouse_pro: [
      { identifier: 'set_fan', name: '设置通风扇', description: '开启或关闭通风扇' },
      { identifier: 'set_light', name: '设置补光灯', description: '控制补光灯开关' },
      { identifier: 'set_pump', name: '设置灌溉泵', description: '控制灌溉水泵' },
      { identifier: 'set_mode', name: '设置工作模式', description: '切换手动/自动模式' },
      { identifier: 'set_light_brightness', name: '调节补光亮度', description: '设置补光灯亮度百分比' },
      { identifier: 'set_fertilizer', name: '设置施肥', description: '控制水肥一体化施肥' },
    ],
    livestock_basic: [
      { identifier: 'set_fan', name: '设置通风扇', description: '开启或关闭通风扇' },
      { identifier: 'set_heater', name: '设置加热器', description: '控制加热器开关' },
      { identifier: 'set_water_valve', name: '设置饮水阀', description: '控制自动饮水阀' },
      { identifier: 'set_mode', name: '设置工作模式', description: '切换手动/自动模式' },
    ],
  }
  return serviceMaps[tpl.template_id] || []
}

function getTemplateAlerts(tpl) {
  const alertMaps = {
    greenhouse_basic: [
      { name: '高温告警', severity: 'warning' },
      { name: '土壤干旱告警', severity: 'warning' },
      { name: '设备离线告警', severity: 'error' },
    ],
    greenhouse_standard: [
      { name: '高温告警', severity: 'warning' },
      { name: '低温告警', severity: 'warning' },
      { name: '高湿告警', severity: 'warning' },
      { name: '土壤干旱告警', severity: 'warning' },
      { name: '设备离线告警', severity: 'error' },
    ],
    greenhouse_pro: [
      { name: '高温告警', severity: 'warning' },
      { name: '低温告警', severity: 'warning' },
      { name: '高湿告警', severity: 'warning' },
      { name: '土壤干旱告警', severity: 'warning' },
      { name: '土壤过湿告警', severity: 'warning' },
      { name: 'CO₂超标告警', severity: 'warning' },
      { name: 'pH异常告警', severity: 'info' },
      { name: '设备离线告警', severity: 'error' },
    ],
    livestock_basic: [
      { name: '高温告警', severity: 'warning' },
      { name: '低温告警', severity: 'warning' },
      { name: '氨气超标告警', severity: 'error' },
      { name: '设备离线告警', severity: 'error' },
    ],
  }
  return alertMaps[tpl.template_id] || []
}

function getTemplateScenes(tpl) {
  const sceneMaps = {
    greenhouse_basic: [
      { name: '高温自动通风', trigger_prop: '温度', operator: '>', threshold: '30', service: '开启通风扇' },
      { name: '干旱自动灌溉', trigger_prop: '土壤湿度', operator: '<', threshold: '30', service: '开启水泵' },
    ],
    greenhouse_standard: [
      { name: '高温自动通风', trigger_prop: '温度', operator: '>', threshold: '30', service: '开启通风扇' },
      { name: '低温自动保温', trigger_prop: '温度', operator: '<', threshold: '15', service: '关闭通风扇' },
      { name: '干旱自动灌溉', trigger_prop: '土壤湿度', operator: '<', threshold: '40', service: '开启水泵' },
      { name: '弱光自动补光', trigger_prop: '光照', operator: '<', threshold: '5000', service: '开启补光灯' },
    ],
    greenhouse_pro: [
      { name: '高温自动通风', trigger_prop: '温度', operator: '>', threshold: '32', service: '开启通风扇' },
      { name: '低温自动保温', trigger_prop: '温度', operator: '<', threshold: '12', service: '关闭通风扇' },
      { name: '干旱自动灌溉', trigger_prop: '土壤湿度', operator: '<', threshold: '40', service: '开启水泵' },
      { name: '弱光自动补光', trigger_prop: '光照', operator: '<', threshold: '5000', service: '开启补光灯' },
      { name: '过湿停止灌溉', trigger_prop: '土壤湿度', operator: '>', threshold: '85', service: '关闭水泵' },
      { name: 'CO₂超标通风', trigger_prop: 'CO₂', operator: '>', threshold: '1500', service: '开启通风扇' },
    ],
    livestock_basic: [
      { name: '高温自动通风', trigger_prop: '温度', operator: '>', threshold: '28', service: '开启通风扇' },
      { name: '低温自动加热', trigger_prop: '温度', operator: '<', threshold: '18', service: '开启加热器' },
      { name: '氨气超标通风', trigger_prop: '氨气', operator: '>', threshold: '10', service: '开启通风扇' },
    ],
  }
  return sceneMaps[tpl.template_id] || []
}

function getSceneDesc(scene) {
  return `${scene.trigger_prop}${scene.operator}${scene.threshold} → ${scene.service}`
}

function showTemplateDetail(tpl) {
  selectedTemplate.value = tpl
  showDetailDialog.value = true
}

async function useTemplate(tpl) {
  if (!tpl) return
  
  usingTemplate.value = tpl.template_id
  try {
    const resp = await api.post(`/products/from-template/${tpl.template_id}`)
    ElMessage.success(`成功创建产品：${resp.data.name}`)
    showDetailDialog.value = false
    router.push('/products')
  } catch (e) {
    console.error('Failed to create product from template:', e)
    ElMessage.error('创建失败，请重试')
  } finally {
    usingTemplate.value = null
  }
}

async function loadTemplates() {
  loading.value = true
  try {
    const resp = await api.get('/products/templates/list')
    templates.value = resp.data
  } catch (e) {
    console.error('Failed to load templates:', e)
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-market {
  padding: 0;
}

.market-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: #fff;
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}

.page-subtitle {
  margin: 6px 0 0;
  font-size: 14px;
  color: rgba(255,255,255,0.8);
}

.header-filters {
  display: flex;
  gap: 12px;
}

.header-filters :deep(.el-select) {
  width: 150px;
}

.template-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.stat-icon {
  font-size: 20px;
}

.stat-text {
  font-size: 14px;
  color: #606266;
}

.stat-num {
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
}

.template-card {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  position: relative;
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.template-card.featured {
  border: 2px solid #f56c6c;
}

.card-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 1;
}

.card-icon-wrap {
  padding: 30px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  text-align: center;
}

.card-icon {
  font-size: 48px;
}

.card-content {
  padding: 20px;
}

.card-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: #303133;
}

.card-desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

.card-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.mini-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.mini-num {
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}

.mini-label {
  font-size: 11px;
  color: #909399;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-preview {
  padding: 16px 20px;
  background: #f8f9fa;
  border-top: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
}

.card-preview:hover {
  background: #f0f2f5;
}

.preview-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.preview-props {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.prop-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #fff;
  border-radius: 12px;
  font-size: 12px;
  color: #606266;
  border: 1px solid #ebeef5;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #909399;
}

.empty-state p {
  margin-top: 16px;
  font-size: 16px;
}

.detail-content {
  max-height: 600px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
}

.detail-icon {
  font-size: 48px;
}

.detail-info h3 {
  margin: 0 0 8px;
  font-size: 20px;
}

.detail-info p {
  margin: 0 0 12px;
  font-size: 14px;
  color: #909399;
}

.detail-meta {
  display: flex;
  gap: 8px;
}

.detail-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section h4 {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
}

.prop-list, .service-list, .alert-list, .scene-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prop-item, .service-item, .alert-item, .scene-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 8px;
}

.prop-icon, .service-icon, .alert-icon, .scene-icon {
  font-size: 18px;
}

.prop-info, .service-info {
  flex: 1;
}

.prop-name, .service-name, .alert-name, .scene-name {
  font-size: 14px;
  color: #303133;
}

.prop-unit {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.service-desc {
  font-size: 12px;
  color: #909399;
}

.scene-desc {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

@media (max-width: 768px) {
  .market-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-filters {
    width: 100%;
  }

  .template-grid {
    grid-template-columns: 1fr;
  }

  .card-stats {
    gap: 8px;
  }

  .mini-stat {
    padding: 6px 12px;
  }
}
</style>
