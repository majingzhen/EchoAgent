<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getPersonaGroups, getPersonaGroupDetail } from "@/api/persona";
import { getFocusGroupSessions } from "@/api/focus_group";
import { downloadReport } from "@/api/export";

const router = useRouter();
const activeTab = ref<"library" | "focus">("library");

// ── 画像库 ──────────────────────────────
const groups = ref<any[]>([]);
const expandedId = ref<number | null>(null);
const groupPersonas = ref<Record<number, any[]>>({});
const groupsLoading = ref(false);

const statusClass = (s: string) => s === "completed" ? "tag-ok" : s === "failed" ? "tag-err" : "tag-run";
const fmtTime = (t: string) => t ? t.replace("T", " ").slice(0, 16) : "";

onMounted(async () => {
  groupsLoading.value = true;
  try {
    const r = await getPersonaGroups();
    groups.value = (r as any).data ?? [];
  } catch { /**/ }
  groupsLoading.value = false;
  loadFocusSessions();
});

const toggleGroup = async (id: number) => {
  if (expandedId.value === id) { expandedId.value = null; return; }
  expandedId.value = id;
  if (!groupPersonas.value[id]) {
    try {
      const r = await getPersonaGroupDetail(id);
      groupPersonas.value[id] = (r as any).data?.personas ?? [];
    } catch { groupPersonas.value[id] = []; }
  }
};

const goNewGroup = () => router.push("/personas/create");
const goFocusGroup = (groupId: number) => router.push(`/focus-groups/session?groupId=${groupId}`);

// ── 焦点小组 ────────────────────────────
const focusSessions = ref<any[]>([]);
const focusLoading = ref(false);

const loadFocusSessions = async () => {
  focusLoading.value = true;
  try {
    const r = await getFocusGroupSessions();
    focusSessions.value = (r as any).data ?? [];
  } catch { /**/ }
  focusLoading.value = false;
};

const focusStatusMap: Record<string, string> = { active: "进行中", completed: "已完成", failed: "失败" };
const goSession = (id: number) => router.push(`/focus-groups/session?session_id=${id}`);
const goNewSession = () => router.push("/focus-groups/session");

const PERSONA_TYPE_COLORS = ["#e0f0ff", "#fef3cd", "#d4edda", "#f8d7da", "#e8e3f8"];
const getTypeColor = (i: number) => PERSONA_TYPE_COLORS[i % PERSONA_TYPE_COLORS.length];
</script>

<template>
  <div class="page">
    <!-- Tab 导航 -->
    <div class="tab-bar">
      <button :class="['tab', activeTab === 'library' && 'active']" @click="activeTab = 'library'">画像库</button>
      <button :class="['tab', activeTab === 'focus' && 'active']" @click="activeTab = 'focus'">焦点小组</button>
    </div>

    <!-- 画像库 -->
    <template v-if="activeTab === 'library'">
      <div class="section-header">
        <div>
          <h2>画像库</h2>
          <p class="tip">管理所有虚拟消费者画像组，可直接发起焦点小组讨论。</p>
        </div>
        <button @click="goNewGroup">生成新画像组</button>
      </div>

      <!-- 画像组列表 -->
      <p v-if="groupsLoading" class="tip">加载中...</p>
      <p v-else-if="!groups.length" class="tip empty">暂无画像组，点击「生成新画像组」开始。</p>

      <div v-else class="group-list">
        <div
          v-for="g in groups" :key="g.id"
          class="group-card card"
        >
          <div class="group-header" @click="toggleGroup(g.id)">
            <div class="group-meta">
              <span class="group-name">{{ g.name }}</span>
<span class="persona-count">{{ g.persona_count }} 人</span>
            </div>
            <p v-if="g.description" class="group-desc">{{ g.description }}</p>
            <div class="group-actions" @click.stop>
              <button class="sm-btn" @click="toggleGroup(g.id)">
                {{ expandedId === g.id ? '收起' : '查看画像' }}
              </button>
              <button class="sm-btn primary-sm" @click="goFocusGroup(g.id)">发起焦点讨论</button>
            </div>
          </div>

          <!-- 展开：画像列表 -->
          <div v-if="expandedId === g.id" class="persona-grid">
            <p v-if="!groupPersonas[g.id]" class="tip">加载中...</p>
            <div
              v-else v-for="(p, i) in groupPersonas[g.id]" :key="p.id"
              class="persona-tile"
              :style="{ background: getTypeColor(i) }"
            >
              <div class="pt-name">{{ p.name }}</div>
              <div class="pt-meta">{{ p.age }}岁 · {{ p.city }}</div>
              <div class="pt-occ">{{ p.occupation }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 焦点小组 -->
    <template v-else>
      <div class="section-header">
        <div>
          <h2>焦点小组</h2>
          <p class="tip">向虚拟消费者提问，AI 实时汇总共识与分歧。</p>
        </div>
        <button @click="goNewSession">新建会话</button>
      </div>

      <p v-if="focusLoading" class="tip">加载中...</p>
      <p v-else-if="!focusSessions.length" class="tip empty">暂无历史会话。</p>

      <div v-else class="session-grid">
        <div v-for="s in focusSessions" :key="s.id" class="session-card card">
          <div class="card-top">
            <span class="card-id">#{{ s.id }}</span>
            <span :class="['tag', statusClass(s.status)]">{{ focusStatusMap[s.status] ?? s.status }}</span>
          </div>
          <div class="card-topic">{{ s.topic }}</div>
          <div class="card-meta">
            <span>画像组 #{{ s.persona_group_id }}</span>
            <span>{{ fmtTime(s.created_at) }}</span>
          </div>
          <div class="card-btns">
            <button class="sm-btn" @click="goSession(s.id)">查看详情</button>
            <template v-if="s.summary">
              <button class="sm-btn export-btn" @click="downloadReport('focus-group', s.id, 'pdf')">PDF</button>
              <button class="sm-btn export-btn" @click="downloadReport('focus-group', s.id, 'pptx')">PPT</button>
            </template>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; }

.tab-bar { display: flex; gap: 4px; border-bottom: 1px solid #d9e2ec; padding-bottom: 0; }
.tab {
  border: none; background: none; padding: 10px 18px; font-size: 15px;
  color: #627d98; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px;
  border-radius: 0;
}
.tab.active { color: #102a43; font-weight: 600; border-bottom-color: #334e68; }

.card { border: 1px solid #d9e2ec; border-radius: 12px; background: #fff; padding: 18px 20px; }
.section-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.section-header h2 { margin: 0 0 4px; }
.header-actions { display: flex; gap: 8px; flex-shrink: 0; margin-top: 4px; }
.tip { color: #486581; font-size: 14px; margin: 0; }
.tip.empty { padding: 24px 0; text-align: center; }

/* Group cards */
.group-list { display: flex; flex-direction: column; gap: 10px; }
.group-card { transition: border-color 0.15s; }
.group-header { cursor: pointer; }
.group-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.group-name { font-size: 15px; font-weight: 600; color: #102a43; }
.persona-count { background: #d9e2ec; color: #486581; font-size: 12px; padding: 2px 6px; border-radius: 8px; }
.group-desc { font-size: 13px; color: #627d98; margin: 0 0 10px; line-height: 1.5; }
.group-actions { display: flex; gap: 8px; }

/* Persona tiles */
.persona-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #e8ecf1;
}
.persona-tile {
  border-radius: 8px;
  padding: 10px 12px;
}
.pt-name { font-size: 13px; font-weight: 600; color: #102a43; margin-bottom: 3px; }
.pt-meta { font-size: 11px; color: #627d98; margin-bottom: 2px; }
.pt-occ { font-size: 11px; color: #486581; }

/* Session grid */
.session-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.session-card { display: flex; flex-direction: column; gap: 8px; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.card-id { font-weight: 600; font-size: 13px; color: #829ab1; }
.card-topic { font-size: 14px; font-weight: 600; color: #102a43; line-height: 1.4; }
.card-meta { font-size: 12px; color: #829ab1; display: flex; justify-content: space-between; }
.card-btns { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }

/* Tags */
.tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.tag-ok { background: #d4edda; color: #155724; }
.tag-err { background: #f8d7da; color: #721c24; }
.tag-run { background: #fff3cd; color: #856404; }

/* Buttons */
button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.secondary { background: #fff; color: #334e68; border: 1px solid #334e68; }
.secondary:hover:not(:disabled) { background: #f0f4f8; }
.sm-btn {
  border: 1px solid #d9e2ec; background: #fff; color: #334e68;
  border-radius: 6px; padding: 4px 10px; font-size: 12px; cursor: pointer;
}
.sm-btn:hover { background: #f0f4f8; }
.primary-sm { background: #334e68; color: #fff; border-color: #334e68; }
.primary-sm:hover { background: #243b53; }
.export-btn { color: #486581; }
</style>
