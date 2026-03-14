import { Bell } from "lucide-react";
import { useStore } from "../store/useStore";
import { useNotifications } from "../hooks/useQueries";
import { useEffect } from "react";

export default function Layout({ children }: { children: React.ReactNode }) {
  const { setNotifications, unreadCount } = useStore();
  const { data: notifications } = useNotifications();

  useEffect(() => {
    if (notifications) {
      setNotifications(notifications);
    }
  }, [notifications, setNotifications]);

  const count = unreadCount();

  return (
    <div className="min-h-screen">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">FC</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">
              Flying Cargo{" "}
              <span className="text-blue-600">AI Learning Buddy</span>
            </h1>
          </div>
          <div className="relative">
            <Bell className="w-6 h-6 text-gray-500" />
            {count > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {count}
              </span>
            )}
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
