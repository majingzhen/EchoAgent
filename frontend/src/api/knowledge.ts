import service from "./index";

export const listProjects = () => service.get("/knowledge/projects");

export const createProject = (payload: { name: string; description?: string }) =>
  service.post("/knowledge/projects", payload);

export const deleteProject = (projectId: number) =>
  service.delete(`/knowledge/projects/${projectId}`);

export const listDocs = (projectId: number) =>
  service.get(`/knowledge/projects/${projectId}/docs`);

export const uploadDoc = (projectId: number, file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return service.post(`/knowledge/projects/${projectId}/docs`, fd);
};

export const deleteDoc = (projectId: number, docId: number) =>
  service.delete(`/knowledge/projects/${projectId}/docs/${docId}`);

export const searchChunks = (projectId: number, q: string, topK = 4) =>
  service.get(`/knowledge/projects/${projectId}/search`, { params: { q, top_k: topK } });
