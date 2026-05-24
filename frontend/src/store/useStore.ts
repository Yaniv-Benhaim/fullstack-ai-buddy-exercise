import { create } from "zustand";
import type { Notification } from "../types";

interface StoreState {
  notifications: Notification[];
  setNotifications: (notifications: Notification[]) => void;
  addNotification: (notification: Notification) => void;
  unreadCount: () => number;
}

export const useStore = create<StoreState>((set, get) => ({
  notifications: [],
  setNotifications: (notifications) => set({ notifications }),
  addNotification: (notification) =>
    set((state) => {
      if (state.notifications.some((item) => item.id === notification.id)) {
        return state;
      }

      return {
        notifications: [notification, ...state.notifications],
      };
    }),
  unreadCount: () => get().notifications.filter((n) => !n.is_read).length,
}));
