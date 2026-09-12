import { Task, TaskPriority, ChatResponsePayload } from '../types';
import { taskService } from './taskService';
import { apiClient } from './apiClient';

export interface ChatResponse {
  response: string;
  tool_used?: string | null;
  created_task?: Task | null;
  tool_calls?: Array<Record<string, unknown>>;
  tool_results?: Array<Record<string, unknown>>;
  suggestedActions?: string[];
  success?: boolean;
}

export type StatusUpdateCallback = (statusText: string) => void;

export const aiService = {
  /**
   * Process a natural language prompt with the TaskMate AI assistant.
   * Dispatches status updates ("Thinking...", "Checking your tasks...", "Creating your task...")
   * without ever exposing chain-of-thought or raw internal reasoning.
   */
  async sendMessage(
    message: string,
    onStatusUpdate?: StatusUpdateCallback,
    messageHistory?: Array<Record<string, unknown>>
  ): Promise<ChatResponse> {
    onStatusUpdate?.('Thinking...');

    // Call live backend POST /api/chat via apiClient with Firebase Bearer authentication
    try {
      const data: ChatResponsePayload = await apiClient.postChat(message, messageHistory);

      if (!data || typeof data.response !== 'string') {
        throw {
          status: 500,
          message: 'Received an unexpected or malformed response from TaskMate server.',
        };
      }

      // Extract created task if returned by backend
      let createdTask: Task | null = null;
      if (data.created_task) {
        createdTask = data.created_task as unknown as Task;
      }

      // Generate context-aware suggestions if not provided
      let suggestedActions = data.suggestedActions;
      if (!suggestedActions || suggestedActions.length === 0) {
        if (data.tool_used?.includes('task')) {
          suggestedActions = ['Show my pending tasks', 'Plan my day'];
        } else if (data.tool_used?.includes('calc')) {
          suggestedActions = ['Show my pending tasks', 'Create a study task'];
        } else {
          suggestedActions = [
            'Create a task to study Python tomorrow',
            'Show my pending tasks',
            'Calculate 30 chapters over 6 days',
          ];
        }
      }

      return {
        response: data.response,
        tool_used: data.tool_used,
        created_task: createdTask,
        tool_calls: data.tool_calls || [],
        tool_results: data.tool_results || [],
        suggestedActions,
        success: data.success,
      };
    } catch (err: unknown) {
      // Propagate API, auth, validation, and network errors so caller handles them truthfully
      throw err;
    }
  },

  async processLocally(
    message: string,
    onStatusUpdate?: StatusUpdateCallback
  ): Promise<ChatResponse> {
    const text = message.trim();
    const lower = text.toLowerCase();

    // 1. Task Creation Intent
    if (
      lower.startsWith('create a task') ||
      lower.startsWith('create task') ||
      lower.startsWith('add task') ||
      lower.startsWith('new task') ||
      lower.includes('remind me to') ||
      lower.includes('todo:')
    ) {
      onStatusUpdate?.('Creating your task...');
      await new Promise((resolve) => setTimeout(resolve, 350));

      // Extract task title
      let title = text
        .replace(/^(create\s+a\s+task\s+to|create\s+task|add\s+task|new\s+task|remind\s+me\s+to|todo:?)/i, '')
        .trim();

      // Extract priority if mentioned
      let priority: TaskPriority = 'medium';
      if (lower.includes('urgent') || lower.includes('high priority')) {
        priority = 'high';
        title = title.replace(/(with\s+)?(urgent|high\s+priority)/i, '').trim();
      } else if (lower.includes('low priority')) {
        priority = 'low';
        title = title.replace(/(with\s+)?low\s+priority/i, '').trim();
      }

      // Extract due date if mentioned
      let dueDate = 'Today';
      if (lower.includes('tomorrow')) {
        dueDate = 'Tomorrow';
        title = title.replace(/tomorrow/i, '').trim();
      } else if (lower.includes('next week') || lower.includes('next monday')) {
        dueDate = 'Next Week';
        title = title.replace(/(next\s+week|next\s+monday)/i, '').trim();
      } else if (lower.includes('friday') || lower.includes('this weekend')) {
        dueDate = 'Friday';
        title = title.replace(/(friday|this\s+weekend)/i, '').trim();
      }

      // Clean up title
      title = title.replace(/^to\s+/i, '').replace(/[.,!]+$/, '').trim();
      if (!title) {
        title = 'New Task';
      }
      title = title.charAt(0).toUpperCase() + title.slice(1);

      // Categorize
      let category = 'General';
      if (/study|read|learn|python|course|exam|chapter/i.test(title)) category = 'Study';
      else if (/work|slide|presentation|meeting|email|client|deploy|code/i.test(title)) category = 'Work';
      else if (/workout|run|gym|meditate|walk|sleep/i.test(title)) category = 'Health';
      else if (/buy|grocery|shop|call|dinner|home/i.test(title)) category = 'Personal';

      const created = await taskService.createTask({
        title,
        description: 'Created via TaskMate AI Assistant',
        due_date: dueDate,
        priority,
        category,
      });

      return {
        response: `Sure! I've created "${created.title}" scheduled for ${dueDate.toLowerCase() === 'today' ? 'today' : dueDate} with ${priority} priority.`,
        tool_used: 'task_tool',
        created_task: created,
        suggestedActions: [
          'Show my pending tasks',
          'Plan my day',
          'Mark a task as completed',
        ],
        success: true,
      };
    }

    // 2. Query Pending / Active Tasks
    if (
      lower.includes('pending') ||
      lower.includes('show my tasks') ||
      lower.includes('what are my tasks') ||
      lower.includes('list tasks') ||
      lower.includes('what should i work on')
    ) {
      onStatusUpdate?.('Checking your tasks...');
      await new Promise((resolve) => setTimeout(resolve, 300));

      const tasks = taskService.getTasks();
      const pendingTasks = tasks.filter((t) => t.status !== 'completed');

      if (pendingTasks.length === 0) {
        return {
          response: "You don't have any pending tasks right now! You're all caught up. Would you like to create a new task?",
          tool_used: 'task_tool',
          suggestedActions: ['Create a task to study Python', 'Plan tomorrow'],
          success: true,
        };
      }

      const taskListStr = pendingTasks
        .slice(0, 4)
        .map((t, idx) => `${idx + 1}. **${t.title}** (${t.priority} priority, due ${t.due_date || 'soon'})`)
        .join('\n');

      const highPriority = pendingTasks.filter((t) => t.priority === 'high');
      const focusRecommendation =
        highPriority.length > 0
          ? `I recommend focusing first on **"${highPriority[0].title}"** as it has high priority.`
          : `You have **${pendingTasks.length} pending tasks** in your workspace.`;

      return {
        response: `You have ${pendingTasks.length} pending ${pendingTasks.length === 1 ? 'task' : 'tasks'}:\n\n${taskListStr}\n\n${focusRecommendation}`,
        tool_used: 'task_tool',
        suggestedActions: [
          'Plan my day',
          'Mark a task as completed',
          'Add a new task',
        ],
        success: true,
      };
    }

    // 3. Planning the Day
    if (lower.includes('plan my day') || lower.includes('daily plan') || lower.includes('schedule')) {
      onStatusUpdate?.('Organizing your schedule...');
      await new Promise((resolve) => setTimeout(resolve, 350));

      const tasks = taskService.getTasks();
      const pending = tasks.filter((t) => t.status !== 'completed');
      const high = pending.filter((t) => t.priority === 'high');
      const medium = pending.filter((t) => t.priority === 'medium');

      return {
        response: `Here is a productive breakdown for your day:
• **Morning Focus (Peak energy)**: Tackle high-priority items like ${high[0] ? `"${high[0].title}"` : 'your primary goal'}.
• **Mid-day**: Handle scheduled syncs and administrative tasks ${medium[0] ? `(e.g., "${medium[0].title}")` : ''}.
• **Afternoon**: Wrap up review items and plan for tomorrow.

Would you like me to add a quick break reminder or adjust any task due dates?`,
        tool_used: 'planning_tool',
        suggestedActions: ['Show my pending tasks', 'Create a task', 'What should I work on today?'],
        success: true,
      };
    }

    // 4. Calculations
    if (
      lower.includes('calculate') ||
      /\d+\s*(chapters?|pages?|tasks?|hours?)\s*(over|in|divided by)\s*\d+\s*(days?|weeks?)/i.test(lower) ||
      /\d+\s*[\+\-\*\/]\s*\d+/.test(lower)
    ) {
      onStatusUpdate?.('Calculating plan...');
      await new Promise((resolve) => setTimeout(resolve, 250));

      const chapterMatch = lower.match(/(\d+)\s*(?:chapters?|pages?|tasks?|items?)\s*(?:over|in|across)\s*(\d+)\s*(?:days?|weeks?)/i);
      if (chapterMatch) {
        const totalItems = parseInt(chapterMatch[1], 10);
        const totalUnits = parseInt(chapterMatch[2], 10);
        const perUnit = Math.ceil(totalItems / totalUnits);
        return {
          response: `That comes out to **${perUnit} per day** (${totalItems} total divided by ${totalUnits} days). Would you like me to create daily recurring study tasks for this?`,
          tool_used: 'calculator_tool',
          suggestedActions: [
            `Create a task: Complete ${perUnit} chapters today`,
            'Show my pending tasks',
          ],
          success: true,
        };
      }

      // Safe arithmetic evaluator
      try {
        const mathClean = lower.replace(/calculate/i, '').replace(/[^0-9+\-*/().]/g, '');
        if (mathClean) {
          const sanitized = mathClean.replace(/[^0-9+\-*/.]/g, '');
          const res = Function(`'use strict'; return (${sanitized})`)();
          return {
            response: `The calculation result is: **${res}**. Let me know if you want to apply this to a task budget or timeline!`,
            tool_used: 'calculator_tool',
            success: true,
          };
        }
      } catch {
        // Fall through
      }
    }

    // 5. Default response
    onStatusUpdate?.('Thinking...');
    await new Promise((resolve) => setTimeout(resolve, 300));

    return {
      response: `I'm here to keep your workload organized and manageable! You can ask me to:
• **"Create a task to study Python tomorrow"**
• **"Show my pending tasks"**
• **"Plan my day"**
• **"Calculate 20 chapters over 5 days"**

What would you like to achieve right now?`,
      suggestedActions: [
        'Create a task to study Python tomorrow',
        'Show my pending tasks',
        'Plan my day',
      ],
      success: true,
    };
  },
};
