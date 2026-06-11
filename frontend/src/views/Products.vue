<template>
  <div class="products-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('products.title') }}</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            {{ $t('products.addProduct') }}
          </el-button>
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
            <el-table-column prop="access_type" :label="$t('products.accessType')" />
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
            <el-button type="primary" size="small" @click="showServiceDialog = true">{{ $t('products.addService') }}</el-button>
          </div>
          <el-table :data="editForm.services" style="width: 100%">
            <el-table-column prop="identifier" :label="$t('products.identifier')" />
            <el-table-column prop="name" :label="$t('products.name')" />
            <el-table-column prop="description" :label="$t('products.description')" />
            <el-table-column :label="$t('common.actions')" width="100">
              <template #default="{ row }">
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
            <el-option value="r" label="Read Only" />
            <el-option value="w" label="Write Only" />
            <el-option value="rw" label="Read/Write" />
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

    <el-dialog v-model="showServiceDialog" :title="$t('products.addService')" width="500px">
      <el-form :model="serviceForm" label-width="100px">
        <el-form-item :label="$t('products.identifier')">
          <el-input v-model="serviceForm.identifier" />
        </el-form-item>
        <el-form-item :label="$t('products.name')">
          <el-input v-model="serviceForm.name" />
        </el-form-item>
        <el-form-item :label="$t('products.description')">
          <el-input v-model="serviceForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="Input Parameters">
          <el-input v-model="serviceForm.input_params" type="textarea" :rows="3" placeholder='[{"name": "param1", "type": "string", "required": true}]' />
          <div class="form-hint">Format: [{"name": "param_name", "type": "string/int/float/bool", "required": true/false, "default": "value"}]</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showServiceDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddService">{{ $t('common.save') }}</el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { useProductStore } from '../stores/product.js'
import { ElMessage, ElMessageBox } from 'element-plus'

const productStore = useProductStore()

const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showPropertyDialog = ref(false)
const showServiceDialog = ref(false)
const showEventDialog = ref(false)
const activeTab = ref('basic')

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
  access_type: 'r',
  unit: ''
})

const serviceForm = reactive({
  identifier: '',
  name: '',
  description: '',
  input_params: '[]'
})

const eventForm = reactive({
  identifier: '',
  name: '',
  event_type: 'info'
})

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

async function handleAddService() {
  try {
    let inputParams = []
    try {
      if (serviceForm.input_params) {
        inputParams = JSON.parse(serviceForm.input_params)
      }
    } catch (e) {
      ElMessage.error('Invalid input parameters format')
      return
    }
    await productStore.addService(editForm.product_key, {
      ...serviceForm,
      input_params: inputParams
    })
    ElMessage.success('Service added')
    showServiceDialog.value = false
    await editProduct({ product_key: editForm.product_key })
    Object.keys(serviceForm).forEach(k => serviceForm[k] = '')
    serviceForm.input_params = '[]'
  } catch (error) {
    ElMessage.error('Failed to add service')
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

.tab-actions {
  margin-bottom: 16px;
}
</style>
