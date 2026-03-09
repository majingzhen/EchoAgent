<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getWorkshopSessions } from "@/api/workshop";
import { searchEnhance } from "@/api/search";
import { downloadReport } from "@/api/export";

const router = useRouter();
const sessions = ref<any[]>([]);
const loading = ref(false);
const showSearch = ref(false);

// ── Search panel ────────────────────────
const searchQuery = ref("");
const searchLoading = ref(false);
const searchResult = ref<any>(null);

const runSearch = async () => {
  if (!searchQuery.value.trim()) return;
  searchLoading.value = true;
  searchResult.value = null;
  try {
    const r = await searchEnhance(searchQuery.value.trim(), "workshop", 5);
    searchResult.value = (r as any).data ?? r;
  } catch { /**/ }
  searchLoading.value = false;
};

const copyInsights = () => {
  if (!searchResult.value?.insights?.length) return;
  navigator.clipboard.writeText(searchResult.value.insights.join("\n")).catch(() => {});
};

// ── Workshop sessions ───────────────────
const statusMap: Record<string, string> = { planning: "规划中", running: "运行中", completed: "已完成", failed: "失败" };
const statusClass = (s: string) => s === "completed" ? "tag-ok" : s === "failed" ? "tag-err" : "tag-run";
const fmtTime = (t: string) => t ? t.replace("T", " ").slice(0, 16) : "";

onMounted(async () => {
  loading.value = true;
  try {
    const r = await getWorkshopSessions();
    sessions.value = (r as any).data ?? [];
  } catch { /**/ }
  loading.value = false;
});

const goDetail = (id: number) => router.push(`/workshop/session?session_id=${id}`);
const goNew = () => router.push("/workshop/session");
</script>

<template>
  <div class="page">
    <div class="section-header">
      <div>
        <h2>内容工坊</h2>
        <p class="tip">多 Agent 协作生成文案，支持联网数据增强创作背景。</p>
      </div>
      <div class="header-actions">
        <button class="secondary" @click="showSearch = !showSearch">
          {{ showSearch ? '收起联网素材' : '联网素材' }}
        </button>
        <button @click="goNew">新建工坊</button>
      </div>
    </div>

    <!-- 联网搜索面板 -->
    <div v-if="showSearch" class="search-panel card">
      <div class="search-header">
        <h4>联网数据增强</h4>
        <p class="tip">搜索市场趋势、竞品动态，AI 提炼创作洞察，可复制粘贴到工坊 Brief。</p>
      </div>
      <div class="search-row">
        <input
          v-model="searchQuery"
          placeholder="例如：小红书 2024 护肤趋势、竞品成分对比..."
          @keydown.enter="runSearch"
        />
        <button :disabled="searchLoading || !searchQuery.trim()" @click="runSearch">
          {{ searchLoading ? '搜索中...' : '搜索增强' }}
        </button>
      </div>

      <div v-if="searchResult" class="search-result">
        <div class="result-summary">
          <div class="result-summary-text">{{ searchResult.summary }}</div>
          <button class="sm-btn" @click="copyInsights">复制洞察</button>
        </div>
        <ul v-if="searchResult.insights?.length" class="insight-list">
          <li v-for="(ins, i) in searchResult.insights" :key="i">
            <span class="ins-num">{{ i + 1 }}</span>{{ ins }}
          </li>
        </ul>
        <div v-if="searchResult.results?.length" class="raw-results">
          <div class="raw-title">来源</div>
          <div v-for="(r, i) in searchResult.results" :key="i" class="raw-item">
            <a :href="r.url" target="_blank" class="raw-link">{{ r.title }}</a>
            <span class="raw-snippet">{{ r.snippet?.slice(0, 100) }}...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 会话列表 -->
    <p v-if="loading" class="tip">加载中...</p>
    <p v-else-if="!sessions.length" class="tip empty">暂无历史工坊，点击「新建工坊」开始。</p>

    <div v-else class="session-grid">
      <div v-for="s in sessions" :key="s.id" class="session-card card">
        <div class="card-top">
          <span class="card-id">#{{ s.id }}</span>
          <span :class="['tag', statusClass(s.status)]">{{ statusMap[s.status] ?? s.status }}</span>
        </div>
        <div class="card-info">
          <span class="info-label">平台</span> {{ s.platform }}
          <span class="info-label ml">调性</span> {{ s.brand_tone }}
        </div>
        <div class="card-meta">
          <span>画像组 #{{ s.persona_group_id }}</span>
          <span>{{ fmtTime(s.created_at) }}</span>
        </div>
        <div class="card-btns">
          <button class="sm-btn" @click="goDetail(s.id)">查看详情</button>
          <template v-if="s.status === 'completed'">
            <button class="sm-btn export-btn" @click="downloadReport('workshop', s.id, 'pdf')">PDF</button>
            <button class="sm-btn export-btn" @click="downloadReport('workshop', s.id, 'pptx')">PPT</button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; }
.card { border: 1px solid #d9e2ec; border-radius: 12px; background: #fff; padding: 18px 20px; }
.section-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.section-header h2 { margin: 0 0 4px; }
.header-actions { display: flex; gap: 8px; flex-shrink: 0; margin-top: 4px; }
.tip { color: #486581; font-size: 14px; margin: 0; }
.tip.empty { padding: 24px 0; text-align: center; }

/* Search panel */
.search-panel { background: #f8fbff; }
.search-header { margin-bottom: 12px; }
.search-header h4 { margin: 0 0 4px; font-size: 14px; color: #334e68; }
.search-row { display: flex; gap: 10px; margin-bottom: 12px; }
.search-row input {
  flex: 1; border: 1px solid #bcccdc; border-radius: 8px;
  padding: 8px 10px; font-size: 14px;
}
.search-result { border-top: 1px solid #d9e2ec; padding-top: 12px; }
.result-summary { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
.result-summary-text { font-size: 14px; color: #334e68; line-height: 1.6; flex: 1; }
.insight-list { list-style: none; margin: 0 0 12px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.insight-list li { display: flex; gap: 8px; font-size: 13px; color: #334e68; line-height: 1.5; }
.ins-num {
  flex-shrink: 0; width: 18px; height: 18px; background: #334e68; color: #fff;
  border-radius: 50%; font-size: 10px; display: flex; align-items: center; justify-content: center;
}
.raw-results { border-top: 1px solid #e8ecf1; padding-top: 10px; display: flex; flex-direction: column; gap: 8px; }
.raw-title { font-size: 12px; color: #829ab1; margin-bottom: 4px; }
.raw-item { display: flex; flex-direction: column; gap: 2px; }
.raw-link { font-size: 13px; color: #334e68; text-decoration: none; font-weight: 600; }
.raw-link:hover { text-decoration: underline; }
.raw-snippet { font-size: 12px; color: #627d98; }

/* Sessions */
.session-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.session-card { display: flex; flex-direction: column; gap: 8px; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.card-id { font-weight: 600; font-size: 13px; color: #829ab1; }
.card-info { font-size: 14px; color: #334e68; }
.info-label { font-size: 12px; color: #829ab1; margin-right: 3px; }
.info-label.ml { margin-left: 10px; }
.card-meta { font-size: 12px; color: #829ab1; display: flex; justify-content: space-between; }
.card-btns { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.tag-ok { background: #d4edda; color: #155724; }
.tag-err { background: #f8d7da; color: #721c24; }
.tag-run { background: #fff3cd; color: #856404; }

button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.secondary { background: #fff; color: #334e68; border: 1px solid #334e68; }
.secondary:hover { background: #f0f4f8; }
.sm-btn {
  border: 1px solid #d9e2ec; background: #fff; color: #334e68;
  border-radius: 6px; padding: 4px 10px; font-size: 12px; cursor: pointer;
}
.sm-btn:hover { background: #f0f4f8; }
.export-btn { color: #486581; }
</style>
