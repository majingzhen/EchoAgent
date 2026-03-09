<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import axios from "axios";

const router = useRouter();
const route = useRoute();

const showNav = computed(() => route.path !== "/setup");

onMounted(async () => {
  if (route.path === "/setup") return;
  try {
    const res = await axios.get("/api/config/status");
    if (!res.data?.llm_configured) router.replace("/setup");
  } catch {
    // 后端未启动时不强制跳转，避免开发环境误拦截
  }
});
</script>

<template>
  <div class="layout">
    <header v-if="showNav" class="header">
      <h1 class="logo">EchoAgent</h1>
      <nav class="nav">
        <RouterLink to="/">仪表盘</RouterLink>
        <RouterLink to="/audience">受众</RouterLink>
        <RouterLink to="/content">内容</RouterLink>
        <RouterLink to="/analysis">分析</RouterLink>
        <RouterLink to="/workflow">工作流</RouterLink>
      </nav>
    </header>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  background: linear-gradient(145deg, #f7faf8 0%, #edf3ff 100%);
  color: #102a43;
  font-family: "Segoe UI", "PingFang SC", sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  border-bottom: 1px solid #d9e2ec;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(6px);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #102a43;
  letter-spacing: -0.3px;
  white-space: nowrap;
}

.nav {
  display: flex;
  gap: 2px;
}

.nav a {
  text-decoration: none;
  color: #486581;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 14px;
  transition: background 0.1s, color 0.1s;
}

.nav a:hover {
  background: #f0f4f8;
  color: #102a43;
}

.nav a.router-link-active {
  background: #102a43;
  color: #fff;
}

.main {
  max-width: 1140px;
  margin: 0 auto;
  padding: 24px 20px;
}
</style>
