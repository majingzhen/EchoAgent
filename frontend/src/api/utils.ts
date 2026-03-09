import api from "./index";

export const extractTextFromFile = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post<{ text: string; filename: string }>("/utils/extract-text", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
