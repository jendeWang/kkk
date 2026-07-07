<template>
  <div class="greenhouse-3d">
    <div ref="containerRef" class="canvas-container"></div>

    <div class="hud-overlay">
      <!-- 顶部标题 -->
      <div class="hud-header">
        <div class="header-deco left"></div>
        <h1>智慧大棚数字孪生平台</h1>
        <div class="header-deco right"></div>
        <div class="hud-time">{{ currentTime }}</div>
      </div>

      <!-- 左侧环境面板 -->
      <div class="hud-left">
        <div class="data-panel">
          <div class="panel-title">🌿 环境监测</div>
          <div class="env-grid">
            <div class="env-card temp">
              <div class="env-icon">🌡️</div>
              <div class="env-val">{{ envData.temperature ? envData.temperature.toFixed(1) : '--' }}</div>
              <div class="env-unit">°C</div>
              <div class="env-label">温度</div>
              <div class="env-status" :class="tempStatus"></div>
            </div>
            <div class="env-card hum">
              <div class="env-icon">💧</div>
              <div class="env-val">{{ envData.humidity ? envData.humidity.toFixed(1) : '--' }}</div>
              <div class="env-unit">%</div>
              <div class="env-label">湿度</div>
              <div class="env-status normal"></div>
            </div>
            <div class="env-card light">
              <div class="env-icon">☀️</div>
              <div class="env-val">{{ envData.light ? (envData.light / 1000).toFixed(1) : '--' }}</div>
              <div class="env-unit">klux</div>
              <div class="env-label">光照</div>
              <div class="env-status normal"></div>
            </div>
            <div class="env-card soil">
              <div class="env-icon">🌱</div>
              <div class="env-val">{{ envData.soil ? envData.soil.toFixed(1) : '--' }}</div>
              <div class="env-unit">%</div>
              <div class="env-label">土壤</div>
              <div class="env-status" :class="soilStatus"></div>
            </div>
            <div class="env-card co2">
              <div class="env-icon">🫁</div>
              <div class="env-val">{{ envData.co2 ? envData.co2.toFixed(0) : '--' }}</div>
              <div class="env-unit">ppm</div>
              <div class="env-label">CO2</div>
              <div class="env-status normal"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧设备面板 -->
      <div class="hud-right">
        <div class="data-panel">
          <div class="panel-title">⚡ 设备控制</div>
          <div class="device-item">
            <span class="device-icon">🌀</span>
            <span class="device-name">通风风扇</span>
            <el-switch v-model="deviceState.fan" @change="toggleFan" active-color="#67c23a" />
          </div>
          <div class="device-item">
            <span class="device-icon">💡</span>
            <span class="device-name">补光灯</span>
            <el-switch v-model="deviceState.light" @change="toggleLight" active-color="#e6a23c" />
          </div>
          <div class="device-item">
            <span class="device-icon">🪟</span>
            <span class="device-name">遮阳帘</span>
            <el-switch v-model="deviceState.curtain" @change="toggleCurtain" active-color="#409eff" />
          </div>
          <div class="device-item">
            <span class="device-icon">💧</span>
            <span class="device-name">灌溉泵</span>
            <el-switch v-model="deviceState.pump" @change="togglePump" active-color="#67c23a" />
          </div>
        </div>

        <div class="data-panel mt-3">
          <div class="panel-title">🎮 视角控制</div>
          <div class="btn-row">
            <el-button size="small" @click="resetCamera">重置</el-button>
            <el-button size="small" @click="toggleAutoRotate">{{ autoRotate ? '停止' : '旋转' }}</el-button>
            <el-button size="small" @click="goBack">返回</el-button>
          </div>
        </div>
      </div>

      <!-- 底部状态栏 -->
      <div class="hud-bottom">
        <div class="status-bar">
          <span class="status-dot" :class="connected ? 'online' : 'offline'"></span>
          <span class="status-item">{{ connected ? '系统运行正常' : '等待连接...' }}</span>
          <span class="status-divider">|</span>
          <span class="status-item">📡 {{ connected ? '1 设备在线' : '无在线设备' }}</span>
          <span class="status-divider">|</span>
          <span class="status-item">{{ envData.temperature ? '实时同步' : '加载中...' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'
import api from '../services/api.js'

const router = useRouter()
const containerRef = ref(null)
const currentTime = ref('')
const deviceId = ref(null)
const connected = ref(false)
const autoRotate = ref(false)

const envData = reactive({ temperature: 0, humidity: 0, light: 0, soil: 0, co2: 0 })
const deviceState = reactive({ fan: true, light: false, curtain: false, pump: false })

const tempStatus = computed(() => envData.temperature > 35 ? 'danger' : envData.temperature > 30 ? 'warning' : 'normal')
const soilStatus = computed(() => envData.soil < 30 ? 'warning' : 'normal')

let scene, camera, renderer, labelRenderer, controls
let animationId
let greenhouseGroup, fanGroup, fanBladeGroup, lightBulbs = [], curtainMesh, pumpGroup, waterParticles
let sensorLabels = []
let eventSource = null
let lastSensorUpdate = 0
let clock = new THREE.Clock()

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
  scene.background = new THREE.Color(0x070e1a)
  scene.fog = new THREE.FogExp2(0x070e1a, 0.015)

  camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000)
  camera.position.set(14, 10, 16)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  container.appendChild(renderer.domElement)

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(width, height)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0'
  labelRenderer.domElement.style.pointerEvents = 'none'
  container.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.06
  controls.minDistance = 5
  controls.maxDistance = 40
  controls.maxPolarAngle = Math.PI / 2.1
  controls.target.set(0, 2, 0)

  // 光照
  scene.add(new THREE.AmbientLight(0x334466, 0.5))
  const dirLight = new THREE.DirectionalLight(0xffeedd, 0.7)
  dirLight.position.set(8, 18, 10)
  dirLight.castShadow = true
  dirLight.shadow.mapSize.set(2048, 2048)
  dirLight.shadow.camera.near = 0.5
  dirLight.shadow.camera.far = 50
  dirLight.shadow.camera.left = -20
  dirLight.shadow.camera.right = 20
  dirLight.shadow.camera.top = 20
  dirLight.shadow.camera.bottom = -20
  scene.add(dirLight)
  scene.add(new THREE.HemisphereLight(0x6699cc, 0x223322, 0.3))

  createGround()
  createGreenhouse()
  createPlants()
  createSensors()
  createWaterParticles()
  animate()
}

function createGround() {
  // 土地
  const groundGeo = new THREE.PlaneGeometry(80, 80, 40, 40)
  const positions = groundGeo.attributes.position
  for (let i = 0; i < positions.count; i++) {
    positions.setZ(i, Math.random() * 0.15)
  }
  groundGeo.computeVertexNormals()
  const groundMat = new THREE.MeshStandardMaterial({ color: 0x1a3a1a, roughness: 0.95, metalness: 0.05 })
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.receiveShadow = true
  scene.add(ground)

  // 网格
  const grid = new THREE.GridHelper(50, 50, 0x0a3040, 0x071828)
  grid.position.y = 0.01
  scene.add(grid)
}

function createGreenhouse() {
  greenhouseGroup = new THREE.Group()
  const W = 12, D = 8, H = 2.8, RH = 2.2

  const frameMat = new THREE.MeshStandardMaterial({ color: 0xc0a030, metalness: 0.8, roughness: 0.25 })
  const coverMat = new THREE.MeshPhysicalMaterial({
    color: 0x88ccff, transparent: true, opacity: 0.18,
    side: THREE.DoubleSide, roughness: 0.05, metalness: 0.0,
    transmission: 0.6, thickness: 0.1,
  })
  const FT = 0.07

  // 立柱（前后各7根）
  for (let i = 0; i <= 6; i++) {
    const z = -D / 2 + (D / 6) * i
    const poleGeo = new THREE.BoxGeometry(FT, H, FT)
    ;[-W / 2, W / 2].forEach(x => {
      const pole = new THREE.Mesh(poleGeo, frameMat)
      pole.position.set(x, H / 2, z)
      pole.castShadow = true
      greenhouseGroup.add(pole)
    })
  }

  // 横梁
  const beamGeo = new THREE.BoxGeometry(W, FT, FT)
  ;[-D / 2, 0, D / 2].forEach(z => {
    const beam = new THREE.Mesh(beamGeo, frameMat)
    beam.position.set(0, H, z)
    beam.castShadow = true
    greenhouseGroup.add(beam)
  })

  // 屋脊
  const ridgeGeo = new THREE.BoxGeometry(FT, FT, D)
  const ridge = new THREE.Mesh(ridgeGeo, frameMat)
  ridge.position.set(0, H + RH, 0)
  ridge.castShadow = true
  greenhouseGroup.add(ridge)

  // 屋顶椽条
  for (let i = 0; i <= 6; i++) {
    const z = -D / 2 + (D / 6) * i
    ;[-1, 1].forEach(side => {
      const len = Math.sqrt((W / 2) ** 2 + RH ** 2)
      const rafterGeo = new THREE.BoxGeometry(len, FT * 0.6, FT * 0.6)
      const rafter = new THREE.Mesh(rafterGeo, frameMat)
      const angle = Math.atan2(RH, W / 2)
      rafter.position.set(side * W / 4, H + RH / 2, z)
      rafter.rotation.z = -side * (Math.PI / 2 - angle)
      rafter.castShadow = true
      greenhouseGroup.add(rafter)
    })
  }

  // 屋顶覆盖
  const roofShape = new THREE.Shape()
  roofShape.moveTo(-W / 2, 0)
  roofShape.lineTo(0, RH)
  roofShape.lineTo(W / 2, 0)
  roofShape.lineTo(-W / 2, 0)
  const roofGeo = new THREE.ExtrudeGeometry(roofShape, { depth: D, bevelEnabled: false })
  const roofCover = new THREE.Mesh(roofGeo, coverMat)
  roofCover.position.set(0, H, -D / 2)
  greenhouseGroup.add(roofCover)

  // 侧墙
  const sideGeo = new THREE.PlaneGeometry(D, H)
  ;[-W / 2, W / 2].forEach((x, i) => {
    const wall = new THREE.Mesh(sideGeo, coverMat)
    wall.position.set(x, H / 2, 0)
    wall.rotation.y = i === 0 ? Math.PI / 2 : -Math.PI / 2
    greenhouseGroup.add(wall)
  })

  // 后墙
  const backWall = new THREE.Mesh(new THREE.PlaneGeometry(W, H), coverMat)
  backWall.position.set(0, H / 2, -D / 2)
  greenhouseGroup.add(backWall)

  // 前墙（带门洞）
  const doorW = 1.8, doorH = 2.2
  const frontL = new THREE.Mesh(new THREE.PlaneGeometry((W - doorW) / 2, H), coverMat)
  frontL.position.set(-(W + doorW) / 4, H / 2, D / 2)
  greenhouseGroup.add(frontL)
  const frontR = new THREE.Mesh(new THREE.PlaneGeometry((W - doorW) / 2, H), coverMat)
  frontR.position.set((W + doorW) / 4, H / 2, D / 2)
  greenhouseGroup.add(frontR)
  // 门上横梁
  const doorTopGeo = new THREE.PlaneGeometry(doorW, H - doorH)
  const doorTop = new THREE.Mesh(doorTopGeo, coverMat)
  doorTop.position.set(0, doorH + (H - doorH) / 2, D / 2)
  greenhouseGroup.add(doorTop)
  // 门
  const doorMat = new THREE.MeshStandardMaterial({ color: 0x8b5e3c, roughness: 0.7, metalness: 0.2 })
  const doorMesh = new THREE.Mesh(new THREE.BoxGeometry(doorW, doorH, 0.06), doorMat)
  doorMesh.position.set(0, doorH / 2, D / 2 + 0.03)
  doorMesh.castShadow = true
  greenhouseGroup.add(doorMesh)

  // 地面
  const floorMat = new THREE.MeshStandardMaterial({ color: 0x3d2b1f, roughness: 0.95 })
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.5, D - 0.5), floorMat)
  floor.rotation.x = -Math.PI / 2
  floor.position.y = 0.02
  floor.receiveShadow = true
  greenhouseGroup.add(floor)

  // ---- 执行器 ----

  // 风扇（墙壁安装式）
  fanGroup = new THREE.Group()
  const fanHousingMat = new THREE.MeshStandardMaterial({ color: 0x3a4a5a, metalness: 0.8, roughness: 0.3 })
  const fanHousing = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 0.15, 24), fanHousingMat)
  fanHousing.rotation.z = Math.PI / 2
  fanGroup.add(fanHousing)
  // 外圈
  const ringMat = new THREE.MeshStandardMaterial({ color: 0x5a6a7a, metalness: 0.9, roughness: 0.2 })
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.65, 0.04, 8, 24), ringMat)
  ring.rotation.y = Math.PI / 2
  fanGroup.add(ring)
  // 扇叶组
  fanBladeGroup = new THREE.Group()
  const bladeMat = new THREE.MeshStandardMaterial({ color: 0x8899aa, metalness: 0.6, roughness: 0.4, side: THREE.DoubleSide })
  for (let i = 0; i < 5; i++) {
    const shape = new THREE.Shape()
    shape.moveTo(0, 0)
    shape.quadraticCurveTo(0.12, 0.25, 0.05, 0.5)
    shape.lineTo(-0.05, 0.5)
    shape.quadraticCurveTo(-0.12, 0.25, 0, 0)
    const bladeGeo = new THREE.ShapeGeometry(shape)
    const blade = new THREE.Mesh(bladeGeo, bladeMat)
    blade.rotation.y = (Math.PI * 2 / 5) * i
    fanBladeGroup.add(blade)
  }
  // 中心轴
  const hubGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.12, 12)
  const hub = new THREE.Mesh(hubGeo, fanHousingMat)
  hub.rotation.z = Math.PI / 2
  fanBladeGroup.add(hub)
  fanGroup.add(fanBladeGroup)
  fanGroup.position.set(-W / 2 - 0.08, 2.0, -1.5)
  fanGroup.rotation.y = Math.PI / 2
  greenhouseGroup.add(fanGroup)

  // 补光灯
  lightBulbs = []
  const bulbPositions = [[-3, H - 0.25, -2], [3, H - 0.25, -2], [-3, H - 0.25, 2], [3, H - 0.25, 2]]
  bulbPositions.forEach(pos => {
    const bg = new THREE.Group()
    // 灯罩
    const shadeMat = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.7, roughness: 0.3 })
    const shade = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.15, 12, 1, true), shadeMat)
    shade.rotation.x = Math.PI
    shade.position.y = 0.08
    bg.add(shade)
    // 灯泡
    const bulbMat = new THREE.MeshStandardMaterial({ color: 0x555555, emissive: 0x000000, emissiveIntensity: 0 })
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 16), bulbMat)
    bg.add(bulb)
    // 吊线
    const wireGeo = new THREE.CylinderGeometry(0.008, 0.008, 0.3, 4)
    const wire = new THREE.Mesh(wireGeo, new THREE.MeshBasicMaterial({ color: 0x333333 }))
    wire.position.y = 0.22
    bg.add(wire)
    // 点光源
    const pl = new THREE.PointLight(0xffdd88, 0, 8, 2)
    bg.add(pl)
    bg.userData = { bulb, pointLight: pl }
    bg.position.set(...pos)
    lightBulbs.push(bg)
    greenhouseGroup.add(bg)
  })

  // 遮阳帘
  curtainMesh = new THREE.Group()
  const curtainMat = new THREE.MeshStandardMaterial({ color: 0x2a3a4a, side: THREE.DoubleSide, roughness: 0.85 })
  // 左侧帘
  const cGeo = new THREE.PlaneGeometry(W / 2 - 0.5, H - 0.5)
  const cLeft = new THREE.Mesh(cGeo, curtainMat)
  cLeft.position.set(-W / 4 - 0.25, (H - 0.5) / 2, 0)
  curtainMesh.add(cLeft)
  // 右侧帘
  const cRight = new THREE.Mesh(cGeo, curtainMat)
  cRight.position.set(W / 4 + 0.25, (H - 0.5) / 2, 0)
  curtainMesh.add(cRight)
  curtainMesh.position.y = H - 0.25
  greenhouseGroup.add(curtainMesh)

  // 灌溉泵
  pumpGroup = new THREE.Group()
  const pumpMat = new THREE.MeshStandardMaterial({ color: 0x2a6e3f, metalness: 0.6, roughness: 0.4 })
  const pumpBody = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.3, 0.5, 12), pumpMat)
  pumpBody.position.y = 0.25
  pumpBody.castShadow = true
  pumpGroup.add(pumpBody)
  // 管道
  const pipeMat = new THREE.MeshStandardMaterial({ color: 0x4488aa, metalness: 0.7, roughness: 0.3 })
  const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.2, 8), pipeMat)
  pipe.position.set(0, 0.7, 0)
  pumpGroup.add(pipe)
  // 出水口
  const nozzle = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.05, 0.15, 8), pipeMat)
  nozzle.position.set(0, 1.3, 0)
  pumpGroup.add(nozzle)
  pumpGroup.position.set(4.5, 0, 3)
  greenhouseGroup.add(pumpGroup)

  scene.add(greenhouseGroup)
}

function createPlants() {
  const stemMat = new THREE.MeshStandardMaterial({ color: 0x2e7d32, roughness: 0.9 })
  const positions = []
  for (let x = -4; x <= 4; x += 2.5) {
    for (let z = -2.5; z <= 2.5; z += 2.5) {
      if (Math.abs(x - 4.5) < 1 && Math.abs(z - 3) < 1) continue // 避开泵位
      positions.push([x, z])
    }
  }
  positions.forEach(([x, z]) => {
    const pg = new THREE.Group()
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.04, 0.35, 6), stemMat)
    stem.position.y = 0.175
    pg.add(stem)
    const count = 4 + Math.floor(Math.random() * 4)
    for (let i = 0; i < count; i++) {
      const lMat = new THREE.MeshStandardMaterial({ color: new THREE.Color().setHSL(0.28 + Math.random() * 0.06, 0.7, 0.22 + Math.random() * 0.15), roughness: 0.85 })
      const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.2 + Math.random() * 0.12, 7, 7), lMat)
      leaf.position.set((Math.random() - 0.5) * 0.35, 0.35 + Math.random() * 0.4, (Math.random() - 0.5) * 0.35)
      leaf.scale.y = 0.7 + Math.random() * 0.3
      pg.add(leaf)
    }
    pg.position.set(x, 0, z)
    pg.scale.setScalar(0.75 + Math.random() * 0.35)
    plants.push(pg)
    greenhouseGroup.add(pg)
  })
}

const plants = []

function createSensors() {
  const sensors = [
    { text: '🌡️ 温度', color: '#ff6b6b', pos: [-4.5, 1.8, -3.2] },
    { text: '💧 湿度', color: '#4ecdc4', pos: [4.5, 1.8, -3.2] },
    { text: '☀️ 光照', color: '#ffd93d', pos: [0, 3.5, 0] },
    { text: '🌱 土壤', color: '#6bc46d', pos: [-3, 0.4, 3] },
  ]
  sensors.forEach(({ text, color, pos }) => {
    // 3D发光点
    const glowMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(color), transparent: true, opacity: 0.8 })
    const sphere = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), glowMat)
    sphere.position.set(...pos)
    greenhouseGroup.add(sphere)
    // CSS标签
    const div = document.createElement('div')
    div.style.cssText = `background:rgba(0,15,30,0.9);color:${color};padding:3px 8px;border-radius:3px;font-size:11px;font-family:monospace;border:1px solid ${color}55;white-space:nowrap;box-shadow:0 0 8px ${color}40;`
    div.textContent = text
    const label = new CSS2DObject(div)
    label.position.set(pos[0], pos[1] + 0.3, pos[2])
    sensorLabels.push({ label, div })
    greenhouseGroup.add(label)
  })
}

function createWaterParticles() {
  const count = 200
  const geo = new THREE.BufferGeometry()
  const positions = new Float32Array(count * 3)
  const velocities = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    positions[i * 3] = 4.5 + (Math.random() - 0.5) * 0.3
    positions[i * 3 + 1] = 1.4 + Math.random() * 2
    positions[i * 3 + 2] = 3 + (Math.random() - 0.5) * 2
    velocities[i * 3] = (Math.random() - 0.5) * 0.01
    velocities[i * 3 + 1] = -0.02 - Math.random() * 0.02
    velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.02
  }
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  const mat = new THREE.PointsMaterial({ color: 0x66bbff, size: 0.04, transparent: true, opacity: 0 })
  waterParticles = new THREE.Points(geo, mat)
  waterParticles.userData.velocities = velocities
  scene.add(waterParticles)
}

function updateSensorLabels() {
  const now = Date.now()
  if (now - lastSensorUpdate < 800) return
  lastSensorUpdate = now
  if (sensorLabels.length >= 4) {
    sensorLabels[0].div.textContent = `🌡️ 温度 ${envData.temperature ? envData.temperature.toFixed(1) + '°C' : '--'}`
    sensorLabels[1].div.textContent = `💧 湿度 ${envData.humidity ? envData.humidity.toFixed(1) + '%' : '--'}`
    sensorLabels[2].div.textContent = `☀️ 光照 ${envData.light ? (envData.light / 1000).toFixed(1) + 'klux' : '--'}`
    sensorLabels[3].div.textContent = `🌱 土壤 ${envData.soil ? envData.soil.toFixed(1) + '%' : '--'}`
  }
}

function updateWaterParticles() {
  if (!waterParticles) return
  const mat = waterParticles.material
  mat.opacity = deviceState.pump ? 0.7 : 0
  if (!deviceState.pump) return
  const pos = waterParticles.geometry.attributes.position
  const vel = waterParticles.userData.velocities
  for (let i = 0; i < pos.count; i++) {
    pos.array[i * 3] += vel[i * 3]
    pos.array[i * 3 + 1] += vel[i * 3 + 1]
    pos.array[i * 3 + 2] += vel[i * 3 + 2]
    if (pos.array[i * 3 + 1] < 0) {
      pos.array[i * 3] = 4.5 + (Math.random() - 0.5) * 0.3
      pos.array[i * 3 + 1] = 1.3 + Math.random() * 0.3
      pos.array[i * 3 + 2] = 3 + (Math.random() - 0.5) * 0.5
    }
  }
  pos.needsUpdate = true
}

function sync3DState() {
  // 灯光
  lightBulbs.forEach(bg => {
    const { bulb, pointLight } = bg.userData
    if (deviceState.light) {
      bulb.material.color.set(0xffdd88)
      bulb.material.emissive.set(0xffdd88)
      bulb.material.emissiveIntensity = 2
      pointLight.intensity = 2
    } else {
      bulb.material.color.set(0x555555)
      bulb.material.emissive.set(0x000000)
      bulb.material.emissiveIntensity = 0
      pointLight.intensity = 0
    }
  })
  // 帘
  if (curtainMesh) {
    const targetY = deviceState.curtain ? 0 : 2.55
    curtainMesh.position.y += (targetY - curtainMesh.position.y) * 0.1
  }
}

function animate() {
  animationId = requestAnimationFrame(animate)
  const dt = clock.getDelta()

  // 风扇旋转
  if (deviceState.fan && fanBladeGroup) {
    fanBladeGroup.rotation.z += 0.2
  }

  // 自动旋转
  if (autoRotate.value && controls) {
    const angle = 0.002
    const r = Math.hypot(camera.position.x - controls.target.x, camera.position.z - controls.target.z)
    const a = Math.atan2(camera.position.z - controls.target.z, camera.position.x - controls.target.x)
    camera.position.x = controls.target.x + Math.cos(a + angle) * r
    camera.position.z = controls.target.z + Math.sin(a + angle) * r
    camera.lookAt(controls.target)
  }

  controls.update()
  updateSensorLabels()
  updateWaterParticles()
  sync3DState()
  updateTime()
  renderer.render(scene, camera)
  labelRenderer.render(scene, camera)
}

// API & SSE
async function loadRealtimeData() {
  try {
    const res = await api.get('/devices/', { params: { status: 'online' } })
    const devices = res.data
    if (devices.length > 0) {
      deviceId.value = devices[0].id
      connected.value = true
    }
    if (!deviceId.value) return
    const latestRes = await api.get('/telemetry/latest', { params: { device_id: deviceId.value } })
    const vals = latestRes.data.latest_values || []
    for (const item of vals) {
      const v = parseFloat(item.value)
      if (item.property_identifier === 'temperature') envData.temperature = v
      else if (item.property_identifier === 'humidity') envData.humidity = v
      else if (item.property_identifier === 'light_intensity') envData.light = v
      else if (item.property_identifier === 'soil_moisture') envData.soil = v
      else if (item.property_identifier === 'co2') envData.co2 = v
    }
    updateSensorLabels()
  } catch (e) { console.warn('Load data failed:', e) }
}

function connectSSE() {
  const token = localStorage.getItem('token')
  if (!token) return
  try {
    eventSource = new EventSource(`/api/v1/sse/devices?token=${token}`)
    eventSource.onmessage = (event) => {
      try {
        const d = JSON.parse(event.data)
        if (d.device_id !== deviceId.value) return
        const v = parseFloat(d.value), p = d.property_identifier
        if (p === 'temperature') envData.temperature = v
        else if (p === 'humidity') envData.humidity = v
        else if (p === 'light_intensity') envData.light = v
        else if (p === 'soil_moisture') envData.soil = v
        else if (p === 'co2') envData.coil = v
        else if (p === 'fan_switch') deviceState.fan = v === 1
        else if (p === 'light_switch') deviceState.light = v === 1
        else if (p === 'curtain_switch') deviceState.curtain = v === 1
        else if (p === 'pump_switch') deviceState.pump = v === 1
        updateSensorLabels()
      } catch (e) {}
    }
    eventSource.onerror = () => { eventSource.close(); setTimeout(connectSSE, 5000) }
  } catch (e) { console.warn('SSE failed:', e) }
}

function resetCamera() { camera.position.set(14, 10, 16); controls.target.set(0, 2, 0); controls.update() }
function toggleAutoRotate() { autoRotate.value = !autoRotate.value }
function goBack() { router.push('/dashboard') }

function toggleFan(v) { deviceState.fan = v; sendCmd('fan_switch', v ? 1 : 0) }
function toggleLight(v) { deviceState.light = v; sync3DState(); sendCmd('light_switch', v ? 1 : 0) }
function toggleCurtain(v) { deviceState.curtain = v; sendCmd('curtain_switch', v ? 1 : 0) }
function togglePump(v) { deviceState.pump = v; sendCmd('pump_switch', v ? 1 : 0) }

async function sendCmd(sid, val) {
  if (!deviceId.value) { ElMessage.warning('未检测到在线设备'); return }
  try { await api.post('/commands/', { device_id: deviceId.value, service_identifier: sid, input_params: { value: String(val) } }); ElMessage.success('命令已下发') }
  catch (e) { ElMessage.error('命令下发失败') }
}

function onResize() {
  if (!containerRef.value || !camera || !renderer) return
  const w = containerRef.value.clientWidth, h = containerRef.value.clientHeight
  camera.aspect = w / h; camera.updateProjectionMatrix()
  renderer.setSize(w, h); labelRenderer.setSize(w, h)
}

onMounted(async () => { init(); window.addEventListener('resize', onResize); await loadRealtimeData(); connectSSE() })
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (eventSource) { eventSource.close(); eventSource = null }
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) renderer.dispose()
})
</script>

<style scoped>
.greenhouse-3d { width:100%; height:100vh; position:relative; overflow:hidden; background:#070e1a; }
.canvas-container { width:100%; height:100%; }
.hud-overlay { position:absolute; inset:0; pointer-events:none; z-index:10; }

/* 顶部 */
.hud-header { position:absolute; top:16px; left:50%; transform:translateX(-50%); text-align:center; }
.hud-header h1 { color:#00d4ff; font-size:22px; margin:0; text-shadow:0 0 30px rgba(0,212,255,0.4); letter-spacing:6px; }
.hud-time { color:#5a7a99; font-size:13px; margin-top:4px; font-family:monospace; }

/* 左侧 */
.hud-left { position:absolute; top:70px; left:16px; pointer-events:auto; }
.env-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.env-card { background:rgba(0,20,40,0.7); border:1px solid rgba(0,212,255,0.2); border-radius:6px; padding:8px 10px; text-align:center; position:relative; overflow:hidden; }
.env-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.env-card.temp::before { background:linear-gradient(90deg,#ff6b6b,#ff6b6b00); }
.env-card.hum::before { background:linear-gradient(90deg,#4ecdc4,#4ecdc400); }
.env-card.light::before { background:linear-gradient(90deg,#ffd93d,#ffd93d00); }
.env-card.soil::before { background:linear-gradient(90deg,#6bc46d,#6bc46d00); }
.env-card.co2::before { background:linear-gradient(90deg,#a78bfa,#a78bfa00); }
.env-icon { font-size:16px; }
.env-val { color:#e6f1ff; font-size:18px; font-weight:700; font-family:monospace; line-height:1.2; }
.env-unit { color:#5a7a99; font-size:11px; }
.env-label { color:#7a9abb; font-size:10px; margin-top:2px; }
.env-status { width:6px; height:6px; border-radius:50%; position:absolute; top:6px; right:6px; }
.env-status.normal { background:#67c23a; box-shadow:0 0 6px #67c23a; }
.env-status.warning { background:#e6a23c; box-shadow:0 0 6px #e6a23c; }
.env-status.danger { background:#f56c6c; box-shadow:0 0 6px #f56c6c; }

/* 右侧 */
.hud-right { position:absolute; top:70px; right:16px; pointer-events:auto; }

/* 通用面板 */
.data-panel { background:rgba(0,15,30,0.85); border:1px solid rgba(0,212,255,0.25); border-radius:8px; padding:12px; width:220px; backdrop-filter:blur(12px); box-shadow:0 0 20px rgba(0,212,255,0.08); }
.panel-title { color:#00d4ff; font-size:13px; font-weight:600; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid rgba(0,212,255,0.15); letter-spacing:2px; }
.device-item { display:flex; align-items:center; gap:6px; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.device-item:last-child { border-bottom:none; }
.device-icon { font-size:14px; }
.device-name { flex:1; color:#b0c4de; font-size:12px; }
.btn-row { display:flex; gap:6px; }
.btn-row :deep(.el-button) { flex:1; font-size:12px; }

/* 底部 */
.hud-bottom { position:absolute; bottom:16px; left:50%; transform:translateX(-50%); }
.status-bar { display:flex; align-items:center; gap:10px; background:rgba(0,15,30,0.85); border:1px solid rgba(0,212,255,0.2); border-radius:20px; padding:6px 20px; backdrop-filter:blur(10px); }
.status-dot { width:7px; height:7px; border-radius:50%; }
.status-dot.online { background:#67c23a; box-shadow:0 0 8px #67c23a; }
.status-dot.offline { background:#f56c6c; box-shadow:0 0 8px #f56c6c; }
.status-item { color:#6a8aa8; font-size:12px; }
.status-divider { color:#1a3a5a; }

.mt-3 { margin-top:10px; }
</style>
