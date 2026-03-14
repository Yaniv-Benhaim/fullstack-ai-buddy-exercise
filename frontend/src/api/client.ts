import axios from "axios";
import type { Module, UserProgress, Notification } from "../types";

const api = axios.create({
  baseURL: "/api",
});

export async function fetchModules(): Promise<Module[]> {
  const { data } = await api.get<Module[]>("/modules/");
  return data;
}

export async function fetchProgress(): Promise<UserProgress[]> {
  const { data } = await api.get<UserProgress[]>("/progress/");
  return data;
}

export async function updateProgress(
  id: number,
  update: { status: string; score?: number }
): Promise<UserProgress> {
  const { data } = await api.patch<UserProgress>(`/progress/${id}/`, update);
  return data;
}

export async function fetchNotifications(): Promise<Notification[]> {
  const { data } = await api.get<Notification[]>("/notifications/");
  return data;
}
