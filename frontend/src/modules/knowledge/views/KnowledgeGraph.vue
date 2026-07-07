<template>
  <div class="knowledge-graph">
    <div class="page-header">
      <h2>📚 农业知识图谱</h2>
      <p>基于Neo4j的农业知识图谱 + RAG智能问答（预留模块）</p>
    </div>
    <div class="feature-grid">
      <div class="feature-card">
        <div class="card-icon">🔗</div>
        <h3>知识图谱查询</h3>
        <p>查询病虫害、作物、农药之间的关联关系</p>
      </div>
      <div class="feature-card">
        <div class="card-icon">💬</div>
        <h3>RAG智能问答</h3>
        <p>基于知识图谱的智能问答系统，提供专业农业咨询</p>
      </div>
      <div class="feature-card">
        <div class="card-icon">🗣️</div>
        <h3>语音交互</h3>
        <p>支持语音输入和语音播报，方便农户操作</p>
      </div>
      <div class="feature-card">
        <div class="card-icon">📊</div>
        <h3>图谱可视化</h3>
        <p>直观展示知识图谱结构，支持搜索和导航</p>
      </div>
    </div>
    <div class="demo-chat">
      <h4>💬 智能问答演示</h4>
      <div class="chat-messages">
        <div class="message user">番茄叶子发黄怎么办？</div>
        <div class="message bot">根据知识图谱分析，番茄叶子发黄可能是以下原因：</div>
        <div class="message bot">1. 缺氮：叶片均匀发黄，补充氮肥</div>
        <div class="message bot">2. 缺铁：新叶发黄，补充铁肥</div>
        <div class="message bot">3. 病虫害：检查是否有病虫害迹象</div>
      </div>
      <div class="chat-input">
        <input type="text" placeholder="输入您的农业问题..." />
        <button>提问</button>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.knowledge-graph { padding:20px; }
.page-header { margin-bottom:30px; }
.page-header h2 { color:#00d4ff; font-size:24px; margin:0; }
.page-header p { color:#7a9abb; font-size:14px; margin:8px 0 0 0; }
.feature-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; margin-bottom:30px; }
.feature-card { background:rgba(0,20,40,0.7); border:1px solid rgba(0,212,255,0.2); border-radius:12px; padding:20px; }
.card-icon { font-size:28px; margin-bottom:12px; }
.feature-card h3 { color:#e6f1ff; font-size:16px; margin:0 0 8px 0; }
.feature-card p { color:#7a9abb; font-size:13px; margin:0; line-height:1.6; }
.demo-chat { background:rgba(0,20,40,0.7); border:1px solid rgba(0,212,255,0.2); border-radius:12px; padding:20px; }
.demo-chat h4 { color:#00d4ff; font-size:16px; margin:0 0 16px 0; }
.chat-messages { margin-bottom:16px; }
.message { padding:10px 14px; border-radius:8px; margin-bottom:8px; font-size:14px; }
.message.user { background:rgba(64,158,255,0.2); color:#409eff; }
.message.bot { background:rgba(103,194,58,0.1); color:#85ce61; }
.chat-input { display:flex; gap:10px; }
.chat-input input { flex:1; padding:10px 14px; border:1px solid rgba(0,212,255,0.3); border-radius:8px; background:rgba(0,10,30,0.6); color:#e6f1ff; outline:none; }
.chat-input button { padding:10px 20px; background:rgba(0,212,255,0.2); border:1px solid rgba(0,212,255,0.5); border-radius:8px; color:#00d4ff; cursor:pointer; }
</style>