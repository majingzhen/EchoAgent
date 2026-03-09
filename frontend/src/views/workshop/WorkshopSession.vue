<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import {
  createWorkshopABTest,
  createWorkshopSession,
  getContentResults,
  getWorkshopSession,
  injectWorkshopInsights,
  runWorkshopSession,
  saveContentResult,
} from "@/api/workshop";
import { getPersonaGroups } from "@/api/persona";
import FileUploadField from "@/components/FileUploadField.vue";
import { briefTemplates } from "@/config/templates";

const route = useRoute();

const groups = ref<any[]>([]);
const form = ref({
  persona_group_id: Number(route.query.groupId) || 0,
  platform: "小红书",
  brand_tone: "专业可信、真诚克制",
  brief: "新品精华液，主打温和提亮，预算在300元内",
  goal: "提升转化率",
  product: "光感精华液",
  market_graph_id: null as number | null,
});

const sessionId = ref<number | null>(null);
const abTest = ref<any>(null);
const error = ref("");
const loading = ref(false);
const readonly = ref(false);

// 流式结果
const steps = ref<{
  angles: any[] | null;
  drafts: any[] | null;
  feedback: any[] | null;
  brand_guard: any | null;
  final_content: string | null;
  winner_variant: string | null;
}>({
  angles: null,
  drafts: null,
  feedback: null,
  brand_guard: null,
  final_content: null,
  winner_variant: null,
});
const currentStep = ref(""); // 当前正在进行的 step label
const done = ref(false);

let wsInstance: WebSocket | null = null;

const setupWorkshopWS = (sid: number) => {
  wsInstance?.close();
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const base = (import.meta.env.VITE_WS_BASE_URL as string) ?? `${proto}://${location.hostname}:8000`;
  const ws = new WebSocket(`${base}/api/ws/workshop/${sid}`);
  ws.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    if (data.type === "progress") {
      currentStep.value = data.message ?? data.step;
    } else if (data.type === "step_done") {
      currentStep.value = "";
      if (data.step === "angles") steps.value.angles = data.data;
      else if (data.step === "drafts") steps.value.drafts = data.data;
      else if (data.step === "feedback") steps.value.feedback = data.data;
      else if (data.step === "brand_guard") steps.value.brand_guard = data.data;
    } else if (data.type === "done") {
      const d = data.data;
      steps.value.angles = d.strategist_angles ?? steps.value.angles;
      steps.value.drafts = d.drafts ?? steps.value.drafts;
      steps.value.feedback = d.consumer_feedback ?? steps.value.feedback;
      steps.value.brand_guard = d.brand_review ?? steps.value.brand_guard;
      steps.value.final_content = d.final_content ?? null;
      steps.value.winner_variant = d.winner_variant ?? null;
      currentStep.value = "";
      done.value = true;
      loading.value = false;
      loadResults();
    } else if (data.type === "error") {
      error.value = data.message ?? "运行失败";
      currentStep.value = "";
      loading.value = false;
    }
  };
  wsInstance = ws;
};

onMounted(async () => {
  try {
    const resp = await getPersonaGroups();
    groups.value = resp.data ?? [];
    if (!form.value.persona_group_id && groups.value.length > 0) {
      form.value.persona_group_id = groups.value[0].id;
    }
  } catch { /* ignore */ }

  // 历史回看模式
  const historyId = Number(route.query.session_id);
  if (historyId) {
    readonly.value = true;
    sessionId.value = historyId;
    try {
      const resp = await getWorkshopSession(historyId);
      const d = resp.data?.payload ?? {};
      steps.value.angles = d.strategist_angles ?? null;
      steps.value.drafts = d.drafts ?? null;
      steps.value.feedback = d.consumer_feedback ?? null;
      steps.value.brand_guard = d.brand_review ?? null;
      steps.value.final_content = d.final_content ?? null;
      steps.value.winner_variant = d.winner_variant ?? null;
      if (resp.data?.status === "completed") done.value = true;
      await loadResults();
    } catch { /* ignore */ }
  }
});

const createSession = async () => {
  loading.value = true;
  error.value = "";
  done.value = false;
  steps.value = { angles: null, drafts: null, feedback: null, brand_guard: null, final_content: null, winner_variant: null };
  try {
    const resp = await createWorkshopSession({
      persona_group_id: form.value.persona_group_id,
      platform: form.value.platform,
      brand_tone: form.value.brand_tone,
      brief: form.value.brief,
      goal: form.value.goal,
      product: form.value.product,
    });
    sessionId.value = resp.data.id as number;
    abTest.value = null;
    setupWorkshopWS(resp.data.id as number);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "创建工坊失败";
  } finally {
    loading.value = false;
  }
};

const runWorkshop = async () => {
  if (!sessionId.value) return;
  loading.value = true;
  error.value = "";
  done.value = false;
  steps.value = { angles: null, drafts: null, feedback: null, brand_guard: null, final_content: null, winner_variant: null };
  try {
    await runWorkshopSession(sessionId.value, { market_graph_id: form.value.market_graph_id });
    // 结果通过 WS 推送，不等待 HTTP 返回内容
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "运行工坊失败";
    loading.value = false;
  }
};

const injectInsights = async () => {
  if (!sessionId.value || !form.value.market_graph_id) return;
  loading.value = true;
  error.value = "";
  try {
    await injectWorkshopInsights(sessionId.value, form.value.market_graph_id);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "注入洞察失败";
  } finally {
    loading.value = false;
  }
};

const launchAB = async () => {
  if (!sessionId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const resp = await createWorkshopABTest(sessionId.value);
    abTest.value = resp.data;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "发起 A/B 测试失败";
  } finally {
    loading.value = false;
  }
};

// 根据 variant 找 feedback 评分
const feedbackFor = (variant: string) =>
  steps.value.feedback?.find((f: any) => f.variant === variant);

// ── 结果回填 ─────────────────────────────────────────────
const resultForm = ref({
  variant: "",
  went_live: false,
  actual_engagement_rate: null as number | null,
  actual_conversion_rate: null as number | null,
  notes: "",
});
const savedResults = ref<any[]>([]);
const resultLoading = ref(false);
const resultError = ref("");
const showResultForm = ref(false);

const loadResults = async () => {
  if (!sessionId.value) return;
  try {
    const resp = await getContentResults(sessionId.value);
    savedResults.value = (resp as any).data ?? [];
  } catch { /* ignore */ }
};

const submitResult = async () => {
  if (!sessionId.value || !resultForm.value.variant) return;
  resultLoading.value = true;
  resultError.value = "";
  try {
    await saveContentResult(sessionId.value, {
      variant: resultForm.value.variant,
      went_live: resultForm.value.went_live,
      actual_engagement_rate: resultForm.value.actual_engagement_rate,
      actual_conversion_rate: resultForm.value.actual_conversion_rate,
      notes: resultForm.value.notes,
    });
    showResultForm.value = false;
    await loadResults();
  } catch (e: any) {
    resultError.value = e.message ?? "保存失败";
  } finally {
    resultLoading.value = false;
  }
};

const variantOptions = () => steps.value.drafts?.map((d: any) => d.variant) ?? [];
</script>

<template>
  <section class="card">
    <h2>内容工坊</h2>
    <p class="tip">填写产品 Brief，AI 依次生成策略方向、多版本文案，并让虚拟画像打分，每步完成后实时展示。</p>

    <div class="grid">
      <label>
        画像组（虚拟消费者评审团）
        <select v-if="groups.length" v-model.number="form.persona_group_id">
          <option v-for="g in groups" :key="g.id" :value="g.id">
            #{{ g.id }} {{ g.name }}（{{ g.persona_count }} 人）
          </option>
        </select>
        <input v-else v-model.number="form.persona_group_id" type="number" min="1" />
      </label>
      <div class="row-2">
        <label>平台<input v-model="form.platform" /></label>
        <label>品牌调性<input v-model="form.brand_tone" /></label>
      </div>
      <div class="row-2">
        <label>产品名<input v-model="form.product" /></label>
        <label>营销目标<input v-model="form.goal" /></label>
      </div>
      <FileUploadField
        v-model="form.brief"
        label="产品资料文件"
        placeholder="上传产品 Brief / 规格说明 / 策划文档"
      />
      <label>
        或选择 Brief 模板（自动填充到上方文件内容）
        <select @change="(e) => { const v = (e.target as HTMLSelectElement).value; if (v) form.brief = v; (e.target as HTMLSelectElement).value = ''; }">
          <option value="">-- 选择预设模板 --</option>
          <option v-for="t in briefTemplates" :key="t.label" :value="t.value">{{ t.label }}</option>
        </select>
      </label>
      <label>市场图谱 ID（可选）<input v-model.number="form.market_graph_id" type="number" /></label>
    </div>

    <div class="actions">
      <button :disabled="loading || !form.persona_group_id || readonly" @click="createSession">① 创建工坊会话</button>
      <button :disabled="loading || !sessionId || readonly" @click="runWorkshop">② 运行多 Agent 流程</button>
      <button :disabled="loading || !sessionId || !form.market_graph_id || readonly" @click="injectInsights">注入市场洞察</button>
      <button :disabled="loading || !done" class="secondary" @click="launchAB">发起 A/B 测试</button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <!-- 进度提示 -->
  <section v-if="currentStep" class="card progress-card">
    <span class="spinner" />
    <span>{{ currentStep }}</span>
  </section>

  <!-- Step 1: 策略方向 -->
  <section v-if="steps.angles" class="card">
    <h3>① 策略方向</h3>
    <div class="angles">
      <div v-for="angle in steps.angles" :key="angle.title" class="angle-card">
        <strong>{{ angle.title }}</strong>
        <p>{{ angle.core_message }}</p>
        <span class="meta">受众：{{ angle.audience }}</span>
      </div>
    </div>
  </section>

  <!-- Step 2: 文案草稿 + 评分 -->
  <section v-if="steps.drafts" class="card">
    <h3>② 文案版本 <span v-if="!steps.feedback" class="badge-loading">评分中...</span></h3>
    <div class="drafts">
      <div
        v-for="draft in steps.drafts"
        :key="draft.variant"
        :class="['draft-card', draft.variant === steps.winner_variant ? 'winner' : '']"
      >
        <div class="draft-header">
          <strong>{{ draft.variant }}</strong>
          <span class="angle-tag">{{ draft.angle }}</span>
          <span v-if="draft.variant === steps.winner_variant" class="win-badge">最优</span>
        </div>
        <pre>{{ draft.content }}</pre>
        <div v-if="feedbackFor(draft.variant)" class="score-row">
          画像评分：<strong>{{ feedbackFor(draft.variant).avg_score }}</strong> / 10 ·
          <span>{{ feedbackFor(draft.variant).highlights.join("；") }}</span>
        </div>
        <div v-else-if="steps.drafts && !steps.feedback" class="score-row loading">
          画像评分生成中...
        </div>
      </div>
    </div>
  </section>

  <!-- Step 3: 品牌审核 -->
  <section v-if="steps.brand_guard" class="card">
    <h3>③ 品牌合规审核</h3>
    <p>
      合规评分：<strong>{{ steps.brand_guard.score }}</strong> / 10 ·
      {{ steps.brand_guard.needs_fix ? "需要修订" : "通过" }}
    </p>
    <p v-if="steps.brand_guard.risk_hits?.length">风险词：{{ steps.brand_guard.risk_hits.join("、") }}</p>
    <ul>
      <li v-for="s in steps.brand_guard.suggestions" :key="s">{{ s }}</li>
    </ul>
  </section>

  <!-- 最终文案 -->
  <section v-if="steps.final_content" class="card final-card">
    <h3>最终文案（{{ steps.winner_variant }}）</h3>
    <pre>{{ steps.final_content }}</pre>
  </section>

  <!-- A/B 测试 -->
  <section v-if="abTest" class="card">
    <h3>A/B 测试已发起</h3>
    <pre>{{ JSON.stringify(abTest, null, 2) }}</pre>
  </section>

  <!-- 上线结果回填 -->
  <section v-if="done" class="card">
    <div class="result-header">
      <h3>记录上线结果</h3>
      <button class="secondary" @click="showResultForm = !showResultForm">
        {{ showResultForm ? '收起' : '+ 新增记录' }}
      </button>
    </div>

    <form v-if="showResultForm" class="result-form" @submit.prevent="submitResult">
      <div class="row-2">
        <label>
          文案版本
          <select v-model="resultForm.variant" required>
            <option value="" disabled>请选择</option>
            <option v-for="v in variantOptions()" :key="v" :value="v">{{ v }}</option>
          </select>
        </label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="resultForm.went_live" />
          已上线投放
        </label>
      </div>
      <div class="row-2">
        <label>实际互动率（%）<input v-model.number="resultForm.actual_engagement_rate" type="number" step="0.01" min="0" max="100" placeholder="可选" /></label>
        <label>实际转化率（%）<input v-model.number="resultForm.actual_conversion_rate" type="number" step="0.01" min="0" max="100" placeholder="可选" /></label>
      </div>
      <label>备注<textarea v-model="resultForm.notes" rows="2" placeholder="记录投放情况、受众反馈等" /></label>
      <div class="form-actions">
        <button type="submit" :disabled="resultLoading || !resultForm.variant">保存记录</button>
        <p v-if="resultError" class="error">{{ resultError }}</p>
      </div>
    </form>

    <div v-if="savedResults.length" class="result-list">
      <table>
        <thead><tr><th>版本</th><th>上线</th><th>互动率</th><th>转化率</th><th>备注</th></tr></thead>
        <tbody>
          <tr v-for="r in savedResults" :key="r.id">
            <td>{{ r.variant }}</td>
            <td>{{ r.went_live ? '是' : '否' }}</td>
            <td>{{ r.actual_engagement_rate != null ? r.actual_engagement_rate + '%' : '-' }}</td>
            <td>{{ r.actual_conversion_rate != null ? r.actual_conversion_rate + '%' : '-' }}</td>
            <td class="notes-cell">{{ r.notes || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else-if="!showResultForm" class="tip" style="margin:0">暂无上线结果记录</p>
  </section>
</template>

<style scoped>
.card {
  border: 1px solid #d9e2ec;
  border-radius: 12px;
  background: #fff;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.tip { color: #486581; font-size: 14px; margin: 0 0 16px; }
.grid { display: grid; gap: 12px; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
label { display: grid; gap: 6px; font-size: 14px; }
input, select, textarea {
  border: 1px solid #bcccdc;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
}
.actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }
button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.secondary { background: #fff; color: #334e68; border: 1px solid #334e68; }
.secondary:hover:not(:disabled) { background: #f0f4f8; }
.error { color: #d64545; font-size: 14px; margin-top: 10px; }

.progress-card {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #486581;
  font-size: 14px;
  padding: 12px 20px;
}
.spinner {
  width: 16px; height: 16px;
  border: 2px solid #d9e2ec;
  border-top-color: #334e68;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

.angles { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.angle-card {
  border: 1px solid #d9e2ec; border-radius: 8px; padding: 12px; background: #f8fbff;
}
.angle-card strong { display: block; margin-bottom: 6px; font-size: 14px; }
.angle-card p { margin: 0 0 8px; font-size: 13px; color: #486581; line-height: 1.5; }
.meta { font-size: 12px; color: #829ab1; }

.badge-loading { font-size: 12px; color: #829ab1; font-weight: normal; margin-left: 8px; }

.drafts { display: flex; flex-direction: column; gap: 14px; }
.draft-card {
  border: 1px solid #d9e2ec; border-radius: 8px; padding: 14px; background: #f8fbff;
}
.draft-card.winner { border-color: #334e68; background: #edf5ff; }
.draft-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.angle-tag {
  font-size: 12px; color: #627d98; background: #d9e2ec; border-radius: 4px; padding: 2px 6px;
}
.win-badge {
  font-size: 12px; background: #334e68; color: #fff; border-radius: 4px; padding: 2px 7px;
}
pre { white-space: pre-wrap; font-size: 14px; line-height: 1.7; margin: 0 0 10px; }
.score-row { font-size: 13px; color: #486581; }
.score-row.loading { color: #9fb3c8; font-style: italic; }

ul { margin: 0; padding-left: 18px; }
li { font-size: 14px; color: #486581; line-height: 1.7; }

.final-card pre {
  background: #f0f4f8; border: 1px solid #d9e2ec; border-radius: 8px; padding: 14px;
}

.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.result-header h3 { margin: 0; }
.result-form { display: grid; gap: 12px; margin-bottom: 16px; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 14px; padding-top: 22px; }
.checkbox-label input { width: auto; }
textarea { border: 1px solid #bcccdc; border-radius: 8px; padding: 8px 10px; font-size: 14px; resize: vertical; font-family: inherit; }
.form-actions { display: flex; align-items: center; gap: 12px; }
.result-list { margin-top: 8px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; padding: 8px 10px; background: #f0f4f8; color: #486581; font-weight: 600; border-bottom: 1px solid #d9e2ec; }
td { padding: 8px 10px; border-bottom: 1px solid #f0f4f8; color: #334e68; }
.notes-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
