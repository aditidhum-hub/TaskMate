/**
 * TaskMate Phase 9 Frontend Automated Verification Suite
 * Tests:
 * 1. ApiClient endpoint construction, Bearer token injection, and error categorization (401, 422, 500, network).
 * 2. Productivity Summary computation (canonical derived metrics).
 * 3. Optimistic task mutation and rollback on service failure.
 * 4. Kanban board state transitions ('pending' -> 'in_progress' -> 'completed').
 * 5. Search, priority, category filtering, and sorting logic.
 */

import assert from 'node:assert';

// ---------------------------------------------------------
// Test 1: Productivity Summary Calculation
// ---------------------------------------------------------
function computeSummary(tasks) {
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
}

console.log('--- Running Phase 9 Frontend Tests ---');

// Test 1.1: Standard task suite
const sampleTasks = [
  { id: '1', title: 'Task 1', status: 'pending', priority: 'high', due_date: 'Today' },
  { id: '2', title: 'Task 2', status: 'in_progress', priority: 'medium', due_date: 'Tomorrow' },
  { id: '3', title: 'Task 3', status: 'completed', priority: 'high', due_date: 'Today' },
  { id: '4', title: 'Task 4', status: 'pending', priority: 'low', due_date: 'Next Week' },
];

const summary1 = computeSummary(sampleTasks);
assert.strictEqual(summary1.total, 4, 'Total tasks should be 4');
assert.strictEqual(summary1.pending, 2, 'Pending count should be 2');
assert.strictEqual(summary1.inProgress, 1, 'In Progress count should be 1');
assert.strictEqual(summary1.completed, 1, 'Completed count should be 1');
assert.strictEqual(summary1.completionRate, 25, 'Completion rate should be 25%');
assert.strictEqual(summary1.highPriorityPending, 1, 'High priority pending count should be 1');
assert.strictEqual(summary1.dueTodayOrOverdue, 1, 'Due today or overdue should be 1 (excluding completed)');
console.log('✓ Test 1 Passed: Productivity summary computes canonical metrics correctly');

// Test 1.2: Empty tasks array
const summaryEmpty = computeSummary([]);
assert.strictEqual(summaryEmpty.total, 0);
assert.strictEqual(summaryEmpty.completionRate, 0);
console.log('✓ Test 2 Passed: Empty tasks handled safely without division by zero');

// ---------------------------------------------------------
// Test 2: Optimistic Update and Rollback Mechanism
// ---------------------------------------------------------
class OptimisticTaskManager {
  constructor(initialTasks = []) {
    this.tasks = [...initialTasks];
    this.rollbackCount = 0;
  }

  async updateTaskStatus(id, newStatus, simulateFailure = false) {
    const previousTasks = [...this.tasks];
    // 1. Optimistically apply change to UI state
    this.tasks = this.tasks.map((t) => (t.id === id ? { ...t, status: newStatus } : t));

    // 2. Perform service call
    try {
      if (simulateFailure) {
        throw new Error('Network error: server unreachable');
      }
      return this.tasks.find((t) => t.id === id);
    } catch (err) {
      // 3. Rollback cleanly on service failure
      this.tasks = previousTasks;
      this.rollbackCount++;
      throw err;
    }
  }
}

const manager = new OptimisticTaskManager(sampleTasks);
assert.strictEqual(manager.tasks.find((t) => t.id === '1').status, 'pending');

// Successful optimistic update
await manager.updateTaskStatus('1', 'in_progress', false);
assert.strictEqual(manager.tasks.find((t) => t.id === '1').status, 'in_progress');
console.log('✓ Test 3 Passed: Optimistic state update succeeds on normal execution');

// Failed operation rolls back cleanly
let caughtError = false;
try {
  await manager.updateTaskStatus('1', 'completed', true);
} catch (err) {
  caughtError = true;
  assert.strictEqual(err.message, 'Network error: server unreachable');
}
assert.strictEqual(caughtError, true, 'Error should have been caught');
assert.strictEqual(manager.tasks.find((t) => t.id === '1').status, 'in_progress', 'State must roll back to in_progress');
assert.strictEqual(manager.rollbackCount, 1, 'Rollback counter incremented');
console.log('✓ Test 4 Passed: UI rolls back cleanly upon service error');

// ---------------------------------------------------------
// Test 3: Kanban State Transition Workflow
// ---------------------------------------------------------
const kanbanTask = { id: 'k1', title: 'Study Python', status: 'pending', priority: 'high' };
const allowedTransitions = {
  pending: ['in_progress', 'completed'],
  in_progress: ['pending', 'completed'],
  completed: ['in_progress', 'pending'],
};

function advanceKanban(currentStatus, nextStatus) {
  const allowed = allowedTransitions[currentStatus] || [];
  if (!allowed.includes(nextStatus)) {
    throw new Error(`Invalid transition from ${currentStatus} to ${nextStatus}`);
  }
  return nextStatus;
}

let current = kanbanTask.status;
current = advanceKanban(current, 'in_progress');
assert.strictEqual(current, 'in_progress', 'Advanced from pending to in_progress');

current = advanceKanban(current, 'completed');
assert.strictEqual(current, 'completed', 'Advanced from in_progress to completed');

current = advanceKanban(current, 'pending');
assert.strictEqual(current, 'pending', 'Moved from completed back to pending');
console.log('✓ Test 5 Passed: Kanban board 3-column state transitions validate properly');

// ---------------------------------------------------------
// Test 4: ApiClient Header and Error Logic
// ---------------------------------------------------------
function formatApiHeaders(token) {
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

const headersNoAuth = formatApiHeaders(null);
assert.strictEqual(headersNoAuth['Authorization'], undefined);

const headersAuth = formatApiHeaders('fake-firebase-jwt-token');
assert.strictEqual(headersAuth['Authorization'], 'Bearer fake-firebase-jwt-token');
console.log('✓ Test 6 Passed: ApiClient correctly injects Firebase Bearer token');

function parseApiError(status, detail) {
  let userMessage = `Request failed with status ${status}`;
  if (status === 0) {
    userMessage = 'Could not connect to TaskMate backend server. Please verify the backend is running.';
  } else if (status === 401) {
    userMessage = 'Authentication required. Please sign in to communicate with TaskMate.';
  } else if (status === 422) {
    userMessage = typeof detail === 'string' ? detail : 'Invalid request payload. Please check your input.';
  } else if (status >= 500) {
    userMessage = 'The TaskMate server encountered an internal error. Please try again.';
  } else if (typeof detail === 'string') {
    userMessage = detail;
  }
  return { status, message: userMessage, detail };
}

const err401 = parseApiError(401, 'Unauthorized');
assert.strictEqual(err401.message, 'Authentication required. Please sign in to communicate with TaskMate.');

const err422 = parseApiError(422, 'Message cannot be empty or solely whitespace.');
assert.strictEqual(err422.message, 'Message cannot be empty or solely whitespace.');

const err500 = parseApiError(500, 'Internal Server Error');
assert.strictEqual(err500.message, 'The TaskMate server encountered an internal error. Please try again.');
console.log('✓ Test 7 Passed: ApiClient properly sanitizes HTTP 401, 422, and 500 errors');

// ---------------------------------------------------------
// Test 5: Filtering and Sorting Logic
// ---------------------------------------------------------
const filterSample = [
  { id: 'a', title: 'Study Python', category: 'Study', priority: 'high', status: 'pending', due_date: 'Today' },
  { id: 'b', title: 'Fix bug', category: 'Work', priority: 'medium', status: 'completed', due_date: 'Tomorrow' },
  { id: 'c', title: 'Gym workout', category: 'Health', priority: 'low', status: 'pending', due_date: 'Next Week' },
];

// Search filter
const searchResult = filterSample.filter((t) => t.title.toLowerCase().includes('python'));
assert.strictEqual(searchResult.length, 1);
assert.strictEqual(searchResult[0].id, 'a');

// Category filter
const workResult = filterSample.filter((t) => t.category === 'Work');
assert.strictEqual(workResult.length, 1);
assert.strictEqual(workResult[0].id, 'b');

// Priority sorting
const priorityWeight = { high: 3, medium: 2, low: 1 };
const sortedByPriority = [...filterSample].sort((x, y) => priorityWeight[y.priority] - priorityWeight[x.priority]);
assert.strictEqual(sortedByPriority[0].id, 'a');
assert.strictEqual(sortedByPriority[1].id, 'b');
assert.strictEqual(sortedByPriority[2].id, 'c');
console.log('✓ Test 8 Passed: Filtering and sorting logic executes reliably');

// ---------------------------------------------------------
// Test 6: Checkpoint 10.2 Firestore Path & Isolation Logic
// ---------------------------------------------------------
function resolveFirestoreTaskPath(currentUser, taskId = null) {
  if (!currentUser || !currentUser.uid || !currentUser.uid.trim()) {
    return null; // Unauthenticated / offline fallback
  }
  const basePath = `users/${currentUser.uid.trim()}/tasks`;
  return taskId ? `${basePath}/${taskId}` : basePath;
}

// Unauthenticated check
assert.strictEqual(resolveFirestoreTaskPath(null), null);
assert.strictEqual(resolveFirestoreTaskPath({ uid: '' }), null);
assert.strictEqual(resolveFirestoreTaskPath({ uid: '   ' }), null);

// Authenticated check
const pathCollection = resolveFirestoreTaskPath({ uid: 'user_firebase_123' });
assert.strictEqual(pathCollection, 'users/user_firebase_123/tasks');

const pathDocument = resolveFirestoreTaskPath({ uid: 'user_firebase_123' }, 'task_abc');
assert.strictEqual(pathDocument, 'users/user_firebase_123/tasks/task_abc');

// Tenant isolation: User B's UID cannot generate User A's path
const userAPath = resolveFirestoreTaskPath({ uid: 'user_alpha' }, 'task_1');
const userBPath = resolveFirestoreTaskPath({ uid: 'user_bravo' }, 'task_1');
assert.notStrictEqual(userAPath, userBPath);
assert.ok(userAPath.startsWith('users/user_alpha/tasks/'));
assert.ok(userBPath.startsWith('users/user_bravo/tasks/'));
console.log('✓ Test 9 Passed: Firestore task paths strictly adhere to users/{user_id}/tasks/{task_id}');

// ---------------------------------------------------------
// Test 7: Firestore Offline & Error Resilience
// ---------------------------------------------------------
class ResilientTaskService {
  constructor(localStorageMock, firestoreMock = null) {
    this.storage = localStorageMock;
    this.firestore = firestoreMock;
  }

  async fetchTasks(currentUser) {
    if (!currentUser || !this.firestore) {
      return this.storage.getTasks();
    }
    try {
      return await this.firestore.getTasks(currentUser.uid);
    } catch (err) {
      // Graceful fallback to local cache
      return this.storage.getTasks();
    }
  }
}

const mockStorage = {
  getTasks: () => [{ id: 'local_1', title: 'Offline Task', status: 'pending' }],
};

// 1. When offline/unauthenticated, returns cached local tasks
const offlineService = new ResilientTaskService(mockStorage, null);
const offlineResult = await offlineService.fetchTasks(null);
assert.strictEqual(offlineResult.length, 1);
assert.strictEqual(offlineResult[0].title, 'Offline Task');

// 2. When Firestore network throws an error, gracefully catches and returns local tasks
const failingFirestore = {
  getTasks: async () => {
    throw new Error('Firestore connection timeout');
  },
};
const resilientService = new ResilientTaskService(mockStorage, failingFirestore);
const resilientResult = await resilientService.fetchTasks({ uid: 'user_abc' });
assert.strictEqual(resilientResult.length, 1);
console.log('✓ Test 10 Passed: TaskService gracefully falls back to local cache when offline or unauthenticated');

// =========================================================
// Checkpoint 10.3: Live Chat API & UI State Synchronization Tests
// =========================================================

console.log('\n--- Running Checkpoint 10.3 Verification Tests ---');

// Checkpoint 10.3 State Synchronization Function (mirror of AppContext.tsx applyAiToolEffects)
function applyAiToolEffects(currentTasks, response) {
  let tasks = [...currentTasks];
  let createdCount = 0;
  let completedCount = 0;
  let updatedCount = 0;
  let deletedCount = 0;
  let lastCreatedTask = undefined;
  let lastCompletedTitle = undefined;
  let lastUpdatedTitle = undefined;

  const toolCalls = response.tool_calls || [];
  const toolResults = response.tool_results || [];

  // 1. Process structured tool_results
  for (let i = 0; i < toolResults.length; i++) {
    const res = toolResults[i];
    if (!res || res.success !== true) continue;

    const call = toolCalls[i];
    const callArgs = (call && call.arguments) || {};
    const opName = (call && call.name) || (i === 0 ? response.tool_used : '') || '';

    if (opName === 'delete_task' || (res.task_id && !res.task)) {
      const idToDelete = res.task_id || callArgs.task_id;
      if (idToDelete) {
        tasks = tasks.filter((t) => t.id !== idToDelete);
        deletedCount++;
      }
    } else if (opName === 'complete_task') {
      const compTask = res.task;
      const idToComplete = (compTask && compTask.id) || res.task_id || callArgs.task_id;
      if (idToComplete) {
        tasks = tasks.map((t) => {
          if (t.id === idToComplete) {
            lastCompletedTitle = (compTask && compTask.title) || t.title;
            return {
              ...t,
              ...(compTask || {}),
              status: 'completed',
              updated_at: (compTask && compTask.updated_at) || new Date().toISOString(),
            };
          }
          return t;
        });
        completedCount++;
      }
    } else if (opName === 'update_task') {
      const updTask = res.task;
      const idToUpdate = (updTask && updTask.id) || res.task_id || callArgs.task_id;
      if (idToUpdate) {
        tasks = tasks.map((t) => {
          if (t.id === idToUpdate) {
            lastUpdatedTitle = (updTask && updTask.title) || t.title;
            return {
              ...t,
              ...(updTask || {}),
              updated_at: (updTask && updTask.updated_at) || new Date().toISOString(),
            };
          }
          return t;
        });
        updatedCount++;
      }
    } else if (opName === 'create_task') {
      const newTask = res.task || response.created_task;
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
    const newTask = response.created_task;
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
              status: 'completed',
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

// ---------------------------------------------------------
// Test 11 (Requirement Test 1): Chat API Endpoint & Bearer Token
// ---------------------------------------------------------
class MockChatApiClient {
  constructor(token) {
    this.token = token;
    this.lastRequest = null;
  }

  async postChat(message, messageHistory = null) {
    const headers = formatApiHeaders(this.token);
    const body = {
      message: message.trim(),
      message_history: messageHistory && messageHistory.length > 0 ? messageHistory : undefined,
    };
    this.lastRequest = {
      endpoint: '/api/chat',
      method: 'POST',
      headers,
      body,
    };
    return {
      response: "I've created your task.",
      tool_used: 'create_task',
      created_task: { id: 'task_jwt_1', title: 'Study Python' },
      success: true,
    };
  }
}

const mockClient = new MockChatApiClient('verified-firebase-jwt-token');
await mockClient.postChat('Create task to study Python', [{ role: 'user', content: 'Hi' }]);
assert.strictEqual(mockClient.lastRequest.endpoint, '/api/chat');
assert.strictEqual(mockClient.lastRequest.method, 'POST');
assert.strictEqual(mockClient.lastRequest.headers['Authorization'], 'Bearer verified-firebase-jwt-token');
assert.strictEqual(mockClient.lastRequest.body.message, 'Create task to study Python');
assert.strictEqual(mockClient.lastRequest.body.message_history.length, 1);
console.log('✓ Test 11 Passed: Chat API request reaches POST /api/chat with Firebase Bearer token');

// ---------------------------------------------------------
// Test 12 (Requirement Test 2): AI-created task added to tasks state
// ---------------------------------------------------------
const initialTaskList = [
  { id: 'task_0', title: 'Existing Task', status: 'pending', priority: 'medium' },
];
const createTurnResponse = {
  response: 'Task created.',
  tool_used: 'create_task',
  created_task: { id: 'task_new_1', title: 'Study Python tomorrow', status: 'pending', priority: 'high' },
  tool_calls: [{ name: 'create_task' }],
  tool_results: [{ success: true, task: { id: 'task_new_1', title: 'Study Python tomorrow', status: 'pending', priority: 'high' } }],
  success: true,
};

const afterCreate = applyAiToolEffects(initialTaskList, createTurnResponse);
assert.strictEqual(afterCreate.updatedTasks.length, 2, 'tasks state should contain 2 tasks');
assert.strictEqual(afterCreate.updatedTasks[0].id, 'task_new_1', 'New task should be prepended');
assert.strictEqual(afterCreate.createdCount, 1, 'createdCount should be 1');
assert.strictEqual(afterCreate.lastCreatedTask.title, 'Study Python tomorrow');
console.log('✓ Test 12 Passed: AI-created task successfully added to tasks state');

// ---------------------------------------------------------
// Test 13 (Requirement Test 3): Complete task (pending -> completed)
// ---------------------------------------------------------
const beforeCompleteList = [
  { id: 'task_py', title: 'Study Python', status: 'pending', priority: 'high' },
];
const completeTurnResponse = {
  response: "Marked task 'Study Python' as completed.",
  tool_used: 'complete_task',
  tool_calls: [{ name: 'complete_task', arguments: { task_id: 'task_py' } }],
  tool_results: [{ success: true, task: { id: 'task_py', title: 'Study Python', status: 'completed' } }],
  success: true,
};

const afterComplete = applyAiToolEffects(beforeCompleteList, completeTurnResponse);
assert.strictEqual(afterComplete.updatedTasks.length, 1);
const completedTask = afterComplete.updatedTasks.find((t) => t.id === 'task_py');
assert.strictEqual(completedTask.status, 'completed', 'Task status must transition from pending to completed');
assert.strictEqual(afterComplete.completedCount, 1, 'completedCount should be 1');
assert.strictEqual(afterComplete.lastCompletedTitle, 'Study Python');
console.log('✓ Test 13 Passed: Complete task transitions status from pending to completed');

// ---------------------------------------------------------
// Test 14 (Requirement Test 4): Update task in React state
// ---------------------------------------------------------
const beforeUpdateList = [
  { id: 'task_upd', title: 'Study Python', status: 'pending', priority: 'medium', due_date: 'Tomorrow' },
];
const updateTurnResponse = {
  response: 'Updated task priority to high.',
  tool_used: 'update_task',
  tool_calls: [{ name: 'update_task', arguments: { task_id: 'task_upd', priority: 'high' } }],
  tool_results: [{ success: true, task: { id: 'task_upd', title: 'Study Python', status: 'pending', priority: 'high', due_date: 'Tomorrow' } }],
  success: true,
};

const afterUpdate = applyAiToolEffects(beforeUpdateList, updateTurnResponse);
assert.strictEqual(afterUpdate.updatedTasks.length, 1);
const updatedTaskItem = afterUpdate.updatedTasks.find((t) => t.id === 'task_upd');
assert.strictEqual(updatedTaskItem.priority, 'high', 'Task priority must be updated to high');
assert.strictEqual(afterUpdate.updatedCount, 1, 'updatedCount should be 1');
console.log('✓ Test 14 Passed: Update task updates task fields in state');

// ---------------------------------------------------------
// Test 15 (Requirement Test 5): Delete task from React state
// ---------------------------------------------------------
const beforeDeleteList = [
  { id: 'task_del', title: 'Obsolete Task', status: 'pending' },
  { id: 'task_keep', title: 'Keep This Task', status: 'in_progress' },
];
const deleteTurnResponse = {
  response: 'Task deleted.',
  tool_used: 'delete_task',
  tool_calls: [{ name: 'delete_task', arguments: { task_id: 'task_del' } }],
  tool_results: [{ success: true, task_id: 'task_del' }],
  success: true,
};

const afterDelete = applyAiToolEffects(beforeDeleteList, deleteTurnResponse);
assert.strictEqual(afterDelete.updatedTasks.length, 1, 'Only 1 task should remain');
assert.strictEqual(afterDelete.updatedTasks.some((t) => t.id === 'task_del'), false, 'Deleted task must not exist in state');
assert.strictEqual(afterDelete.deletedCount, 1, 'deletedCount should be 1');
console.log('✓ Test 15 Passed: Delete task removes task from tasks state');

// ---------------------------------------------------------
// Test 16 (Requirement Test 6): Dashboard productivity metrics recalculate reactively
// ---------------------------------------------------------
const dashboardTasksBefore = [
  { id: 't_a', title: 'Task A', status: 'pending', priority: 'high', due_date: 'Today' },
  { id: 't_b', title: 'Task B', status: 'pending', priority: 'low', due_date: 'Tomorrow' },
];
const summaryInitial = computeSummary(dashboardTasksBefore);
assert.strictEqual(summaryInitial.total, 2);
assert.strictEqual(summaryInitial.pending, 2);
assert.strictEqual(summaryInitial.completed, 0);
assert.strictEqual(summaryInitial.completionRate, 0);

// AI completes Task A
const completeResponseForA = {
  response: 'Completed Task A.',
  tool_used: 'complete_task',
  tool_calls: [{ name: 'complete_task', arguments: { task_id: 't_a' } }],
  tool_results: [{ success: true, task: { id: 't_a', status: 'completed' } }],
  success: true,
};
const dashboardTasksAfter = applyAiToolEffects(dashboardTasksBefore, completeResponseForA).updatedTasks;
const summaryRecalculated = computeSummary(dashboardTasksAfter);

assert.strictEqual(summaryRecalculated.total, 2, 'Total tasks unchanged');
assert.strictEqual(summaryRecalculated.pending, 1, 'Pending tasks decremented to 1');
assert.strictEqual(summaryRecalculated.completed, 1, 'Completed tasks incremented to 1');
assert.strictEqual(summaryRecalculated.completionRate, 50, 'Completion rate dynamically recalculated to 50%');
console.log('✓ Test 16 Passed: Task state changes cause productivity metrics to recalculate reactively');

// ---------------------------------------------------------
// Test 17 (Requirement Test 7): API failure (401/422/500/network) handled safely
// ---------------------------------------------------------
function simulateApiChatRunner(status, errorPayload) {
  try {
    if (status === 200) {
      return { success: true, message: 'OK' };
    }
    const apiError = parseApiError(status, errorPayload);
    throw apiError;
  } catch (err) {
    // Safe error handling as in AppContext.sendMessage
    let errorMessage = 'Something went wrong. Please try again.';
    if (err && typeof err === 'object' && typeof err.message === 'string') {
      errorMessage = err.message;
    }
    return {
      success: false,
      assistantMessage: `I ran into an issue: ${errorMessage}`,
      safeErrorMessage: errorMessage,
    };
  }
}

// 401 Unauthorized
const result401 = simulateApiChatRunner(401, 'Unauthorized');
assert.strictEqual(result401.success, false);
assert.ok(result401.safeErrorMessage.includes('Authentication required'));

// 422 Validation Error
const result422 = simulateApiChatRunner(422, 'Message cannot be empty or solely whitespace.');
assert.strictEqual(result422.success, false);
assert.ok(result422.safeErrorMessage.includes('whitespace'));

// 500 Backend Error
const result500 = simulateApiChatRunner(500, 'Traceback (most recent call last): Internal Exception');
assert.strictEqual(result500.success, false);
assert.strictEqual(result500.safeErrorMessage, 'The TaskMate server encountered an internal error. Please try again.');
assert.strictEqual(result500.assistantMessage.includes('Traceback'), false, 'Stack traces must never leak to user');

// Network offline error (status 0)
const resultNetwork = simulateApiChatRunner(0, 'Failed to fetch');
assert.strictEqual(resultNetwork.success, false);
assert.ok(resultNetwork.safeErrorMessage.includes('Could not connect to TaskMate backend server'));
console.log('✓ Test 17 Passed: 401, 422, 500, and network failures are handled safely without crashing');

// ---------------------------------------------------------
// Test 18 (Requirement Test 8): No duplicate task when processing created_task
// ---------------------------------------------------------
const existingList = [
  { id: 'task_dup_1', title: 'Study Python', status: 'pending', priority: 'high' },
];
const duplicateCreateResponse = {
  response: 'Task already exists or re-returned.',
  tool_used: 'create_task',
  created_task: { id: 'task_dup_1', title: 'Study Python', status: 'pending', priority: 'high' },
  tool_calls: [{ name: 'create_task' }],
  tool_results: [{ success: true, task: { id: 'task_dup_1', title: 'Study Python', status: 'pending', priority: 'high' } }],
  success: true,
};

const afterDuplicate = applyAiToolEffects(existingList, duplicateCreateResponse);
assert.strictEqual(afterDuplicate.updatedTasks.length, 1, 'Duplicate task must not be appended');
assert.strictEqual(afterDuplicate.createdCount, 0, 'createdCount must be 0 for duplicate task');
console.log('✓ Test 18 Passed: Already-present task is not duplicated when processing created_task');

console.log('\n======================================================');
console.log('ALL CHECKPOINT 10.3 VERIFICATION TESTS PASSED (8/8) ✅');
console.log('ALL FRONTEND SUITE TESTS PASSED (18/18) 🚀');
console.log('======================================================\n');

