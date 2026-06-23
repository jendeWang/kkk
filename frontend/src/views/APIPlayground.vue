<template>
  <div class="api-playground-page">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速开始</span>
            </div>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="Base URL">
              <code>{{ baseUrl }}</code>
              <el-button size="small" type="primary" link @click="copyText(baseUrl)">复制</el-button>
            </el-descriptions-item>
            <el-descriptions-item label="认证方式">
              <el-tag type="success">API Key (Bearer Token)</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="选择 API Key">
              <el-select v-model="selectedApiKey" placeholder="选择一个 API Key" style="width: 280px">
                <el-option
                  v-for="key in apiKeys"
                  :key="key.id"
                  :label="key.name + ' (' + key.key.substring(0, 12) + '...)'"
                  :value="key.key"
                />
              </el-select>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" style="margin-top: 20px">
      <el-tab-pane label="API 调试" name="debug">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card>
              <template #header><span>接口列表</span></template>
              <el-input
                v-model="apiSearch"
                placeholder="搜索接口..."
                style="margin-bottom: 12px"
                clearable
              />
              <div class="api-list">
                <div
                  v-for="api in filteredApis"
                  :key="api.path + api.method"
                  class="api-item"
                  :class="{ active: selectedApi?.path === api.path && selectedApi?.method === api.method }"
                  @click="selectApi(api)"
                >
                  <el-tag :type="methodColor(api.method)" size="small" class="method-tag">
                    {{ api.method }}
                  </el-tag>
                  <span class="api-path">{{ api.path }}</span>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="16">
            <el-card v-if="selectedApi">
              <template #header>
                <div class="card-header">
                  <div>
                    <el-tag :type="methodColor(selectedApi.method)" size="small">
                      {{ selectedApi.method }}
                    </el-tag>
                    <span style="margin-left: 8px; font-weight: bold">{{ selectedApi.path }}</span>
                  </div>
                  <el-button type="primary" @click="sendRequest" :loading="requesting">
                    发送请求
                  </el-button>
                </div>
              </template>

              <el-form label-width="80px">
                <el-form-item label="Headers">
                  <div style="display: flex; gap: 8px; margin-bottom: 8px">
                    <el-input v-model="headerKey" placeholder="Key" style="width: 180px" />
                    <el-input v-model="headerValue" placeholder="Value" style="flex: 1" />
                    <el-button @click="addHeader">添加</el-button>
                  </div>
                  <div v-for="(v, k) in requestHeaders" :key="k" class="header-row">
                    <span class="header-key">{{ k }}</span>
                    <span class="header-value">{{ v }}</span>
                    <el-button size="small" type="danger" link @click="removeHeader(k)">删除</el-button>
                  </div>
                </el-form-item>

                <el-form-item v-if="hasQueryParams" label="Query 参数">
                  <el-input
                    v-model="queryParams"
                    type="textarea"
                    :rows="3"
                    placeholder='如: {"device_id": 1, "limit": 10}'
                  />
                </el-form-item>

                <el-form-item v-if="hasBody" label="Body">
                  <el-input
                    v-model="requestBody"
                    type="textarea"
                    :rows="6"
                    placeholder='JSON 请求体'
                  />
                </el-form-item>
              </el-form>

              <el-divider />

              <div class="response-section">
                <div class="response-header">
                  <span>响应</span>
                  <el-tag v-if="responseStatus" :type="responseStatus < 300 ? 'success' : 'danger'" size="small">
                    {{ responseStatus }}
                  </el-tag>
                  <el-button size="small" link @click="copyText(responseBody)">复制</el-button>
                </div>
                <pre class="response-body">{{ responseBody || '点击「发送请求」查看响应' }}</pre>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="实时数据 (SSE)" name="sse">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card>
              <template #header><span>SSE 通道</span></template>
              <div class="sse-channel-list">
                <div
                  v-for="channel in sseChannels"
                  :key="channel.id"
                  class="channel-item"
                  :class="{ active: activeSseChannel === channel.id }"
                  @click="selectSseChannel(channel.id)"
                >
                  <div class="channel-name">{{ channel.name }}</div>
                  <div class="channel-path">{{ channel.path }}</div>
                  <div class="channel-status">
                    <el-tag :type="sseConnected[channel.id] ? 'success' : 'info'" size="small">
                      {{ sseConnected[channel.id] ? '已连接' : '未连接' }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <el-button
                type="primary"
                style="width: 100%; margin-top: 12px"
                @click="toggleSseConnection"
                :disabled="!selectedApiKey"
              >
                {{ sseConnected[activeSseChannel] ? '断开连接' : '连接 SSE' }}
              </el-button>
              <el-button
                style="width: 100%; margin-top: 8px"
                @click="clearSseMessages"
              >
                清空消息
              </el-button>
            </el-card>
          </el-col>

          <el-col :span="16">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>实时消息 ({{ sseMessages.length }})</span>
                </div>
              </template>
              <div class="sse-messages">
                <div
                  v-for="(msg, idx) in sseMessages.slice().reverse()"
                  :key="idx"
                  class="sse-message"
                >
                  <div class="sse-message-header">
                    <el-tag size="small">{{ msg.event }}</el-tag>
                    <span class="sse-message-time">{{ msg.time }}</span>
                  </div>
                  <pre class="sse-message-body">{{ msg.data }}</pre>
                </div>
                <div v-if="sseMessages.length === 0" class="empty-messages">
                  暂无消息，连接 SSE 后开始接收
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="命令下发测试" name="command">
        <el-row :gutter="20">
          <el-col :span="10">
            <el-card>
              <template #header><span>发送命令</span></template>
              <el-form label-width="100px">
                <el-form-item label="选择设备">
                  <el-select v-model="commandForm.device_id" placeholder="选择设备" style="width: 100%">
                    <el-option
                      v-for="dev in devices"
                      :key="dev.id"
                      :label="dev.device_name + ' (' + dev.device_key + ')'"
                      :value="dev.id"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="服务标识">
                  <el-input v-model="commandForm.service_identifier" placeholder="如: set_light" />
                </el-form-item>
                <el-form-item label="参数 (JSON)">
                  <el-input
                    v-model="commandParamsJson"
                    type="textarea"
                    :rows="4"
                    placeholder='如: {"power": "on"}'
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="sendCommand" :loading="sendingCommand">
                    发送命令
                  </el-button>
                  <el-button @click="clearCommandForm">清空</el-button>
                </el-form-item>
              </el-form>

              <el-alert
                title="提示"
                type="info"
                :closable="false"
                style="margin-top: 12px"
              >
                <p>1. 在「实时数据」标签页连接 SSE 命令通道后，可实时看到命令响应</p>
                <p>2. 也可以在下方命令历史中点击「查询」查看状态</p>
              </el-alert>
            </el-card>
          </el-col>

          <el-col :span="14">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>命令历史</span>
                  <el-button size="small" @click="loadCommands">刷新</el-button>
                </div>
              </template>
              <el-table :data="commandHistory" style="width: 100%" size="small">
                <el-table-column prop="command_id" label="命令ID" width="200">
                  <template #default="{ row }">
                    <span class="command-id">{{ row.command_id.substring(0, 16) }}...</span>
                  </template>
                </el-table-column>
                <el-table-column prop="service_identifier" label="服务" width="140" />
                <el-table-column label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="statusColor(row.status)" size="small">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160">
                  <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" link @click="viewCommandDetail(row)">
                      详情
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="MQTT 接入" name="mqtt">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header><span>连接参数</span></template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="Broker 地址">
                  <code>{{ mqttConfig.host }}</code>
                  <el-button size="small" type="primary" link @click="copyText(mqttConfig.host)">复制</el-button>
                </el-descriptions-item>
                <el-descriptions-item label="端口">
                  <code>{{ mqttConfig.port }}</code>
                </el-descriptions-item>
                <el-descriptions-item label="协议">
                  <code>MQTT 3.1.1 / 5.0</code>
                </el-descriptions-item>
                <el-descriptions-item label="用户名">
                  <code>{{ mqttConfig.username }}</code>
                  <el-button size="small" type="primary" link @click="copyText(mqttConfig.username)">复制</el-button>
                </el-descriptions-item>
                <el-descriptions-item label="密码">
                  <code>{{ mqttConfig.password }}</code>
                  <el-button size="small" type="primary" link @click="copyText(mqttConfig.password)">复制</el-button>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header><span>Topic 规范</span></template>
              <el-table :data="mqttTopics" style="width: 100%" size="small">
                <el-table-column prop="direction" label="方向" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.direction === '订阅' ? 'success' : 'warning'" size="small">
                      {{ row.direction }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="topic" label="Topic">
                  <template #default="{ row }">
                    <code class="topic-code">{{ row.topic }}</code>
                  </template>
                </el-table-column>
                <el-table-column prop="desc" label="说明" width="120" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>

        <el-card style="margin-top: 20px">
          <template #header><span>消息格式示例</span></template>
          <el-tabs>
            <el-tab-pane label="遥测上报" name="telemetry">
              <pre class="code-block">{{ mqttExamples.telemetry }}</pre>
            </el-tab-pane>
            <el-tab-pane label="命令下发" name="command">
              <pre class="code-block">{{ mqttExamples.command }}</pre>
            </el-tab-pane>
            <el-tab-pane label="命令响应" name="response">
              <pre class="code-block">{{ mqttExamples.response }}</pre>
            </el-tab-pane>
            <el-tab-pane label="状态上报" name="status">
              <pre class="code-block">{{ mqttExamples.status }}</pre>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="commandDetailVisible" title="命令详情" width="600px">
      <el-descriptions :column="1" border v-if="currentCommand">
        <el-descriptions-item label="命令ID">{{ currentCommand.command_id }}</el-descriptions-item>
        <el-descriptions-item label="服务">{{ currentCommand.service_identifier }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusColor(currentCommand.status)">{{ currentCommand.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="输入参数">
          <pre class="inline-pre">{{ JSON.stringify(currentCommand.input_params, null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="输出数据" v-if="currentCommand.output_data">
          <pre class="inline-pre">{{ JSON.stringify(currentCommand.output_data, null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" v-if="currentCommand.error_message">
          <span style="color: #f56c6c">{{ currentCommand.error_message }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentCommand.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="发送时间" v-if="currentCommand.sent_at">{{ formatTime(currentCommand.sent_at) }}</el-descriptions-item>
        <el-descriptions-item label="执行时间" v-if="currentCommand.executed_at">{{ formatTime(currentCommand.executed_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const baseUrl = location.origin + '/api/v1'

const activeTab = ref('debug')
const apiSearch = ref('')
const selectedApi = ref(null)
const apiKeys = ref([])
const selectedApiKey = ref('')
const devices = ref([])

const requesting = ref(false)
const responseStatus = ref(null)
const responseBody = ref('')
const requestHeaders = reactive({})
const headerKey = ref('')
const headerValue = ref('')
const queryParams = ref('')
const requestBody = ref('')

const sseChannels = [
  { id: 'alerts', name: '告警事件', path: '/api/v1/sse/alerts' },
  { id: 'devices', name: '设备状态/遥测', path: '/api/v1/sse/devices' },
  { id: 'commands', name: '命令响应', path: '/api/v1/sse/commands' },
]
const activeSseChannel = ref('alerts')
const sseConnected = reactive({ alerts: false, devices: false, commands: false })
const sseMessages = ref([])
let sseSource = null

const commandForm = reactive({
  device_id: null,
  service_identifier: 'set_light',
})
const commandParamsJson = ref('{\n  "power": "on"\n}')
const sendingCommand = ref(false)
const commandHistory = ref([])
const commandDetailVisible = ref(false)
const currentCommand = ref(null)

const mqttConfig = {
  host: 'localhost',
  port: 1883,
  username: 'tksm4ju31ci0r0j8',
  password: '7cTf9UQYgcDK52zoRpNKnFdQ3EPlTkaV',
}

const mqttTopics = [
  { direction: '订阅', topic: 'devices/{device_key}/telemetry', desc: '遥测数据' },
  { direction: '订阅', topic: 'devices/{device_key}/status', desc: '设备状态' },
  { direction: '订阅', topic: 'devices/{device_key}/events', desc: '事件上报' },
  { direction: '订阅', topic: 'devices/{device_key}/commands/response', desc: '命令响应' },
  { direction: '发布', topic: 'devices/{device_key}/commands', desc: '下发命令' },
]

const mqttExamples = {
  telemetry: JSON.stringify({
    property_identifier: "temperature",
    value: 25.5,
    timestamp: "2026-06-23T08:00:00",
    quality: "good"
  }, null, 2),
  command: JSON.stringify({
    command_id: "cmd-uuid-xxx",
    service_identifier: "set_light",
    input_params: { power: "on", brightness: 80 },
    timestamp: "2026-06-23T08:00:00"
  }, null, 2),
  response: JSON.stringify({
    command_id: "cmd-uuid-xxx",
    status: "executed",
    output_data: { result: "success" },
    timestamp: "2026-06-23T08:00:01"
  }, null, 2),
  status: JSON.stringify({
    status: "online",
    timestamp: "2026-06-23T08:00:00"
  }, null, 2),
}

const apiList = [
  { method: 'GET', path: '/api/v1/devices/', desc: '获取设备列表', hasQuery: true, hasBody: false },
  { method: 'POST', path: '/api/v1/devices/', desc: '创建设备', hasQuery: false, hasBody: true },
  { method: 'GET', path: '/api/v1/devices/{device_id}', desc: '获取设备详情', hasQuery: false, hasBody: false },
  { method: 'PUT', path: '/api/v1/devices/{device_id}', desc: '更新设备', hasQuery: false, hasBody: true },
  { method: 'DELETE', path: '/api/v1/devices/{device_id}', desc: '删除设备', hasQuery: false, hasBody: false },
  { method: 'GET', path: '/api/v1/telemetry/', desc: '获取遥测数据列表', hasQuery: true, hasBody: false },
  { method: 'GET', path: '/api/v1/telemetry/devices/{device_id}', desc: '获取设备遥测', hasQuery: true, hasBody: false },
  { method: 'GET', path: '/api/v1/commands/', desc: '获取命令列表', hasQuery: true, hasBody: false },
  { method: 'POST', path: '/api/v1/commands/', desc: '下发命令', hasQuery: false, hasBody: true },
  { method: 'GET', path: '/api/v1/commands/{command_id}', desc: '获取命令详情', hasQuery: false, hasBody: false },
  { method: 'GET', path: '/api/v1/alerts/events', desc: '获取告警事件', hasQuery: true, hasBody: false },
  { method: 'GET', path: '/api/v1/alerts/rules', desc: '获取告警规则', hasQuery: false, hasBody: false },
  { method: 'GET', path: '/api/v1/products/', desc: '获取产品列表', hasQuery: false, hasBody: false },
  { method: 'GET', path: '/api/v1/api-keys/', desc: '获取 API Key 列表', hasQuery: false, hasBody: false },
  { method: 'GET', path: '/api/v1/auth/me', desc: '获取当前用户', hasQuery: false, hasBody: false },
]

const filteredApis = computed(() => {
  if (!apiSearch.value) return apiList
  const q = apiSearch.value.toLowerCase()
  return apiList.filter(a =>
    a.path.toLowerCase().includes(q) || a.method.toLowerCase().includes(q) || a.desc.toLowerCase().includes(q)
  )
})

const hasQueryParams = computed(() => selectedApi.value?.hasQuery)
const hasBody = computed(() => selectedApi.value?.hasBody)

function methodColor(method) {
  const colors = { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger' }
  return colors[method] || 'info'
}

function statusColor(status) {
  const colors = { pending: 'info', sent: 'primary', executed: 'success', failed: 'danger' }
  return colors[status] || 'info'
}

function formatTime(t) {
  if (!t) return '-'
  return new Date(t).toLocaleString()
}

function copyText(text) {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}

function selectApi(api) {
  selectedApi.value = api
  responseBody.value = ''
  responseStatus.value = null
  if (api.hasBody) {
    requestBody.value = api.method === 'POST' && api.path.includes('commands')
      ? '{\n  "device_id": 1,\n  "service_identifier": "set_light",\n  "input_params": {"power": "on"}\n}'
      : '{}'
  } else {
    requestBody.value = ''
  }
  if (api.hasQuery) {
    queryParams.value = '{}'
  } else {
    queryParams.value = ''
  }
  Object.keys(requestHeaders).forEach(k => delete requestHeaders[k])
  if (selectedApiKey.value) {
    requestHeaders['Authorization'] = 'Bearer ' + selectedApiKey.value
  }
}

function addHeader() {
  if (headerKey.value && headerValue.value) {
    requestHeaders[headerKey.value] = headerValue.value
    headerKey.value = ''
    headerValue.value = ''
  }
}

function removeHeader(key) {
  delete requestHeaders[key]
}

async function sendRequest() {
  if (!selectedApi.value) return
  if (!selectedApiKey.value) {
    ElMessage.warning('请先选择 API Key')
    return
  }

  requesting.value = true
  responseBody.value = ''
  responseStatus.value = null

  try {
    let url = selectedApi.value.path
    url = url.replace('{device_id}', '1').replace('{command_id}', 'cmd-')

    let params = {}
    if (queryParams.value) {
      try {
        params = JSON.parse(queryParams.value)
      } catch (e) {
        ElMessage.error('Query 参数不是合法 JSON')
        requesting.value = false
        return
      }
    }

    let data = undefined
    if (hasBody.value && requestBody.value) {
      try {
        data = JSON.parse(requestBody.value)
      } catch (e) {
        ElMessage.error('请求体不是合法 JSON')
        requesting.value = false
        return
      }
    }

    const headers = { ...requestHeaders }
    if (!headers['Authorization']) {
      headers['Authorization'] = 'Bearer ' + selectedApiKey.value
    }

    const resp = await axios({
      method: selectedApi.value.method.toLowerCase(),
      url,
      params,
      data,
      headers,
      baseURL: location.origin,
    })
    responseStatus.value = resp.status
    responseBody.value = JSON.stringify(resp.data, null, 2)
  } catch (e) {
    responseStatus.value = e.response?.status || 0
    responseBody.value = e.response?.data ? JSON.stringify(e.response.data, null, 2) : e.message
  } finally {
    requesting.value = false
  }
}

function selectSseChannel(id) {
  activeSseChannel.value = id
}

function toggleSseConnection() {
  if (!selectedApiKey.value) {
    ElMessage.warning('请先选择 API Key')
    return
  }
  if (sseConnected[activeSseChannel.value]) {
    closeSse()
  } else {
    connectSse()
  }
}

function connectSse() {
  const channel = sseChannels.find(c => c.id === activeSseChannel.value)
  if (!channel) return

  closeSse()

  const url = location.origin + channel.path + '?token=' + encodeURIComponent(selectedApiKey.value)
  sseSource = new EventSource(url)

  sseSource.onopen = () => {
    sseConnected[activeSseChannel.value] = true
    ElMessage.success('SSE 连接成功')
  }

  sseSource.onerror = () => {
    sseConnected[activeSseChannel.value] = false
    ElMessage.error('SSE 连接断开')
  }

  sseSource.addEventListener('new_alert', (e) => {
    addSseMessage('new_alert', e.data)
  })
  sseSource.addEventListener('device_status', (e) => {
    addSseMessage('device_status', e.data)
  })
  sseSource.addEventListener('command_response', (e) => {
    addSseMessage('command_response', e.data)
    loadCommands()
  })
  sseSource.onmessage = (e) => {
    addSseMessage('message', e.data)
  }
}

function closeSse() {
  if (sseSource) {
    sseSource.close()
    sseSource = null
  }
  sseConnected[activeSseChannel.value] = false
}

function addSseMessage(event, data) {
  sseMessages.value.push({
    event,
    data,
    time: new Date().toLocaleTimeString(),
  })
  if (sseMessages.value.length > 100) {
    sseMessages.value.shift()
  }
}

function clearSseMessages() {
  sseMessages.value = []
}

async function loadApiKeys() {
  try {
    const resp = await axios.get('/api/v1/api-keys/')
    apiKeys.value = resp.data
    if (resp.data.length > 0) {
      selectedApiKey.value = resp.data[0].key
      requestHeaders['Authorization'] = 'Bearer ' + resp.data[0].key
    }
  } catch (e) {
    ElMessage.error('加载 API Key 失败')
  }
}

async function loadDevices() {
  try {
    const resp = await axios.get('/api/v1/devices/')
    devices.value = resp.data
    if (resp.data.length > 0) {
      commandForm.device_id = resp.data[0].id
    }
  } catch (e) {
    ElMessage.error('加载设备失败')
  }
}

async function sendCommand() {
  if (!commandForm.device_id) {
    ElMessage.warning('请选择设备')
    return
  }
  if (!commandForm.service_identifier) {
    ElMessage.warning('请输入服务标识')
    return
  }

  let input_params = {}
  try {
    input_params = JSON.parse(commandParamsJson.value)
  } catch (e) {
    ElMessage.error('参数不是合法 JSON')
    return
  }

  sendingCommand.value = true
  try {
    const headers = selectedApiKey.value
      ? { Authorization: 'Bearer ' + selectedApiKey.value }
      : {}
    const resp = await axios.post('/api/v1/commands/', {
      device_id: commandForm.device_id,
      service_identifier: commandForm.service_identifier,
      input_params,
    }, { headers })
    ElMessage.success('命令已发送，命令ID: ' + resp.data.command_id.substring(0, 16) + '...')
    await loadCommands()
  } catch (e) {
    ElMessage.error('发送失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    sendingCommand.value = false
  }
}

function clearCommandForm() {
  commandForm.service_identifier = 'set_light'
  commandParamsJson.value = '{\n  "power": "on"\n}'
}

async function loadCommands() {
  try {
    const headers = selectedApiKey.value
      ? { Authorization: 'Bearer ' + selectedApiKey.value }
      : {}
    const resp = await axios.get('/api/v1/commands/', { headers, params: { limit: 20 } })
    commandHistory.value = resp.data
  } catch (e) {
    console.error('加载命令历史失败', e)
  }
}

async function viewCommandDetail(row) {
  try {
    const headers = selectedApiKey.value
      ? { Authorization: 'Bearer ' + selectedApiKey.value }
      : {}
    const resp = await axios.get('/api/v1/commands/' + row.command_id, { headers })
    currentCommand.value = resp.data
    commandDetailVisible.value = true
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
}

onMounted(() => {
  loadApiKeys()
  loadDevices()
  loadCommands()
  if (apiList.length > 0) {
    selectApi(apiList[0])
  }
})

onUnmounted(() => {
  closeSse()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.api-list {
  max-height: 600px;
  overflow-y: auto;
}

.api-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.api-item:hover {
  background: #f5f7fa;
}

.api-item.active {
  background: #ecf5ff;
}

.method-tag {
  margin-right: 10px;
  min-width: 60px;
  text-align: center;
}

.api-path {
  font-family: monospace;
  font-size: 13px;
  color: #303133;
  word-break: break-all;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid #ebeef5;
}

.header-key {
  font-weight: bold;
  min-width: 180px;
  color: #409eff;
}

.header-value {
  flex: 1;
  font-family: monospace;
  font-size: 13px;
}

.response-section {
  margin-top: 8px;
}

.response-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-weight: bold;
}

.response-body {
  background: #282c34;
  color: #abb2bf;
  padding: 16px;
  border-radius: 4px;
  max-height: 400px;
  overflow: auto;
  font-size: 13px;
  margin: 0;
}

.sse-channel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.channel-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.channel-item:hover {
  border-color: #409eff;
}

.channel-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.channel-name {
  font-weight: bold;
  margin-bottom: 4px;
}

.channel-path {
  font-family: monospace;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.sse-messages {
  max-height: 500px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sse-message {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
}

.sse-message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.sse-message-time {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.sse-message-body {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  margin: 0;
  max-height: 200px;
  overflow: auto;
}

.empty-messages {
  text-align: center;
  color: #909399;
  padding: 60px 0;
}

.command-id {
  font-family: monospace;
  font-size: 12px;
}

.topic-code {
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}

.code-block {
  background: #282c34;
  color: #abb2bf;
  padding: 16px;
  border-radius: 4px;
  font-size: 13px;
  margin: 0;
  max-height: 300px;
  overflow: auto;
}

.inline-pre {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
  font-size: 12px;
  max-height: 200px;
  overflow: auto;
}
</style>
