<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { generatePersonas } from "@/api/persona";
import { personaDescTemplates } from "@/config/templates";

const router = useRouter();
const loading = ref(false);
const error = ref("");
const personas = ref<any[]>([]);
const groupId = ref<number | null>(null);
const completed = ref(0);
const total = ref(0);
const done = ref(false);
const form = ref({
  group_name: "新品目标人群",
  description: "25-35岁一线城市白领，关注性价比与品质",
  count: 6,
});

let wsInstance: WebSocket | null = null;

const setupWS = (gid: number) => {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const base = (import.meta.env.VITE_WS_BASE_URL as string) ?? `${proto}://${location.hostname}:8000`;
  const ws = new WebSocket(`${base}/api/ws/persona/${gid}`);
  ws.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    if (data.type === "persona_ready") {
      personas.value.push(data.persona);
      completed.value = data.completed;
    } else if (data.type === "done") {
      done.value = true;
      loading.value = false;
      ws.close();
    } else if (data.type === "error") {
      error.value = data.message ?? "生成失败";
      loading.value = false;
      ws.close();
    }
  };
  ws.onerror = () => {
    error.value = "WebSocket 连接失败";
    loading.value = false;
  };
  return ws;
};

const submit = async () => {
  loading.value = true;
  error.value = "";
  personas.value = [];
  done.value = false;
  completed.value = 0;
  total.value = form.value.count;
  wsInstance?.close();

  try {
    const resp = await generatePersonas(form.value);
    groupId.value = resp.data.group_id;
    wsInstance = setupWS(resp.data.group_id);
  } catch (e: any) {
    error.value = e.message ?? "生成失败";
    loading.value = false;
  }
};

const goFocusGroup = () => router.push({ path: "/focus-groups/session", query: { groupId: groupId.value } });
const goWorkshop = () => router.push({ path: "/workshop/session", query: { groupId: groupId.value } });
</script>

<template>
  <section class="card">
    <h2>画像工厂</h2>
    <p class="tip">描述你的目标消费群体，AI 会生成一组差异化虚拟用户，用于后续焦点小组提问和内容工坊评测。</p>
    <div class="form-grid">
      <label>画像组名<input v-model="form.group_name" /></label>
      <label>
        人群描述
        <textarea v-model="form.description" rows="3" placeholder="如：25-35岁一线城市白领，关注性价比与品质" />
        <select style="margin-top:4px" @change="(e) => { const v = (e.target as HTMLSelectElement).value; if (v) form.description = v; (e.target as HTMLSelectElement).value = ''; }">
          <option value="">-- 选择人群模板 --</option>
          <option v-for="t in personaDescTemplates" :key="t.label" :value="t.value">{{ t.label }}</option>
        </select>
      </label>
      <label>生成数量<input v-model.number="form.count" type="number" min="3" max="20" /></label>
      <button :disabled="loading" @click="submit">{{ loading ? "AI 生成中..." : "生成画像" }}</button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <section v-if="total > 0" class="card">
    <div class="progress-header">
      <h3>{{ done ? `生成完成 — 画像组 #${groupId}` : `正在生成画像...` }}</h3>
      <span class="progress-label">{{ completed }} / {{ total }}</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: `${(completed / total) * 100}%` }" />
    </div>

    <div v-if="personas.length" class="persona-list">
      <div v-for="p in personas" :key="p.id" class="persona-card">
        <div class="persona-header">
          <span class="name">{{ p.name }}</span>
          <span class="tag">{{ p.gender }} · {{ p.age }}岁 · {{ p.city }}</span>
        </div>
        <div class="persona-meta">{{ p.occupation }} · 月收入 {{ p.monthly_income?.toLocaleString() }} 元</div>
        <div class="persona-tags">
          <span class="badge">价格敏感 {{ ((p.consumer_profile?.price_sensitivity ?? 0) * 100).toFixed(0) }}%</span>
          <span class="badge">品牌忠诚 {{ ((p.consumer_profile?.brand_loyalty ?? 0) * 100).toFixed(0) }}%</span>
          <span v-for="f in (p.consumer_profile?.decision_factors ?? []).slice(0, 2)" :key="f" class="badge light">{{ f }}</span>
        </div>
        <div class="persona-platforms">常用平台：{{ (p.media_behavior?.platforms ?? []).join(' · ') }}</div>
      </div>
    </div>

    <div v-if="done" class="next-actions">
      <p>下一步：用这组画像做什么？</p>
      <div class="btn-group">
        <button @click="goFocusGroup">前往焦点小组 — 向他们提问 →</button>
        <button class="secondary" @click="goWorkshop">前往内容工坊 — 生成文案并评测 →</button>
      </div>
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
.tip {
  color: #486581;
  font-size: 14px;
  margin: 0 0 16px;
}
.form-grid {
  display: grid;
  gap: 12px;
}
label {
  display: grid;
  gap: 6px;
  font-size: 14px;
}
input,
textarea {
  border: 1px solid #bcccdc;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
}
button {
  width: fit-content;
  border: 0;
  border-radius: 8px;
  padding: 9px 16px;
  color: #fff;
  background: #334e68;
  cursor: pointer;
  font-size: 14px;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
button:hover:not(:disabled) {
  background: #243b53;
}
.error {
  color: #d64545;
  font-size: 14px;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.progress-header h3 { margin: 0; }
.progress-label {
  font-size: 14px;
  color: #627d98;
}
.progress-bar {
  height: 6px;
  background: #d9e2ec;
  border-radius: 4px;
  margin-bottom: 20px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #334e68;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.persona-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.persona-card {
  border: 1px solid #d9e2ec;
  border-radius: 10px;
  padding: 14px;
  background: #f8fbff;
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.persona-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}
.name {
  font-weight: 600;
  font-size: 15px;
}
.tag {
  color: #627d98;
  font-size: 13px;
}
.persona-meta {
  color: #486581;
  font-size: 13px;
  margin-bottom: 8px;
}
.persona-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.badge {
  background: #d9e2ec;
  border-radius: 4px;
  padding: 2px 7px;
  font-size: 12px;
  color: #334e68;
}
.badge.light {
  background: #e8f4fd;
  color: #1a6fa8;
}
.persona-platforms {
  font-size: 12px;
  color: #829ab1;
}

.next-actions {
  border-top: 1px solid #d9e2ec;
  padding-top: 16px;
}
.next-actions p {
  margin: 0 0 10px;
  font-size: 14px;
  color: #486581;
}
.btn-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.secondary {
  background: #fff;
  color: #334e68;
  border: 1px solid #334e68;
}
.secondary:hover {
  background: #f0f4f8;
}
</style>
