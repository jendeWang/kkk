import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api.js'

export const useProductStore = defineStore('product', () => {
  const products = ref([])
  const currentProduct = ref(null)

  async function fetchProducts() {
    const response = await api.get('/products/')
    products.value = response.data
    return response.data
  }

  async function fetchProduct(productKey) {
    const response = await api.get(`/products/${productKey}`)
    currentProduct.value = response.data
    return response.data
  }

  async function createProduct(data) {
    const response = await api.post('/products/', data)
    products.value.push(response.data)
    return response.data
  }

  async function updateProduct(productKey, data) {
    const response = await api.put(`/products/${productKey}`, data)
    const index = products.value.findIndex(p => p.product_key === productKey)
    if (index !== -1) products.value[index] = response.data
    return response.data
  }

  async function deleteProduct(productKey) {
    await api.delete(`/products/${productKey}`)
    products.value = products.value.filter(p => p.product_key !== productKey)
  }

  async function addProperty(productKey, data) {
    const response = await api.post(`/products/${productKey}/properties`, data)
    if (currentProduct.value?.product_key === productKey) {
      currentProduct.value.properties.push(response.data)
    }
    return response.data
  }

  async function deleteProperty(productKey, identifier) {
    await api.delete(`/products/${productKey}/properties/${identifier}`)
    if (currentProduct.value?.product_key === productKey) {
      currentProduct.value.properties = currentProduct.value.properties.filter(p => p.identifier !== identifier)
    }
  }

  async function addService(productKey, data) {
    const response = await api.post(`/products/${productKey}/services`, data)
    if (currentProduct.value?.product_key === productKey) {
      currentProduct.value.services.push(response.data)
    }
    return response.data
  }

  async function deleteService(productKey, identifier) {
    await api.delete(`/products/${productKey}/services/${identifier}`)
    if (currentProduct.value?.product_key === productKey) {
      currentProduct.value.services = currentProduct.value.services.filter(s => s.identifier !== identifier)
    }
  }

  async function updateService(productKey, serviceId, data) {
    const response = await api.put(`/products/${productKey}/services/${serviceId}`, data)
    if (currentProduct.value?.product_key === productKey) {
      const index = currentProduct.value.services.findIndex(s => s.id === serviceId)
      if (index !== -1) {
        currentProduct.value.services[index] = response.data
      }
    }
    return response.data
  }

  async function addEvent(productKey, data) {
    const response = await api.post(`/products/${productKey}/events`, data)
    if (currentProduct.value?.product_key === productKey) {
      currentProduct.value.events.push(response.data)
    }
    return response.data
  }

  async function deleteEvent(productKey, identifier) {
    await api.delete(`/products/${productKey}/events/${identifier}`)
    if (currentProduct.value?.product_key === productKey) {
      currentProduct.value.events = currentProduct.value.events.filter(e => e.identifier !== identifier)
    }
  }

  return {
    products, currentProduct,
    fetchProducts, fetchProduct, createProduct, updateProduct, deleteProduct,
    addProperty, deleteProperty, addService, deleteService, updateService, addEvent, deleteEvent
  }
})
