import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchJobs, fetchSchedulerHealth, pauseJob, resumeJob, triggerJob } from "../api/jobs";
import { useToastStore } from "../store/toastStore";

export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: fetchJobs,
    refetchInterval: 10_000, // system page needs to feel "live" -- jobs run every 90s
  });
}

export function useSchedulerHealth() {
  return useQuery({
    queryKey: ["scheduler-health"],
    queryFn: fetchSchedulerHealth,
    refetchInterval: 10_000,
  });
}

function useJobMutation(fn: (jobId: string) => Promise<void>, successMessage: (id: string) => string) {
  const queryClient = useQueryClient();
  const pushToast = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: fn,
    onSuccess: (_data, jobId) => {
      pushToast({ variant: "success", message: successMessage(jobId) });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (error: Error, jobId) => {
      pushToast({ variant: "error", message: `${jobId}: ${error.message}` });
    },
  });
}

export function useTriggerJob() {
  return useJobMutation(triggerJob, (id) => `${id} triggered`);
}
export function usePauseJob() {
  return useJobMutation(pauseJob, (id) => `${id} paused`);
}
export function useResumeJob() {
  return useJobMutation(resumeJob, (id) => `${id} resumed`);
}
