import service from "./index";

export const buildMarketGraph = (payload: { name: string; source_text: string }) =>
  service.post("/market/graphs/build", payload);

export const uploadMarketGraph = (formData: FormData) => service.post("/market/graphs/upload", formData);

export const getMarketGraph = (graphId: number) => service.get(`/market/graphs/${graphId}`);

export const getMarketReport = (graphId: number) => service.get(`/market/graphs/${graphId}/report`);
