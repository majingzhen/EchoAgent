<script setup lang="ts">
import { ref } from "vue";
import { searchEnhance } from "@/api/search";

const MODULE_OPTIONS = [
  { value: "general",   label: "通用增强" },
  { value: "workshop",  label: "内容工坊" },
  { value: "market",    label: "市场分析" },
  { value: "persona",   label: "画像研究" },
];

const query = ref("");
const module = ref("general");
const maxResults = ref(5);
const loading = ref(false);
const error = ref("");
const result = ref<any>(null);

const submit = async () => {
  if (!query.value.trim()) return;
  loading.value = true;
  error.value = "";
  result.value = null;
  try {
    const resp = await searchEnhance(query.value.trim(), module.value, maxResults.value);
    result.value = (resp as any).data ?? resp;
  } catch (e: any) {
    error.value = e.message ?? "搜索失败";
  } finally {
    loading.value = false;
  }
};

const copyInsights = () => {
  if (!result.value?.insights?.length) return;
  const text = result.value.insights.join("\n");
  navigator.clipboard.writeText(text).catch(() => {});
};

const copySummary = () => {
  if (!result.value?.summary) return;
  navigator.clipboard.writeText(result.value.summary).catch(() => {});
};
</script>

<template>
  <section class="card">
    <h2>联网数据增强</h2>
    <p class="tip">搜索互联网实时数据，AI 提炼关键洞察，注入到各模块增强分析效果。</p>

    <div class="form-grid">
      <div class="row-3">
        <label>
          搜索关键词
          <input v-model="query" placeholder="例如：2024年小红书护肤趋势" @keydown.enter="submit" />
        </label>
        <label>
          应用场景
          <select v-model="module">
            <option v-for="o in MODULE_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
        <label>
          结果数量
          <select v-model.number="maxResults">
            <option :value="3">3 条</option>
            <option :value="5">5 条</option>
            <option :value="8">8 条</option>
          </select>
        </label>
      </div>
      <button :disabled="loading || !query.trim()" @click="submit">
        {{ loading ? "搜索中..." : "联网搜索 + AI 增强" }}
      </button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <!-- Results -->
  <template v-if="result">
    <!-- AI Summary & Insights -->
    <section class="card insight-card">
      <div class="insight-header">
        <div>
          <h3>AI 洞察摘要</h3>
          <span class="module-tag">{{ MODULE_OPTIONS.find(o => o.value === result.module)?.label }}</span>
        </div>
        <button class="copy-btn" @click="copySummary">复制摘要</button>
      </div>
      <p class="summary-text">{{ result.summary }}</p>

      <div v-if="result.insights?.length" class="insights-block">
        <div class="insights-header">
          <h4>关键洞察（{{ result.insights.length }} 条）</h4>
          <button class="copy-btn" @click="copyInsights">复制全部</button>
        </div>
        <ul class="insights-list">
          <li v-for="(insight, i) in result.insights" :key="i">
            <span class="insight-num">{{ i + 1 }}</span>
            <span>{{ insight }}</span>
          </li>
        </ul>
      </div>

      <div v-if="result.suggested_use" class="suggest-use">
        <span class="suggest-label">使用建议</span>
        <span>{{ result.suggested_use }}</span>
      </div>
    </section>

    <!-- Raw Search Results -->
    <section v-if="result.results?.length" class="card">
      <h3>原始搜索结果（{{ result.results.length }} 条）</h3>
      <div class="results-list">
        <div v-for="(r, i) in result.results" :key="i" class="result-item">
          <div class="result-top">
            <span class="result-index">{{ i + 1 }}</span>
            <a :href="r.url" target="_blank" rel="noopener" class="result-title">{{ r.title }}</a>
          </div>
          <p class="result-snippet">{{ r.snippet }}</p>
          <span class="result-url">{{ r.url }}</span>
        </div>
      </div>
    </section>
  </template>
</template>

<style scoped>
.card {
  border: 1px solid #d9e2ec;
  border-radius: 12px;
  background: #fff;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.tip { color: #486581; font-size: 14px; margin: 0 0 14px; }
.form-grid { display: grid; gap: 12px; }
.row-3 {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 12px;
}
label { display: grid; gap: 6px; font-size: 14px; }
input, select {
  border: 1px solid #bcccdc;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
}
button {
  border: 0; border-radius: 8px; padding: 8px 16px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.error { color: #d64545; font-size: 14px; margin-top: 8px; }

/* insight card */
.insight-card { background: #f8fbff; }
.insight-header {
  display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;
}
.insight-header h3 { margin: 0 0 4px; }
.module-tag {
  display: inline-block;
  background: #d9e2ec; color: #334e68;
  font-size: 12px; padding: 2px 8px; border-radius: 10px;
}
.copy-btn {
  background: #fff; color: #334e68; border: 1px solid #334e68;
  padding: 4px 10px; font-size: 12px; border-radius: 6px; cursor: pointer;
}
.copy-btn:hover { background: #f0f4f8; }
.summary-text { font-size: 14px; color: #334e68; line-height: 1.7; margin: 0 0 16px; }
.insights-block { border-top: 1px solid #d9e2ec; padding-top: 14px; }
.insights-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;
}
.insights-header h4 { margin: 0; font-size: 14px; color: #334e68; }
.insights-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.insights-list li { display: flex; gap: 10px; align-items: flex-start; font-size: 14px; color: #334e68; line-height: 1.6; }
.insight-num {
  flex-shrink: 0;
  width: 20px; height: 20px;
  background: #334e68; color: #fff;
  border-radius: 50%; font-size: 11px;
  display: flex; align-items: center; justify-content: center;
}
.suggest-use {
  margin-top: 14px;
  padding: 10px 14px;
  background: #fff3cd;
  border-radius: 8px;
  font-size: 13px;
  color: #856404;
  display: flex;
  gap: 8px;
}
.suggest-label {
  font-weight: 600;
  white-space: nowrap;
}

/* raw results */
.results-list { display: flex; flex-direction: column; gap: 14px; }
.result-item {
  border: 1px solid #d9e2ec; border-radius: 8px; padding: 12px 14px; background: #f8fbff;
}
.result-top { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.result-index {
  flex-shrink: 0; width: 20px; height: 20px;
  background: #829ab1; color: #fff; border-radius: 50%; font-size: 11px;
  display: flex; align-items: center; justify-content: center;
}
.result-title {
  font-size: 14px; font-weight: 600; color: #334e68; text-decoration: none;
}
.result-title:hover { text-decoration: underline; }
.result-snippet { font-size: 13px; color: #486581; line-height: 1.6; margin: 0 0 6px; }
.result-url { font-size: 11px; color: #9fb3c8; word-break: break-all; }
</style>
