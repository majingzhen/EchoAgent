import service from "./index";

export const searchEnhance = (query: string, module = "general", maxResults = 5) =>
  service.post("/search/enhance", { query, module, max_results: maxResults });
