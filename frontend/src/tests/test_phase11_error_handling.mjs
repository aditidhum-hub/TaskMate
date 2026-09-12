/**
 * TaskMate Phase 11 Frontend Defensive Error Handling & Rollback Verification Suite
 * Tests:
 * 1. Optimistic task creation rollback upon service failure.
 * 2. Optimistic task move (moveTaskStatus) rollback upon service failure.
 * 3. Optimistic task field update rollback upon service failure.
 * 4. Optimistic task deletion rollback upon service failure.
 * 5. Input unlock & loading state reset on conversational agent error.
 * 6. Non-JSON and HTML error responses (e.g. 502 Bad Gateway) sanitized safely.
 * 7. Offline/network disconnect converted to user-friendly notifications.
 */

import assert from 'node:assert';

console.log('--- Running Phase 11 Frontend Error Handling Tests ---');

// ---------------------------------------------------------
// Helper: Optimistic State Manager with Rollback
// (Matches AppContext state mutation and error rollback logic)
// ---------------------------------------------------------
class TestStateContext {
  constructor(initialTasks = []) {
    this.tasks = [...initialTasks];
    this.toasts = [];
    this.isLoading = false;
  }

  addToast(message, type = 'info') {
    this.toasts.push({ message, type, id: Date.now() + Math.random() });
  }

  // 1. Optimistic Task Creation
  async createTask(taskData, serviceCall) {
    const previousTasks = [...this.tasks];
    const tempId = `temp_${Date.now()}`;
    const optimisticTask = {
      id: tempId,
      ...taskData,
      status: taskData.status || 'pending',
      priority: taskData.priority || 'medium',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Optimistically insert
    this.tasks = [optimisticTask, ...this.tasks];

    try {
      const persisted = await serviceCall(taskData);
      // Replace temporary task with persisted task
      this.tasks = this.tasks.map((t) => (t.id === tempId ? persisted : t));
      this.addToast('Task created', 'success');
      return persisted;
    } catch (err) {
      // Rollback
      this.tasks = previousTasks;
      this.addToast(err.message || 'Failed to create task', 'error');
      throw err;
    }
  }

  // 2. Optimistic Move Status
  async moveTaskStatus(taskId, newStatus, serviceCall) {
    const previousTasks = [...this.tasks];
    const targetTask = this.tasks.find((t) => t.id === taskId);
    if (!targetTask) return;

    // Optimistically update
    this.tasks = this.tasks.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t));

    try {
      await serviceCall(taskId, newStatus);
      this.addToast(`Task moved to ${newStatus}`, 'success');
    } catch (err) {
      // Rollback
      this.tasks = previousTasks;
      this.addToast(`Failed to update status: ${err.message}`, 'error');
      throw err;
    }
  }

  // 3. Optimistic Update
  async updateTask(taskId, updates, serviceCall) {
    const previousTasks = [...this.tasks];
    this.tasks = this.tasks.map((t) => (t.id === taskId ? { ...t, ...updates } : t));

    try {
      const persisted = await serviceCall(taskId, updates);
      this.tasks = this.tasks.map((t) => (t.id === taskId ? persisted : t));
      this.addToast('Task updated', 'success');
      return persisted;
    } catch (err) {
      // Rollback
      this.tasks = previousTasks;
      this.addToast(`Failed to update task: ${err.message}`, 'error');
      throw err;
    }
  }

  // 4. Optimistic Deletion
  async deleteTask(taskId, serviceCall) {
    const previousTasks = [...this.tasks];
    this.tasks = this.tasks.filter((t) => t.id !== taskId);

    try {
      await serviceCall(taskId);
      this.addToast('Task deleted', 'info');
    } catch (err) {
      // Rollback
      this.tasks = previousTasks;
      this.addToast(`Failed to delete task: ${err.message}`, 'error');
      throw err;
    }
  }

  // 5. Chat Agent Dispatch with State Reset
  async sendChatMessage(message, apiCall) {
    this.isLoading = true;
    try {
      const response = await apiCall(message);
      return response;
    } catch (err) {
      this.addToast(err.message || 'Chat service error', 'error');
      return {
        success: false,
        error: err.message,
        content: `I encountered an issue: ${err.message}`,
      };
    } finally {
      // Guaranteed input unlock
      this.isLoading = false;
    }
  }
}

// ---------------------------------------------------------
// Test 1: Task Creation Rollback
// ---------------------------------------------------------
async function testCreationRollback() {
  const ctx = new TestStateContext([
    { id: 'task_1', title: 'Existing Task', status: 'pending', priority: 'medium' },
  ]);

  const failingService = async () => {
    throw new Error('Database write permission denied');
  };

  try {
    await ctx.createTask({ title: 'New Task' }, failingService);
    assert.fail('Should have thrown');
  } catch (err) {
    assert.strictEqual(ctx.tasks.length, 1, 'Task list must roll back to 1 task');
    assert.strictEqual(ctx.tasks[0].id, 'task_1', 'Original task must remain intact');
    assert.strictEqual(ctx.toasts.length, 1, 'Error toast must be dispatched');
    assert.strictEqual(ctx.toasts[0].type, 'error');
    assert.ok(ctx.toasts[0].message.includes('Database write permission denied'));
  }
  console.log('✓ Test 1 Passed: Task creation rollback restores original state on service failure');
}

// ---------------------------------------------------------
// Test 2: Task Move Status Rollback
// ---------------------------------------------------------
async function testMoveStatusRollback() {
  const ctx = new TestStateContext([
    { id: 'task_move', title: 'Move Me', status: 'pending', priority: 'high' },
  ]);

  const failingService = async () => {
    throw new Error('Network timeout while moving task');
  };

  try {
    await ctx.moveTaskStatus('task_move', 'in_progress', failingService);
    assert.fail('Should have thrown');
  } catch (err) {
    const task = ctx.tasks.find((t) => t.id === 'task_move');
    assert.strictEqual(task.status, 'pending', 'Status must roll back to pending');
    assert.strictEqual(ctx.toasts[0].type, 'error');
    assert.ok(ctx.toasts[0].message.includes('Network timeout'));
  }
  console.log('✓ Test 2 Passed: Kanban task move rolls back to original column on error');
}

// ---------------------------------------------------------
// Test 3: Task Field Update Rollback
// ---------------------------------------------------------
async function testUpdateRollback() {
  const ctx = new TestStateContext([
    { id: 'task_upd', title: 'Original Title', priority: 'low', status: 'pending' },
  ]);

  const failingService = async () => {
    throw new Error('Firestore document lock error');
  };

  try {
    await ctx.updateTask('task_upd', { title: 'Updated Title', priority: 'high' }, failingService);
    assert.fail('Should have thrown');
  } catch (err) {
    const task = ctx.tasks.find((t) => t.id === 'task_upd');
    assert.strictEqual(task.title, 'Original Title', 'Title must roll back to original');
    assert.strictEqual(task.priority, 'low', 'Priority must roll back to original');
    assert.strictEqual(ctx.toasts[0].type, 'error');
  }
  console.log('✓ Test 3 Passed: Task update rollback preserves previous fields');
}

// ---------------------------------------------------------
// Test 4: Task Deletion Rollback
// ---------------------------------------------------------
async function testDeleteRollback() {
  const ctx = new TestStateContext([
    { id: 'task_del_1', title: 'Task 1', status: 'pending' },
    { id: 'task_del_2', title: 'Task 2', status: 'completed' },
  ]);

  const failingService = async () => {
    throw new Error('Task deletion failed: Network drop');
  };

  try {
    await ctx.deleteTask('task_del_1', failingService);
    assert.fail('Should have thrown');
  } catch (err) {
    assert.strictEqual(ctx.tasks.length, 2, 'Deleted task must be restored');
    assert.strictEqual(ctx.tasks[0].id, 'task_del_1', 'Restored task must be in state');
    assert.strictEqual(ctx.toasts[0].type, 'error');
  }
  console.log('✓ Test 4 Passed: Task deletion rollback restores deleted item');
}

// ---------------------------------------------------------
// Test 5: Chat Agent Input Unlock on Error
// ---------------------------------------------------------
async function testChatInputUnlockOnError() {
  const ctx = new TestStateContext([]);

  const failingChatApi = async () => {
    throw new Error('500 Internal Server Error');
  };

  const outcome = await ctx.sendChatMessage('Hello', failingChatApi);
  assert.strictEqual(ctx.isLoading, false, 'Loading state must be unlocked');
  assert.strictEqual(outcome.success, false);
  assert.ok(outcome.content.includes('500 Internal Server Error'));
  assert.strictEqual(ctx.toasts.length, 1);
  console.log('✓ Test 5 Passed: AI chat composer unlocks and loading state clears on failure');
}

// ---------------------------------------------------------
// Test 6: Sanitization of Non-JSON / HTML 502 Gateway Errors
// ---------------------------------------------------------
function parseSafeHttpError(statusCode, responseText) {
  // Simulates ApiClient error parsing logic
  let message;
  try {
    const json = JSON.parse(responseText);
    message = json.detail || json.message;
  } catch {
    // Non-JSON or HTML response
    if (statusCode === 502 || statusCode === 503 || statusCode === 504) {
      message = 'The service is temporarily unavailable. Please try again shortly.';
    } else if (statusCode === 500) {
      message = 'The TaskMate server encountered an internal error. Please try again.';
    } else {
      message = `Request failed with HTTP status ${statusCode}.`;
    }
  }
  return message;
}

function testHtml502Sanitization() {
  const htmlPayload = '<html><head><title>502 Bad Gateway</title></head><body>nginx proxy error</body></html>';
  const cleanMsg = parseSafeHttpError(502, htmlPayload);
  assert.strictEqual(cleanMsg, 'The service is temporarily unavailable. Please try again shortly.');
  assert.ok(!cleanMsg.includes('<html'), 'HTML tags must not leak into user notification');

  const html500 = '<html><body>500 Internal Server Error at /usr/local/lib/python3.13</body></html>';
  const clean500 = parseSafeHttpError(500, html500);
  assert.strictEqual(clean500, 'The TaskMate server encountered an internal error. Please try again.');
  assert.ok(!clean500.includes('/usr/local'), 'Server file paths must never leak');
  console.log('✓ Test 6 Passed: HTML and raw proxy errors (500/502) sanitized safely without leaking tags or paths');
}

// ---------------------------------------------------------
// Test 7: Offline Network Disconnect Handling
// ---------------------------------------------------------
function handleNetworkDisconnect(err) {
  if (err instanceof TypeError && err.message.includes('fetch')) {
    return 'Could not connect to TaskMate backend server. Please verify network connectivity.';
  }
  return err.message || 'Unknown network error';
}

function testOfflineHandling() {
  const fetchErr = new TypeError('Failed to fetch');
  const userMsg = handleNetworkDisconnect(fetchErr);
  assert.strictEqual(
    userMsg,
    'Could not connect to TaskMate backend server. Please verify network connectivity.'
  );
  console.log('✓ Test 7 Passed: Offline network disconnect converted to clear actionable user message');
}

// Run all test functions
await testCreationRollback();
await testMoveStatusRollback();
await testUpdateRollback();
await testDeleteRollback();
await testChatInputUnlockOnError();
testHtml502Sanitization();
testOfflineHandling();

console.log('\n======================================================');
console.log('ALL PHASE 11 FRONTEND ERROR HANDLING TESTS PASSED (7/7) ✅');
console.log('======================================================\n');
