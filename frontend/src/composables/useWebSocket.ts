import { onUnmounted, ref } from "vue";

export type WSMessage = Record<string, unknown>;

export const useWebSocket = (path: string | (() => string)) => {
  const connected = ref(false);
  const messages = ref<WSMessage[]>([]);
  const wsRef = ref<WebSocket | null>(null);

  const connect = () => {
    const resolvedPath = typeof path === "function" ? path() : path;
    if (!resolvedPath) return;
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsBase = import.meta.env.VITE_WS_BASE_URL ?? `${protocol}://${window.location.hostname}:8000`;
    wsRef.value = new WebSocket(`${wsBase}${resolvedPath}`);
    wsRef.value.onopen = () => {
      connected.value = true;
    };
    wsRef.value.onclose = () => {
      connected.value = false;
    };
    wsRef.value.onmessage = (evt) => {
      try {
        messages.value.push(JSON.parse(evt.data));
      } catch {
        messages.value.push({ raw: evt.data });
      }
    };
  };

  const send = (payload: WSMessage) => {
    if (!wsRef.value || wsRef.value.readyState !== WebSocket.OPEN) return;
    wsRef.value.send(JSON.stringify(payload));
  };

  const disconnect = () => {
    wsRef.value?.close();
    wsRef.value = null;
    connected.value = false;
  };

  onUnmounted(() => disconnect());
  return { connected, messages, connect, send, disconnect };
};
