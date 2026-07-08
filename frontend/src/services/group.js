import api from '../services/api.js'

export const groupService = {
  // 获取分组列表
  async getGroups(params = {}) {
    const resp = await api.get('/groups/', { params })
    return resp.data
  },

  // 获取单个分组
  async getGroup(groupId) {
    const resp = await api.get(`/groups/${groupId}`)
    return resp.data
  },

  // 创建分组
  async createGroup(data) {
    const resp = await api.post('/groups/', data)
    return resp.data
  },

  // 更新分组
  async updateGroup(groupId, data) {
    const resp = await api.put(`/groups/${groupId}`, data)
    return resp.data
  },

  // 删除分组
  async deleteGroup(groupId) {
    await api.delete(`/groups/${groupId}`)
  },

  // 获取分组内设备列表
  async getGroupDevices(groupId, params = {}) {
    const resp = await api.get(`/groups/${groupId}/devices`, { params })
    return resp.data
  },

  // 添加设备到分组
  async addDevicesToGroup(groupId, deviceIds) {
    const resp = await api.post(`/groups/${groupId}/devices`, { device_ids: deviceIds })
    return resp.data
  },

  // 从分组移除设备
  async removeDevicesFromGroup(groupId, deviceIds) {
    const resp = await api.delete(`/groups/${groupId}/devices`, { data: { device_ids: deviceIds } })
    return resp.data
  }
}

// 预设分组模板
export const groupTemplates = [
  {
    name: '1号大棚',
    description: '第1号种植大棚'
  },
  {
    name: '2号大棚',
    description: '第2号种植大棚'
  },
  {
    name: '3号大棚',
    description: '第3号种植大棚'
  }
]
