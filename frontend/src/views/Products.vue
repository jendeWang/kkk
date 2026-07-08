<template>
  <div class="products-page">
    <el-alert
      type="success"
      :closable="false"
      show-icon
      class="page-intro"
    >
      <template #title>📦 产品 = 设备的"模板/型号"</template>
      <template #default>
        产品定义了一类设备的<strong>物模型</strong>（有哪些传感器、能执行什么命令、会触发什么事件）。
        例如："智慧大棚标准款"、"畜牧养殖款"等。
        <br/>
        <strong>设备</strong>是产品下的具体实例（一台真实的设备），
        而<strong>设备分组</strong>是把设备按位置/用途归类整理。
        <router-link to="/groups" style="margin-left: 8px;">去管理设备分组 →</router-link>
      </template>
    </el-alert>

    <el-card style="margin-top: 16px;">
      <template #header>
        <div class="card-header">
          <span>{{ $t('products.title') }}</span>
          <div class="header-buttons">
            <el-button type="success" @click="showTemplateDialog = true">
              <el-icon><MagicStick /></el-icon>
              从模板创建
            </el-button>
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              {{ $t('products.addProduct') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="productStore.products" style="width: 100%" v-loading="loading">
        <el-table-column prop="product_key" :label="$t('products.productKey')" width="180" />
        <el-table-column prop="name" :label="$t('products.productName')" />
        <el-table-column prop="category" :label="$t('products.category')" />
        <el-table-column prop="model" :label="$t('products.model')" />
        <el-table-column prop="manufacturer" :label="$t('products.manufacturer')" />
        <el-table-column :label="$t('common.actions')" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editProduct(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" :title="$t('products.addProduct')" width="600px">
      <el-form :model="productForm" label-width="100px">
        <el-form-item :label="$t('products.productName')">
          <el-input v-model="productForm.name" />
        </el-form-item>
        <el-form-item :label="$t('products.category')">
          <el-input v-model="productForm.category" />
        </el-form-item>
        <el-form-item :label="$t('products.model')">
          <el-input v-model="productForm.model" />
        </el-form-item>
        <el-form-item :label="$t('products.manufacturer')">
          <el-input v-model="productForm.manufacturer" />
        </el-form-item>
        <el-form-item :label="$t('products.description')">
          <el-input v-model="productForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAdd" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <el-dialog v-model="showTemplateDialog" title="选择产品模板" width="900px" class="template-dialog">
      <div class="template-intro">
        <el-alert
          type="info"
          :closable="false"
          title="选择一个模板，一键创建产品 + 设备 + 告警规则 + 自动化场景"
          description="新手推荐使用模板，免去手动配置的麻烦。如果需要完全自定义，请选择「新建产品」。"
        />
      </div>
      <div class="template-grid" v-loading="templatesLoading">
        <div
          v-for="tpl in templates"
          :key="tpl.template_id"
          class="template-card"
        >
          <div class="template-header">
            <span class="template-icon">{{ tpl.icon }}</span>
            <el-tag :color="getLevelColor(tpl.level)" effect="dark" size="small">{{ tpl.level }}</el-tag>
          </div>
          <div class="template-name">{{ tpl.name }}</div>
          <div class="template-desc">{{ tpl.description }}</div>
          <div class="template-stats">
            <div class="stat-item">
              <span class="stat-num">{{ tpl.sensor_count }}</span>
              <span class="stat-label">传感器</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ tpl.actuator_count }}</span>
              <span class="stat-label">执行器</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ tpl.alert_count }}</span>
              <span class="stat-label">告警</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ tpl.scene_count }}</span>
              <span class="stat-label">场景</span>
            </div>
          </div>
          <div class="template-tags">
            <el-tag v-for="tag in tpl.tags" :key="tag" size="small" type="info" effect="plain">{{ tag }}</el-tag>
          </div>
          <el-button type="primary" class="use-template-btn" @click="useTemplate(tpl)" :loading="templateCreating">
            使用此模板
          </el-button>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showEditDialog" :title="$t('products.editProduct')" width="800px">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="$t('products.tabs.basic')" name="basic">
          <el-form :model="editForm" label-width="100px">
            <el-form-item :label="$t('products.productKey')">
              <el-input v-model="editForm.product_key" disabled />
            </el-form-item>
            <el-form-item :label="$t('products.productName')">
              <el-input v-model="editForm.name" />
            </el-form-item>
            <el-form-item :label="$t('products.category')">
              <el-input v-model="editForm.category" />
            </el-form-item>
            <el-form-item :label="$t('products.model')">
              <el-input v-model="editForm.model" />
            </el-form-item>
            <el-form-item :label="$t('products.manufacturer')">
              <el-input v-model="editForm.manufacturer" />
            </el-form-item>
            <el-form-item :label="$t('products.description')">
              <el-input v-model="editForm.description" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane :label="$t('products.tabs.properties')" name="properties">
          <div class="tab-actions">
            <el-button type="primary" size="small" @click="showPropertyDialog = true">{{ $t('products.addProperty') }}</el-button>
          </div>
          <el-table :data="editForm.properties" style="width: 100%">
            <el-table-column prop="identifier" :label="$t('products.identifier')" />
            <el-table-column prop="name" :label="$t('products.name')" />
            <el-table-column prop="data_type" :label="$t('products.dataType')" />
            <el-table-column :label="$t('products.accessType')">
              <template #default="{ row }">
                {{ row.access_type === 'read_only' ? 'Read Only' : (row.access_type === 'read_write' ? 'Read/Write' : row.access_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="unit" :label="$t('products.unit')" />
            <el-table-column :label="$t('common.actions')" width="100">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="deleteProperty(row.identifier)">{{ $t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane :label="$t('products.tabs.services')" name="services">
          <div class="tab-actions">
            <el-button type="primary" size="small" @click="openAddServiceDialog">{{ $t('products.addService') }}</el-button>
          </div>
          <el-table :data="editForm.services" style="width: 100%">
            <el-table-column prop="identifier" :label="$t('products.identifier')" />
            <el-table-column prop="name" :label="$t('products.name')" />
            <el-table-column prop="description" :label="$t('products.description')" />
            <el-table-column :label="$t('common.actions')" width="180">
              <template #default="{ row }">
                <el-button size="small" @click="openEditServiceDialog(row)">{{ $t('common.edit') }}</el-button>
                <el-button size="small" type="danger" @click="deleteService(row.identifier)">{{ $t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane :label="$t('products.tabs.events')" name="events">
          <div class="tab-actions">
            <el-button type="primary" size="small" @click="showEventDialog = true">{{ $t('products.addEvent') }}</el-button>
          </div>
          <el-table :data="editForm.events" style="width: 100%">
            <el-table-column prop="identifier" :label="$t('products.identifier')" />
            <el-table-column prop="name" :label="$t('products.name')" />
            <el-table-column prop="event_type" label="Type" />
            <el-table-column :label="$t('common.actions')" width="100">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="deleteEvent(row.identifier)">{{ $t('common.delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="物模型TSL" name="tsl">
          <div class="tsl-actions">
            <el-button type="primary" @click="exportTSL">
              <el-icon><Download /></el-icon>
              导出TSL (JSON)
            </el-button>
            <el-upload
              :show-file-list="false"
              :before-upload="importTSL"
              accept=".json"
              style="display: inline-block; margin-left: 12px;"
            >
              <el-button type="success">
                <el-icon><Upload /></el-icon>
                导入TSL
              </el-button>
            </el-upload>
          </div>
          <el-descriptions :column="2" border style="margin-top: 20px;">
            <el-descriptions-item label="版本">{{ tslData.version || '-' }}</el-descriptions-item>
            <el-descriptions-item label="产品名称">{{ tslData.name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="属性数量">{{ tslData.properties?.length || 0 }}</el-descriptions-item>
            <el-descriptions-item label="服务数量">{{ tslData.services?.length || 0 }}</el-descriptions-item>
            <el-descriptions-item label="事件数量">{{ tslData.events?.length || 0 }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ tslData.category || '-' }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 20px;">
            <div class="tsl-section-title">属性列表 (Properties)</div>
            <el-table :data="tslData.properties || []" size="small" style="width: 100%">
              <el-table-column prop="identifier" label="标识符" width="140" />
              <el-table-column prop="name" label="名称" width="120" />
              <el-table-column prop="dataType" label="类型" width="80" />
              <el-table-column prop="accessType" label="读写" width="100">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.accessType === 'read_only' ? 'info' : 'success'">
                    {{ row.accessType === 'read_only' ? '只读' : '读写' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="规格">
                <template #default="{ row }">
                  <span v-if="row.specs">
                    <template v-if="row.specs.min !== undefined && row.specs.min !== null">min:{{ row.specs.min }} </template>
                    <template v-if="row.specs.max !== undefined && row.specs.max !== null">max:{{ row.specs.max }} </template>
                    <template v-if="row.specs.step !== undefined && row.specs.step !== null">step:{{ row.specs.step }} </template>
                    <template v-if="row.specs.unit">单位:{{ row.specs.unit }}</template>
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showEditDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPropertyDialog" :title="$t('products.addProperty')" width="500px">
      <el-form :model="propertyForm" label-width="100px">
        <el-form-item :label="$t('products.identifier')">
          <el-input v-model="propertyForm.identifier" />
        </el-form-item>
        <el-form-item :label="$t('products.name')">
          <el-input v-model="propertyForm.name" />
        </el-form-item>
        <el-form-item :label="$t('products.dataType')">
          <el-select v-model="propertyForm.data_type">
            <el-option value="string" label="String" />
            <el-option value="int" label="Integer" />
            <el-option value="float" label="Float" />
            <el-option value="bool" label="Boolean" />
            <el-option value="date" label="Date" />
            <el-option value="enum" label="Enum" />
            <el-option value="json" label="JSON" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('products.accessType')">
          <el-select v-model="propertyForm.access_type">
            <el-option value="read_only" label="Read Only" />
            <el-option value="read_write" label="Read/Write" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('products.unit')">
          <el-input v-model="propertyForm.unit" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPropertyDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddProperty">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showServiceDialog" :title="editingService ? 'Edit Service' : $t('products.addService')" width="700px">
      <el-form :model="serviceForm" label-width="100px">
        <el-form-item :label="$t('products.identifier')" required>
          <el-input v-model="serviceForm.identifier" placeholder="e.g. set_light, get_status" />
        </el-form-item>
        <el-form-item :label="$t('products.name')" required>
          <el-input v-model="serviceForm.name" placeholder="e.g. 设置灯光, 获取状态" />
        </el-form-item>
        <el-form-item :label="$t('products.description')">
          <el-input v-model="serviceForm.description" type="textarea" placeholder="Service description..." />
        </el-form-item>
      </el-form>

      <div class="params-section">
        <div class="params-header">
          <span>Input Parameters (服务参数定义)</span>
          <el-button size="small" type="primary" @click="addServiceParam">+ Add Parameter</el-button>
        </div>

        <div v-if="serviceParams.length === 0" class="params-empty">
          No parameters defined. Click "Add Parameter" to define command parameters.
        </div>

        <div v-for="(param, index) in serviceParams" :key="index" class="param-item">
          <el-form label-width="100px" class="param-form">
            <el-form-item label="Name" required>
              <el-input v-model="param.name" placeholder="e.g. brightness" />
            </el-form-item>
            <el-form-item label="Type" required>
              <el-select v-model="param.type" style="width: 100%" @change="onParamTypeChange(param)">
                <el-option value="string" label="String" />
                <el-option value="int" label="Integer" />
                <el-option value="float" label="Float" />
                <el-option value="bool" label="Boolean" />
              </el-select>
            </el-form-item>
            <el-form-item label="Required">
              <el-switch v-model="param.required" />
            </el-form-item>
            <el-form-item v-if="param.type !== 'bool'" label="Default">
              <el-input v-model="param.default" :placeholder="getDefaultPlaceholder(param.type)" />
            </el-form-item>
            <el-form-item v-else label="Default">
              <el-switch v-model="param.bool_default" />
            </el-form-item>
            <el-form-item v-if="param.type !== 'bool'" label="Options">
              <el-select
                v-model="param.options"
                multiple
                filterable
                allow-create
                default-first-option
                style="width: 100%"
                placeholder="输入值后回车添加多个可选值"
              >
                <el-option v-for="opt in param.options" :key="opt" :value="opt" :label="opt" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="param.type !== 'bool'" label="Allow Custom">
              <el-switch v-model="param.allow_custom" />
            </el-form-item>
            <el-form-item v-if="param.type === 'int' || param.type === 'float'" label="Min">
              <el-input v-model="param.min" placeholder="Minimum value" />
            </el-form-item>
            <el-form-item v-if="param.type === 'int' || param.type === 'float'" label="Max">
              <el-input v-model="param.max" placeholder="Maximum value" />
            </el-form-item>
            <el-form-item v-if="param.type === 'int' || param.type === 'float'" label="Step">
              <el-input v-model="param.step" :placeholder="param.type === 'int' ? '1' : '0.01'" />
            </el-form-item>
            <el-form-item v-if="param.type === 'string'" label="Pattern">
              <el-input v-model="param.pattern" placeholder="正则表达式, e.g. ^[a-zA-Z0-9_]+$" />
            </el-form-item>
            <el-form-item label="Description">
              <el-input v-model="param.description" placeholder="Parameter description" />
            </el-form-item>
            <el-form-item label="">
              <el-button size="small" type="danger" @click="removeServiceParam(index)">Remove</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>

      <template #footer>
        <el-button @click="closeServiceDialog">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveService" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEventDialog" :title="$t('products.addEvent')" width="500px">
      <el-form :model="eventForm" label-width="100px">
        <el-form-item :label="$t('products.identifier')">
          <el-input v-model="eventForm.identifier" />
        </el-form-item>
        <el-form-item :label="$t('products.name')">
          <el-input v-model="eventForm.name" />
        </el-form-item>
        <el-form-item label="Type">
          <el-select v-model="eventForm.event_type">
            <el-option value="info" label="Info" />
            <el-option value="warning" label="Warning" />
            <el-option value="error" label="Error" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEventDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddEvent">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useProductStore } from '../stores/product.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Upload, Plus, MagicStick } from '@element-plus/icons-vue'
import api from '../services/api.js'

const productStore = useProductStore()

const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)
const showTemplateDialog = ref(false)
const showEditDialog = ref(false)
const showPropertyDialog = ref(false)
const showServiceDialog = ref(false)
const showEventDialog = ref(false)
const activeTab = ref('basic')
const editingService = ref(null)

const productForm = reactive({
  name: '',
  category: '',
  model: '',
  manufacturer: '',
  description: ''
})

const editForm = reactive({
  product_key: '',
  name: '',
  category: '',
  model: '',
  manufacturer: '',
  description: '',
  properties: [],
  services: [],
  events: []
})

const propertyForm = reactive({
  identifier: '',
  name: '',
  data_type: 'string',
  access_type: 'read_only',
  unit: ''
})

const serviceForm = reactive({
  identifier: '',
  name: '',
  description: ''
})

const serviceParams = ref([])

function getDefaultPlaceholder(type) {
  if (type === 'string') return 'Default string value'
  if (type === 'int') return 'Default integer value (e.g. 100)'
  if (type === 'float') return 'Default float value (e.g. 0.5)'
  return 'Default value'
}

function onParamTypeChange(param) {
  if (param.type === 'bool') {
    param.bool_default = false
  } else {
    param.default = ''
  }
}

function addServiceParam() {
  serviceParams.value.push({
    name: '',
    type: 'string',
    required: false,
    default: '',
    bool_default: false,
    description: '',
    options: [],
    allow_custom: true,
    min: '',
    max: '',
    step: '',
    pattern: '^[a-zA-Z0-9_]+$'
  })
}

function removeServiceParam(index) {
  serviceParams.value.splice(index, 1)
}

function resetServiceForm() {
  serviceForm.identifier = ''
  serviceForm.name = ''
  serviceForm.description = ''
  serviceParams.value = []
  editingService.value = null
}

function openAddServiceDialog() {
  resetServiceForm()
  showServiceDialog.value = true
}

function openEditServiceDialog(service) {
  serviceForm.identifier = service.identifier
  serviceForm.name = service.name
  serviceForm.description = service.description || ''
  editingService.value = service

  if (Array.isArray(service.input_params)) {
    serviceParams.value = service.input_params.map(p => ({
      name: p.name || '',
      type: p.type || 'string',
      required: p.required || false,
      default: p.default !== undefined ? p.default : '',
      bool_default: p.type === 'bool' ? (p.default === true || p.default === 'true') : false,
      description: p.description || '',
      options: Array.isArray(p.options) ? p.options.map(String) : [],
      allow_custom: p.allow_custom !== false,
      min: p.min !== undefined ? String(p.min) : '',
      max: p.max !== undefined ? String(p.max) : '',
      step: p.step !== undefined ? String(p.step) : '',
      pattern: p.pattern || '^[a-zA-Z0-9_]+$'
    }))
  } else if (typeof service.input_params === 'object' && service.input_params) {
    serviceParams.value = Object.keys(service.input_params).map(key => {
      const def = service.input_params[key]
      return {
        name: key,
        type: typeof def === 'object' && def.type ? def.type : 'string',
        required: false,
        default: typeof def === 'object' && def.default !== undefined ? def.default : '',
        bool_default: false,
        description: typeof def === 'object' && def.description ? def.description : '',
        options: [],
        allow_custom: true,
        min: '',
        max: '',
        step: '',
        pattern: '^[a-zA-Z0-9_]+$'
      }
    })
  } else {
    serviceParams.value = []
  }

  showServiceDialog.value = true
}

function closeServiceDialog() {
  showServiceDialog.value = false
  resetServiceForm()
}

function buildServicePayload() {
  const params = serviceParams.value
    .filter(p => p.name)
    .map(p => {
      const payload = {
        name: p.name,
        type: p.type,
        required: p.required,
        description: p.description || ''
      }
      if (p.type === 'bool') {
        payload.default = p.bool_default
      } else if (p.default !== '' && p.default !== undefined && p.default !== null) {
        if (p.type === 'int') {
          const v = parseInt(p.default)
          payload.default = isNaN(v) ? p.default : v
        } else if (p.type === 'float') {
          const v = parseFloat(p.default)
          payload.default = isNaN(v) ? p.default : v
        } else {
          payload.default = p.default
        }
      }
      if (p.type !== 'bool') {
        if (Array.isArray(p.options) && p.options.length > 0) {
          payload.options = p.options.filter(o => o !== '' && o !== null && o !== undefined)
        }
        payload.allow_custom = p.allow_custom
      }
      if (p.type === 'int' || p.type === 'float') {
        if (p.min !== '' && p.min !== null && p.min !== undefined) {
          payload.min = p.type === 'int' ? parseInt(p.min) : parseFloat(p.min)
        }
        if (p.max !== '' && p.max !== null && p.max !== undefined) {
          payload.max = p.type === 'int' ? parseInt(p.max) : parseFloat(p.max)
        }
        if (p.step !== '' && p.step !== null && p.step !== undefined) {
          payload.step = p.type === 'int' ? parseInt(p.step) : parseFloat(p.step)
        }
      }
      if (p.type === 'string' && p.pattern) {
        payload.pattern = p.pattern
      }
      return payload
    })

  return {
    identifier: serviceForm.identifier,
    name: serviceForm.name,
    description: serviceForm.description,
    input_params: params.length > 0 ? params : null,
    output_params: null
  }
}

async function handleSaveService() {
  if (!serviceForm.identifier || !serviceForm.name) {
    ElMessage.error('Please fill in identifier and name')
    return
  }

  for (const param of serviceParams.value) {
    if (!param.name) {
      ElMessage.error('Parameter name is required')
      return
    }
    if (param.type === 'int' || param.type === 'float') {
      if (param.min !== '' && param.max !== '') {
        const mn = parseFloat(param.min)
        const mx = parseFloat(param.max)
        if (!isNaN(mn) && !isNaN(mx) && mn > mx) {
          ElMessage.error(`Parameter "${param.name}": min (${mn}) cannot be greater than max (${mx})`)
          return
        }
      }
    }
  }

  try {
    const payload = buildServicePayload()
    if (editingService.value) {
      await productStore.updateService(editForm.product_key, editingService.value.id, payload)
      ElMessage.success('Service updated')
    } else {
      await productStore.addService(editForm.product_key, payload)
      ElMessage.success('Service added')
    }
    showServiceDialog.value = false
    await editProduct({ product_key: editForm.product_key })
    resetServiceForm()
  } catch (error) {
    ElMessage.error('Failed to save service')
  }
}

const eventForm = reactive({
  identifier: '',
  name: '',
  event_type: 'info'
})

const tslData = reactive({
  version: '',
  product_key: '',
  name: '',
  category: '',
  description: '',
  properties: [],
  services: [],
  events: []
})

watch(activeTab, async (newTab) => {
  if (newTab === 'tsl' && editForm.product_key) {
    await loadTSL()
  }
})

async function loadTSL() {
  try {
    const resp = await api.get(`/products/${editForm.product_key}/tsl`)
    Object.assign(tslData, resp.data)
  } catch (e) {
    console.error('Failed to load TSL:', e)
  }
}

async function exportTSL() {
  try {
    const response = await api.get(`/products/${editForm.product_key}/tsl/export`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${editForm.product_key}_tsl.json`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('导出成功')
  } catch (e) {
    console.error('TSL导出失败:', e)
    ElMessage.error('TSL导出失败: ' + (e.response?.data?.detail || e.message))
  }
}

function importTSL(file) {
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const tslJson = JSON.parse(e.target.result)
      await ElMessageBox.confirm(
        `确定要导入物模型创建新产品吗？\n产品名称: ${tslJson.name}\n属性: ${tslJson.properties?.length || 0}个\n服务: ${tslJson.services?.length || 0}个`,
        '导入确认',
        { type: 'info' }
      )
      const resp = await api.post('/products/tsl/import', tslJson)
      ElMessage.success(`产品"${resp.data.name}"创建成功`)
      showEditDialog.value = false
      await loadProducts()
    } catch (err) {
      if (err !== 'cancel') {
        ElMessage.error('导入失败: ' + (err.response?.data?.detail || err.message))
      }
    }
  }
  reader.readAsText(file)
  return false
}

async function loadProducts() {
  loading.value = true
  try {
    await productStore.fetchProducts()
  } catch (error) {
    ElMessage.error('Failed to load products')
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  saving.value = true
  try {
    await productStore.createProduct(productForm)
    ElMessage.success('Product created')
    showAddDialog.value = false
    Object.keys(productForm).forEach(k => productForm[k] = '')
    await loadProducts()
  } catch (error) {
    ElMessage.error('Failed to create product')
  } finally {
    saving.value = false
  }
}

// ===== 模板相关 =====
const templates = ref([])
const templatesLoading = ref(false)
const templateCreating = ref(false)

async function loadTemplates() {
  templatesLoading.value = true
  try {
    const resp = await api.get('/products/templates/list')
    templates.value = resp.data || []
  } catch (e) {
    console.error('加载模板失败:', e)
    ElMessage.error('加载模板列表失败')
  } finally {
    templatesLoading.value = false
  }
}

watch(showTemplateDialog, (val) => {
  if (val) {
    loadTemplates()
  }
})

function getLevelColor(level) {
  const colors = {
    '入门': '#909399',
    '推荐': '#67c23a',
    '专业': '#e6a23c',
  }
  return colors[level] || '#409eff'
}

async function useTemplate(template) {
  try {
    await ElMessageBox.confirm(
      `确定使用【${template.name}】创建产品吗？\n\n将自动为您创建：\n• ${template.sensor_count} 个传感器属性\n• ${template.actuator_count} 个执行器/服务\n• ${template.alert_count} 条告警规则\n• ${template.scene_count} 个自动化场景\n\n（还会自动创建1台默认设备）`,
      '确认使用模板',
      {
        confirmButtonText: '立即创建',
        cancelButtonText: '我再想想',
        type: 'info',
      }
    )
  } catch {
    return
  }

  templateCreating.value = true
  try {
    await api.post(`/products/from-template/${template.template_id}`)
    ElMessage.success(`🎉 已从模板【${template.name}】创建成功！`)
    showTemplateDialog.value = false
    await loadProducts()
  } catch (e) {
    console.error('从模板创建失败:', e)
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    templateCreating.value = false
  }
}

async function editProduct(product) {
  try {
    const fullProduct = await productStore.fetchProduct(product.product_key)
    Object.assign(editForm, {
      product_key: fullProduct.product_key,
      name: fullProduct.name,
      category: fullProduct.category || '',
      model: fullProduct.model || '',
      manufacturer: fullProduct.manufacturer || '',
      description: fullProduct.description || '',
      properties: fullProduct.properties || [],
      services: fullProduct.services || [],
      events: fullProduct.events || []
    })
    showEditDialog.value = true
  } catch (error) {
    ElMessage.error('Failed to load product details')
  }
}

async function handleUpdate() {
  saving.value = true
  try {
    await productStore.updateProduct(editForm.product_key, {
      name: editForm.name,
      category: editForm.category,
      model: editForm.model,
      manufacturer: editForm.manufacturer,
      description: editForm.description
    })
    ElMessage.success('Product updated')
    showEditDialog.value = false
    await loadProducts()
  } catch (error) {
    ElMessage.error('Failed to update product')
  } finally {
    saving.value = false
  }
}

async function handleDelete(product) {
  try {
    await ElMessageBox.confirm('Delete this product?', 'Warning', { type: 'warning' })
    await productStore.deleteProduct(product.product_key)
    ElMessage.success('Product deleted')
    await loadProducts()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('Failed to delete product')
  }
}

async function handleAddProperty() {
  try {
    await productStore.addProperty(editForm.product_key, propertyForm)
    ElMessage.success('Property added')
    showPropertyDialog.value = false
    await editProduct({ product_key: editForm.product_key })
    Object.keys(propertyForm).forEach(k => propertyForm[k] = '')
  } catch (error) {
    ElMessage.error('Failed to add property')
  }
}

async function handleAddEvent() {
  try {
    await productStore.addEvent(editForm.product_key, eventForm)
    ElMessage.success('Event added')
    showEventDialog.value = false
    await editProduct({ product_key: editForm.product_key })
    Object.keys(eventForm).forEach(k => eventForm[k] = '')
  } catch (error) {
    ElMessage.error('Failed to add event')
  }
}

async function deleteProperty(identifier) {
  try {
    await productStore.deleteProperty(editForm.product_key, identifier)
    ElMessage.success('Property deleted')
    await editProduct({ product_key: editForm.product_key })
  } catch (error) {
    ElMessage.error('Failed to delete property')
  }
}

async function deleteService(identifier) {
  try {
    await productStore.deleteService(editForm.product_key, identifier)
    ElMessage.success('Service deleted')
    await editProduct({ product_key: editForm.product_key })
  } catch (error) {
    ElMessage.error('Failed to delete service')
  }
}

async function deleteEvent(identifier) {
  try {
    await productStore.deleteEvent(editForm.product_key, identifier)
    ElMessage.success('Event deleted')
    await editProduct({ product_key: editForm.product_key })
  } catch (error) {
    ElMessage.error('Failed to delete event')
  }
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.template-intro {
  margin-bottom: 20px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.template-card {
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.template-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.template-icon {
  font-size: 36px;
}

.template-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.template-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
  margin-bottom: 16px;
  min-height: 42px;
}

.template-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-item {
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.use-template-btn {
  width: 100%;
  margin-top: auto;
}

:deep(.template-dialog .el-dialog__body) {
  padding-top: 10px;
}

.tab-actions {
  margin-bottom: 16px;
}

.params-section {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  max-height: 450px;
  overflow-y: auto;
}

.params-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
  color: #303133;
}

.params-empty {
  text-align: center;
  color: #909399;
  padding: 20px;
  font-size: 14px;
}

.param-item {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 12px;
}

.param-form {
  margin-bottom: 0;
}

.param-form .el-form-item {
  margin-bottom: 8px;
}

.tsl-actions {
  display: flex;
  align-items: center;
}

.tsl-section-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  font-size: 14px;
}
</style>
