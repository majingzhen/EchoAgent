<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getSimulations } from "@/api/simulation";
import { getSentimentGuardSessions } from "@/api/sentiment_guard";
import { getStrategyAdvisorSessions } from "@/api/strategy_advisor";
import { downloadReport } from "@/api/export";

const route = useRoute();
const router = useRouter();

type Tab = "market" | "simulation" | "sentiment" | "strategy";
const activeTab = ref<Tab>((route.query.tab as Tab) || "simulation");
const setTab = (t: Tab) => {
  activeTab.value = t;
  router.replace({ query: { tab: t } });
};

watch(() => route.query.tab, (v) => {
  if (v) activeTab.value = v as Tab;
});

const fmtTime = (t: string) => t ? t.replace("T", " ").slice(0, 16) : "";
const statusClass = (s: string) => s === "completed" ? "tag-ok" : s === "failed" ? "tag-err" : "tag-run";

// ── 传播推演 ────────────────────────────
const simSessions = ref<any[]>([]);
const simLoading = ref(false);
const simStatusMap: Record<string, string> = { pending: "待运行", running: "运行中", completed: "已完成", failed: "失败" };

const loadSims = async () => {
  simLoading.value = true;
  try { simSessions.value = ((await getSimulations()) as any).data ?? []; } catch { /**/ }
  simLoading.value = false;
};

const goSimDetail = (id: number) => router.push(`/simulation/run?session_id=${id}`);
const goNewSim = () => router.push("/simulation/run");

// ── 舆情预判 ────────────────────────────
const sentSessions = ref<any[]>([]);
const sentLoading = ref(false);
const sentStatusMap: Record<string, string> = { pending: "待运行", running: "运行中", completed: "已完成", failed: "失败" };

const loadSent = async () => {
  sentLoading.value = true;
  try { sentSessions.value = ((await getSentimentGuardSessions()) as any).data ?? []; } catch { /**/ }
  sentLoading.value = false;
};

const goSentDetail = (id: number) => router.push(`/sentiment-guard/session?session_id=${id}`);
const goNewSent = () => router.push("/sentiment-guard/session");

// ── 策略建议 ────────────────────────────
const stratSessions = ref<any[]>([]);
const stratLoading = ref(false);
const stratStatusMap: Record<string, string> = { pending: "待运行", running: "运行中", completed: "已完成", failed: "失败" };

const loadStrat = async () => {
  stratLoading.value = true;
  try { stratSessions.value = ((await getStrategyAdvisorSessions()) as any).data ?? []; } catch { /**/ }
  stratLoading.value = false;
};

const goStratDetail = (id: number) => router.push(`/strategy-advisor/session?session_id=${id}`);
const goNewStrat = () => router.push("/strategy-advisor/session");

// ── 初始加载 ────────────────────────────
onMounted(() => {
  loadSims();
  loadSent();
  loadStrat();
});
</script>

<template>
  <div class="page">
    <!-- Tab 导航 -->
    <div class="tab-bar">
      <button :class="['tab', activeTab === 'market' && 'active']" @click="setTab('market')">市场图谱</button>
      <button :class="['tab', activeTab === 'simulation' && 'active']" @click="setTab('simulation')">传播推演</button>
      <button :class="['tab', activeTab === 'sentiment' && 'active']" @click="setTab('sentiment')">舆情预判</button>
      <button :class="['tab', activeTab === 'strategy' && 'active']" @click="setTab('strategy')">策略建议</button>
    </div>

    <!-- 市场图谱 -->
    <template v-if="activeTab === 'market'">
      <div class="section-header">
        <div>
          <h2>市场图谱</h2>
          <p class="tip">上传竞品文章、评测、舆情文本，AI 构建可视化知识图谱并生成竞品分析报告。</p>
        </div>
        <button @click="router.push('/market/graph')">打开图谱工具</button>
      </div>
      <div class="market-intro card">
        <div class="intro-grid">
          <div class="intro-step">
            <div class="step-n">1</div>
            <div class="step-text">上传竞品文章、用户评论、舆情汇总（.txt / .md / .pdf）</div>
          </div>
          <div class="intro-arrow">→</div>
          <div class="intro-step">
            <div class="step-n">2</div>
            <div class="step-text">AI 提取实体关系，构建价格 / 成分 / 口碑知识图谱</div>
          </div>
          <div class="intro-arrow">→</div>
          <div class="intro-step">
            <div class="step-n">3</div>
            <div class="step-text">生成竞品短板报告，可注入内容工坊生成差异化文案</div>
          </div>
        </div>
        <div class="intro-action">
          <button @click="router.push('/market/graph')">进入市场图谱</button>
        </div>
      </div>
    </template>

    <!-- 传播推演 -->
    <template v-else-if="activeTab === 'simulation'">
      <div class="section-header">
        <div>
          <h2>传播推演</h2>
          <p class="tip">让虚拟画像在模拟社交平台传播 N 轮，预判互动率、情绪曲线与扩散路径。</p>
        </div>
        <button @click="goNewSim">新建推演</button>
      </div>

      <p v-if="simLoading" class="tip">加载中...</p>
      <p v-else-if="!simSessions.length" class="tip empty">暂无推演记录。</p>

      <div v-else class="session-grid">
        <div v-for="s in simSessions" :key="s.id" class="session-card card">
          <div class="card-top">
            <span class="card-id">#{{ s.id }}</span>
            <span :class="['tag', statusClass(s.status)]">{{ simStatusMap[s.status] ?? s.status }}</span>
          </div>
          <div class="card-info">
            <span class="info-label">平台</span> {{ s.platform }}
            <span class="info-label ml">轮次</span> {{ s.current_round }}/{{ s.total_rounds }}
          </div>
          <div class="card-meta">
            <span>画像组 #{{ s.persona_group_id }}</span>
            <span>{{ fmtTime(s.created_at) }}</span>
          </div>
          <div class="card-btns" @click.stop>
            <button class="sm-btn" @click="goSimDetail(s.id)">查看详情</button>
            <template v-if="s.status === 'completed'">
              <button class="sm-btn export-btn" @click="downloadReport('simulation', s.id, 'pdf')">PDF</button>
              <button class="sm-btn export-btn" @click="downloadReport('simulation', s.id, 'pptx')">PPT</button>
            </template>
          </div>
        </div>
      </div>
    </template>

    <!-- 舆情预判 -->
    <template v-else-if="activeTab === 'sentiment'">
      <div class="section-header">
        <div>
          <h2>舆情预判</h2>
          <p class="tip">输入潜在或已发生的负面事件，AI 评估传播风险，输出多套应对方案。</p>
        </div>
        <button @click="goNewSent">新建评估</button>
      </div>

      <p v-if="sentLoading" class="tip">加载中...</p>
      <p v-else-if="!sentSessions.length" class="tip empty">暂无评估记录。</p>

      <div v-else class="session-grid">
        <div v-for="s in sentSessions" :key="s.id" class="session-card card">
          <div class="card-top">
            <span class="card-id">#{{ s.id }}</span>
            <span :class="['tag', statusClass(s.status)]">{{ sentStatusMap[s.status] ?? s.status }}</span>
          </div>
          <div class="card-mode">
            <span class="mode-tag" :class="s.mode === 'proactive' ? 'mode-pro' : 'mode-re'">
              {{ s.mode === 'proactive' ? '事前预判' : '事后应对' }}
            </span>
          </div>
          <div class="card-desc">{{ (s.event_description ?? "").slice(0, 70) }}</div>
          <div class="card-meta"><span>{{ fmtTime(s.created_at) }}</span></div>
          <div class="card-btns">
            <button class="sm-btn" @click="goSentDetail(s.id)">查看详情</button>
            <template v-if="s.status === 'completed'">
              <button class="sm-btn export-btn" @click="downloadReport('sentiment-guard', s.id, 'pdf')">PDF</button>
              <button class="sm-btn export-btn" @click="downloadReport('sentiment-guard', s.id, 'pptx')">PPT</button>
            </template>
          </div>
        </div>
      </div>
    </template>

    <!-- 策略建议 -->
    <template v-else-if="activeTab === 'strategy'">
      <div class="section-header">
        <div>
          <h2>策略建议</h2>
          <p class="tip">5 种思维模型同时分析同一个业务决策问题，交叉辩论后输出综合决策框架。</p>
        </div>
        <button @click="goNewStrat">新建分析</button>
      </div>

      <p v-if="stratLoading" class="tip">加载中...</p>
      <p v-else-if="!stratSessions.length" class="tip empty">暂无分析记录。</p>

      <div v-else class="session-grid">
        <div v-for="s in stratSessions" :key="s.id" class="session-card card">
          <div class="card-top">
            <span class="card-id">#{{ s.id }}</span>
            <span :class="['tag', statusClass(s.status)]">{{ stratStatusMap[s.status] ?? s.status }}</span>
          </div>
          <div class="card-desc">{{ (s.question ?? "").slice(0, 80) }}</div>
          <div class="card-meta"><span>{{ fmtTime(s.created_at) }}</span></div>
          <div class="card-btns">
            <button class="sm-btn" @click="goStratDetail(s.id)">查看详情</button>
            <template v-if="s.status === 'completed'">
              <button class="sm-btn export-btn" @click="downloadReport('strategy-advisor', s.id, 'pdf')">PDF</button>
              <button class="sm-btn export-btn" @click="downloadReport('strategy-advisor', s.id, 'pptx')">PPT</button>
            </template>
          </div>
        </div>
      </div>
    </template>
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

.tab-bar { display: flex; gap: 4px; border-bottom: 1px solid #d9e2ec; }
.tab {
  border: none; background: none; padding: 10px 18px; font-size: 15px;
  color: #627d98; cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -1px; border-radius: 0;
}
.tab.active { color: #102a43; font-weight: 600; border-bottom-color: #334e68; }

/* Market intro */
.market-intro { margin-top: 4px; }
.intro-grid {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  margin-bottom: 20px;
}
.intro-step {
  display: flex; gap: 12px; align-items: flex-start;
  background: #f0f4f8; border-radius: 10px; padding: 14px 16px;
  max-width: 200px; flex: 1 1 160px;
}
.step-n {
  width: 24px; height: 24px; background: #334e68; color: #fff;
  border-radius: 50%; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-text { font-size: 13px; color: #334e68; line-height: 1.5; }
.intro-arrow { font-size: 20px; color: #9fb3c8; flex-shrink: 0; }
.intro-action { display: flex; justify-content: flex-start; }

/* Sessions */
.session-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.session-card {
  display: flex; flex-direction: column; gap: 8px; cursor: pointer;
  transition: border-color 0.15s;
}
.session-card:hover { border-color: #829ab1; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.card-id { font-weight: 600; font-size: 13px; color: #829ab1; }
.card-info { font-size: 14px; color: #334e68; }
.info-label { font-size: 12px; color: #829ab1; margin-right: 3px; }
.info-label.ml { margin-left: 10px; }
.card-desc { font-size: 13px; color: #627d98; line-height: 1.5; }
.card-meta { font-size: 12px; color: #829ab1; display: flex; justify-content: space-between; }
.card-btns { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.card-mode { margin: -2px 0 2px; }
.mode-tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.mode-pro { background: #d4edda; color: #155724; }
.mode-re { background: #fff3cd; color: #856404; }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.tag-ok { background: #d4edda; color: #155724; }
.tag-err { background: #f8d7da; color: #721c24; }
.tag-run { background: #fff3cd; color: #856404; }

button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
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
