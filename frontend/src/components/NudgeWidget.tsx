import { useEffect, useMemo, useState } from "react";
import { Bot, WifiOff, X } from "lucide-react";
import { useStore } from "../store/useStore";
import type { Notification } from "../types";

export default function NudgeWidget() {
  const { notifications, addNotification } = useStore();
  const [isConnected, setIsConnected] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    const source = new EventSource("/api/notifications/stream/");

    source.onopen = () => {
      setIsConnected(true);
    };

    source.addEventListener("notification", (event) => {
      const notification = JSON.parse(event.data) as Notification;
      addNotification(notification);
      setIsDismissed(false);
    });

    source.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      source.close();
    };
  }, [addNotification]);

  const latestNudge = useMemo(
    () =>
      notifications.find(
        (notification) =>
          notification.notification_type === "ai_nudge" ||
          notification.notification_type === "system"
      ),
    [notifications]
  );

  if (isDismissed) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 max-w-sm w-[calc(100%-2rem)] bg-white border border-gray-200 rounded-xl shadow-lg p-4">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-blue-600" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <h4 className="font-medium text-gray-900 text-sm">AI Nudge</h4>
            {!isConnected && (
              <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                <WifiOff className="w-3 h-3" />
                Reconnecting
              </span>
            )}
            <button
              type="button"
              onClick={() => setIsDismissed(true)}
              className="p-1 rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
              aria-label="Close nudge"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            {latestNudge
              ? latestNudge.message
              : "Complete a module to receive a learning nudge."}
          </p>
        </div>
      </div>
    </div>
  );
}
