<template>
  <div class="thing-model-editor">
    <div class="editor-header">
      <div class="header-left">
        <h2 class="page-title">🛠️ 物模型编辑器</h2>
        <p class="page-subtitle">可视化管理产品的属性、服务和事件</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedProduct" placeholder="选择产品" @change="loadProductData">
          <el-option v-for="p in products" :key="p.product_key" :label="p.name" :value="p.product_key" />
        </el-select>
        <el-button type="primary" @click="saveAllChanges" :loading="saving">
          <el-icon><Check /></el-icon>
          保存更改
        </el-button>
      </div>
    </div>

    <div v-if="!selectedProduct" class="empty-state">
      <el-icon :size="64" color="#909399"><Box /></el-icon>
      <p>请先选择一个产品</p>
      <el-button type="primary" @click="goToProducts">去创建产品</el-button>
    </div>

    <div v-else class="editor-content">
      <div class="editor-sidebar">
        <div class="sidebar-section">
          <div class="section-title">📦 快捷添加</div>
          <div class="quick-add-grid">
            <div class="quick-add-item" @click="addPropertyFromTemplate('temperature')">
              <span class="item-icon">🌡️</span>
              <span class="item-name">温度</span>
            </div>
            <div class="quick-add-item" @click="addPropertyFromTemplate('humidity')">
              <span class="item-icon">💧</span>
              <span class="item-name">湿度</span>
            </div>
            <div class="quick-add-item" @click="addPropertyFromTemplate('light_intensity')">
              <span class="item-icon">☀️</span>
              <span class="item-name">光照</span>
            </div>
            <div class="quick-add-item" @click="addPropertyFromTemplate('soil_moisture')">
              <span class="item-icon">🌱</span>
              <span class="item-name">土壤湿度</span>
            </div>
            <div class="quick-add-item" @click="addPropertyFromTemplate('co2')">
              <span class="item-icon">💨</span>
              <span class="item-name">CO₂</span>
            </div>
            <div class="quick-add-item" @click="addPropertyFromTemplate('wind_speed')">
              <span class="item-icon">🌬️</span>
              <span class="item-name">风速</span>
            </div>
            <div class="quick-add-item" @click="addPropertyFromTemplate('soil_ph')">
              <span class="item-icon">⚗️</span>
              <span class="item-name">pH值</span>
            </div>
            <div class="quick-add-item" @click="addPropertyFromTemplate('rainfall')">
              <span class="item-icon">🌧️</span>
              <span class="item-name">雨量</span>
            </div>
          </div>
        </div>

        <div class="sidebar-section">
          <div class="section-title">⚡ 执行器服务</div>
          <div class="quick-add-grid">
            <div class="quick-add-item" @click="addServiceFromTemplate('set_fan')">
              <span class="item-icon">🌀</span>
              <span class="item-name">通风扇</span>
            </div>
            <div class="quick-add-item" @click="addServiceFromTemplate('set_light')">
              <span class="item-icon">💡</span>
              <span class="item-name">补光灯</span>
            </div>
            <div class="quick-add-item" @click="addServiceFromTemplate('set_pump')">
              <span class="item-icon">🚿</span>
              <span class="item-name">水泵</span>
            </div>
            <div class="quick-add-item" @click="addServiceFromTemplate('set_curve')">
              <span class="item-icon">🎭</span>
              <span class="item-name">卷帘</span>
            </div>
            <div class="quick-add-item" @click="addServiceFromTemplate('set_valve')">
              <span class="item-icon">🔐</span>
              <span class="item-name">电磁阀</span>
            </div>
            <div class="quick-add-item" @click="addServiceFromTemplate('set_heater')">
              <span class="item-icon">🔥</span>
              <span class="item-name">加热膜</span>
            </div>
          </div>
        </div>
      </div>

      <div class="editor-main">
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane label="📊 属性 (Properties)" name="properties">
            <div class="tab-header">
              <span class="tab-title">设备上报的数据，如温度、湿度等</span>
              <el-button type="primary" size="small" @click="showAddPropertyDialog = true">
                <el-icon><Plus /></el-icon>
                添加属性
              </el-button>
            </div>
            <div class="model-grid">
              <div v-for="prop in localProperties" :key="prop.id || prop.identifier" class="model-card prop-card">
                <div class="card-header">
                  <span class="card-icon">📊</span>
                  <span class="card-name">{{ prop.name }}</span>
                  <el-tag :type="prop.access_type === 'read_write' ? 'success' : 'info'" size="small">
                    {{ prop.access_type === 'read_write' ? '读写' : '只读' }}
                  </el-tag>
                  <div class="card-actions">
                    <el-button size="small" @click="editProperty(prop)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeProperty(prop)">删除</el-button>
                  </div>
                </div>
                <div class="card-body">
                  <div class="prop-info">
                    <span class="info-label">标识符</span>
                    <span class="info-value">{{ prop.identifier }}</span>
                  </div>
                  <div class="prop-info">
                    <span class="info-label">类型</span>
                    <span class="info-value">{{ getDataTypeLabel(prop.data_type) }}</span>
                  </div>
                  <div class="prop-info" v-if="prop.unit">
                    <span class="info-label">单位</span>
                    <span class="info-value">{{ prop.unit }}</span>
                  </div>
                  <div class="prop-info" v-if="prop.min_value || prop.max_value">
                    <span class="info-label">范围</span>
                    <span class="info-value">{{ prop.min_value || '-' }} ~ {{ prop.max_value || '-' }}</span>
                  </div>
                  <div class="prop-info" v-if="prop.description">
                    <span class="info-label">描述</span>
                    <span class="info-value">{{ prop.description }}</span>
                  </div>
                </div>
              </div>
              <div v-if="localProperties.length === 0" class="empty-card">
                <el-icon :size="48" color="#c0c4cc"><Plus /></el-icon>
                <p>暂无属性，点击上方按钮添加</p>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="⚡ 服务 (Services)" name="services">
            <div class="tab-header">
              <span class="tab-title">设备可执行的命令，如开启风扇、调节灯光等</span>
              <el-button type="primary" size="small" @click="showAddServiceDialog = true">
                <el-icon><Plus /></el-icon>
                添加服务
              </el-button>
            </div>
            <div class="model-grid">
              <div v-for="svc in localServices" :key="svc.id || svc.identifier" class="model-card service-card">
                <div class="card-header">
                  <span class="card-icon">⚡</span>
                  <span class="card-name">{{ svc.name }}</span>
                  <div class="card-actions">
                    <el-button size="small" @click="editService(svc)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeService(svc)">删除</el-button>
                  </div>
                </div>
                <div class="card-body">
                  <div class="prop-info">
                    <span class="info-label">标识符</span>
                    <span class="info-value">{{ svc.identifier }}</span>
                  </div>
                  <div class="prop-info" v-if="svc.description">
                    <span class="info-label">描述</span>
                    <span class="info-value">{{ svc.description }}</span>
                  </div>
                  <div v-if="svc.input_params && svc.input_params.length > 0">
                    <div class="prop-info">
                      <span class="info-label">输入参数</span>
                    </div>
                    <div v-for="param in svc.input_params" :key="param.identifier" class="param-item">
                      <span class="param-name">{{ param.name }}</span>
                      <span class="param-type">{{ param.dataType }}</span>
                    </div>
                  </div>
                  <div v-if="svc.output_params && svc.output_params.length > 0">
                    <div class="prop-info">
                      <span class="info-label">输出参数</span>
                    </div>
                    <div v-for="param in svc.output_params" :key="param.identifier" class="param-item">
                      <span class="param-name">{{ param.name }}</span>
                      <span class="param-type">{{ param.dataType }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="localServices.length === 0" class="empty-card">
                <el-icon :size="48" color="#c0c4cc"><Plus /></el-icon>
                <p>暂无服务，点击上方按钮添加</p>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="🔔 事件 (Events)" name="events">
            <div class="tab-header">
              <span class="tab-title">设备主动上报的事件，如告警、状态变更等</span>
              <el-button type="primary" size="small" @click="showAddEventDialog = true">
                <el-icon><Plus /></el-icon>
                添加事件
              </el-button>
            </div>
            <div class="model-grid">
              <div v-for="evt in localEvents" :key="evt.id || evt.identifier" class="model-card event-card">
                <div class="card-header">
                  <span class="card-icon">🔔</span>
                  <span class="card-name">{{ evt.name }}</span>
                  <el-tag :type="getEventTypeTag(evt.event_type)" size="small">
                    {{ getEventTypeLabel(evt.event_type) }}
                  </el-tag>
                  <div class="card-actions">
                    <el-button size="small" @click="editEvent(evt)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeEvent(evt)">删除</el-button>
                  </div>
                </div>
                <div class="card-body">
                  <div class="prop-info">
                    <span class="info-label">标识符</span>
                    <span class="info-value">{{ evt.identifier }}</span>
                  </div>
                  <div class="prop-info" v-if="evt.description">
                    <span class="info-label">描述</span>
                    <span class="info-value">{{ evt.description }}</span>
                  </div>
                  <div v-if="evt.output_params && evt.output_params.length > 0">
                    <div class="prop-info">
                      <span class="info-label">输出参数</span>
                    </div>
                    <div v-for="param in evt.output_params" :key="param.identifier" class="param-item">
                      <span class="param-name">{{ param.name }}</span>
                      <span class="param-type">{{ param.dataType }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="localEvents.length === 0" class="empty-card">
                <el-icon :size="48" color="#c0c4cc"><Plus /></el-icon>
                <p>暂无事件，点击上方按钮添加</p>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <el-dialog v-model="showAddPropertyDialog" :title="editingProperty ? '编辑属性' : '添加属性'" width="600px">
      <el-form :model="propertyForm" label-width="100px">
        <el-form-item label="标识符" required>
          <el-input v-model="propertyForm.identifier" placeholder="如 temperature" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="propertyForm.name" placeholder="如 温度" />
        </el-form-item>
        <el-form-item label="数据类型" required>
          <el-select v-model="propertyForm.data_type">
            <el-option value="string" label="字符串 (String)" />
            <el-option value="int" label="整数 (Integer)" />
            <el-option value="float" label="浮点数 (Float)" />
            <el-option value="bool" label="布尔值 (Boolean)" />
            <el-option value="date" label="日期 (Date)" />
            <el-option value="enum" label="枚举 (Enum)" />
            <el-option value="json" label="JSON" />
          </el-select>
        </el-form-item>
        <el-form-item label="读写类型">
          <el-select v-model="propertyForm.access_type">
            <el-option value="read_only" label="只读" />
            <el-option value="read_write" label="读写" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="propertyForm.unit" placeholder="如 °C, %, ppm" />
        </el-form-item>
        <el-form-item label="最小值">
          <el-input v-model="propertyForm.min_value" placeholder="数值类型必填" />
        </el-form-item>
        <el-form-item label="最大值">
          <el-input v-model="propertyForm.max_value" placeholder="数值类型必填" />
        </el-form-item>
        <el-form-item label="步长">
          <el-input v-model="propertyForm.step" placeholder="如 0.1" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="propertyForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPropertyDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProperty">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddServiceDialog" :title="editingService ? '编辑服务' : '添加服务'" width="650px">
      <el-form :model="serviceForm" label-width="100px">
        <el-form-item label="标识符" required>
          <el-input v-model="serviceForm.identifier" placeholder="如 set_fan" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="serviceForm.name" placeholder="如 通风扇控制" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="serviceForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="输入参数">
          <el-button type="success" size="small" @click="addServiceParam('input')">添加参数</el-button>
          <div v-for="(param, idx) in serviceForm.input_params" :key="idx" class="param-row">
            <el-input v-model="param.identifier" placeholder="标识符" size="small" style="width: 120px;" />
            <el-input v-model="param.name" placeholder="名称" size="small" style="width: 120px;" />
            <el-select v-model="param.dataType" size="small" style="width: 100px;">
              <el-option value="string" label="String" />
              <el-option value="int" label="Integer" />
              <el-option value="float" label="Float" />
              <el-option value="bool" label="Boolean" />
            </el-select>
            <el-button size="small" type="danger" @click="removeServiceParam('input', idx)">删除</el-button>
          </div>
        </el-form-item>
        <el-form-item label="输出参数">
          <el-button type="success" size="small" @click="addServiceParam('output')">添加参数</el-button>
          <div v-for="(param, idx) in serviceForm.output_params" :key="idx" class="param-row">
            <el-input v-model="param.identifier" placeholder="标识符" size="small" style="width: 120px;" />
            <el-input v-model="param.name" placeholder="名称" size="small" style="width: 120px;" />
            <el-select v-model="param.dataType" size="small" style="width: 100px;">
              <el-option value="string" label="String" />
              <el-option value="int" label="Integer" />
              <el-option value="float" label="Float" />
              <el-option value="bool" label="Boolean" />
            </el-select>
            <el-button size="small" type="danger" @click="removeServiceParam('output', idx)">删除</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddServiceDialog = false">取消</el-button>
        <el-button type="primary" @click="saveService">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddEventDialog" :title="editingEvent ? '编辑事件' : '添加事件'" width="600px">
      <el-form :model="eventForm" label-width="100px">
        <el-form-item label="标识符" required>
          <el-input v-model="eventForm.identifier" placeholder="如 alert_temperature" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="eventForm.name" placeholder="如 温度告警" />
        </el-form-item>
        <el-form-item label="事件类型">
          <el-select v-model="eventForm.event_type">
            <el-option value="info" label="提示" />
            <el-option value="warning" label="警告" />
            <el-option value="error" label="错误" />
            <el-option value="critical" label="严重" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="eventForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="输出参数">
          <el-button type="success" size="small" @click="addEventParam()">添加参数</el-button>
          <div v-for="(param, idx) in eventForm.output_params" :key="idx" class="param-row">
            <el-input v-model="param.identifier" placeholder="标识符" size="small" style="width: 120px;" />
            <el-input v-model="param.name" placeholder="名称" size="small" style="width: 120px;" />
            <el-select v-model="param.dataType" size="small" style="width: 100px;">
              <el-option value="string" label="String" />
              <el-option value="int" label="Integer" />
              <el-option value="float" label="Float" />
              <el-option value="bool" label="Boolean" />
            </el-select>
            <el-button size="small" type="danger" @click="removeEventParam(idx)">删除</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddEventDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEvent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api.js'
import { ElMessage } from 'element-plus'
import { Check, Box, Plus } from '@element-plus/icons-vue'

const router = useRouter()

const products = ref([])
const selectedProduct = ref('')
const saving = ref(false)
const activeTab = ref('properties')

const localProperties = ref([])
const localServices = ref([])
const localEvents = ref([])

const showAddPropertyDialog = ref(false)
const showAddServiceDialog = ref(false)
const showAddEventDialog = ref(false)

const editingProperty = ref(null)
const editingService = ref(null)
const editingEvent = ref(null)

const propertyForm = reactive({
  identifier: '',
  name: '',
  data_type: 'float',
  access_type: 'read_only',
  unit: '',
  min_value: '',
  max_value: '',
  step: '',
  description: '',
})

const serviceForm = reactive({
  identifier: '',
  name: '',
  description: '',
  input_params: [],
  output_params: [],
})

const eventForm = reactive({
  identifier: '',
  name: '',
  event_type: 'info',
  description: '',
  output_params: [],
})

const PROPERTY_TEMPLATES = {
  temperature: { identifier: 'temperature', name: '温度', data_type: 'float', access_type: 'read_only', unit: '°C', min_value: '-40', max_value: '80', step: '0.1' },
  humidity: { identifier: 'humidity', name: '湿度', data_type: 'float', access_type: 'read_only', unit: '%', min_value: '0', max_value: '100', step: '0.1' },
  light_intensity: { identifier: 'light_intensity', name: '光照强度', data_type: 'float', access_type: 'read_only', unit: 'lux', min_value: '0', max_value: '100000', step: '1' },
  soil_moisture: { identifier: 'soil_moisture', name: '土壤湿度', data_type: 'float', access_type: 'read_only', unit: '%', min_value: '0', max_value: '100', step: '0.1' },
  co2: { identifier: 'co2', name: 'CO₂浓度', data_type: 'float', access_type: 'read_only', unit: 'ppm', min_value: '0', max_value: '10000', step: '1' },
  wind_speed: { identifier: 'wind_speed', name: '风速', data_type: 'float', access_type: 'read_only', unit: 'm/s', min_value: '0', max_value: '50', step: '0.1' },
  soil_ph: { identifier: 'soil_ph', name: '土壤pH', data_type: 'float', access_type: 'read_only', unit: 'pH', min_value: '0', max_value: '14', step: '0.1' },
  rainfall: { identifier: 'rainfall', name: '雨量', data_type: 'float', access_type: 'read_only', unit: 'mm', min_value: '0', max_value: '200', step: '0.1' },
  soil_temperature: { identifier: 'soil_temperature', name: '土壤温度', data_type: 'float', access_type: 'read_only', unit: '°C', min_value: '-20', max_value: '50', step: '0.1' },
}

const SERVICE_TEMPLATES = {
  set_fan: { identifier: 'set_fan', name: '通风扇控制', description: '控制通风扇开关', input_params: [{ identifier: 'status', name: '状态', dataType: 'bool' }] },
  set_light: { identifier: 'set_light', name: '补光灯控制', description: '控制补光灯开关和亮度', input_params: [{ identifier: 'status', name: '状态', dataType: 'bool' }, { identifier: 'brightness', name: '亮度', dataType: 'int' }] },
  set_pump: { identifier: 'set_pump', name: '水泵控制', description: '控制灌溉水泵开关', input_params: [{ identifier: 'status', name: '状态', dataType: 'bool' }] },
  set_curve: { identifier: 'set_curve', name: '卷帘控制', description: '控制遮阳卷帘', input_params: [{ identifier: 'status', name: '状态', dataType: 'bool' }, { identifier: 'percent', name: '开度', dataType: 'int' }] },
  set_valve: { identifier: 'set_valve', name: '电磁阀控制', description: '控制电磁阀开关', input_params: [{ identifier: 'status', name: '状态', dataType: 'bool' }] },
  set_heater: { identifier: 'set_heater', name: '加热膜控制', description: '控制加热膜开关', input_params: [{ identifier: 'status', name: '状态', dataType: 'bool' }] },
}

async function loadProducts() {
  try {
    const resp = await api.get('/products/', { params: { page: 1, page_size: 100 } })
    products.value = resp.data
  } catch (e) {
    console.error('Failed to load products:', e)
  }
}

async function loadProductData(productKey) {
  if (!productKey) return
  try {
    const resp = await api.get(`/products/${productKey}/tsl/detail`)
    localProperties.value = resp.data.properties || []
    localServices.value = resp.data.services || []
    localEvents.value = resp.data.events || []
    ElMessage.success('物模型数据已加载')
  } catch (e) {
    console.error('Failed to load product data:', e)
    ElMessage.error('加载物模型数据失败')
  }
}

function getDataTypeLabel(type) {
  const labels = { string: '字符串', int: '整数', float: '浮点数', bool: '布尔值', date: '日期', enum: '枚举', json: 'JSON' }
  return labels[type] || type
}

function getEventTypeTag(type) {
  const tags = { info: 'info', warning: 'warning', error: 'danger', critical: 'danger' }
  return tags[type] || 'info'
}

function getEventTypeLabel(type) {
  const labels = { info: '提示', warning: '警告', error: '错误', critical: '严重' }
  return labels[type] || type
}

function addPropertyFromTemplate(identifier) {
  const template = PROPERTY_TEMPLATES[identifier]
  if (!template) return
  
  const exists = localProperties.value.some(p => p.identifier === identifier)
  if (exists) {
    ElMessage.warning(`属性 "${template.name}" 已存在`)
    return
  }
  
  localProperties.value.push({ ...template, id: Date.now() })
  ElMessage.success(`已添加属性 "${template.name}"`)
}

function addServiceFromTemplate(identifier) {
  const template = SERVICE_TEMPLATES[identifier]
  if (!template) return
  
  const exists = localServices.value.some(s => s.identifier === identifier)
  if (exists) {
    ElMessage.warning(`服务 "${template.name}" 已存在`)
    return
  }
  
  localServices.value.push({ ...template, id: Date.now() })
  ElMessage.success(`已添加服务 "${template.name}"`)
}

function editProperty(prop) {
  editingProperty.value = prop
  Object.assign(propertyForm, {
    identifier: prop.identifier,
    name: prop.name,
    data_type: prop.data_type,
    access_type: prop.access_type,
    unit: prop.unit || '',
    min_value: prop.min_value || '',
    max_value: prop.max_value || '',
    step: prop.step || '',
    description: prop.description || '',
  })
  showAddPropertyDialog.value = true
}

function removeProperty(prop) {
  const idx = localProperties.value.findIndex(p => p.id === prop.id || p.identifier === prop.identifier)
  if (idx > -1) {
    localProperties.value.splice(idx, 1)
    ElMessage.success('属性已删除')
  }
}

function saveProperty() {
  if (editingProperty.value) {
    const idx = localProperties.value.findIndex(p => p.id === editingProperty.value.id)
    if (idx > -1) {
      localProperties.value[idx] = { ...localProperties.value[idx], ...propertyForm }
    }
    editingProperty.value = null
  } else {
    localProperties.value.push({ ...propertyForm, id: Date.now() })
  }
  showAddPropertyDialog.value = false
  resetPropertyForm()
  ElMessage.success('属性已保存')
}

function resetPropertyForm() {
  Object.assign(propertyForm, {
    identifier: '',
    name: '',
    data_type: 'float',
    access_type: 'read_only',
    unit: '',
    min_value: '',
    max_value: '',
    step: '',
    description: '',
  })
}

function editService(svc) {
  editingService.value = svc
  Object.assign(serviceForm, {
    identifier: svc.identifier,
    name: svc.name,
    description: svc.description || '',
    input_params: svc.input_params ? JSON.parse(JSON.stringify(svc.input_params)) : [],
    output_params: svc.output_params ? JSON.parse(JSON.stringify(svc.output_params)) : [],
  })
  showAddServiceDialog.value = true
}

function removeService(svc) {
  const idx = localServices.value.findIndex(s => s.id === svc.id || s.identifier === svc.identifier)
  if (idx > -1) {
    localServices.value.splice(idx, 1)
    ElMessage.success('服务已删除')
  }
}

function addServiceParam(type) {
  serviceForm[`${type}_params`].push({ identifier: '', name: '', dataType: 'string' })
}

function removeServiceParam(type, idx) {
  serviceForm[`${type}_params`].splice(idx, 1)
}

function saveService() {
  if (editingService.value) {
    const idx = localServices.value.findIndex(s => s.id === editingService.value.id)
    if (idx > -1) {
      localServices.value[idx] = { ...localServices.value[idx], ...serviceForm }
    }
    editingService.value = null
  } else {
    localServices.value.push({ ...serviceForm, id: Date.now() })
  }
  showAddServiceDialog.value = false
  resetServiceForm()
  ElMessage.success('服务已保存')
}

function resetServiceForm() {
  Object.assign(serviceForm, {
    identifier: '',
    name: '',
    description: '',
    input_params: [],
    output_params: [],
  })
}

function editEvent(evt) {
  editingEvent.value = evt
  Object.assign(eventForm, {
    identifier: evt.identifier,
    name: evt.name,
    event_type: evt.event_type || 'info',
    description: evt.description || '',
    output_params: evt.output_params ? JSON.parse(JSON.stringify(evt.output_params)) : [],
  })
  showAddEventDialog.value = true
}

function removeEvent(evt) {
  const idx = localEvents.value.findIndex(e => e.id === evt.id || e.identifier === evt.identifier)
  if (idx > -1) {
    localEvents.value.splice(idx, 1)
    ElMessage.success('事件已删除')
  }
}

function addEventParam() {
  eventForm.output_params.push({ identifier: '', name: '', dataType: 'string' })
}

function removeEventParam(idx) {
  eventForm.output_params.splice(idx, 1)
}

function saveEvent() {
  if (editingEvent.value) {
    const idx = localEvents.value.findIndex(e => e.id === editingEvent.value.id)
    if (idx > -1) {
      localEvents.value[idx] = { ...localEvents.value[idx], ...eventForm }
    }
    editingEvent.value = null
  } else {
    localEvents.value.push({ ...eventForm, id: Date.now() })
  }
  showAddEventDialog.value = false
  resetEventForm()
  ElMessage.success('事件已保存')
}

function resetEventForm() {
  Object.assign(eventForm, {
    identifier: '',
    name: '',
    event_type: 'info',
    description: '',
    output_params: [],
  })
}

async function saveAllChanges() {
  if (!selectedProduct.value) {
    ElMessage.warning('请先选择产品')
    return
  }
  
  saving.value = true
  try {
    for (const prop of localProperties.value) {
      if (prop.id && typeof prop.id === 'number' && prop.id > 1000000000) {
        await api.post(`/products/${selectedProduct.value}/properties`, {
          identifier: prop.identifier,
          name: prop.name,
          data_type: prop.data_type,
          access_type: prop.access_type,
          unit: prop.unit,
          min_value: prop.min_value,
          max_value: prop.max_value,
          step: prop.step,
          description: prop.description,
        })
      } else if (prop.id) {
        await api.put(`/products/${selectedProduct.value}/properties/${prop.id}`, {
          identifier: prop.identifier,
          name: prop.name,
          data_type: prop.data_type,
          access_type: prop.access_type,
          unit: prop.unit,
          min_value: prop.min_value,
          max_value: prop.max_value,
          step: prop.step,
          description: prop.description,
        })
      }
    }
    
    for (const svc of localServices.value) {
      if (svc.id && typeof svc.id === 'number' && svc.id > 1000000000) {
        await api.post(`/products/${selectedProduct.value}/services`, {
          identifier: svc.identifier,
          name: svc.name,
          description: svc.description,
          input_params: svc.input_params,
          output_params: svc.output_params,
        })
      } else if (svc.id) {
        await api.put(`/products/${selectedProduct.value}/services/${svc.id}`, {
          identifier: svc.identifier,
          name: svc.name,
          description: svc.description,
          input_params: svc.input_params,
          output_params: svc.output_params,
        })
      }
    }
    
    for (const evt of localEvents.value) {
      if (evt.id && typeof evt.id === 'number' && evt.id > 1000000000) {
        await api.post(`/products/${selectedProduct.value}/events`, {
          identifier: evt.identifier,
          name: evt.name,
          event_type: evt.event_type,
          description: evt.description,
          output_params: evt.output_params,
        })
      } else if (evt.id) {
        await api.put(`/products/${selectedProduct.value}/events/${evt.id}`, {
          identifier: evt.identifier,
          name: evt.name,
          event_type: evt.event_type,
          description: evt.description,
          output_params: evt.output_params,
        })
      }
    }
    
    await loadProductData(selectedProduct.value)
    ElMessage.success('所有更改已保存')
  } catch (e) {
    console.error('Failed to save changes:', e)
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

function goToProducts() {
  router.push('/products')
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.thing-model-editor {
  padding: 0;
}

.editor-header {
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

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-actions :deep(.el-select) {
  width: 200px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  color: #909399;
}

.empty-state p {
  margin-top: 16px;
  font-size: 16px;
}

.empty-state button {
  margin-top: 24px;
}

.editor-content {
  display: flex;
  gap: 24px;
}

.editor-sidebar {
  width: 280px;
  flex-shrink: 0;
}

.sidebar-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.quick-add-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.quick-add-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-add-item:hover {
  background: #ecf5ff;
  transform: translateY(-2px);
}

.item-icon {
  font-size: 18px;
}

.item-name {
  font-size: 12px;
  color: #606266;
}

.editor-main {
  flex: 1;
}

.tab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.tab-title {
  font-size: 13px;
  color: #909399;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.model-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #ebeef5;
}

.model-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.prop-card {
  border-left: 4px solid #409eff;
}

.service-card {
  border-left: 4px solid #67c23a;
}

.event-card {
  border-left: 4px solid #e6a23c;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.card-icon {
  font-size: 16px;
}

.card-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.card-actions {
  display: flex;
  gap: 4px;
}

.card-actions :deep(.el-button) {
  padding: 0 8px;
  font-size: 11px;
}

.card-body {
  padding: 14px 16px;
}

.prop-info {
  display: flex;
  margin-bottom: 8px;
}

.prop-info:last-child {
  margin-bottom: 0;
}

.info-label {
  width: 70px;
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.info-value {
  flex: 1;
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.param-name {
  font-size: 12px;
  color: #606266;
}

.param-type {
  font-size: 11px;
  color: #909399;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
}

.empty-card p {
  margin-top: 12px;
  font-size: 13px;
  color: #909399;
}

.param-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

@media (max-width: 1200px) {
  .editor-content {
    flex-direction: column;
  }
  
  .editor-sidebar {
    width: 100%;
  }
  
  .quick-add-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .quick-add-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .model-grid {
    grid-template-columns: 1fr;
  }
}
</style>
