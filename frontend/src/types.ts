export type TaskPriority = 'low' | 'medium' | 'high';
export type TaskStatus = 'pending' | 'in_progress' | 'completed';

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  due_date?: string; // Formatted or ISO string, e.g. "Today", "Tomorrow", "2026-09-15"
  priority: TaskPriority;
  status: TaskStatus;
  category?: string; // e.g. "Work", "Study", "Personal", "Health"
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  preferences?: {
    dailyGoal: number;
    defaultPriority: TaskPriority;
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tool_activity?: string; // Safe user-facing activity, e.g. "✓ Task created: Study Python" or "✓ 3 pending tasks found"
  created_task?: Task;
  suggestedActions?: string[];
}

export type NavView = 'workspace' | 'dashboard' | 'assistant' | 'tasks';

export interface TaskFilters {
  status: 'all' | TaskStatus;
  priority: 'all' | TaskPriority;
  category: 'all' | string;
  search: string;
  sortBy: 'dueDate' | 'priority' | 'createdAt' | 'title';
  sortOrder: 'asc' | 'desc';
}

export interface ProductivitySummary {
  total: number;
  pending: number;
  inProgress: number;
  completed: number;
  completionRate: number;
  highPriorityPending: number;
  dueTodayOrOverdue: number;
}
