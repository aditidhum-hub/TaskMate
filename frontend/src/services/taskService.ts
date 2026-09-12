import {
  collection,
  doc,
  getDocs,
  setDoc,
  updateDoc,
  deleteDoc,
  query,
  orderBy,
  CollectionReference,
  DocumentData,
} from 'firebase/firestore';
import { auth, db } from './firebase';
import { Task, TaskPriority, TaskStatus } from '../types';
import { INITIAL_TASKS } from '../data/mockData';

const TASKS_STORAGE_KEY = 'taskmate_tasks_collection';

/**
 * Helper to get the Firestore collection reference strictly scoped to the authenticated user:
 * users/{user_id}/tasks
 * Returns null if the user is unauthenticated or Firestore is unavailable.
 */
function getUserTasksCollection(): CollectionReference<DocumentData> | null {
  try {
    const user = auth.currentUser;
    if (!user || !user.uid || !user.uid.trim()) {
      return null;
    }
    return collection(db, 'users', user.uid.trim(), 'tasks');
  } catch (err) {
    console.warn('Could not resolve Firestore user tasks collection reference:', err);
    return null;
  }
}

export const taskService = {
  /**
   * Fetch all tasks for the authenticated user from Cloud Firestore.
   * Scoped to: users/{user_id}/tasks
   * Falls back to local storage cache if offline or unauthenticated.
   */
  async fetchTasks(): Promise<Task[]> {
    const tasksCollection = getUserTasksCollection();
    if (!tasksCollection) {
      // Offline / unauthenticated fallback
      return this.getTasks();
    }

    try {
      const q = query(tasksCollection, orderBy('created_at', 'desc'));
      const snapshot = await getDocs(q);
      const firestoreTasks: Task[] = [];
      snapshot.forEach((docSnap) => {
        const data = docSnap.data();
        firestoreTasks.push({
          id: docSnap.id,
          user_id: data.user_id || auth.currentUser?.uid || 'user_tm_demo',
          title: data.title || '',
          description: data.description || '',
          due_date: data.due_date,
          priority: (data.priority as TaskPriority) || 'medium',
          status: (data.status as TaskStatus) || 'pending',
          category: data.category || 'General',
          created_at: data.created_at || new Date().toISOString(),
          updated_at: data.updated_at || new Date().toISOString(),
        });
      });

      // If documents were found, update the local storage cache
      if (firestoreTasks.length > 0) {
        this.saveTasks(firestoreTasks);
        return firestoreTasks;
      }
      return this.getTasks();
    } catch (err) {
      console.warn('Failed to fetch tasks from Cloud Firestore, falling back to local cache:', err);
      return this.getTasks();
    }
  },

  /**
   * Synchronous getter returning current cached tasks from localStorage.
   */
  getTasks(): Task[] {
    try {
      const stored = localStorage.getItem(TASKS_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Fallback
    }
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

  /**
   * Create a task document under users/{user_id}/tasks/{task_id} in Cloud Firestore.
   * Also persists to local storage cache.
   */
  async createTask(data: {
    title: string;
    description?: string;
    due_date?: string;
    priority?: TaskPriority;
    category?: string;
    user_id?: string;
  }): Promise<Task> {
    const now = new Date().toISOString();
    const uid = auth.currentUser?.uid || data.user_id || 'user_tm_demo';
    const taskId = `task_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;

    const newTask: Task = {
      id: taskId,
      user_id: uid,
      title: data.title.trim(),
      description: data.description?.trim() || '',
      due_date: data.due_date || 'Today',
      priority: data.priority || 'medium',
      status: 'pending',
      category: data.category || 'General',
      created_at: now,
      updated_at: now,
    };

    // 1. If authenticated, persist to Cloud Firestore under users/{uid}/tasks/{taskId}
    const tasksCollection = getUserTasksCollection();
    if (tasksCollection) {
      try {
        const taskDocRef = doc(tasksCollection, taskId);
        await setDoc(taskDocRef, {
          id: newTask.id,
          user_id: uid,
          title: newTask.title,
          description: newTask.description,
          due_date: newTask.due_date,
          priority: newTask.priority,
          status: newTask.status,
          category: newTask.category,
          created_at: newTask.created_at,
          updated_at: newTask.updated_at,
        });
      } catch (err) {
        console.warn('Failed to persist task to Cloud Firestore, saving locally:', err);
      }
    }

    // 2. Persist to local cache
    const currentTasks = this.getTasks();
    const updated = [newTask, ...currentTasks.filter((t) => t.id !== taskId)];
    this.saveTasks(updated);
    return newTask;
  },

  /**
   * Update a task document under users/{user_id}/tasks/{task_id} in Cloud Firestore.
   */
  async updateTask(id: string, updates: Partial<Task>): Promise<Task> {
    const now = new Date().toISOString();
    const tasks = this.getTasks();
    const index = tasks.findIndex((t) => t.id === id);
    if (index === -1) {
      throw new Error(`Task ${id} not found`);
    }

    const updatedTask: Task = {
      ...tasks[index],
      ...updates,
      updated_at: now,
    };

    // 1. If authenticated, update Cloud Firestore under users/{uid}/tasks/{id}
    const tasksCollection = getUserTasksCollection();
    if (tasksCollection) {
      try {
        const taskDocRef = doc(tasksCollection, id);
        // Sanitize updates to omit undefined values
        const firestoreUpdates: Record<string, any> = { updated_at: now };
        if (updates.title !== undefined) firestoreUpdates.title = updates.title.trim();
        if (updates.description !== undefined) firestoreUpdates.description = updates.description.trim();
        if (updates.due_date !== undefined) firestoreUpdates.due_date = updates.due_date;
        if (updates.priority !== undefined) firestoreUpdates.priority = updates.priority;
        if (updates.status !== undefined) firestoreUpdates.status = updates.status;
        if (updates.category !== undefined) firestoreUpdates.category = updates.category;

        await updateDoc(taskDocRef, firestoreUpdates);
      } catch (err) {
        console.warn(`Failed to update task ${id} in Cloud Firestore, updating locally:`, err);
      }
    }

    // 2. Update local storage cache
    tasks[index] = updatedTask;
    this.saveTasks(tasks);
    return updatedTask;
  },

  /**
   * Delete a task document under users/{user_id}/tasks/{task_id} from Cloud Firestore.
   */
  async deleteTask(id: string): Promise<boolean> {
    // 1. If authenticated, delete from Cloud Firestore
    const tasksCollection = getUserTasksCollection();
    if (tasksCollection) {
      try {
        const taskDocRef = doc(tasksCollection, id);
        await deleteDoc(taskDocRef);
      } catch (err) {
        console.warn(`Failed to delete task ${id} from Cloud Firestore, deleting locally:`, err);
      }
    }

    // 2. Remove from local cache
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

  async moveTaskStatus(id: string, newStatus: TaskStatus): Promise<Task> {
    return this.updateTask(id, { status: newStatus });
  },

  resetToInitialTasks(): Task[] {
    this.saveTasks(INITIAL_TASKS);
    return INITIAL_TASKS;
  },
};
