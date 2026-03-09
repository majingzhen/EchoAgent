<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import * as api from "@/api/knowledge";

interface Project { id: number; name: string; description: string | null; created_at: string }
interface Doc { id: number; filename: string; file_type: string; char_count: number; chunk_count: number; status: string; created_at: string }
interface SearchResult { chunk_id: number; doc_id: number; filename: string; content: string; score: number }

// ── state ──────────────────────────────────────────────────────────────────────
const projects = ref<Project[]>([]);
const selectedProject = ref<Project | null>(null);
const docs = ref<Doc[]>([]);
const searchResults = ref<SearchResult[]>([]);
const searchQuery = ref("");

const loading = ref(false);
const docsLoading = ref(false);
const uploading = ref(false);
const searching = ref(false);

const showCreate = ref(false);
const newName = ref("");
const newDesc = ref("");
const fileInput = ref<HTMLInputElement | null>(null);

const statusLabel: Record<string, string> = {
  pending: "处理中",
  ready: "就绪",
  error: "失败",
};
const statusColor: Record<string, string> = {
  pending: "#d4a017",
  ready: "#1d9b74",
  error: "#e74c3c",
};

// ── computed ────────────────────────────────────────────────────────────────────
const readyDocs = computed(() => docs.value.filter(d => d.status === "ready").length);
const totalChunks = computed(() => docs.value.reduce((s, d) => s + d.chunk_count, 0));

// ── lifecycle ───────────────────────────────────────────────────────────────────
onMounted(fetchProjects);

async function fetchProjects() {
  loading.value = true;
  try {
    const res: any = await api.listProjects();
    projects.value = res.data ?? [];
  } finally {
    loading.value = false;
  }
}

async function selectProject(p: Project) {
  selectedProject.value = p;
  docs.value = [];
  searchResults.value = [];
  searchQuery.value = "";
  docsLoading.value = true;
  try {
    const res: any = await api.listDocs(p.id);
    docs.value = res.data ?? [];
  } finally {
    docsLoading.value = false;
  }
}

async function createProject() {
  if (!newName.value.trim()) return;
  const res: any = await api.createProject({ name: newName.value.trim(), description: newDesc.value.trim() || undefined });
  projects.value.unshift(res.data);
  newName.value = "";
  newDesc.value = "";
  showCreate.value = false;
}

async function deleteProject(p: Project) {
  if (!confirm(`确认删除知识库「${p.name}」及其所有文档？`)) return;
  await api.deleteProject(p.id);
  projects.value = projects.value.filter(x => x.id !== p.id);
  if (selectedProject.value?.id === p.id) {
    selectedProject.value = null;
    docs.value = [];
  }
}

function triggerUpload() {
  fileInput.value?.click();
}

async function handleUpload(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file || !selectedProject.value) return;
  input.value = "";
  uploading.value = true;
  try {
    const res: any = await api.uploadDoc(selectedProject.value.id, file);
    docs.value.unshift(res.data);
    // 轮询等待 ready（最多 30s）
    pollDocStatus(res.data.id);
  } finally {
    uploading.value = false;
  }
}

async function pollDocStatus(docId: number) {
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 1000));
    if (!selectedProject.value) return;
    const res: any = await api.listDocs(selectedProject.value.id);
    const updated = (res.data ?? []) as Doc[];
    const doc = updated.find(d => d.id === docId);
    if (doc && doc.status !== "pending") {
      docs.value = updated;
      return;
    }
    docs.value = updated;
  }
}

async function deleteDoc(doc: Doc) {
  if (!selectedProject.value) return;
  if (!confirm(`确认删除文档「${doc.filename}」？`)) return;
  await api.deleteDoc(selectedProject.value.id, doc.id);
  docs.value = docs.value.filter(d => d.id !== doc.id);
}

async function doSearch() {
  if (!searchQuery.value.trim() || !selectedProject.value) return;
  searching.value = true;
  try {
    const res: any = await api.searchChunks(selectedProject.value.id, searchQuery.value.trim());
    searchResults.value = res.data ?? [];
  } finally {
    searching.value = false;
  }
}
</script>

<template>
  <div class="kb-page">
    <div class="page-head">
      <h2 class="page-title">知识库</h2>
      <p class="page-desc">上传产品手册、品牌指南或竞品报告，让 AI 回答更精准</p>
    </div>

    <div class="kb-layout">
      <!-- 左侧：项目列表 -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <span>我的知识库</span>
          <button class="btn-icon" @click="showCreate = !showCreate" title="新建">+</button>
        </div>

        <!-- 新建表单 -->
        <div v-if="showCreate" class="create-form">
          <input v-model="newName" placeholder="知识库名称" class="input" maxlength="100" />
          <input v-model="newDesc" placeholder="描述（可选）" class="input" maxlength="200" />
          <div class="row-btns">
            <button class="btn-primary" @click="createProject">创建</button>
            <button class="btn-ghost" @click="showCreate = false">取消</button>
          </div>
        </div>

        <div v-if="loading" class="hint">加载中…</div>
        <div v-else-if="!projects.length" class="hint">暂无知识库，点击 + 创建</div>

        <div
          v-for="p in projects"
          :key="p.id"
          class="proj-item"
          :class="{ active: selectedProject?.id === p.id }"
          @click="selectProject(p)"
        >
          <div class="proj-name">{{ p.name }}</div>
          <div class="proj-desc">{{ p.description || "—" }}</div>
          <button class="del-btn" @click.stop="deleteProject(p)" title="删除">×</button>
        </div>
      </aside>

      <!-- 右侧：文档管理 + 搜索 -->
      <main class="content" v-if="selectedProject">
        <div class="content-head">
          <h3>{{ selectedProject.name }}</h3>
          <div class="stats">
            <span class="stat">{{ readyDocs }} 份文档</span>
            <span class="stat">{{ totalChunks }} 个片段</span>
          </div>
          <input ref="fileInput" type="file" accept=".pdf,.txt,.md,.docx" style="display:none" @change="handleUpload" />
          <button class="btn-primary" :disabled="uploading" @click="triggerUpload">
            {{ uploading ? "上传中…" : "+ 上传文档" }}
          </button>
        </div>

        <p class="supported-types">支持：PDF · TXT · MD · DOCX（单文件最大 2 万字符）</p>

        <!-- 文档列表 -->
        <div v-if="docsLoading" class="hint">加载文档…</div>
        <div v-else-if="!docs.length" class="empty-docs">
          <p>还没有文档，上传第一个文件开始构建知识库吧</p>
        </div>

        <table v-else class="doc-table">
          <thead>
            <tr>
              <th>文件名</th>
              <th>类型</th>
              <th>字符数</th>
              <th>片段数</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in docs" :key="doc.id">
              <td class="doc-name">{{ doc.filename }}</td>
              <td><span class="tag">{{ doc.file_type }}</span></td>
              <td>{{ doc.char_count.toLocaleString() }}</td>
              <td>{{ doc.chunk_count }}</td>
              <td>
                <span class="status-dot" :style="{ color: statusColor[doc.status] ?? '#999' }">
                  {{ statusLabel[doc.status] ?? doc.status }}
                </span>
              </td>
              <td>
                <button class="del-btn" @click="deleteDoc(doc)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 语义搜索 -->
        <div class="search-section">
          <h4>知识库检索</h4>
          <div class="search-row">
            <input
              v-model="searchQuery"
              placeholder="输入关键词或问题，检索相关片段…"
              class="input search-input"
              @keyup.enter="doSearch"
            />
            <button class="btn-primary" :disabled="searching || !searchQuery.trim()" @click="doSearch">
              {{ searching ? "检索中…" : "检索" }}
            </button>
          </div>

          <div v-if="searchResults.length" class="search-results">
            <div v-for="r in searchResults" :key="r.chunk_id" class="result-card">
              <div class="result-meta">
                <span class="result-file">{{ r.filename }}</span>
                <span class="result-score">相关度 {{ (r.score * 100).toFixed(1) }}%</span>
              </div>
              <p class="result-content">{{ r.content }}</p>
            </div>
          </div>
          <div v-else-if="!searching && searchQuery" class="hint">未找到相关片段</div>
        </div>
      </main>

      <!-- 右侧未选择时 -->
      <main class="content placeholder" v-else>
        <p>← 从左侧选择一个知识库，或创建新知识库</p>
      </main>
    </div>
  </div>
</template>

<style scoped>
.kb-page { padding: 0; }

.page-head { margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; margin: 0 0 4px; }
.page-desc { font-size: 14px; color: #627d98; margin: 0; }

.kb-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 20px;
  min-height: 500px;
}

/* ── sidebar ── */
.sidebar {
  background: #fff;
  border: 1px solid #d9e2ec;
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
  max-height: 70vh;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #486581;
  margin-bottom: 12px;
}
.btn-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid #d9e2ec;
  background: #f0f4f8;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.create-form { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.row-btns { display: flex; gap: 6px; }
.hint { font-size: 13px; color: #9fb3c8; text-align: center; padding: 12px 0; }

.proj-item {
  position: relative;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.1s;
  margin-bottom: 4px;
}
.proj-item:hover { background: #f0f4f8; }
.proj-item.active { background: #e8f4ff; border-left: 3px solid #2d9cdb; }
.proj-name { font-size: 14px; font-weight: 600; color: #102a43; }
.proj-desc { font-size: 12px; color: #9fb3c8; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #bcccdc;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 4px;
  border-radius: 4px;
}
.del-btn:hover { color: #e74c3c; background: #ffeaea; }

/* ── content ── */
.content {
  background: #fff;
  border: 1px solid #d9e2ec;
  border-radius: 12px;
  padding: 24px;
  overflow-y: auto;
  max-height: 70vh;
}
.content.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9fb3c8;
  font-size: 14px;
}
.content-head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}
.content-head h3 { margin: 0; font-size: 18px; font-weight: 700; flex: 1; }
.stats { display: flex; gap: 12px; }
.stat {
  font-size: 13px;
  color: #486581;
  background: #f0f4f8;
  padding: 3px 10px;
  border-radius: 20px;
}
.supported-types { font-size: 12px; color: #9fb3c8; margin: 0 0 20px; }
.empty-docs { text-align: center; padding: 40px 0; color: #9fb3c8; font-size: 14px; }

/* ── doc table ── */
.doc-table { width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 24px; }
.doc-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: 12px;
  color: #627d98;
  border-bottom: 1px solid #d9e2ec;
  font-weight: 500;
}
.doc-table td { padding: 10px 12px; border-bottom: 1px solid #f0f4f8; }
.doc-name { font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tag {
  font-size: 11px;
  background: #e8f4ff;
  color: #2d9cdb;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}
.status-dot { font-size: 13px; font-weight: 500; }

/* ── search ── */
.search-section { border-top: 1px solid #f0f4f8; padding-top: 20px; }
.search-section h4 { margin: 0 0 12px; font-size: 15px; font-weight: 600; }
.search-row { display: flex; gap: 8px; margin-bottom: 16px; }
.search-input { flex: 1; }
.search-results { display: flex; flex-direction: column; gap: 12px; }
.result-card {
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 12px 16px;
  background: #fafcff;
}
.result-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.result-file { font-size: 12px; color: #486581; font-weight: 500; }
.result-score { font-size: 12px; color: #1d9b74; font-weight: 600; }
.result-content { font-size: 13px; color: #334e68; line-height: 1.6; margin: 0; }

/* ── common ── */
.input {
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}
.input:focus { border-color: #2d9cdb; }
.btn-primary {
  padding: 8px 16px;
  background: #102a43;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  transition: background 0.1s;
}
.btn-primary:hover:not(:disabled) { background: #243b53; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost {
  padding: 8px 14px;
  background: #f0f4f8;
  color: #486581;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.btn-ghost:hover { background: #d9e2ec; }
</style>
