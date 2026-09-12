import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import {
  Task,
  UserProfile,
  ChatMessage,
  NavView,
  TaskFilters,
  ProductivitySummary,
  TaskPriority,
  TaskStatus,
  ToastState,
} from '../types';
import { INITIAL_TASKS, INITIAL_CHAT_MESSAGES } from '../data/mockData';
import { taskService } from '../services/taskService';
import { authService } from '../services/authService';
import { aiService } from '../services/aiService';

interface AppContextType {
  currentUser: UserProfile | null;
  tasks: Task[];
  messages: ChatMessage[];
  activeNavView: NavView;
  mobileTab: 'assistant' | 'tasks';
  filters: TaskFilters;
  isAiThinking: boolean;
  aiStatusText: string;
  summary: ProductivitySummary;
  isNewTaskModalOpen: boolean;
  editingTask: Task | null;
  isAuthModalOpen: boolean;
  authModalMode: 'signin' | 'signup' | 'forgot';
  toast: ToastState | null;

  // Navigation
  setActiveNavView: (view: NavView) => void;
  setMobileTab: (tab: 'assistant' | 'tasks') => void;

  // Task Actions (with optimistic updates and rollback)
  createTask: (data: {
    title: string;
    description?: string;
    due_date?: string;
    priority?: TaskPriority;
    category?: string;
  }) => Promise<Task>;
  updateTask: (id: string, updates: Partial<Task>) => Promise<Task>;
  deleteTask: (id: string) => Promise<boolean>;
  toggleTaskStatus: (id: string) => Promise<void>;
  moveTaskStatus: (id: string, newStatus: TaskStatus) => Promise<Task>;
  resetTasksToDefault: () => void;

  // Filter Actions
  setFilters: React.Dispatch<React.SetStateAction<TaskFilters>>;
  resetFilters: () => void;

  // Chat Actions
  sendMessage: (prompt: string) => Promise<void>;
  clearChat: () => void;

  // Modal Actions
  openNewTaskModal: () => void;
  closeNewTaskModal: () => void;
  openEditTaskModal: (task: Task) => void;
  closeEditTaskModal: () => void;
  openAuthModal: (mode?: 'signin' | 'signup' | 'forgot') => void;
  closeAuthModal: () => void;

  // Auth Actions
  signInWithEmail: (email: string, pass: string) => Promise<void>;
  signUpWithEmail: (name: string, email: string, pass: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signInDemoUser: () => Promise<void>;
  signOut: () => Promise<void>;

  // Toast
  showToast: (message: string, type?: 'success' | 'info' | 'error') => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const DEFAULT_FILTERS: TaskFilters = {
  status: 'all',
  priority: 'all',
  category: 'all',
  search: '',
  sortBy: 'dueDate',
  sortOrder: 'asc',
};

export interface AiToolSyncResult {
  updatedTasks: Task[];
  createdCount: number;
  completedCount: number;
  updatedCount: number;
  deletedCount: number;
  lastCreatedTask?: Task;
  lastCompletedTitle?: string;
  lastUpdatedTitle?: string;
}

/**
 * Synchronize AI agent tool results (create_task, complete_task, update_task, delete_task)
 * with the React tasks state, preventing duplicate tasks and avoiding duplicate Firestore writes.
 */
export function applyAiToolEffects(
  currentTasks: Task[],
  response: {
    created_task?: Task | null;
    tool_used?: string | null;
    tool_calls?: Array<Record<string, unknown>>;
    tool_results?: Array<Record<string, unknown>>;
  }
): AiToolSyncResult {
  let tasks = [...currentTasks];
  let createdCount = 0;
  let completedCount = 0;
  let updatedCount = 0;
  let deletedCount = 0;
  let lastCreatedTask: Task | undefined;
  let lastCompletedTitle: string | undefined;
  let lastUpdatedTitle: string | undefined;

  const toolCalls = response.tool_calls || [];
  const toolResults = response.tool_results || [];

  // 1. Process structured tool_results if present
  for (let i = 0; i < toolResults.length; i++) {
    const res = toolResults[i];
    if (!res || res.success !== true) continue;

    const call = toolCalls[i];
    const callArgs = (call?.arguments as Record<string, unknown>) || {};
    const opName = (call?.name as string) || (i === 0 ? response.tool_used : '') || '';

    // Handle delete_task
    if (opName === 'delete_task' || (res.task_id && !res.task)) {
      const idToDelete = (res.task_id as string) || (callArgs.task_id as string);
      if (idToDelete) {
        tasks = tasks.filter((t) => t.id !== idToDelete);
        deletedCount++;
      }
    }
    // Handle complete_task
    else if (opName === 'complete_task') {
      const compTask = res.task as Task | undefined;
      const idToComplete = compTask?.id || (res.task_id as string) || (callArgs.task_id as string);
      if (idToComplete) {
        tasks = tasks.map((t) => {
          if (t.id === idToComplete) {
            lastCompletedTitle = compTask?.title || t.title;
            return {
              ...t,
              ...(compTask || {}),
              status: 'completed' as TaskStatus,
              updated_at: compTask?.updated_at || new Date().toISOString(),
            };
          }
          return t;
        });
        completedCount++;
      }
    }
    // Handle update_task
    else if (opName === 'update_task') {
      const updTask = res.task as Task | undefined;
      const idToUpdate = updTask?.id || (res.task_id as string) || (callArgs.task_id as string);
      if (idToUpdate) {
        tasks = tasks.map((t) => {
          if (t.id === idToUpdate) {
            lastUpdatedTitle = updTask?.title || t.title;
            return {
              ...t,
              ...(updTask || {}),
              updated_at: updTask?.updated_at || new Date().toISOString(),
            };
          }
          return t;
        });
        updatedCount++;
      }
    }
    // Handle create_task
    else if (opName === 'create_task') {
      const newTask = (res.task || response.created_task) as Task | undefined;
      if (newTask && newTask.id) {
        if (!tasks.some((t) => t.id === newTask.id)) {
          tasks = [newTask, ...tasks];
          lastCreatedTask = newTask;
          createdCount++;
        }
      }
    }
  }

  // 2. Fallback: if tool_results did not process task, but response.created_task is present
  if (response.created_task && response.created_task.id) {
    const newTask = response.created_task as Task;
    const isCreateTool = !response.tool_used || response.tool_used === 'create_task';
    const isCompleteTool = response.tool_used === 'complete_task';
    const isUpdateTool = response.tool_used === 'update_task';
    const isDeleteTool = response.tool_used === 'delete_task';

    if (isCompleteTool) {
      if (completedCount === 0) {
        tasks = tasks.map((t) => {
          if (t.id === newTask.id) {
            lastCompletedTitle = newTask.title || t.title;
            return {
              ...t,
              ...newTask,
              status: 'completed' as TaskStatus,
              updated_at: newTask.updated_at || new Date().toISOString(),
            };
          }
          return t;
        });
        completedCount++;
      }
    } else if (isUpdateTool) {
      if (updatedCount === 0) {
        tasks = tasks.map((t) => {
          if (t.id === newTask.id) {
            lastUpdatedTitle = newTask.title || t.title;
            return {
              ...t,
              ...newTask,
              updated_at: newTask.updated_at || new Date().toISOString(),
            };
          }
          return t;
        });
        updatedCount++;
      }
    } else if (isDeleteTool) {
      if (deletedCount === 0) {
        tasks = tasks.filter((t) => t.id !== newTask.id);
        deletedCount++;
      }
    } else if (isCreateTool && createdCount === 0) {
      if (!tasks.some((t) => t.id === newTask.id)) {
        tasks = [newTask, ...tasks];
        lastCreatedTask = newTask;
        createdCount++;
      }
    }
  }

  return {
    updatedTasks: tasks,
    createdCount,
    completedCount,
    updatedCount,
    deletedCount,
    lastCreatedTask,
    lastCompletedTitle,
    lastUpdatedTitle,
  };
}

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Auth state
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(() => authService.getCurrentUser());

  // Tasks state
  const [tasks, setTasks] = useState<Task[]>(() => taskService.getTasks());

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem('taskmate_chat_history');
      if (saved) return JSON.parse(saved);
    } catch {
      // Fallback
    }
    return INITIAL_CHAT_MESSAGES;
  });

  // Navigation state
  const [activeNavView, setActiveNavView] = useState<NavView>('workspace');
  const [mobileTab, setMobileTab] = useState<'assistant' | 'tasks'>('assistant');

  // Filters state
  const [filters, setFilters] = useState<TaskFilters>(DEFAULT_FILTERS);

  // AI execution state
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [aiStatusText, setAiStatusText] = useState('Thinking...');

  // Modal states
  const [isNewTaskModalOpen, setIsNewTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'signin' | 'signup' | 'forgot'>('signin');

  // Toast state
  const [toast, setToast] = useState<ToastState | null>(null);

  // Save chat history
  useEffect(() => {
    try {
      localStorage.setItem('taskmate_chat_history', JSON.stringify(messages));
    } catch {
      // Ignore storage errors
    }
  }, [messages]);

  // Real-time Firebase Auth observer
  useEffect(() => {
    return authService.onAuthStateChanged((user) => {
      setCurrentUser(user);
    });
  }, []);

  const showToast = useCallback((message: string, type: 'success' | 'info' | 'error' = 'success') => {
    const id = `toast_${Date.now()}`;
    setToast({ id, message, type });
    setTimeout(() => {
      setToast((current) => (current?.id === id ? null : current));
    }, 3500);
  }, []);

  // Compute canonical derived metrics
  const summary: ProductivitySummary = useMemo(() => {
    const total = tasks.length;
    const completed = tasks.filter((t) => t.status === 'completed').length;
    const inProgress = tasks.filter((t) => t.status === 'in_progress').length;
    const pending = tasks.filter((t) => t.status === 'pending').length;
    const highPriorityPending = tasks.filter(
      (t) => t.priority === 'high' && t.status !== 'completed'
    ).length;
    const dueTodayOrOverdue = tasks.filter((t) => {
      if (t.status === 'completed') return false;
      const due = (t.due_date || '').toLowerCase();
      return due === 'today' || due === 'yesterday';
    }).length;
    const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;

    return {
      total,
      pending,
      inProgress,
      completed,
      completionRate,
      highPriorityPending,
      dueTodayOrOverdue,
    };
  }, [tasks]);

  // Task Actions with optimistic updates & rollback
  const createTask = useCallback(
    async (data: {
      title: string;
      description?: string;
      due_date?: string;
      priority?: TaskPriority;
      category?: string;
    }): Promise<Task> => {
      try {
        const created = await taskService.createTask({
          ...data,
          user_id: currentUser?.id || 'user_tm_demo',
        });
        setTasks(taskService.getTasks());
        showToast(`Task "${created.title}" created`, 'success');
        return created;
      } catch (err: unknown) {
        showToast('Failed to create task', 'error');
        throw err;
      }
    },
    [currentUser, showToast]
  );

  const updateTask = useCallback(
    async (id: string, updates: Partial<Task>): Promise<Task> => {
      const previousTasks = [...tasks];
      // Optimistic update
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, ...updates, updated_at: new Date().toISOString() } : t))
      );

      try {
        const updated = await taskService.updateTask(id, updates);
        setTasks(taskService.getTasks());
        showToast('Task updated', 'info');
        return updated;
      } catch (err: unknown) {
        // Rollback on error
        setTasks(previousTasks);
        showToast('Failed to update task. Reverted changes.', 'error');
        throw err;
      }
    },
    [tasks, showToast]
  );

  const deleteTask = useCallback(
    async (id: string): Promise<boolean> => {
      const previousTasks = [...tasks];
      // Optimistic delete
      setTasks((prev) => prev.filter((t) => t.id !== id));

      try {
        await taskService.deleteTask(id);
        setTasks(taskService.getTasks());
        showToast('Task deleted', 'info');
        return true;
      } catch (err: unknown) {
        // Rollback
        setTasks(previousTasks);
        showToast('Failed to delete task. Reverted.', 'error');
        throw err;
      }
    },
    [tasks, showToast]
  );

  const toggleTaskStatus = useCallback(
    async (id: string) => {
      const target = tasks.find((t) => t.id === id);
      if (!target) return;

      const previousTasks = [...tasks];
      const nextStatus: TaskStatus = target.status === 'completed' ? 'pending' : 'completed';

      // Optimistic status update
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, status: nextStatus, updated_at: new Date().toISOString() } : t))
      );

      try {
        const updated = await taskService.toggleTaskStatus(id);
        setTasks(taskService.getTasks());
        if (updated.status === 'completed') {
          showToast(`Completed: "${updated.title}"! 🎉`, 'success');
        } else {
          showToast(`Moved "${updated.title}" to pending`, 'info');
        }
      } catch (err: unknown) {
        // Rollback
        setTasks(previousTasks);
        showToast('Failed to toggle status. Reverted.', 'error');
        throw err;
      }
    },
    [tasks, showToast]
  );

  const moveTaskStatus = useCallback(
    async (id: string, newStatus: TaskStatus): Promise<Task> => {
      const target = tasks.find((t) => t.id === id);
      if (!target) {
        throw new Error(`Task ${id} not found`);
      }

      const previousTasks = [...tasks];
      // Optimistic update
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, status: newStatus, updated_at: new Date().toISOString() } : t))
      );

      try {
        const updated = await taskService.moveTaskStatus(id, newStatus);
        setTasks(taskService.getTasks());
        const statusLabel =
          newStatus === 'in_progress' ? 'In Progress' : newStatus === 'completed' ? 'Completed' : 'Pending';
        showToast(`Moved to ${statusLabel}`, 'info');
        return updated;
      } catch (err: unknown) {
        // Rollback
        setTasks(previousTasks);
        showToast('Failed to move task. Reverted.', 'error');
        throw err;
      }
    },
    [tasks, showToast]
  );

  const resetTasksToDefault = useCallback(() => {
    const refreshed = taskService.resetToInitialTasks();
    setTasks(refreshed);
    showToast('Reset tasks to starter template', 'info');
  }, [showToast]);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  // Send message to AI Assistant
  const sendMessage = useCallback(
    async (prompt: string) => {
      const trimmed = prompt.trim();
      if (!trimmed) return;

      const userMsg: ChatMessage = {
        id: `msg_user_${Date.now()}`,
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsAiThinking(true);
      setAiStatusText('Thinking...');

      try {
        // Build message history for the backend request
        const history = messages.slice(-6).map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const response = await aiService.sendMessage(
          trimmed,
          (status) => {
            setAiStatusText(status);
          },
          history
        );

        // Apply task effects to React tasks state and sync local cache
        const currentTasks = taskService.getTasks();
        const syncOutcome = applyAiToolEffects(currentTasks, response);
        if (
          syncOutcome.createdCount > 0 ||
          syncOutcome.completedCount > 0 ||
          syncOutcome.updatedCount > 0 ||
          syncOutcome.deletedCount > 0
        ) {
          taskService.saveTasks(syncOutcome.updatedTasks);
          setTasks(syncOutcome.updatedTasks);
        }

        // Trigger truthful toast notifications based on real outcome
        if (syncOutcome.createdCount > 0 && syncOutcome.lastCreatedTask) {
          showToast(`Task "${syncOutcome.lastCreatedTask.title}" added to your workspace`, 'success');
        } else if (syncOutcome.completedCount > 0) {
          showToast(`Task "${syncOutcome.lastCompletedTitle || 'task'}" marked as completed! 🎉`, 'success');
        } else if (syncOutcome.updatedCount > 0) {
          showToast(`Task "${syncOutcome.lastUpdatedTitle || 'task'}" updated`, 'info');
        } else if (syncOutcome.deletedCount > 0) {
          showToast('Task deleted', 'info');
        }

        const isCreationTurn = syncOutcome.createdCount > 0;
        const createdTaskForCard = isCreationTurn ? syncOutcome.lastCreatedTask : undefined;

        const aiMsg: ChatMessage = {
          id: `msg_ai_${Date.now()}`,
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
          tool_activity: response.tool_used ? `✓ ${response.tool_used.replace(/_/g, ' ')} executed` : undefined,
          created_task: createdTaskForCard,
          suggestedActions: response.suggestedActions,
        };

        setMessages((prev) => [...prev, aiMsg]);
      } catch (err: unknown) {
        let errorMessage = 'Something went wrong. Please try again.';
        if (err && typeof err === 'object' && 'message' in err && typeof (err as { message: unknown }).message === 'string') {
          errorMessage = (err as { message: string }).message;
        } else if (err instanceof Error) {
          errorMessage = err.message;
        }

        const errorAiMsg: ChatMessage = {
          id: `msg_err_${Date.now()}`,
          role: 'assistant',
          content: `I ran into an issue: ${errorMessage}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorAiMsg]);
        showToast(errorMessage, 'error');
      } finally {
        setIsAiThinking(false);
      }
    },
    [messages, showToast]
  );

  const clearChat = useCallback(() => {
    setMessages(INITIAL_CHAT_MESSAGES);
    showToast('Conversation cleared', 'info');
  }, [showToast]);

  // Modal Handlers
  const openNewTaskModal = useCallback(() => setIsNewTaskModalOpen(true), []);
  const closeNewTaskModal = useCallback(() => setIsNewTaskModalOpen(false), []);

  const openEditTaskModal = useCallback((task: Task) => {
    setEditingTask(task);
  }, []);
  const closeEditTaskModal = useCallback(() => {
    setEditingTask(null);
  }, []);

  const openAuthModal = useCallback((mode: 'signin' | 'signup' | 'forgot' = 'signin') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  }, []);
  const closeAuthModal = useCallback(() => setIsAuthModalOpen(false), []);

  // Auth operations
  const signInWithEmail = useCallback(
    async (email: string, pass: string) => {
      const user = await authService.signInWithEmail(email, pass);
      setCurrentUser(user);
      setIsAuthModalOpen(false);
      showToast(`Welcome back, ${user.name}!`, 'success');
    },
    [showToast]
  );

  const signUpWithEmail = useCallback(
    async (name: string, email: string, pass: string) => {
      const user = await authService.signUpWithEmail(name, email, pass);
      setCurrentUser(user);
      setIsAuthModalOpen(false);
      showToast(`Account created! Welcome, ${user.name}`, 'success');
    },
    [showToast]
  );

  const signInWithGoogle = useCallback(async () => {
    const user = await authService.signInWithGoogle();
    setCurrentUser(user);
    setIsAuthModalOpen(false);
    showToast(`Welcome, ${user.name}!`, 'success');
  }, [showToast]);

  const signInDemoUser = useCallback(async () => {
    const user = await authService.signInWithDemo();
    setCurrentUser(user);
    setIsAuthModalOpen(false);
    showToast(`Signed in as demo user (${user.name})`, 'success');
  }, [showToast]);

  const signOut = useCallback(async () => {
    await authService.signOut();
    setCurrentUser(null);
    showToast('Signed out of TaskMate', 'info');
  }, [showToast]);

  return (
    <AppContext.Provider
      value={{
        currentUser,
        tasks,
        messages,
        activeNavView,
        mobileTab,
        filters,
        isAiThinking,
        aiStatusText,
        summary,
        isNewTaskModalOpen,
        editingTask,
        isAuthModalOpen,
        authModalMode,
        toast,
        setActiveNavView,
        setMobileTab,
        createTask,
        updateTask,
        deleteTask,
        toggleTaskStatus,
        moveTaskStatus,
        resetTasksToDefault,
        setFilters,
        resetFilters,
        sendMessage,
        clearChat,
        openNewTaskModal,
        closeNewTaskModal,
        openEditTaskModal,
        closeEditTaskModal,
        openAuthModal,
        closeAuthModal,
        signInWithEmail,
        signUpWithEmail,
        signInWithGoogle,
        signInDemoUser,
        signOut,
        showToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
