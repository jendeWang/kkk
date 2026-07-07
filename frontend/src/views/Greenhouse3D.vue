<template>
  <div class="greenhouse-3d">
    <div ref="containerRef" class="canvas-container"></div>

    <div class="hud-overlay">
      <div class="hud-header">
        <h1>智慧大棚数字孪生平台</h1>
        <div class="hud-time">{{ currentTime }}</div>
      </div>

      <div class="hud-left">
        <div class="data-panel">
          <div class="panel-title">环境监测</div>
          <div class="data-row">
            <div class="data-icon temp">🌡️</div>
            <div class="data-info">
              <div class="data-label">温度</div>
              <div class="data-value">{{ envData.temperature ? envData.temperature.toFixed(1) + '°C' : '--' }} {{ envData.temperature > 30 ? '🔴' : envData.temperature > 0 ? '🟢' : '' }}</div>
            </div>
          </div>
          <div class="data-row">
            <div class="data-icon hum">💧</div>
            <div class="data-info">
              <div class="data-label">湿度</div>
              <div class="data-value">{{ envData.humidity ? envData.humidity.toFixed(1) + '%' : '--' }} {{ envData.humidity > 0 ? '🟢' : '' }}</div>
            </div>
          </div>
          <div class="data-row">
            <div class="data-icon light">☀️</div>
            <div class="data-info">
              <div class="data-label">光照</div>
              <div class="data-value">{{ envData.light ? envData.light.toFixed(0) + ' lux' : '--' }} {{ envData.light > 0 ? '🟢' : '' }}</div>
            </div>
          </div>
          <div class="data-row">
            <div class="data-icon soil">🌱</div>
            <div class="data-info">
              <div class="data-label">土壤湿度</div>
              <div class="data-value">{{ envData.soil ? envData.soil.toFixed(1) + '%' : '--' }} {{ envData.soil > 0 ? '🟢' : '' }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="hud-right">
        <div class="data-panel">
          <div class="panel-title">设备状态</div>
          <div class="device-item">
            <span class="device-name">通风风扇</span>
            <el-switch v-model="deviceState.fan" @change="toggleFan" active-color="#67c23a" />
          </div>
          <div class="device-item">
            <span class="device-name">补光灯</span>
            <el-switch v-model="deviceState.light" @change="toggleLight" active-color="#e6a23c" />
          </div>
          <div class="device-item">
            <span class="device-name">卷帘</span>
            <el-switch v-model="deviceState.curtain" @change="toggleCurtain" active-color="#409eff" />
          </div>
          <div class="device-item">
            <span class="device-name">灌溉泵</span>
            <el-switch v-model="deviceState.pump" @change="togglePump" active-color="#67c23a" />
          </div>
        </div>

        <div class="data-panel mt-3">
          <div class="panel-title">快捷操作</div>
          <div class="btn-row">
            <el-button size="small" @click="resetCamera">重置视角</el-button>
            <el-button size="small" @click="toggleAutoRotate">自动旋转</el-button>
          </div>
        </div>
      </div>

      <div class="hud-bottom">
        <div class="status-bar">
          <span class="status-item">{{ connected ? '✅' : '⚠️' }} {{ connected ? '系统运行正常' : '等待连接设备...' }}</span>
          <span class="status-item">📡 {{ connected ? '1个设备在线' : '无在线设备' }}</span>
          <span class="status-item">⏱️ {{ envData.temperature ? '数据实时同步' : '加载中...' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'
import api from '../services/api.js'

const containerRef = ref(null)
const currentTime = ref('')
const deviceId = ref(null)
const connected = ref(false)

const envData = reactive({
  temperature: 0,
  humidity: 0,
  light: 0,
  soil: 0,
  co2: 0,
})

const deviceState = reactive({
  fan: true,
  light: false,
  curtain: false,
  pump: false,
})

let scene, camera, renderer, labelRenderer, controls
let animationId
let greenhouseGroup, fanGroup, lightBulbs = [], curtainGroup, plants = [], pumpGroup
let autoRotate = false
let sensorLabels = []
let eventSource = null
let lastSensorUpdate = 0

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

function init() {
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a1628)
  scene.fog = new THREE.Fog(0x0a1628, 30, 80)

  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
  camera.position.set(15, 12, 18)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(width, height)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0'
  labelRenderer.domElement.style.pointerEvents = 'none'
  container.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 5
  controls.maxDistance = 50
  controls.maxPolarAngle = Math.PI / 2.1
  controls.target.set(0, 2, 0)

  const ambientLight = new THREE.AmbientLight(0x404060, 0.6)
  scene.add(ambientLight)

  const dirLight = new THREE.DirectionalLight(0xfff0d0, 0.8)
  dirLight.position.set(10, 20, 10)
  dirLight.castShadow = true
  dirLight.shadow.mapSize.width = 2048
  dirLight.shadow.mapSize.height = 2048
  dirLight.shadow.camera.near = 0.5
  dirLight.shadow.camera.far = 50
  dirLight.shadow.camera.left = -20
  dirLight.shadow.camera.right = 20
  dirLight.shadow.camera.top = 20
  dirLight.shadow.camera.bottom = -20
  scene.add(dirLight)

  const hemiLight = new THREE.HemisphereLight(0x87ceeb, 0x362d1f, 0.4)
  scene.add(hemiLight)

  createGround()
  createGreenhouse()
  createPlants()
  createSensors()
  animate()
}

function createGround() {
  const groundGeo = new THREE.PlaneGeometry(60, 60)
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0x1a3a1a,
    roughness: 0.9,
    metalness: 0.1,
  })
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.receiveShadow = true
  scene.add(ground)

  const gridHelper = new THREE.GridHelper(40, 40, 0x0d3d52, 0x0d2940)
  gridHelper.position.y = 0.01
  scene.add(gridHelper)
}

function createGreenhouse() {
  greenhouseGroup = new THREE.Group()

  const width = 12
  const depth = 8
  const wallHeight = 2.5
  const roofHeight = 2

  const frameMat = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    metalness: 0.7,
    roughness: 0.3,
  })

  const coverMat = new THREE.MeshStandardMaterial({
    color: 0x88ccff,
    transparent: true,
    opacity: 0.25,
    side: THREE.DoubleSide,
    roughness: 0.1,
    metalness: 0.1,
  })

  const frameThickness = 0.08

  for (let i = 0; i <= 6; i++) {
    const z = -depth / 2 + (depth / 6) * i
    const poleGeo = new THREE.BoxGeometry(frameThickness, wallHeight, frameThickness)
    const pole1 = new THREE.Mesh(poleGeo, frameMat)
    pole1.position.set(-width / 2, wallHeight / 2, z)
    pole1.castShadow = true
    greenhouseGroup.add(pole1)
    const pole2 = new THREE.Mesh(poleGeo, frameMat)
    pole2.position.set(width / 2, wallHeight / 2, z)
    pole2.castShadow = true
    greenhouseGroup.add(pole2)
  }

  const beamGeo = new THREE.BoxGeometry(width, frameThickness, frameThickness)
  const beamMat = frameMat
  const beam1 = new THREE.Mesh(beamGeo, beamMat)
  beam1.position.set(0, wallHeight, -depth / 2)
  beam1.castShadow = true
  greenhouseGroup.add(beam1)
  const beam2 = new THREE.Mesh(beamGeo, beamMat)
  beam2.position.set(0, wallHeight, depth / 2)
  beam2.castShadow = true
  greenhouseGroup.add(beam2)

  const roofGeo = new THREE.BufferGeometry()
  const roofVertices = new Float32Array([
    -width / 2, wallHeight, -depth / 2,
    width / 2, wallHeight, -depth / 2,
    0, wallHeight + roofHeight, -depth / 2,
    -width / 2, wallHeight, depth / 2,
    width / 2, wallHeight, depth / 2,
    0, wallHeight + roofHeight, depth / 2,
  ])
  const roofIndices = [
    0, 2, 1,
    3, 4, 5,
    0, 3, 2,
    1, 2, 4,
    0, 1, 4,
    0, 4, 3,
  ]
  roofGeo.setAttribute('position', new THREE.BufferAttribute(roofVertices, 3))
  roofGeo.setIndex(roofIndices)
  roofGeo.computeVertexNormals()
  const roofFrame = new THREE.Mesh(roofGeo, frameMat.clone())
  roofFrame.material.wireframe = true
  roofFrame.castShadow = true
  greenhouseGroup.add(roofFrame)

  const roofCover = new THREE.Mesh(roofGeo, coverMat)
  greenhouseGroup.add(roofCover)

  const sideWallGeo = new THREE.PlaneGeometry(depth, wallHeight)
  const leftWall = new THREE.Mesh(sideWallGeo, coverMat)
  leftWall.position.set(-width / 2, wallHeight / 2, 0)
  leftWall.rotation.y = Math.PI / 2
  greenhouseGroup.add(leftWall)
  const rightWall = new THREE.Mesh(sideWallGeo, coverMat)
  rightWall.position.set(width / 2, wallHeight / 2, 0)
  rightWall.rotation.y = -Math.PI / 2
  greenhouseGroup.add(rightWall)

  const backWallGeo = new THREE.PlaneGeometry(width, wallHeight)
  const backWall = new THREE.Mesh(backWallGeo, coverMat)
  backWall.position.set(0, wallHeight / 2, -depth / 2)
  greenhouseGroup.add(backWall)

  const doorWidth = 1.8
  const doorHeight = 2.2
  const frontLeftGeo = new THREE.PlaneGeometry((width - doorWidth) / 2, wallHeight)
  const frontLeft = new THREE.Mesh(frontLeftGeo, coverMat)
  frontLeft.position.set(-(width + doorWidth) / 4, wallHeight / 2, depth / 2)
  greenhouseGroup.add(frontLeft)
  const frontRightGeo = new THREE.PlaneGeometry((width - doorWidth) / 2, wallHeight)
  const frontRight = new THREE.Mesh(frontRightGeo, coverMat)
  frontRight.position.set((width + doorWidth) / 4, wallHeight / 2, depth / 2)
  greenhouseGroup.add(frontRight)

  const doorMat = new THREE.MeshStandardMaterial({
    color: 0x6b4423,
    roughness: 0.8,
    metalness: 0.2,
  })
  const doorGeo = new THREE.BoxGeometry(doorWidth, doorHeight, 0.05)
  const door = new THREE.Mesh(doorGeo, doorMat)
  door.position.set(0, doorHeight / 2, depth / 2 + 0.02)
  door.castShadow = true
  greenhouseGroup.add(door)

  const fanMat = new THREE.MeshStandardMaterial({
    color: 0x4a5568,
    metalness: 0.8,
    roughness: 0.3,
  })
  fanGroup = new THREE.Group()
  const fanBodyGeo = new THREE.CylinderGeometry(0.6, 0.6, 0.2, 16)
  const fanBody = new THREE.Mesh(fanBodyGeo, fanMat)
  fanBody.rotation.z = Math.PI / 2
  fanBody.castShadow = true
  fanGroup.add(fanBody)

  const bladeMat = new THREE.MeshStandardMaterial({
    color: 0x718096,
    metalness: 0.6,
    roughness: 0.4,
  })
  for (let i = 0; i < 5; i++) {
    const bladeGeo = new THREE.BoxGeometry(0.06, 0.5, 0.01)
    const blade = new THREE.Mesh(bladeGeo, bladeMat)
    blade.position.y = 0.25
    blade.rotation.y = (Math.PI * 2 / 5) * i
    blade.castShadow = true
    fanGroup.add(blade)
  }

  fanGroup.position.set(-width / 2 - 0.1, 1.8, -2)
  fanGroup.rotation.y = Math.PI / 2
  greenhouseGroup.add(fanGroup)

  lightBulbs = []
  const bulbPositions = [
    [-3, wallHeight - 0.3, -2],
    [3, wallHeight - 0.3, -2],
    [-3, wallHeight - 0.3, 2],
    [3, wallHeight - 0.3, 2],
  ]
  bulbPositions.forEach(pos => {
    const bulbGroup = new THREE.Group()
    const bulbGeo = new THREE.SphereGeometry(0.12, 16, 16)
    const bulbMat = new THREE.MeshStandardMaterial({
      color: 0x555555,
      emissive: 0x000000,
      emissiveIntensity: 0,
    })
    const bulb = new THREE.Mesh(bulbGeo, bulbMat)
    bulbGroup.add(bulb)

    const pointLight = new THREE.PointLight(0xffdd88, 0, 10)
    bulbGroup.add(pointLight)
    bulbGroup.userData = { bulb, pointLight }
    bulbGroup.position.set(...pos)
    lightBulbs.push(bulbGroup)
    greenhouseGroup.add(bulbGroup)
  })

  curtainGroup = new THREE.Group()
  const curtainMat = new THREE.MeshStandardMaterial({
    color: 0x2d3748,
    side: THREE.DoubleSide,
    roughness: 0.9,
  })
  const curtainGeo = new THREE.PlaneGeometry(3, wallHeight - 0.5)
  const curtainLeft = new THREE.Mesh(curtainGeo, curtainMat)
  curtainLeft.position.set(-width / 2 + 0.05, (wallHeight - 0.5) / 2, 0)
  curtainLeft.rotation.y = Math.PI / 2
  curtainGroup.add(curtainLeft)
  curtainGroup.position.y = 0
  greenhouseGroup.add(curtainGroup)

  const floorGeo = new THREE.PlaneGeometry(width - 0.5, depth - 0.5)
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x4a3728,
    roughness: 0.9,
  })
  const floor = new THREE.Mesh(floorGeo, floorMat)
  floor.rotation.x = -Math.PI / 2
  floor.position.y = 0.02
  floor.receiveShadow = true
  greenhouseGroup.add(floor)

  scene.add(greenhouseGroup)
}

function createPlants() {
  const plantMat = new THREE.MeshStandardMaterial({
    color: 0x228b22,
    roughness: 0.8,
    metalness: 0.1,
  })
  const stemMat = new THREE.MeshStandardMaterial({
    color: 0x2e8b57,
    roughness: 0.9,
  })

  const positions = []
  for (let x = -4; x <= 4; x += 2.5) {
    for (let z = -2.5; z <= 2.5; z += 2.5) {
      positions.push([x, z])
    }
  }

  positions.forEach(([x, z]) => {
    const plantGroup = new THREE.Group()
    const stemGeo = new THREE.CylinderGeometry(0.04, 0.05, 0.4, 8)
    const stem = new THREE.Mesh(stemGeo, stemMat)
    stem.position.y = 0.2
    stem.castShadow = true
    plantGroup.add(stem)

    const leafCount = 5 + Math.floor(Math.random() * 4)
    for (let i = 0; i < leafCount; i++) {
      const leafGeo = new THREE.SphereGeometry(0.25 + Math.random() * 0.15, 8, 8)
      const leaf = new THREE.Mesh(leafGeo, plantMat.clone())
      leaf.material.color.setHSL(0.3, 0.7, 0.25 + Math.random() * 0.15)
      leaf.position.set(
        (Math.random() - 0.5) * 0.4,
        0.4 + Math.random() * 0.5,
        (Math.random() - 0.5) * 0.4
      )
      leaf.scale.y = 0.8 + Math.random() * 0.4
      leaf.castShadow = true
      plantGroup.add(leaf)
    }

    plantGroup.position.set(x, 0, z)
    plantGroup.scale.setScalar(0.8 + Math.random() * 0.4)
    plants.push(plantGroup)
    greenhouseGroup.add(plantGroup)
  })
}

function createSensorLabel(text, color, position) {
  const div = document.createElement('div')
  div.className = 'sensor-label'
  div.style.cssText = `
    background: rgba(0, 20, 40, 0.85);
    color: ${color};
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
    border: 1px solid ${color};
    white-space: nowrap;
    box-shadow: 0 0 10px ${color}60;
  `
  div.textContent = text
  const label = new CSS2DObject(div)
  label.position.set(...position)
  sensorLabels.push({ label, div })
  greenhouseGroup.add(label)
  return { label, div }
}

function createSensors() {
  createSensorLabel('🌡️ 温度 26.5°C', '#ff6b6b', [-4, 1.5, -3])
  createSensorLabel('💧 湿度 65%', '#4ecdc4', [4, 1.5, -3])
  createSensorLabel('☀️ 光照 35000lux', '#ffd93d', [0, 3, 0])
  createSensorLabel('🌱 土壤 58%', '#6bc46d', [-3, 0.5, 2.5])
}

function updateSensorData() {
  const now = Date.now()
  if (now - lastSensorUpdate < 1000) return
  lastSensorUpdate = now

  if (sensorLabels.length >= 4) {
    sensorLabels[0].div.textContent = `🌡️ 温度 ${envData.temperature.toFixed(1)}°C`
    sensorLabels[1].div.textContent = `💧 湿度 ${envData.humidity.toFixed(1)}%`
    sensorLabels[2].div.textContent = `☀️ 光照 ${envData.light.toFixed(0)}lux`
    sensorLabels[3].div.textContent = `🌱 土壤 ${envData.soil.toFixed(1)}%`
  }
}

async function loadRealtimeData() {
  try {
    const res = await api.get('/devices/', { params: { status: 'online' } })
    const onlineDevices = res.data
    if (onlineDevices.length > 0) {
      deviceId.value = onlineDevices[0].id
      connected.value = true
    }
    if (!deviceId.value) return

    const latestRes = await api.get('/telemetry/latest', { params: { device_id: deviceId.value } })
    const latestValues = latestRes.data.latest_values || []
    for (const item of latestValues) {
      const val = parseFloat(item.value)
      if (item.property_identifier === 'temperature') envData.temperature = val
      else if (item.property_identifier === 'humidity') envData.humidity = val
      else if (item.property_identifier === 'light_intensity') envData.light = val
      else if (item.property_identifier === 'soil_moisture') envData.soil = val
      else if (item.property_identifier === 'co2') envData.co2 = val
    }
    updateSensorData()
  } catch (e) {
    console.warn('Failed to load realtime data:', e)
  }
}

function connectSSE() {
  const token = localStorage.getItem('token')
  if (!token) return

  try {
    eventSource = new EventSource(`/api/v1/sse/devices?token=${token}`)
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.device_id !== deviceId.value) return

        const val = parseFloat(data.value)
        const prop = data.property_identifier

        if (prop === 'temperature') envData.temperature = val
        else if (prop === 'humidity') envData.humidity = val
        else if (prop === 'light_intensity') envData.light = val
        else if (prop === 'soil_moisture') envData.soil = val
        else if (prop === 'co2') envData.co2 = val
        else if (prop === 'fan_switch') deviceState.fan = val === 1
        else if (prop === 'light_switch') deviceState.light = val === 1
        else if (prop === 'curtain_switch') deviceState.curtain = val === 1
        else if (prop === 'pump_switch') deviceState.pump = val === 1

        updateSensorData()
        sync3DState()
      } catch (e) {}
    }
    eventSource.onerror = () => {
      eventSource.close()
      setTimeout(connectSSE, 5000)
    }
  } catch (e) {
    console.warn('SSE connection failed:', e)
  }
}

function sync3DState() {
  if (deviceState.light) {
    lightBulbs.forEach(bg => {
      const { bulb, pointLight } = bg.userData
      bulb.material.color.set(0xffdd88)
      bulb.material.emissive.set(0xffdd88)
      bulb.material.emissiveIntensity = 1
      pointLight.intensity = 1.5
    })
  } else {
    lightBulbs.forEach(bg => {
      const { bulb, pointLight } = bg.userData
      bulb.material.color.set(0x555555)
      bulb.material.emissive.set(0x000000)
      bulb.material.emissiveIntensity = 0
      pointLight.intensity = 0
    })
  }
  if (curtainGroup) {
    curtainGroup.position.y = deviceState.curtain ? -2 : 0
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)

  if (deviceState.fan && fanGroup) {
    fanGroup.rotation.x += 0.15
  }

  if (autoRotate && controls) {
    const angle = 0.003
    const radius = Math.sqrt(
      Math.pow(camera.position.x - controls.target.x, 2) +
      Math.pow(camera.position.z - controls.target.z, 2)
    )
    const currentAngle = Math.atan2(
      camera.position.z - controls.target.z,
      camera.position.x - controls.target.x
    )
    camera.position.x = controls.target.x + Math.cos(currentAngle + angle) * radius
    camera.position.z = controls.target.z + Math.sin(currentAngle + angle) * radius
    camera.lookAt(controls.target)
  }

  controls.update()
  updateSensorData()
  updateTime()
  renderer.render(scene, camera)
  labelRenderer.render(scene, camera)
}

function onResize() {
  if (!containerRef.value || !camera || !renderer) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
  labelRenderer.setSize(width, height)
}

function resetCamera() {
  camera.position.set(15, 12, 18)
  controls.target.set(0, 2, 0)
  controls.update()
}

function toggleAutoRotate() {
  autoRotate = !autoRotate
}

function toggleFan(val) {
  deviceState.fan = val
  sendDeviceCommand('fan_switch', val ? 1 : 0)
}

function toggleLight(val) {
  deviceState.light = val
  sync3DState()
  sendDeviceCommand('light_switch', val ? 1 : 0)
}

function toggleCurtain(val) {
  deviceState.curtain = val
  sync3DState()
  sendDeviceCommand('curtain_switch', val ? 1 : 0)
}

function togglePump(val) {
  deviceState.pump = val
  sendDeviceCommand('pump_switch', val ? 1 : 0)
}

async function sendDeviceCommand(serviceId, value) {
  if (!deviceId.value) {
    ElMessage.warning('未检测到在线设备')
    return
  }
  try {
    await api.post('/commands/', {
      device_id: deviceId.value,
      service_identifier: serviceId,
      input_params: { value: String(value) },
    })
    ElMessage.success('命令已下发')
  } catch (e) {
    ElMessage.error('命令下发失败')
  }
}

onMounted(async () => {
  init()
  window.addEventListener('resize', onResize)
  await loadRealtimeData()
  connectSSE()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
})
</script>

<style scoped>
.greenhouse-3d {
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: #0a1628;
}

.canvas-container {
  width: 100%;
  height: 100%;
}

.hud-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 10;
}

.hud-header {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  pointer-events: none;
}

.hud-header h1 {
  color: #00d4ff;
  font-size: 24px;
  margin: 0;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  letter-spacing: 4px;
}

.hud-time {
  color: #8892b0;
  font-size: 14px;
  margin-top: 5px;
  font-family: monospace;
}

.hud-left {
  position: absolute;
  top: 80px;
  left: 20px;
  pointer-events: auto;
}

.hud-right {
  position: absolute;
  top: 80px;
  right: 20px;
  pointer-events: auto;
}

.hud-bottom {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

.data-panel {
  background: rgba(0, 20, 40, 0.85);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  padding: 15px;
  width: 220px;
  backdrop-filter: blur(10px);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
}

.panel-title {
  color: #00d4ff;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  letter-spacing: 2px;
}

.data-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.data-row:last-child {
  border-bottom: none;
}

.data-icon {
  font-size: 20px;
}

.data-info {
  flex: 1;
}

.data-label {
  color: #8892b0;
  font-size: 12px;
}

.data-value {
  color: #e6f1ff;
  font-size: 16px;
  font-weight: 600;
  font-family: monospace;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.device-item:last-child {
  border-bottom: none;
}

.device-name {
  color: #ccd6f6;
  font-size: 13px;
}

.btn-row {
  display: flex;
  gap: 8px;
}

.btn-row :deep(.el-button) {
  flex: 1;
}

.status-bar {
  display: flex;
  gap: 30px;
  background: rgba(0, 20, 40, 0.85);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 20px;
  padding: 8px 24px;
  backdrop-filter: blur(10px);
}

.status-item {
  color: #8892b0;
  font-size: 13px;
}

.mt-3 {
  margin-top: 12px;
}
</style>