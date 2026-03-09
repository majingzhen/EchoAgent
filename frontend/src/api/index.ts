import axios from "axios";

const explicitBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
const backendTarget = import.meta.env.VITE_BACKEND_TARGET as string | undefined;
const normalizedTarget = backendTarget ? backendTarget.replace(/\/$/, "") : undefined;

const service = axios.create({
  baseURL: explicitBase ?? (normalizedTarget ? `${normalizedTarget}/api` : "/api"),
  timeout: 120000,
});

service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error?.response?.data?.detail ?? error?.message ?? "unknown error";
    return Promise.reject(new Error(message));
  },
);

export default service;
