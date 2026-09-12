import React from 'react';
import { useApp } from '../../context/AppContext';
import { TaskCard } from '../tasks/TaskCard';
import {
  LayoutDashboard,
  CheckCircle2,
  Clock,
  Flame,
  TrendingUp,
  Sparkles,
  ArrowRight,
  ListTodo,
  Calendar,
  Layers,
} from 'lucide-react';

export const DashboardView: React.FC = () => {
  const {
    currentUser,
    tasks,
    summary,
    setActiveNavView,
    sendMessage,
    openNewTaskModal,
  } = useApp();

  const highPriorityTasks = tasks.filter(
    (t) => t.priority === 'high' && t.status !== 'completed'
  );

  const dueTodayTasks = tasks.filter((t) => {
    if (t.status === 'completed') return false;
    const due = (t.due_date || '').toLowerCase();
    return due === 'today' || due === 'tomorrow';
  });

  return (
    <div className="flex-1 overflow-y-auto max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Top Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-tr from-indigo-900 via-indigo-800 to-indigo-700 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 backdrop-blur-md text-indigo-100 border border-white/20">
            <Sparkles className="w-3.5 h-3.5 text-indigo-300" />
            <span>AI-Powered Productivity Hub</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome, {currentUser?.name || 'Friend'}!
          </h1>
          <p className="text-xs sm:text-sm text-indigo-100/90 leading-relaxed">
            You currently have{' '}
            <strong className="text-white underline decoration-indigo-300">
              {summary.pending} pending tasks
            </strong>{' '}
            and have finished{' '}
            <strong className="text-white underline decoration-emerald-300">
              {summary.completed} tasks
            </strong>
            . TaskMate is ready to help you plan your next moves.
          </p>

          <div className="pt-3 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => {
                setActiveNavView('workspace');
                sendMessage('Plan my day');
              }}
              className="px-4 py-2 rounded-xl bg-white text-indigo-900 text-xs font-bold shadow-xs hover:bg-indigo-50 transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Ask AI to Plan My Day</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveNavView('kanban')}
              className="px-4 py-2 rounded-xl bg-indigo-700/70 hover:bg-indigo-700 text-white text-xs font-semibold border border-white/20 transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Open Kanban Board</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveNavView('workspace')}
              className="px-4 py-2 rounded-xl bg-indigo-800/60 hover:bg-indigo-800 text-white text-xs font-semibold border border-white/20 transition-all cursor-pointer flex items-center gap-1.5"
            >
              <span>Two-Column Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Decorative background glow */}
        <div className="absolute -right-16 -bottom-16 w-80 h-80 rounded-full bg-indigo-500/20 blur-3xl pointer-events-none"></div>
      </div>

      {/* Strict Derived Productivity Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total */}
        <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-stone-500 text-xs font-medium">
            <span>Total Tasks</span>
            <ListTodo className="w-4 h-4 text-stone-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-stone-900">
            {summary.total}
          </div>
          <p className="text-[11px] text-stone-500">In your current workspace</p>
        </div>

        {/* Pending */}
        <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-amber-600 text-xs font-medium">
            <span>Pending</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-amber-600">
            {summary.pending}
          </div>
          <p className="text-[11px] text-stone-500">
            {summary.highPriorityPending} urgent / high priority
          </p>
        </div>

        {/* Completed */}
        <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-emerald-600 text-xs font-medium">
            <span>Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-emerald-600">
            {summary.completed}
          </div>
          <p className="text-[11px] text-stone-500">Accomplished milestones</p>
        </div>

        {/* Completion Rate */}
        <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-indigo-600 text-xs font-medium">
            <span>Completion Rate</span>
            <TrendingUp className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-indigo-600 font-mono">
            {summary.completionRate}%
          </div>
          <div className="w-full bg-stone-100 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-indigo-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${summary.completionRate}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Main Focus Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Urgent Priorities (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1 rounded-md bg-rose-50 text-rose-600">
                <Flame className="w-4 h-4" />
              </span>
              <h3 className="text-base font-bold text-stone-900">
                High Priority Focus
              </h3>
            </div>
            <button
              type="button"
              onClick={openNewTaskModal}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 cursor-pointer"
            >
              + Add Task
            </button>
          </div>

          <div className="space-y-3">
            {highPriorityTasks.length === 0 ? (
              <div className="p-6 rounded-2xl bg-white border border-stone-200 text-center space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                <p className="text-xs font-semibold text-stone-800">
                  No high-priority tasks pending!
                </p>
                <p className="text-[11px] text-stone-500">
                  You can tackle medium priority items or plan new milestones.
                </p>
              </div>
            ) : (
              highPriorityTasks.map((task) => <TaskCard key={task.id} task={task} />)
            )}
          </div>

          {/* Due Soon section */}
          {dueTodayTasks.length > 0 && (
            <div className="pt-4 space-y-3">
              <h4 className="text-xs font-bold text-stone-700 uppercase tracking-wider">
                Scheduled for Today & Tomorrow
              </h4>
              <div className="space-y-2">
                {dueTodayTasks.map((task) => (
                  <TaskCard key={task.id} task={task} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* AI Quick Automation Cards */}
        <div className="space-y-4">
          <h3 className="text-base font-bold text-stone-900 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>AI Actions</span>
          </h3>

          <div className="space-y-3">
            <button
              type="button"
              onClick={() => {
                setActiveNavView('workspace');
                sendMessage('Show my pending tasks');
              }}
              className="w-full p-4 rounded-2xl bg-white hover:bg-stone-50 border border-stone-200/80 text-left transition-all shadow-xs group cursor-pointer"
            >
              <p className="text-xs font-bold text-stone-900 group-hover:text-indigo-600 flex items-center justify-between">
                <span>Check Pending Tasks</span>
                <ArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
              </p>
              <p className="text-[11px] text-stone-500 mt-1">
                Ask TaskMate to audit active deadlines and recommend what to tackle first.
              </p>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveNavView('workspace');
                sendMessage('Create a task to study Python tomorrow');
              }}
              className="w-full p-4 rounded-2xl bg-white hover:bg-stone-50 border border-stone-200/80 text-left transition-all shadow-xs group cursor-pointer"
            >
              <p className="text-xs font-bold text-stone-900 group-hover:text-indigo-600 flex items-center justify-between">
                <span>Study Goal Assistant</span>
                <ArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
              </p>
              <p className="text-[11px] text-stone-500 mt-1">
                &ldquo;Create a task to study Python tomorrow&rdquo;
              </p>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveNavView('workspace');
                sendMessage('Calculate 20 chapters over 5 days');
              }}
              className="w-full p-4 rounded-2xl bg-white hover:bg-stone-50 border border-stone-200/80 text-left transition-all shadow-xs group cursor-pointer"
            >
              <p className="text-xs font-bold text-stone-900 group-hover:text-indigo-600 flex items-center justify-between">
                <span>Timeline Calculator</span>
                <ArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
              </p>
              <p className="text-[11px] text-stone-500 mt-1">
                &ldquo;Calculate 20 chapters over 5 days&rdquo;
              </p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
