import api from '../services/api.js'

export const sceneService = {
  // 获取场景列表
  async getScenes(params = {}) {
    const resp = await api.get('/scenes/', { params })
    return resp.data
  },

  // 获取单个场景
  async getScene(sceneId) {
    const resp = await api.get(`/scenes/${sceneId}`)
    return resp.data
  },

  // 创建场景
  async createScene(data) {
    const resp = await api.post('/scenes/', data)
    return resp.data
  },

  // 更新场景
  async updateScene(sceneId, data) {
    const resp = await api.put(`/scenes/${sceneId}`, data)
    return resp.data
  },

  // 删除场景
  async deleteScene(sceneId) {
    await api.delete(`/scenes/${sceneId}`)
  },

  // 启用/禁用场景
  async toggleScene(sceneId) {
    const resp = await api.post(`/scenes/${sceneId}/toggle`)
    return resp.data
  },

  // 手动触发场景
  async triggerScene(sceneId, triggerData = {}) {
    const resp = await api.post(`/scenes/${sceneId}/trigger`, { trigger_data: triggerData })
    return resp.data
  },

  // 获取执行日志
  async getExecutionLogs(sceneId, params = {}) {
    const resp = await api.get(`/scenes/${sceneId}/executions`, { params })
    return resp.data
  }
}

// 预设模板
export const sceneTemplates = [
  {
    id: 'temp-high',
    name: '🌡️ 高温自动通风',
    description: '当温度超过30°C时，自动开启通风扇降温',
    trigger_type: 'threshold',
    trigger_config: {
      property_identifier: 'temperature',
      operator: 'gt',
      threshold_value: 30
    },
    action_type: 'command',
    action_config: {
      service_identifier: 'set_fan',
      input_params: { status: true }
    }
  },
  {
    id: 'temp-low',
    name: '❄️ 低温自动保温',
    description: '当温度低于15°C时，自动关闭通风扇',
    trigger_type: 'threshold',
    trigger_config: {
      property_identifier: 'temperature',
      operator: 'lt',
      threshold_value: 15
    },
    action_type: 'command',
    action_config: {
      service_identifier: 'set_fan',
      input_params: { status: false }
    }
  },
  {
    id: 'soil-dry',
    name: '💧 土壤干燥自动灌溉',
    description: '当土壤湿度低于50%时，自动开启灌溉水泵',
    trigger_type: 'threshold',
    trigger_config: {
      property_identifier: 'soil_moisture',
      operator: 'lt',
      threshold_value: 50
    },
    action_type: 'command',
    action_config: {
      service_identifier: 'set_pump',
      input_params: { status: true }
    }
  },
  {
    id: 'soil-wet',
    name: '🚿 土壤过湿停止灌溉',
    description: '当土壤湿度高于80%时，自动关闭灌溉水泵',
    trigger_type: 'threshold',
    trigger_config: {
      property_identifier: 'soil_moisture',
      operator: 'gt',
      threshold_value: 80
    },
    action_type: 'command',
    action_config: {
      service_identifier: 'set_pump',
      input_params: { status: false }
    }
  },
  {
    id: 'humidity-high',
    name: '💨 高湿自动通风',
    description: '当空气湿度高于80%时，自动开启通风扇除湿',
    trigger_type: 'threshold',
    trigger_config: {
      property_identifier: 'humidity',
      operator: 'gt',
      threshold_value: 80
    },
    action_type: 'command',
    action_config: {
      service_identifier: 'set_fan',
      input_params: { status: true }
    }
  },
  {
    id: 'light-dim',
    name: '💡 光照不足自动补光',
    description: '当光照强度低于5000 lux时，自动开启补光灯',
    trigger_type: 'threshold',
    trigger_config: {
      property_identifier: 'light_intensity',
      operator: 'lt',
      threshold_value: 5000
    },
    action_type: 'command',
    action_config: {
      service_identifier: 'set_light',
      input_params: { status: true, brightness: 80 }
    }
  }
]

// 属性标识符映射（中文名称）
export const propertyLabels = {
  temperature: '空气温度',
  humidity: '空气湿度',
  soil_moisture: '土壤湿度',
  soil_temperature: '土壤温度',
  light_intensity: '光照强度',
  co2: 'CO₂浓度'
}

// 操作符映射
export const operatorLabels = {
  gt: '大于',
  gte: '大于等于',
  lt: '小于',
  lte: '小于等于',
  eq: '等于',
  neq: '不等于'
}

// 服务标识符映射
export const serviceLabels = {
  set_fan: '通风扇',
  set_light: '补光灯',
  set_pump: '灌溉水泵'
}
