import service from "./index";

export const getFocusGroupSessions = () => service.get("/focus-groups");

export const createFocusGroupSession = (formData: FormData) =>
  service.post("/focus-groups", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const getFocusGroupSession = (sessionId: number) =>
  service.get(`/focus-groups/${sessionId}`);

export const askFocusGroup = (sessionId: number, formData: FormData) =>
  service.post(`/focus-groups/${sessionId}/ask`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const getFocusGroupMessages = (sessionId: number) => service.get(`/focus-groups/${sessionId}/messages`);
export const summarizeFocusGroup = (sessionId: number) => service.post(`/focus-groups/${sessionId}/summarize`);
