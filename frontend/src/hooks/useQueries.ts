import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchModules,
  fetchProgress,
  updateProgress,
  fetchNotifications,
} from "../api/client";

export function useModules() {
  return useQuery({
    queryKey: ["modules"],
    queryFn: fetchModules,
  });
}

export function useProgress() {
  return useQuery({
    queryKey: ["progress"],
    queryFn: fetchProgress,
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: fetchNotifications,
    refetchInterval: 10000, // Poll every 10s for new nudges
  });
}

export function useUpdateProgress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      status,
      score,
    }: {
      id: number;
      status: string;
      score?: number;
    }) => updateProgress(id, { status, score }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      // Also refetch notifications since a nudge may be generated
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["notifications"] });
      }, 5000);
    },
  });
}
