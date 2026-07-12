import { apiClient } from "./client";
import type { Job, SchedulerHealth } from "../types/job";

export async function fetchJobs(): Promise<Job[]> {
  const { data } = await apiClient.get<Job[]>("/api/v1/jobs");
  return data;
}

export async function fetchSchedulerHealth(): Promise<SchedulerHealth> {
  const { data } = await apiClient.get<SchedulerHealth>("/health/scheduler");
  return data;
}

export async function triggerJob(jobId: string): Promise<void> {
  await apiClient.post(`/api/v1/jobs/${jobId}/run`);
}

export async function pauseJob(jobId: string): Promise<void> {
  await apiClient.post(`/api/v1/jobs/${jobId}/pause`);
}

export async function resumeJob(jobId: string): Promise<void> {
  await apiClient.post(`/api/v1/jobs/${jobId}/resume`);
}