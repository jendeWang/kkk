import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function getErrorMessage(error) {
  if (error.response) {
    const status = error.response.status
    const detail = error.response.data?.detail
    
    if (status === 400) {
      return detail || '请求参数错误，请检查输入'
    }
    if (status === 401) {
      return '登录已过期，请重新登录'
    }
    if (status === 403) {
      return '没有权限执行此操作'
    }
    if (status === 404) {
      return detail || '请求的资源不存在'
    }
    if (status === 409) {
      return detail || '数据冲突，请刷新后重试'
    }
    if (status >= 500) {
      return '服务器错误，请稍后重试'
    }
    return detail || `请求失败 (${status})`
  }
  
  if (error.request) {
    return '网络连接失败，请检查网络'
  }
  
  return error.message || '未知错误'
}

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const publicRoutes = ['/login', '/register', '/big-screen']
      const isPublicRoute = publicRoutes.includes(window.location.pathname)
      if (!isPublicRoute) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        ElMessage.warning('登录已过期，请重新登录')
        setTimeout(() => {
          window.location.href = '/login'
        }, 1000)
      }
    } else if (error.response?.status >= 500) {
      console.error('Server error:', error)
    }
    
    error.userMessage = getErrorMessage(error)
    return Promise.reject(error)
  }
)

export default api

