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
} from '../types';
import { INITIAL_USER, INITIAL_TASKS, INITIAL_CHAT_MESSAGES } from '../data/mockData';
import { taskService } from '../services/taskService';
import { authService } from '../services/authService';
import { aiService } from '../services/aiService';

interface ToastState {
  id: string;
  type: 'success' | 'info' | 'error';
  message: string;
}

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

  // Task Actions
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
  signInDemoUser: () => Promise<void>;
  signOut: () => Promise<void>;

  // Toast
  showToast: (message: string, type?: 'success' | 'info' | 'error') => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const DEFAULT_FILTERS: TaskFilters = {
  status: 'all',
  priority: 'all',
  category: 'all',
  search: '',
  sortBy: 'dueDate',
  sortOrder: 'asc',
};

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
      // Ignore
    }
  }, [messages]);

  // Auth observer
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

  // Compute clean productivity summary derived strictly from current task collection
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

  // Task Actions
  const createTask = useCallback(
    async (data: {
      title: string;
      description?: string;
      due_date?: string;
      priority?: TaskPriority;
      category?: string;
    }): Promise<Task> => {
      const created = await taskService.createTask({
        ...data,
        user_id: currentUser?.id || 'user_tm_demo',
      });
      setTasks(taskService.getTasks());
      showToast(`Task "${created.title}" created`, 'success');
      return created;
    },
    [currentUser, showToast]
  );

  const updateTask = useCallback(
    async (id: string, updates: Partial<Task>): Promise<Task> => {
      const updated = await taskService.updateTask(id, updates);
      setTasks(taskService.getTasks());
      showToast(`Task updated`, 'info');
      return updated;
    },
    [showToast]
  );

  const deleteTask = useCallback(
    async (id: string): Promise<boolean> => {
      await taskService.deleteTask(id);
      setTasks(taskService.getTasks());
      showToast(`Task deleted`, 'info');
      return true;
    },
    [showToast]
  );

  const toggleTaskStatus = useCallback(
    async (id: string) => {
      const updated = await taskService.toggleTaskStatus(id);
      setTasks(taskService.getTasks());
      if (updated.status === 'completed') {
        showToast(`Completed: "${updated.title}"! 🎉`, 'success');
      } else {
        showToast(`Moved "${updated.title}" back to pending`, 'info');
      }
    },
    [showToast]
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
        const response = await aiService.sendMessage(trimmed, (status) => {
          setAiStatusText(status);
        });

        // If AI created a task, sync tasks state
        if (response.created_task) {
          setTasks(taskService.getTasks());
          showToast(`Task "${response.created_task.title}" added to your workspace`, 'success');
        }

        const aiMsg: ChatMessage = {
          id: `msg_ai_${Date.now()}`,
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
          tool_activity: response.tool_used ? `✓ ${response.tool_used.replace('_', ' ')} executed` : undefined,
          created_task: response.created_task,
          suggestedActions: response.suggestedActions,
        };

        setMessages((prev) => [...prev, aiMsg]);
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
        const errorAiMsg: ChatMessage = {
          id: `msg_err_${Date.now()}`,
          role: 'assistant',
          content: `I ran into a temporary issue: ${errorMessage}. Please feel free to try again.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorAiMsg]);
      } finally {
        setIsAiThinking(false);
      }
    },
    [showToast]
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
      showToast(`Account created! Welcome to TaskMate, ${user.name}`, 'success');
    },
    [showToast]
  );

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
