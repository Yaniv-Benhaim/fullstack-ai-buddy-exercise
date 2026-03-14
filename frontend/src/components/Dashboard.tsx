import { useProgress } from "../hooks/useQueries";
import ModuleCard from "./ModuleCard";

export default function Dashboard() {
  const { data: progress, isLoading, error } = useProgress();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500">Loading modules...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-red-500">
          Failed to load modules. Is the backend running?
        </div>
      </div>
    );
  }

  const completed = progress?.filter((p) => p.status === "completed").length ?? 0;
  const total = progress?.length ?? 0;

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Learning Modules</h2>
        <p className="text-gray-500 mt-1">
          {completed} of {total} modules completed
        </p>
        <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: total > 0 ? `${(completed / total) * 100}%` : "0%" }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {progress?.map((p) => (
          <ModuleCard key={p.id} progress={p} />
        ))}
      </div>
    </div>
  );
}
