<template>
  <div class="agents-panel">
    <div class="page-header">
      <h2>🤖 多智能体协同系统</h2>
      <p>气象Agent + 病虫害Agent + 调控Agent 协同工作（预留模块）</p>
    </div>
    <div class="agents-grid">
      <div class="agent-card weather">
        <div class="agent-icon">🌤️</div>
        <h3>气象Agent</h3>
        <p>环境监测与预警</p>
        <div class="agent-status online">运行中</div>
      </div>
      <div class="agent-card disease">
        <div class="agent-icon">🦠</div>
        <h3>病虫害Agent</h3>
        <p>AI识别+防治建议</p>
        <div class="agent-status online">运行中</div>
      </div>
      <div class="agent-card control">
        <div class="agent-icon"><SvgIcon name="bolt" :size="24" /></div>
        <h3>调控Agent</h3>
        <p>设备调度与控制</p>
        <div class="agent-status online">运行中</div>
      </div>
    </div>
    <div class="info-panel">
      <h4>协同机制</h4>
      <ul>
        <li>三个Agent通过消息队列通信</li>
        <li>气象Agent监测环境变化，触发病虫害预警</li>
        <li>病虫害Agent识别问题，推送防治建议</li>
        <li>调控Agent自动执行设备控制命令</li>
        <li>冲突检测与解决机制确保安全</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.agents-panel { padding:20px; }
.page-header { margin-bottom:30px; }
.page-header h2 { color:#00d4ff; font-size:24px; margin:0; }
.page-header p { color:#7a9abb; font-size:14px; margin:8px 0 0 0; }
.agents-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-bottom:30px; }
.agent-card { background:rgba(0,20,40,0.7); border:1px solid rgba(0,212,255,0.2); border-radius:12px; padding:24px; text-align:center; }
.agent-card.weather { border-color:rgba(52,152,219,0.4); }
.agent-card.disease { border-color:rgba(155,89,182,0.4); }
.agent-card.control { border-color:rgba(46,134,222,0.4); }
.agent-icon { font-size:48px; margin-bottom:12px; }
.agent-card h3 { color:#e6f1ff; font-size:18px; margin:0 0 8px 0; }
.agent-card p { color:#7a9abb; font-size:13px; margin:0 0 16px 0; }
.agent-status { display:inline-block; padding:4px 12px; border-radius:12px; font-size:12px; font-weight:500; }
.agent-status.online { background:rgba(103,194,58,0.2); color:#67c23a; }
.info-panel { background:rgba(0,20,40,0.7); border:1px solid rgba(0,212,255,0.2); border-radius:12px; padding:20px; }
.info-panel h4 { color:#00d4ff; font-size:16px; margin:0 0 16px 0; }
.info-panel ul { margin:0; padding-left:20px; }
.info-panel li { color:#7a9abb; font-size:14px; line-height:2; }
</style>