import { Task, UserProfile, ChatMessage } from '../types';

export const INITIAL_USER: UserProfile = {
  id: 'user_tm_demo',
  name: 'Alex Morgan',
  email: 'alex.morgan@example.com',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
  preferences: {
    dailyGoal: 5,
    defaultPriority: 'medium',
  },
};

export const INITIAL_TASKS: Task[] = [
  {
    id: 'task-001',
    user_id: 'user_tm_demo',
    title: 'Study Python',
    description: 'Complete functions and modules practice with coding exercises.',
    priority: 'high',
    status: 'pending',
    due_date: 'Today',
    category: 'Study',
    created_at: '2026-09-10T10:00:00Z',
    updated_at: '2026-09-10T10:00:00Z',
  },
  {
    id: 'task-002',
    user_id: 'user_tm_demo',
    title: 'Finalize product launch slides',
    description: 'Add visual metrics and milestone roadmaps for the upcoming sprint demo.',
    priority: 'high',
    status: 'in_progress',
    due_date: 'Tomorrow',
    category: 'Work',
    created_at: '2026-09-09T14:30:00Z',
    updated_at: '2026-09-10T11:20:00Z',
  },
  {
    id: 'task-003',
    user_id: 'user_tm_demo',
    title: 'Schedule weekly team sync',
    description: 'Send calendar invites and agenda outline to engineering and design leads.',
    priority: 'medium',
    status: 'pending',
    due_date: 'Sep 14, 2026',
    category: 'Work',
    created_at: '2026-09-10T08:15:00Z',
    updated_at: '2026-09-10T08:15:00Z',
  },
  {
    id: 'task-004',
    user_id: 'user_tm_demo',
    title: 'Review user feedback on v1.2',
    description: 'Categorize top feature requests and summarize UX friction points.',
    priority: 'medium',
    status: 'in_progress',
    due_date: 'Sep 16, 2026',
    category: 'Work',
    created_at: '2026-09-08T16:00:00Z',
    updated_at: '2026-09-10T09:45:00Z',
  },
  {
    id: 'task-005',
    user_id: 'user_tm_demo',
    title: 'Morning 30-min run',
    description: 'Interval cardio training session in the neighborhood park.',
    priority: 'low',
    status: 'completed',
    due_date: 'Today',
    category: 'Health',
    created_at: '2026-09-10T06:30:00Z',
    updated_at: '2026-09-10T07:15:00Z',
  },
  {
    id: 'task-006',
    user_id: 'user_tm_demo',
    title: 'Prepare healthy grocery shopping list',
    description: 'Fresh fruits, greens, organic almond milk, and coffee beans.',
    priority: 'low',
    status: 'completed',
    due_date: 'Yesterday',
    category: 'Personal',
    created_at: '2026-09-09T18:00:00Z',
    updated_at: '2026-09-09T19:30:00Z',
  },
];

export const INITIAL_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-welcome-01',
    role: 'assistant',
    content: "Good morning! I'm TaskMate, your AI productivity assistant. I'm here to help you plan your day, create tasks, and stay on top of your priorities. What would you like to get done today?",
    timestamp: '2026-09-11T08:00:00Z',
    suggestedActions: [
      'Create a task to study Python tomorrow',
      'Show my pending tasks',
      'Plan my day',
      'Calculate 20 chapters over 5 days',
    ],
  },
];

export const SUGGESTED_PROMPT_CHIPS = [
  'Create a task',
  'Show my pending tasks',
  'Plan my day',
  'Calculate 20 chapters over 5 days',
  'What should I work on today?',
];
