import axios from "axios";

// Base URL: uses env variable in production, localhost in development
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If we get 401, clear the stored token (it expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const signup = (data) => api.post("/auth/signup", data);
export const login = (data) => api.post("/auth/login", data);
export const getMe = () => api.get("/auth/me");
export const listUsers = () => api.get("/auth/users");

// ── Groups ────────────────────────────────────────────────────────────────────
export const listGroups = () => api.get("/groups/");
export const createGroup = (data) => api.post("/groups/", data);
export const getGroup = (id) => api.get(`/groups/${id}`);
export const updateGroup = (id, data) => api.patch(`/groups/${id}`, data);
export const addMember = (groupId, data) => api.post(`/groups/${groupId}/members`, data);
export const removeMember = (groupId, userId) => api.delete(`/groups/${groupId}/members/${userId}`);

// ── Expenses ──────────────────────────────────────────────────────────────────
export const listGroupExpenses = (groupId) => api.get(`/expenses/group/${groupId}`);
export const createExpense = (data) => api.post("/expenses/", data);
export const deleteExpense = (id) => api.delete(`/expenses/${id}`);

// ── Settlements ───────────────────────────────────────────────────────────────
export const recordSettlement = (data) => api.post("/settlements/", data);
export const listGroupSettlements = (groupId) => api.get(`/settlements/group/${groupId}`);

// ── Balances ──────────────────────────────────────────────────────────────────
export const getGroupBalances = (groupId) => api.get(`/balances/group/${groupId}`);
export const getMySummary = () => api.get("/balances/user/summary");

// ── Imports ───────────────────────────────────────────────────────────────────
export const uploadCSV = (formData) =>
  api.post("/imports/", formData, { headers: { "Content-Type": "multipart/form-data" } });
export const listImportSessions = () => api.get("/imports/");
export const getImportSession = (id) => api.get(`/imports/${id}`);

// ── Anomalies ─────────────────────────────────────────────────────────────────
export const getPendingAnomalies = () => api.get("/anomalies/pending");
export const getSessionAnomalies = (sessionId) => api.get(`/anomalies/session/${sessionId}`);
export const reviewAnomaly = (id, decision) => api.patch(`/anomalies/${id}/review`, { decision });
