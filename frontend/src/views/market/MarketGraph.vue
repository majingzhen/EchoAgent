<script setup lang="ts">
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from "d3-force";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { buildMarketGraph, getMarketReport, uploadMarketGraph } from "@/api/market";

type MarketEntity = {
  entity_id: string;
  name: string;
  entity_type: string;
  score: number;
};

type MarketRelation = {
  source: string;
  target: string;
  relation_type: string;
  weight: number;
};

type MarketGraphData = {
  id: number;
  name: string;
  entities: MarketEntity[];
  relations: MarketRelation[];
};

type ForceNode = SimulationNodeDatum & MarketEntity;
type ForceLink = SimulationLinkDatum<ForceNode> & MarketRelation;

const form = ref({
  name: "竞品舆情图谱",
  source_text:
    "竞品A在价格战中获得声量，竞品B强调成分与口碑。用户讨论主要集中在价格、功效、售后与渠道。",
});

const uploadFile = ref<File | null>(null);
const graph = ref<MarketGraphData | null>(null);
const report = ref<Record<string, unknown> | null>(null);
const loading = ref(false);
const reportLoading = ref(false);
const error = ref("");
const showGraph = ref(false);

const width = 760;
const height = 420;

const simNodes = ref<ForceNode[]>([]);
const simLinks = ref<ForceLink[]>([]);
let simulation: Simulation<ForceNode, ForceLink> | null = null;

const nodeIndex = computed(() => {
  return new Map(simNodes.value.map((node) => [node.entity_id, node]));
});

const resolveNode = (value: string | number | ForceNode | undefined): ForceNode | undefined => {
  if (!value) return undefined;
  if (typeof value === "object") return value;
  return nodeIndex.value.get(String(value));
};

const linkKey = (link: ForceLink): string => {
  const sourceId = resolveNode(link.source)?.entity_id ?? String(link.source);
  const targetId = resolveNode(link.target)?.entity_id ?? String(link.target);
  return `${sourceId}-${targetId}-${link.relation_type}`;
};

const stopSimulation = () => {
  simulation?.stop();
  simulation = null;
};

const runForceLayout = (data: MarketGraphData) => {
  stopSimulation();
  const nodes: ForceNode[] = data.entities.map((entity) => ({
    ...entity,
    x: width / 2 + (Math.random() - 0.5) * 80,
    y: height / 2 + (Math.random() - 0.5) * 80,
  }));
  const validIds = new Set(nodes.map((node) => node.entity_id));
  const links: ForceLink[] = data.relations
    .filter((relation) => validIds.has(relation.source) && validIds.has(relation.target))
    .map((relation) => ({ ...relation, source: relation.source, target: relation.target }));

  simulation = forceSimulation(nodes)
    .force("link", forceLink<ForceNode, ForceLink>(links)
      .id((node) => node.entity_id)
      .distance((link) => Math.max(60, 150 - (link.weight ?? 0.2) * 70))
      .strength((link) => Math.max(0.12, link.weight ?? 0.2)))
    .force("charge", forceManyBody<ForceNode>().strength(-220))
    .force("collide", forceCollide<ForceNode>().radius((node) => 18 + Math.round(node.score * 6)))
    .force("center", forceCenter(width / 2, height / 2))
    .alpha(1)
    .alphaDecay(0.06)
    .on("tick", () => {
      simNodes.value = [...nodes];
      simLinks.value = [...links];
    });

  simNodes.value = [...nodes];
  simLinks.value = [...links];
};

watch(graph, (value) => {
  if (!value) {
    stopSimulation();
    simNodes.value = [];
    simLinks.value = [];
    return;
  }
  runForceLayout(value);
}, { immediate: true });

onBeforeUnmount(() => stopSimulation());

const fetchReport = async (graphId: number) => {
  reportLoading.value = true;
  try {
    const resp = await getMarketReport(graphId);
    report.value = resp.data as Record<string, unknown>;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "生成报告失败";
  } finally {
    reportLoading.value = false;
  }
};

const buildByText = async () => {
  loading.value = true;
  error.value = "";
  report.value = null;
  showGraph.value = false;
  try {
    const resp = await buildMarketGraph(form.value);
    graph.value = resp.data as MarketGraphData;
    await fetchReport(graph.value.id);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "构建图谱失败";
  } finally {
    loading.value = false;
  }
};

const buildByUpload = async () => {
  if (!uploadFile.value) return;
  loading.value = true;
  error.value = "";
  report.value = null;
  showGraph.value = false;
  try {
    const fd = new FormData();
    fd.append("name", form.value.name);
    fd.append("file", uploadFile.value);
    const resp = await uploadMarketGraph(fd);
    graph.value = resp.data as MarketGraphData;
    await fetchReport(graph.value.id);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "上传构建失败";
  } finally {
    loading.value = false;
  }
};

const strList = (val: unknown): string[] => (Array.isArray(val) ? val.map(String) : []);
</script>

<template>
  <section class="card">
    <h2>市场智脑</h2>
    <p class="tip">
      上传竞品文章、用户评论或舆情汇总（.txt / .md / .pdf），或直接粘贴文本，AI 提取关键实体构建知识图谱，并生成结构化竞品分析报告。图谱 ID 可注入内容工坊让文案更有针对性。
    </p>
    <div class="grid">
      <label>图谱名称<input v-model="form.name" /></label>
      <label>
        文本输入
        <textarea v-model="form.source_text" rows="4" placeholder="粘贴竞品评论、文章摘要等..." />
      </label>
      <label>
        文档上传（.txt / .md / .pdf）
        <input type="file" accept=".txt,.md,.pdf" @change="uploadFile = (($event.target as HTMLInputElement).files?.[0] ?? null)" />
      </label>
    </div>
    <div class="actions">
      <button :disabled="loading" @click="buildByText">文本构建图谱</button>
      <button :disabled="loading || !uploadFile" @click="buildByUpload">上传构建图谱</button>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <!-- 报告生成中 -->
  <section v-if="(loading || reportLoading) && !report" class="card progress-card">
    <span class="spinner" />
    <span>{{ loading ? '图谱构建中...' : 'AI 生成竞品分析报告...' }}</span>
  </section>

  <!-- 竞品分析报告（主体） -->
  <section v-if="report" class="card report-card">
    <div class="report-header">
      <h3>竞品分析报告</h3>
      <span v-if="graph" class="graph-id-badge">图谱 ID: {{ graph.id }}</span>
    </div>

    <div class="summary-block">
      <p>{{ report.summary }}</p>
    </div>

    <div class="report-grid">
      <div v-if="strList(report.competitor_landscape).length" class="report-section">
        <h4>竞品格局</h4>
        <div class="tag-list">
          <span v-for="c in strList(report.competitor_landscape)" :key="c" class="tag brand-tag">{{ c }}</span>
        </div>
      </div>

      <div v-if="strList(report.key_insights).length" class="report-section">
        <h4>核心洞察</h4>
        <ul>
          <li v-for="i in strList(report.key_insights)" :key="i">{{ i }}</li>
        </ul>
      </div>

      <div v-if="strList(report.opportunities).length" class="report-section">
        <h4>市场机会</h4>
        <ul class="opp-list">
          <li v-for="o in strList(report.opportunities)" :key="o">{{ o }}</li>
        </ul>
      </div>

      <div v-if="strList(report.risks).length" class="report-section">
        <h4>风险提示</h4>
        <ul class="risk-list">
          <li v-for="r in strList(report.risks)" :key="r">{{ r }}</li>
        </ul>
      </div>
    </div>

    <div v-if="strList(report.recommended_actions).length" class="actions-section">
      <h4>推荐行动</h4>
      <ol>
        <li v-for="a in strList(report.recommended_actions)" :key="a">{{ a }}</li>
      </ol>
    </div>
  </section>

  <!-- 图谱可视化（折叠） -->
  <section v-if="graph" class="card">
    <button class="toggle-btn" @click="showGraph = !showGraph">
      {{ showGraph ? '收起知识图谱' : '展开知识图谱' }}
      <span class="graph-meta">{{ graph.entities.length }} 实体 · {{ graph.relations.length }} 关系</span>
    </button>

    <template v-if="showGraph">
      <p class="tip" style="margin-top:12px">
        <span class="dot brand" />品牌&nbsp;&nbsp;<span class="dot attr" />属性/功效&nbsp;&nbsp;<span class="dot topic" />话题/情绪。
        节点大小代表热度，连线粗细代表关联强度。
      </p>
      <svg :width="width" :height="height" viewBox="0 0 760 420" class="graph">
        <line
          v-for="item in simLinks"
          :key="linkKey(item)"
          :x1="resolveNode(item.source)?.x ?? width / 2"
          :y1="resolveNode(item.source)?.y ?? height / 2"
          :x2="resolveNode(item.target)?.x ?? width / 2"
          :y2="resolveNode(item.target)?.y ?? height / 2"
          :stroke-width="Math.max(1, item.weight * 3)"
          stroke="#8aa6c1"
          opacity="0.65"
        />
        <g v-for="node in simNodes" :key="node.entity_id">
          <circle
            :cx="node.x ?? width / 2"
            :cy="node.y ?? height / 2"
            :r="16 + Math.round(node.score * 6)"
            :fill="node.entity_type === 'brand' ? '#4062bb' : node.entity_type === 'attribute' ? '#4f9d69' : '#8f63b8'"
            opacity="0.88"
          />
          <text :x="node.x ?? width / 2" :y="(node.y ?? height / 2) + 4" text-anchor="middle" class="label">
            {{ node.name }}
          </text>
        </g>
      </svg>
    </template>
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
.grid { display: grid; gap: 10px; }
label { display: grid; gap: 6px; font-size: 14px; }
input, textarea {
  border: 1px solid #bcccdc;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
}
textarea { resize: vertical; font-family: inherit; }
.actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
button {
  border: 0; border-radius: 8px; padding: 8px 14px;
  color: #fff; background: #334e68; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: 0.6; cursor: not-allowed; }
button:hover:not(:disabled) { background: #243b53; }
.error { color: #d64545; font-size: 14px; margin-top: 8px; }
.tip { color: #486581; font-size: 14px; margin: 0 0 14px; line-height: 1.7; }

.progress-card { display: flex; align-items: center; gap: 10px; color: #486581; font-size: 14px; padding: 12px 20px; }
.spinner {
  width: 16px; height: 16px;
  border: 2px solid #d9e2ec; border-top-color: #334e68;
  border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

.report-card { background: #fafcff; }
.report-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.report-header h3 { margin: 0; }
.graph-id-badge {
  font-size: 12px; background: #334e68; color: #fff;
  border-radius: 4px; padding: 2px 8px;
}
.summary-block {
  background: #edf5ff; border-left: 3px solid #334e68;
  border-radius: 0 8px 8px 0; padding: 10px 14px; margin-bottom: 16px;
}
.summary-block p { margin: 0; font-size: 14px; color: #334e68; line-height: 1.7; }

.report-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.report-section { background: #f8fbff; border: 1px solid #e4ecf5; border-radius: 8px; padding: 12px 14px; }
.report-section h4 { margin: 0 0 8px; font-size: 13px; color: #627d98; text-transform: uppercase; letter-spacing: 0.5px; }
.report-section ul { margin: 0; padding-left: 16px; }
.report-section li { font-size: 14px; color: #334e68; line-height: 1.7; }
.opp-list li::marker { color: #4f9d69; }
.risk-list li::marker { color: #d64545; }

.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { font-size: 13px; border-radius: 4px; padding: 3px 8px; }
.brand-tag { background: #e0e8ff; color: #4062bb; }

.actions-section { background: #f8fbff; border: 1px solid #e4ecf5; border-radius: 8px; padding: 12px 14px; }
.actions-section h4 { margin: 0 0 8px; font-size: 13px; color: #627d98; text-transform: uppercase; letter-spacing: 0.5px; }
.actions-section ol { margin: 0; padding-left: 18px; }
.actions-section li { font-size: 14px; color: #334e68; line-height: 1.8; }

.toggle-btn {
  background: transparent; color: #334e68; border: 1px solid #d9e2ec;
  display: flex; align-items: center; gap: 8px; width: 100%;
}
.toggle-btn:hover:not(:disabled) { background: #f0f4f8; }
.graph-meta { font-size: 12px; color: #829ab1; font-weight: normal; }

.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.dot.brand { background: #4062bb; }
.dot.attr  { background: #4f9d69; }
.dot.topic { background: #8f63b8; }
.graph {
  width: 100%; max-width: 760px;
  border: 1px solid #e4ecf5; border-radius: 8px;
  background: linear-gradient(180deg, #f6f9ff 0%, #f2fff5 100%);
}
.label { fill: #fff; font-size: 11px; font-weight: 600; }
</style>
