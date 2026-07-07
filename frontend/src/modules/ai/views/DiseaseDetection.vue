<template>
  <div class="ai-detection">
    <div class="page-header">
      <h2>🌿 AI病虫害识别</h2>
      <p>基于YOLOv8的智能病虫害识别服务（预留模块）</p>
    </div>
    <div class="feature-card">
      <div class="card-icon">📷</div>
      <div class="card-content">
        <h3>图像上传与识别</h3>
        <p>上传作物叶片照片，AI自动识别病虫害类型和严重程度</p>
      </div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🔍</div>
      <div class="card-content">
        <h3>实时摄像头识别</h3>
        <p>连接USB/RTSP摄像头，实时监测作物健康状况</p>
      </div>
    </div>
    <div class="feature-card">
      <div class="card-icon">💊</div>
      <div class="card-content">
        <h3>防治建议</h3>
        <p>识别结果关联知识图谱，提供针对性防治建议</p>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.ai-detection { padding:20px; }
.page-header { margin-bottom:30px; }
.page-header h2 { color:#00d4ff; font-size:24px; margin:0; }
.page-header p { color:#7a9abb; font-size:14px; margin:8px 0 0 0; }
.feature-card { display:flex; align-items:center; gap:16px; background:rgba(0,20,40,0.7); border:1px solid rgba(0,212,255,0.2); border-radius:12px; padding:20px; margin-bottom:16px; }
.card-icon { font-size:32px; }
.card-content h3 { color:#e6f1ff; font-size:16px; margin:0 0 8px 0; }
.card-content p { color:#7a9abb; font-size:14px; margin:0; line-height:1.6; }
</style>