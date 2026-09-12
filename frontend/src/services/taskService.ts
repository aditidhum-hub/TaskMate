import { Task, TaskPriority, TaskStatus } from '../types';
import { INITIAL_TASKS } from '../data/mockData';

const TASKS_STORAGE_KEY = 'taskmate_tasks_collection';

export const taskService = {
  getTasks(): Task[] {
    try {
      const stored = localStorage.getItem(TASKS_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Fallback to default
    }
    // Seed initial tasks
    localStorage.setItem(TASKS_STORAGE_KEY, JSON.stringify(INITIAL_TASKS));
    return INITIAL_TASKS;
  },

  saveTasks(tasks: Task[]): void {
    try {
      localStorage.setItem(TASKS_STORAGE_KEY, JSON.stringify(tasks));
    } catch (e) {
      console.error('Failed to persist tasks to storage', e);
    }
  },

  async createTask(data: {
    title: string;
    description?: string;
    due_date?: string;
    priority?: TaskPriority;
    category?: string;
    user_id?: string;
  }): Promise<Task> {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const tasks = this.getTasks();
    const newTask: Task = {
      id: `task_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      user_id: data.user_id || 'user_tm_demo',
      title: data.title.trim(),
      description: data.description?.trim() || '',
      due_date: data.due_date || 'Today',
      priority: data.priority || 'medium',
      status: 'pending',
      category: data.category || 'General',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    const updated = [newTask, ...tasks];
    this.saveTasks(updated);
    return newTask;
  },

  async updateTask(id: string, updates: Partial<Task>): Promise<Task> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const tasks = this.getTasks();
    const index = tasks.findIndex((t) => t.id === id);
    if (index === -1) {
      throw new Error(`Task ${id} not found`);
    }

    const updatedTask: Task = {
      ...tasks[index],
      ...updates,
      updated_at: new Date().toISOString(),
    };

    tasks[index] = updatedTask;
    this.saveTasks(tasks);
    return updatedTask;
  },

  async deleteTask(id: string): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const tasks = this.getTasks();
    const filtered = tasks.filter((t) => t.id !== id);
    this.saveTasks(filtered);
    return true;
  },

  async toggleTaskStatus(id: string): Promise<Task> {
    const tasks = this.getTasks();
    const task = tasks.find((t) => t.id === id);
    if (!task) throw new Error(`Task ${id} not found`);

    const newStatus: TaskStatus = task.status === 'completed' ? 'pending' : 'completed';
    return this.updateTask(id, { status: newStatus });
  },

  resetToInitialTasks(): Task[] {
    this.saveTasks(INITIAL_TASKS);
    return INITIAL_TASKS;
  },
};
