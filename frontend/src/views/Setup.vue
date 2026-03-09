<script setup lang="ts">
import { ref } from "vue";

const copied = ref("");

const copy = (text: string, key: string) => {
  navigator.clipboard.writeText(text);
  copied.value = key;
  setTimeout(() => (copied.value = ""), 2000);
};

const providers = [
  {
    name: "通义千问（推荐）",
    comment: "# 阿里云百炼控制台获取：https://bailian.console.aliyun.com/",
    yaml: `llm:
  api_key: sk-your-key
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model_name: qwen-plus
  light_model_name: qwen-turbo
  vision_model_name: qwen-vl-plus`,
  },
  {
    name: "OpenAI",
    comment: "# 从 https://platform.openai.com/api-keys 获取",
    yaml: `llm:
  api_key: sk-your-key
  base_url: https://api.openai.com/v1
  model_name: gpt-4o
  light_model_name: gpt-4o-mini
  vision_model_name: gpt-4o`,
  },
  {
    name: "DeepSeek",
    comment: "# 从 https://platform.deepseek.com 获取",
    yaml: `llm:
  api_key: sk-your-key
  base_url: https://api.deepseek.com/v1
  model_name: deepseek-chat
  light_model_name: deepseek-chat`,
  },
  {
    name: "Ollama（本地）",
    comment: "# 本地运行，无需 API Key",
    yaml: `llm:
  api_key: ollama
  base_url: http://localhost:11434/v1
  model_name: qwen2.5:14b
  light_model_name: qwen2.5:7b`,
  },
];

const activeProvider = ref(0);

const steps = [
  {
    num: 1,
    title: "复制配置模板",
    code: "cp backend/config/app.yaml.example backend/config/app.yaml",
    note: "Docker 用户可跳过此步，直接编辑挂载的配置文件",
  },
  {
    num: 2,
    title: "填写 API Key",
    note: "选择你使用的 LLM 提供商，将下方配置填入 app.yaml",
  },
  {
    num: 3,
    title: "重启服务",
    code: "docker compose restart  # Docker\n# 或\nuvicorn app.main:app --reload  # 本地开发",
    note: "启动日志会打印当前使用的模型，确认配置生效",
  },
];
</script>

<template>
  <div class="setup">
    <div class="hero">
      <div class="badge">配置向导</div>
      <h1>配置 LLM API Key</h1>
      <p>EchoAgent 需要一个兼容 OpenAI 接口的 LLM 服务才能运行。<br>按以下步骤完成配置，配置完成后刷新页面即可使用。</p>
    </div>

    <div class="steps">
      <div v-for="step in steps" :key="step.num" class="step">
        <div class="step-num">{{ step.num }}</div>
        <div class="step-body">
          <div class="step-title">{{ step.title }}</div>
          <div v-if="step.num === 2" class="providers">
            <div class="provider-tabs">
              <button
                v-for="(p, i) in providers"
                :key="i"
                :class="['tab', { active: activeProvider === i }]"
                @click="activeProvider = i"
              >{{ p.name }}</button>
            </div>
            <div class="code-block">
              <pre>{{ providers[activeProvider].comment }}
{{ providers[activeProvider].yaml }}</pre>
              <button
                class="copy-btn"
                @click="copy(providers[activeProvider].yaml, 'yaml')"
              >{{ copied === 'yaml' ? '已复制' : '复制' }}</button>
            </div>
          </div>
          <div v-else-if="step.code" class="code-block">
            <pre>{{ step.code }}</pre>
            <button
              class="copy-btn"
              @click="copy(step.code!, `step${step.num}`)"
            >{{ copied === `step${step.num}` ? '已复制' : '复制' }}</button>
          </div>
          <div class="step-note">{{ step.note }}</div>
        </div>
      </div>
    </div>

    <div class="footer">
      <p>配置完成后，<a href="/" @click.prevent="() => location.reload()">刷新页面</a>即可开始使用</p>
      <p class="hint">完整文档：<code>backend/config/app.yaml.example</code> · 后端 API 文档：<code>http://localhost:8000/docs</code></p>
    </div>
  </div>
</template>

<style scoped>
.setup {
  max-width: 720px;
  margin: 40px auto;
}

.hero {
  text-align: center;
  margin-bottom: 40px;
}

.badge {
  display: inline-block;
  background: #e8f4fd;
  color: #2b6cb0;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  margin-bottom: 16px;
  letter-spacing: 0.5px;
}

.hero h1 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #102a43;
}

.hero p {
  color: #486581;
  font-size: 15px;
  line-height: 1.7;
  margin: 0;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.step {
  display: flex;
  gap: 16px;
  background: #fff;
  border: 1px solid #d9e2ec;
  border-radius: 12px;
  padding: 20px;
}

.step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #102a43;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-body {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: 15px;
  font-weight: 600;
  color: #102a43;
  margin-bottom: 12px;
}

.step-note {
  font-size: 13px;
  color: #829ab1;
  margin-top: 10px;
}

.provider-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.tab {
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid #d9e2ec;
  background: #f7faf8;
  color: #486581;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.1s;
}

.tab.active {
  background: #102a43;
  color: #fff;
  border-color: #102a43;
}

.code-block {
  position: relative;
  background: #1a2332;
  border-radius: 8px;
  padding: 16px;
}

.code-block pre {
  margin: 0;
  font-family: "Cascadia Code", "Fira Code", monospace;
  font-size: 13px;
  color: #e2e8f0;
  white-space: pre;
  overflow-x: auto;
  line-height: 1.6;
}

.copy-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.1);
  color: #a0aec0;
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 5px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.1s;
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.footer {
  margin-top: 32px;
  text-align: center;
  padding: 20px;
  background: #f7faf8;
  border-radius: 12px;
}

.footer p {
  margin: 4px 0;
  font-size: 14px;
  color: #486581;
}

.footer a {
  color: #2b6cb0;
  text-decoration: underline;
  cursor: pointer;
}

.hint {
  font-size: 13px !important;
  color: #829ab1 !important;
}

code {
  background: #e8edf2;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}
</style>
