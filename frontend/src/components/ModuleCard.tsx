import { CheckCircle, Circle, Loader } from "lucide-react";
import type { UserProgress } from "../types";
import { useUpdateProgress } from "../hooks/useQueries";

const statusConfig = {
  not_started: {
    icon: Circle,
    label: "Not Started",
    color: "text-gray-400",
    bg: "bg-gray-50",
  },
  in_progress: {
    icon: Loader,
    label: "In Progress",
    color: "text-yellow-500",
    bg: "bg-yellow-50",
  },
  completed: {
    icon: CheckCircle,
    label: "Completed",
    color: "text-green-500",
    bg: "bg-green-50",
  },
};

export default function ModuleCard({ progress }: { progress: UserProgress }) {
  const { mutate: update, isPending } = useUpdateProgress();
  const config = statusConfig[progress.status];
  const Icon = config.icon;

  const handleComplete = () => {
    update({ id: progress.id, status: "completed" });
  };

  const handleUndo = () => {
    update({ id: progress.id, status: "not_started" });
  };

  return (
    <div className={`rounded-xl border border-gray-200 p-6 ${config.bg} transition-all hover:shadow-md`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
          {progress.module.category}
        </span>
        <Icon className={`w-5 h-5 ${config.color}`} />
      </div>

      <h3 className="font-semibold text-gray-900 mb-2">{progress.module.name}</h3>
      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
        {progress.module.description}
      </p>

      <div className="flex items-center justify-between">
        <span className={`text-xs font-medium ${config.color}`}>
          {config.label}
        </span>
        {progress.status === "completed" ? (
          <button
            onClick={handleUndo}
            disabled={isPending}
            className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-300 disabled:opacity-50 transition-colors"
          >
            {isPending ? "Updating..." : "Mark Incomplete"}
          </button>
        ) : (
          <button
            onClick={handleComplete}
            disabled={isPending}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isPending ? "Updating..." : "Mark Complete"}
          </button>
        )}
      </div>
    </div>
  );
}
