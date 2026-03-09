<script setup lang="ts">
import { onMounted, ref } from "vue";
import { createWorkflow, getWorkflowTemplates, completeWorkflowStep } from "@/api/workflow";
import { getPersonaGroups } from "@/api/persona";
import FileUploadField from "@/components/FileUploadField.vue";

const groups = ref<any[]>([]);
const templates = ref<Record<string, any>>({});
const workflowType = ref("content_validation");
const personaGroupId = ref(0);
const platform = ref("小红书");
const brandTone = ref("专业、可信");
const brief = ref("");
const marketSourceText = ref("");
const disabledSteps = ref<string[]>([]);

const session = ref<any>(null);
const loading = ref(false);
const error = ref("");
const completing = ref<string | null>(null);

const currentSteps = () => {
  const tpl = templates.value[workflowType.value];
  return tpl ? tpl.steps : [];
};

const stepStatus = (stepName: string) => {
  if (!session.value) return "pending";
  const found = session.value.steps?.find((s: any) => s.name === stepName);
  return found ? found.status : "pending";
};

// 判断当前步骤是否解锁（前面所有非跳过步骤均已完成）
const isStepUnlocked = (stepName: string) => {
  if (!session.value) return false;
  const steps: any[] = session.value.steps ?? [];
  for (const s of steps) {
    if (s.name === stepName) return true;
    if (s.status !== "completed" && s.status !== "skipped") return false;
  }
  return false;
};

// 生成跳转链接，携带工作流参数
const stepNavPath = (stepName: string): string | null => {
  if (!session.value) return null;
  const cfg = session.value.config ?? {};
  const params = new URLSearchParams();
  if (cfg.persona_group_id) params.set("groupId", String(cfg.persona_group_id));
  const routeMap: Record<string, string> = {
    workshop: "/workshop/session",
    simulation: "/simulation/run",
    sentiment_guard: "/sentiment-guard",
    strategy_advisor: "/strategy-advisor",
    market: "/market/graph",
  };
  const base = routeMap[stepName];
  if (!base) return null;
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
};

const stepDescMap: Record<string, string> = {
  workshop: "用 AI 生成多版本文案，进行品牌合规审核并评出最优版本。",
  simulation: "让虚拟画像模拟传播，预测互动率和转化率。",
  sentiment_guard: "监控舆情风险，预判负面话题并获取应对建议。",
  strategy_advisor: "基于全流程数据生成营销策略建议。",
  market: "分析竞品舆情，构建知识图谱，生成竞品洞察报告。",
};

onMounted(async () => {
  try {
    const [groupResp, tplResp] = await Promise.all([
      getPersonaGroups(1),
      getWorkflowTemplates(),
    ]);
    groups.value = groupResp.data ?? [];
    templates.value = tplResp.data ?? {};
    if (groups.value.length) personaGroupId.value = groups.value[0].id;
  } catch { /* ignore */ }
});

const submit = async () => {
  if (!personaGroupId.value || !brief.value.trim()) return;
  loading.value = true;
  error.value = "";
  try {
    const resp = await createWorkflow({
      workflow_type: workflowType.value,
      persona_group_id: personaGroupId.value,
      platform: platform.value,
      brand_tone: brandTone.value,
      brief: brief.value,
      market_source_text: marketSourceText.value,
      disabled_steps: disabledSteps.value,
    });
    session.value = resp.data;
  } catch (e: any) {
    error.value = e.message ?? "创建失败";
  } finally {
    loading.value = false;
  }
};

const markComplete = async (stepName: string) => {
  if (!session.value) return;
  completing.value = stepName;
  try {
    const resp = await completeWorkflowStep(session.value.id, stepName);
    session.value = resp.data;
  } catch (e: any) {
    error.value = e.message ?? "标记失败";
  } finally {
    completing.value = null;
  }
};

const allDone = () =>
  session.value?.steps?.every((s: any) => s.status === "completed" || s.status === "skipped");

const toggleStep = (stepName: string) => {
  const idx = disabledSteps.value.indexOf(stepName);
  if (idx >= 0) disabledSteps.value.splice(idx, 1);
  else disabledSteps.value.push(stepName);
};
</script>

<template>
  <section class="card">
    <h2>工作流引导</h2>
    <p class="tip">选择营销场景，系统按顺序引导你逐步完成各模块操作。每个步骤都提供直达链接，完成后手动标记，流程清晰可控。</p>

    <!-- 配置表单 -->
    <div v-if="!session" class="form-grid">
      <div class="row-2">
        <label>
          营销场景
          <select v-model="workflowType">
            <option v-for="(tpl, key) in templates" :key="key" :value="key">{{ tpl.label }}</option>
          </select>
        </label>
        <label>
          画像组
          <select v-if="groups.length" v-model.number="personaGroupId">
            <option v-for="g in groups" :key="g.id" :value="g.id">#{{ g.id }} {{ g.name }}（{{ g.persona_count }} 人）</option>
          </select>
          <input v-else v-model.number="personaGroupId" type="number" min="1" />
        </label>
      </div>

      <div class="row-2">
        <label>
          平台
          <select v-model="platform">
            <option value="小红书">小红书</option>
            <option value="抖音">抖音</option>
            <option value="微博">微博</option>
            <option value="微信">微信</option>
          </select>
        </label>
        <label>品牌调性<input v-model="brandTone" /></label>
      </div>

      <FileUploadField v-model="brief" label="产品 Brief" placeholder="上传或粘贴营销简报、产品特点..." />

      <FileUploadField
        v-if="workflowType === 'full_campaign'"
        v-model="marketSourceText"
        label="市场分析文本（可选）"
        placeholder="上传竞品分析、行业报告..."
      />

      <!-- 步骤预览与开关 -->
      <div v-if="currentSteps().length" class="steps-preview">
        <p class="steps-title">执行步骤</p>
        <div class="steps-list">
          <div v-for="step in currentSteps()" :key="step.name" class="step-item">
            <span class="step-dot" :class="{ optional: !step.required }" />
            <span class="step-label">{{ step.label }}</span>
            <span v-if="step.required" class="badge-required">必须</span>
            <label v-else class="toggle">
              <input type="checkbox" :checked="!disabledSteps.includes(step.name)" @change="toggleStep(step.name)" />
              启用
            </label>
          </div>
        </div>
      </div>

      <button :disabled="loading || !personaGroupId || !brief.trim()" @click="submit">
        {{ loading ? "创建中..." : "开始引导流程" }}
      </button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- 引导步骤卡片 -->
    <div v-else class="guide-area">
      <div class="guide-header">
        <div>
          <span class="type-badge">{{ templates[session.workflow_type]?.label ?? session.workflow_type }}</span>
          <span v-if="allDone()" class="done-badge">已完成</span>
        </div>
        <span class="session-id">#{{ session.id }}</span>
      </div>

      <div class="step-cards">
        <div
          v-for="(step, idx) in session.steps"
          :key="step.name"
          class="step-card"
          :class="{
            completed: step.status === 'completed',
            active: isStepUnlocked(step.name) && step.status === 'pending',
            skipped: step.status === 'skipped',
            locked: !isStepUnlocked(step.name) && step.status === 'pending',
          }"
        >
          <div class="step-card-left">
            <div class="step-num" :class="step.status">
              <span v-if="step.status === 'completed'">✓</span>
              <span v-else-if="step.status === 'skipped'">—</span>
              <span v-else>{{ idx + 1 }}</span>
            </div>
          </div>
          <div class="step-card-body">
            <div class="step-card-title">
              {{ step.label }}
              <span v-if="!step.required" class="opt-badge">可选</span>
            </div>
            <p class="step-card-desc">{{ stepDescMap[step.name] ?? '' }}</p>
            <div v-if="step.status === 'skipped'" class="step-skip-hint">此步骤已跳过</div>
            <div v-else-if="step.status === 'completed'" class="step-done-hint">已标记完成</div>
            <div v-else class="step-actions">
              <a
                v-if="isStepUnlocked(step.name) && stepNavPath(step.name)"
                :href="stepNavPath(step.name)"
                class="go-btn"
                target="_blank"
              >前往该模块</a>
              <button
                v-if="isStepUnlocked(step.name)"
                :disabled="completing === step.name"
                class="complete-btn"
                @click="markComplete(step.name)"
              >{{ completing === step.name ? '标记中...' : '标记已完成' }}</button>
              <span v-if="!isStepUnlocked(step.name)" class="locked-hint">等待前置步骤完成</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="allDone()" class="done-summary">
        所有步骤已完成，本次营销活动流程已记录。
      </div>
      <p v-if="error" class="error" style="margin-top:10px">{{ error }}</p>
    </div>
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
.tip { color: #486581; font-size: 14px; margin: 0 0 16px; line-height: 1.6; }
.form-grid { display: grid; gap: 12px; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
label { display: grid; gap: 6px; font-size: 14px; }
input, select { border: 1px solid #bcccdc; border-radius: 8px; padding: 8px 10px; font-size: 14px; }
.error { color: #d64545; font-size: 14px; }

.steps-preview { border: 1px solid #e8ecf1; border-radius: 8px; padding: 12px 16px; }
.steps-title { margin: 0 0 10px; font-size: 13px; color: #829ab1; font-weight: 600; }
.steps-list { display: flex; flex-direction: column; gap: 8px; }
.step-item { display: flex; align-items: center; gap: 10px; font-size: 14px; }
.step-dot { width: 8px; height: 8px; border-radius: 50%; background: #334e68; flex-shrink: 0; }
.step-dot.optional { background: #9fb3c8; }
.step-label { flex: 1; color: #334e68; }
.badge-required { font-size: 11px; background: #e8ecf1; color: #486581; border-radius: 4px; padding: 2px 6px; }
.toggle { display: flex; align-items: center; gap: 4px; font-size: 13px; color: #486581; cursor: pointer; }

button {
  border: 0; border-radius: 8px; padding: 8px 16px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }

/* 执行区 */
.guide-area { }
.guide-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.type-badge { font-size: 14px; font-weight: 600; color: #334e68; margin-right: 10px; }
.done-badge { font-size: 12px; border-radius: 4px; padding: 2px 8px; background: #d1fae5; color: #065f46; }
.session-id { font-size: 13px; color: #829ab1; }

.step-cards { display: flex; flex-direction: column; gap: 10px; }
.step-card {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid #e4ecf5;
  border-radius: 10px;
  background: #f8fafc;
  transition: border-color 0.2s;
}
.step-card.completed { border-color: #6ee7b7; background: #f0fdf4; }
.step-card.active { border-color: #334e68; background: #edf5ff; }
.step-card.locked { opacity: 0.55; }
.step-card.skipped { opacity: 0.4; }

.step-card-left { flex-shrink: 0; padding-top: 2px; }
.step-num {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: #d9e2ec;
  color: #486581;
  font-size: 13px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.step-num.completed { background: #6ee7b7; color: #065f46; }
.step-num.skipped { background: #e4ecf5; color: #9fb3c8; }

.step-card-body { flex: 1; min-width: 0; }
.step-card-title { font-size: 15px; font-weight: 600; color: #334e68; display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.opt-badge { font-size: 11px; background: #e4ecf5; color: #627d98; border-radius: 4px; padding: 1px 5px; }
.step-card-desc { font-size: 13px; color: #627d98; margin: 0 0 10px; line-height: 1.6; }
.step-done-hint { font-size: 13px; color: #059669; }
.step-skip-hint { font-size: 13px; color: #9fb3c8; }

.step-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.go-btn {
  font-size: 13px; padding: 5px 12px;
  background: #fff; color: #334e68;
  border: 1px solid #334e68; border-radius: 6px;
  cursor: pointer; text-decoration: none;
}
.go-btn:hover { background: #f0f4f8; }
.complete-btn {
  font-size: 13px; padding: 5px 12px;
  background: #334e68; color: #fff;
  border: 0; border-radius: 6px; cursor: pointer;
}
.complete-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.complete-btn:hover:not(:disabled) { background: #243b53; }
.locked-hint { font-size: 12px; color: #9fb3c8; }

.done-summary {
  margin-top: 16px;
  padding: 12px 16px;
  background: #d1fae5;
  border-radius: 8px;
  color: #065f46;
  font-size: 14px;
}
</style>
