import { Bell } from "lucide-react";
import { useStore } from "../store/useStore";
import { useNotifications } from "../hooks/useQueries";
import { useEffect, useState } from "react";

export default function Layout({ children }: { children: React.ReactNode }) {
  const { notifications: storedNotifications, setNotifications, markAllRead, unreadCount } = useStore();
  const { data: notifications } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (notifications) {
      setNotifications(notifications);
    }
  }, [notifications, setNotifications]);

  const count = unreadCount();
  const displayedNotifications = storedNotifications.slice(0, 5);

  const toggleNotifications = () => {
    setIsOpen((open) => {
      const nextOpen = !open;
      if (nextOpen) {
        markAllRead();
      }
      return nextOpen;
    });
  };

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
            <button
              type="button"
              onClick={toggleNotifications}
              className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Notifications"
            >
              <Bell className="w-6 h-6 text-gray-500" />
            </button>
            {count > 0 && (
              <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {count}
              </span>
            )}
            {isOpen && (
              <div className="absolute right-0 top-12 w-96 max-w-[calc(100vw-2rem)] bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                <div className="px-4 py-3 border-b border-gray-100">
                  <h2 className="text-sm font-semibold text-gray-900">
                    Notifications
                  </h2>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {displayedNotifications.length > 0 ? (
                    displayedNotifications.map((notification) => (
                      <div
                        key={notification.id}
                        className="px-4 py-3 border-b border-gray-100 last:border-b-0"
                      >
                        <p className="text-sm text-gray-700">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(notification.created_at).toLocaleString()}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="px-4 py-6 text-sm text-gray-500">
                      No notifications yet.
                    </p>
                  )}
                </div>
              </div>
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
