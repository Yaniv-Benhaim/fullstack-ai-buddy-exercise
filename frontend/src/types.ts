export interface Module {
  id: number;
  name: string;
  category: string;
  description: string;
}

export interface UserProgress {
  id: number;
  module: Module;
  status: "not_started" | "in_progress" | "completed";
  score: number | null;
  completed_at: string | null;
}

export interface Notification {
  id: number;
  message: string;
  notification_type: "ai_nudge" | "system";
  is_read: boolean;
  created_at: string;
}
