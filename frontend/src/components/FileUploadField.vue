<script setup lang="ts">
import { ref } from "vue";
import { extractTextFromFile } from "@/api/utils";

const props = defineProps<{
  modelValue: string;
  label?: string;
  placeholder?: string;
  accept?: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const filename = ref("");
const loading = ref(false);
const error = ref("");
const dragging = ref(false);

const DEFAULT_ACCEPT = ".pdf,.txt,.md,.doc,.docx";

const processFile = async (file: File) => {
  loading.value = true;
  error.value = "";
  filename.value = "";
  try {
    const resp = await extractTextFromFile(file);
    const text = (resp as any).text ?? "";
    filename.value = file.name;
    emit("update:modelValue", text);
  } catch (e: any) {
    error.value = e.message ?? "文件解析失败";
  } finally {
    loading.value = false;
  }
};

const onFileChange = (evt: Event) => {
  const file = (evt.target as HTMLInputElement).files?.[0];
  if (file) processFile(file);
};

const onDrop = (evt: DragEvent) => {
  dragging.value = false;
  const file = evt.dataTransfer?.files?.[0];
  if (file) processFile(file);
};

const clear = () => {
  filename.value = "";
  error.value = "";
  emit("update:modelValue", "");
  if (fileInput.value) fileInput.value.value = "";
};
</script>

<template>
  <div class="fuf-wrap">
    <span v-if="label" class="fuf-label">{{ label }}</span>

    <div
      v-if="!filename && !loading"
      class="fuf-drop"
      :class="{ dragging }"
      @click="fileInput?.click()"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
    >
      <span class="fuf-icon">📄</span>
      <span class="fuf-hint">{{ placeholder ?? '拖放或点击上传文件' }}</span>
      <span class="fuf-formats">支持 PDF / TXT / MD / DOC / DOCX</span>
    </div>

    <div v-else-if="loading" class="fuf-loading">
      <span class="fuf-spinner" />
      <span>正在解析文件...</span>
    </div>

    <div v-else class="fuf-done">
      <span class="fuf-file-icon">✓</span>
      <span class="fuf-filename">{{ filename }}</span>
      <button type="button" class="fuf-clear" @click="clear">重新上传</button>
    </div>

    <span v-if="error" class="fuf-error">{{ error }}</span>

    <input
      ref="fileInput"
      type="file"
      :accept="accept ?? DEFAULT_ACCEPT"
      style="display: none"
      @change="onFileChange"
    />
  </div>
</template>

<style scoped>
.fuf-wrap { display: grid; gap: 6px; }
.fuf-label { font-size: 14px; color: #243b53; }

.fuf-drop {
  border: 2px dashed #bcccdc;
  border-radius: 10px;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  background: #f8fbff;
  text-align: center;
}
.fuf-drop:hover, .fuf-drop.dragging {
  border-color: #334e68;
  background: #edf5ff;
}
.fuf-icon { font-size: 28px; }
.fuf-hint { font-size: 14px; color: #334e68; font-weight: 500; }
.fuf-formats { font-size: 12px; color: #829ab1; }

.fuf-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid #d9e2ec;
  border-radius: 10px;
  background: #f8fbff;
  font-size: 14px;
  color: #486581;
}
.fuf-spinner {
  width: 16px; height: 16px;
  border: 2px solid #d9e2ec;
  border-top-color: #334e68;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

.fuf-done {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border: 1px solid #27ab83;
  border-radius: 10px;
  background: #f0faf5;
}
.fuf-file-icon { color: #27ab83; font-size: 16px; flex-shrink: 0; }
.fuf-filename { font-size: 14px; color: #243b53; font-weight: 500; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fuf-clear {
  border: 1px solid #bcccdc; background: #fff; color: #486581;
  border-radius: 6px; padding: 4px 10px; font-size: 12px; cursor: pointer;
  flex-shrink: 0;
}
.fuf-clear:hover { background: #f0f4f8; }
.fuf-error { font-size: 12px; color: #d64545; }
</style>
