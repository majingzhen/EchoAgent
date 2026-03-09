<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getFocusGroupSessions } from "@/api/focus_group";
import { downloadReport } from "@/api/export";

const router = useRouter();
const sessions = ref<any[]>([]);
const loading = ref(false);
const selected = ref<Set<number>>(new Set());

const statusMap: Record<string, string> = { active: "进行中", completed: "已完成", failed: "失败" };
const statusClass = (s: string) => s === "completed" ? "tag-ok" : s === "failed" ? "tag-err" : "tag-run";

onMounted(async () => {
  loading.value = true;
  try {
    const resp = await getFocusGroupSessions();
    sessions.value = resp.data ?? [];
  } catch { /* ignore */ }
  loading.value = false;
});

const toggle = (id: number) => {
  if (selected.value.has(id)) selected.value.delete(id);
  else if (selected.value.size < 2) selected.value.add(id);
};

const goNew = () => router.push("/focus-groups/session");
const goDetail = (id: number) => router.push(`/focus-groups/session?session_id=${id}`);
const goCompare = () => {
  const ids = [...selected.value].join(",");
  router.push(`/focus-groups/compare?ids=${ids}`);
};
const fmtTime = (t: string) => t ? t.replace("T", " ").slice(0, 19) : "";
</script>

<template>
  <section class="card">
    <div class="header-row">
      <h2>焦点小组 - 历史会话</h2>
      <div class="header-actions">
        <button v-if="selected.size === 2" class="secondary" @click="goCompare">对比选中 ({{ selected.size }})</button>
        <button @click="goNew">新建会话</button>
      </div>
    </div>

    <p v-if="loading" class="tip">加载中...</p>
    <p v-else-if="!sessions.length" class="tip">暂无历史会话，点击上方按钮创建</p>

    <div v-else class="grid-list">
      <div
        v-for="s in sessions" :key="s.id"
        :class="['item-card', selected.has(s.id) ? 'selected' : '']"
        @click="toggle(s.id)"
      >
        <div class="item-top">
          <span class="item-id">#{{ s.id }}</span>
          <span :class="['tag', statusClass(s.status)]">{{ statusMap[s.status] ?? s.status }}</span>
        </div>
        <div class="item-body">
          <span class="label">话题</span> {{ s.topic }}
        </div>
        <div class="item-meta">
          <span>画像组 #{{ s.persona_group_id }}</span>
          <span>{{ fmtTime(s.created_at) }}</span>
        </div>
        <button class="detail-btn" @click.stop="goDetail(s.id)">查看详情</button>
        <div v-if="s.summary" class="export-row" @click.stop>
          <button class="export-btn" @click="downloadReport('focus-group', s.id, 'pdf')">PDF</button>
          <button class="export-btn" @click="downloadReport('focus-group', s.id, 'pptx')">PPT</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card { border: 1px solid #d9e2ec; border-radius: 12px; background: #fff; padding: 20px 24px; }
.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-row h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }
.tip { color: #486581; font-size: 14px; }
.grid-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.item-card {
  border: 1px solid #d9e2ec; border-radius: 10px; padding: 14px;
  background: #f8fbff; cursor: pointer; transition: border-color 0.15s;
}
.item-card:hover { border-color: #829ab1; }
.item-card.selected { border-color: #334e68; background: #edf5ff; }
.item-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.item-id { font-weight: 600; font-size: 14px; color: #334e68; }
.tag { font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.tag-ok { background: #d4edda; color: #155724; }
.tag-err { background: #f8d7da; color: #721c24; }
.tag-run { background: #fff3cd; color: #856404; }
.item-body { font-size: 14px; color: #334e68; margin-bottom: 8px; }
.item-body .label { color: #829ab1; font-size: 12px; margin-right: 4px; }
.item-meta { font-size: 12px; color: #829ab1; display: flex; justify-content: space-between; margin-bottom: 10px; }
.detail-btn {
  width: 100%; border: 1px solid #334e68; background: #fff; color: #334e68;
  border-radius: 6px; padding: 6px; font-size: 13px; cursor: pointer;
}
.detail-btn:hover { background: #f0f4f8; }
.export-row { display: flex; gap: 6px; margin-top: 6px; }
.export-btn {
  flex: 1; border: 1px solid #bcccdc; background: #f8fbff; color: #486581;
  border-radius: 6px; padding: 4px; font-size: 12px; cursor: pointer;
}
.export-btn:hover { background: #edf3ff; }
button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:hover { background: #243b53; }
.secondary { background: #fff; color: #334e68; border: 1px solid #334e68; }
.secondary:hover { background: #f0f4f8; }
</style>
