import api from './api.js'

// 属性标识符 -> 中文名称映射（默认配置）
const defaultPropertyLabels = {
  temperature: '温度',
  humidity: '湿度',
  soil_moisture: '土壤湿度',
  soil_temperature: '土壤温度',
  light_intensity: '光照强度',
  co2: 'CO₂浓度',
  soil_ph: '土壤pH值',
  wind_speed: '风速',
  rain_fall: '降雨量',
  atmospheric_pressure: '大气压强',
  soil_nitrogen: '土壤氮含量',
  soil_phosphorus: '土壤磷含量',
  soil_potassium: '土壤钾含量',
  leaf_temperature: '叶面温度',
  leaf_humidity: '叶面湿度',
  water_level: '水位',
  power_voltage: '电压',
  power_current: '电流',
}

// 属性标识符 -> 单位映射（默认配置）
const defaultPropertyUnits = {
  temperature: '°C',
  humidity: '%',
  soil_moisture: '%',
  soil_temperature: '°C',
  light_intensity: ' lux',
  co2: ' ppm',
  soil_ph: '',
  wind_speed: ' m/s',
  rain_fall: ' mm',
  atmospheric_pressure: ' hPa',
  soil_nitrogen: ' mg/kg',
  soil_phosphorus: ' mg/kg',
  soil_potassium: ' mg/kg',
  leaf_temperature: '°C',
  leaf_humidity: '%',
  water_level: ' m',
  power_voltage: ' V',
  power_current: ' A',
}

// 操作符 -> 中文映射
const defaultOperatorLabels = {
  gt: '大于',
  gte: '大于等于',
  lt: '小于',
  lte: '小于等于',
  eq: '等于',
  neq: '不等于',
}

// 运行时动态加载的映射（从后端物模型获取）
let dynamicPropertyLabels = {}
let dynamicPropertyUnits = {}

// 是否已加载动态配置
let isLoaded = false

/**
 * 加载所有产品的物模型属性定义
 * 从后端API获取，缓存到内存中
 */
export async function loadPropertyMappings() {
  if (isLoaded) return

  try {
    const resp = await api.get('/products/')
    const products = resp.data || []

    products.forEach(product => {
      // 从产品物模型加载属性定义
      if (product.properties) {
        product.properties.forEach(prop => {
          if (prop.identifier && prop.name) {
            dynamicPropertyLabels[prop.identifier] = prop.name
          }
          if (prop.identifier && prop.unit) {
            dynamicPropertyUnits[prop.identifier] = prop.unit
          }
        })
      }
    })

    isLoaded = true
    console.log('[PropertyMapper] 已加载物模型属性映射:', {
      labels: Object.keys(dynamicPropertyLabels).length,
      units: Object.keys(dynamicPropertyUnits).length
    })
  } catch (e) {
    console.error('[PropertyMapper] 加载物模型失败，使用默认配置:', e)
    isLoaded = true
  }
}

/**
 * 获取属性中文名称
 * 优先级：动态配置 > 默认配置
 */
export function getPropertyLabel(identifier) {
  return dynamicPropertyLabels[identifier]
    || defaultPropertyLabels[identifier]
    || identifier
}

/**
 * 获取属性单位
 * 优先级：动态配置 > 默认配置
 */
export function getPropertyUnit(identifier) {
  return dynamicPropertyUnits[identifier]
    || defaultPropertyUnits[identifier]
    || ''
}

/**
 * 获取操作符中文名称
 */
export function getOperatorLabel(operator) {
  return defaultOperatorLabels[operator] || operator
}

/**
 * 通用告警消息格式化函数
 * 自动识别属性名称，无需硬编码
 */
export function formatAlertMessage(alert) {
  if (!alert) return ''
  
  let message = alert.message || ''
  
  // 提取属性标识符和值
  // 支持多种格式：
  // 1. "temperature = 24.5" -> { prop: 'temperature', value: '24.5' }
  // 2. "temperature: 24.5" -> { prop: 'temperature', value: '24.5' }
  // 3. "soil_moisture: 85.2%" -> { prop: 'soil_moisture', value: '85.2', unit: '%' }
  
  const patterns = [
    /(\w+)\s*=\s*([\d.]+)/g,  // prop = value
    /(\w+):\s*([\d.]+)/g,      // prop: value
    /(\w+)\s*([\d.]+)/g,        // prop value
  ]
  
  patterns.forEach(pattern => {
    const matches = [...message.matchAll(pattern)]
    matches.forEach(match => {
      const propId = match[1]
      const value = match[2]
      const label = getPropertyLabel(propId)
      const unit = getPropertyUnit(propId)
      
      if (label !== propId) {
        message = message.replace(match[0], `${label} ${value}${unit}`)
      }
    })
  })
  
  // 阈值相关术语口语化
  message = message
    .replace(/超过阈值\s*([\d.]+)/g, '超过警戒值 $1')
    .replace(/低于阈值\s*([\d.]+)/g, '低于警戒值 $1')
    .replace(/超过上限阈值/g, '超过最高限制')
    .replace(/低于下限阈值/g, '低于最低限制')
    .replace(/超过最大/g, '超过最大')
    .replace(/低于最小/g, '低于最小')
  
  // 设备状态术语口语化
  message = message
    .replace(/设备离线/g, '设备断开连接')
    .replace(/device.*offline/gi, '设备断开连接')
    .replace(/设备在线/g, '设备正常连接')
    .replace(/device.*online/gi, '设备正常连接')
  
  return message
}

/**
 * 格式化传感器值显示
 */
export function formatSensorValue(identifier, value) {
  const label = getPropertyLabel(identifier)
  const unit = getPropertyUnit(identifier)
  return `${label}: ${value}${unit}`
}

/**
 * 格式化条件表达式
 * 如：temperature > 30 转换为 "温度 大于 30°C"
 */
export function formatCondition(propId, operator, value) {
  const label = getPropertyLabel(propId)
  const unit = getPropertyUnit(propId)
  const opLabel = getOperatorLabel(operator)
  return `${label} ${opLabel} ${value}${unit}`
}

export default {
  loadPropertyMappings,
  getPropertyLabel,
  getPropertyUnit,
  getOperatorLabel,
  formatAlertMessage,
  formatSensorValue,
  formatCondition,
}
