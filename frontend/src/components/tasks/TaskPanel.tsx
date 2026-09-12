import React, { useMemo, useState } from 'react';
import { useApp } from '../../context/AppContext';
import { TaskCard } from './TaskCard';
import { KanbanBoard } from './KanbanBoard';
import { Task, TaskPriority, TaskStatus } from '../../types';
import {
  Plus,
  Search,
  CheckCircle2,
  Clock,
  Filter,
  Layers,
  Sparkles,
  ListTodo,
  X,
  ArrowUpDown,
  LayoutGrid,
  List,
} from 'lucide-react';

export const TaskPanel: React.FC = () => {
  const {
    tasks,
    summary,
    filters,
    setFilters,
    resetFilters,
    openNewTaskModal,
    sendMessage,
  } = useApp();

  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');

  // Filter and sort logic
  const filteredAndSortedTasks = useMemo(() => {
    const result = tasks.filter((task) => {
      // Status filter
      if (filters.status !== 'all' && task.status !== filters.status) {
        return false;
      }
      // Priority filter
      if (filters.priority !== 'all' && task.priority !== filters.priority) {
        return false;
      }
      // Category filter
      if (filters.category !== 'all' && task.category !== filters.category) {
        return false;
      }
      // Search query
      if (filters.search.trim()) {
        const q = filters.search.toLowerCase();
        const matchesTitle = task.title.toLowerCase().includes(q);
        const matchesDesc = (task.description || '').toLowerCase().includes(q);
        const matchesCat = (task.category || '').toLowerCase().includes(q);
        if (!matchesTitle && !matchesDesc && !matchesCat) return false;
      }
      return true;
    });

    // Sorting
    const priorityWeight: Record<TaskPriority, number> = { high: 3, medium: 2, low: 1 };

    result.sort((a, b) => {
      let comparison = 0;
      if (filters.sortBy === 'priority') {
        comparison = (priorityWeight[b.priority] || 0) - (priorityWeight[a.priority] || 0);
      } else if (filters.sortBy === 'title') {
        comparison = a.title.localeCompare(b.title);
      } else if (filters.sortBy === 'createdAt') {
        comparison = new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      } else {
        // Default: dueDate
        const dueA = (a.due_date || '').toLowerCase();
        const dueB = (b.due_date || '').toLowerCase();
        if (dueA === 'today' && dueB !== 'today') comparison = -1;
        else if (dueB === 'today' && dueA !== 'today') comparison = 1;
        else comparison = dueA.localeCompare(dueB);
      }

      return filters.sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [tasks, filters]);

  // Categories extracted dynamically from tasks
  const availableCategories = useMemo(() => {
    const set = new Set<string>();
    tasks.forEach((t) => {
      if (t.category) set.add(t.category);
    });
    return Array.from(set);
  }, [tasks]);

  const filterTabs: { id: 'all' | TaskStatus; label: string; count: number }[] = [
    { id: 'all', label: 'All', count: summary.total },
    { id: 'pending', label: 'Pending', count: summary.pending },
    { id: 'in_progress', label: 'In Progress', count: summary.inProgress },
    { id: 'completed', label: 'Completed', count: summary.completed },
  ];

  if (viewMode === 'kanban') {
    return (
      <div className="flex-1 flex flex-col h-full space-y-2">
        {/* Toggle bar */}
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-stone-500 font-medium">Viewing as Kanban</span>
          <div className="inline-flex p-0.5 rounded-xl bg-stone-200/80 border border-stone-300/60">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className="px-2.5 py-1 rounded-lg text-xs font-semibold text-stone-600 hover:text-stone-900 transition-colors cursor-pointer flex items-center gap-1"
            >
              <List className="w-3.5 h-3.5" />
              <span>List</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('kanban')}
              className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-white text-indigo-700 shadow-2xs transition-colors cursor-pointer flex items-center gap-1"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Kanban</span>
            </button>
          </div>
        </div>
        <div className="flex-1 min-h-0">
          <KanbanBoard />
        </div>
      </div>
    );
  }

  return (
    <div
      id="task-management-panel"
      className="flex-1 flex flex-col h-full bg-white rounded-2xl border border-stone-200/80 shadow-xs overflow-hidden"
    >
      {/* Header with Title, Mode Switcher & Add Task button */}
      <div className="p-4 sm:p-5 border-b border-stone-100 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-stone-900 tracking-tight">
            My Tasks
          </h2>
          <p className="text-xs text-stone-500 mt-0.5">
            {summary.pending} pending · {summary.completed} completed
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* List / Kanban Mode Toggle */}
          <div className="inline-flex p-0.5 rounded-xl bg-stone-100 border border-stone-200">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              title="List View"
              className="p-1.5 rounded-lg text-xs font-semibold bg-white text-indigo-700 shadow-2xs cursor-pointer"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('kanban')}
              title="Kanban View"
              className="p-1.5 rounded-lg text-xs font-semibold text-stone-600 hover:text-stone-900 cursor-pointer"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>

          <button
            type="button"
            id="add-task-header-button"
            onClick={openNewTaskModal}
            className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-all duration-150 active:scale-95 cursor-pointer"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Add Task</span>
          </button>
        </div>
      </div>

      {/* Clean Productivity Summary Strip */}
      <div className="px-4 sm:px-5 py-3 bg-stone-50/70 border-b border-stone-100 flex items-center justify-between gap-2 overflow-x-auto text-xs">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-stone-600">
            <span className="font-bold text-stone-900 text-sm">{summary.total}</span>
            <span className="text-[11px] text-stone-500">Total</span>
          </div>

          <div className="w-px h-4 bg-stone-200"></div>

          <div className="flex items-center gap-1.5 text-amber-700">
            <span className="font-bold text-amber-700 text-sm">{summary.pending}</span>
            <span className="text-[11px] text-amber-600">Pending</span>
          </div>

          <div className="w-px h-4 bg-stone-200"></div>

          <div className="flex items-center gap-1.5 text-indigo-700">
            <span className="font-bold text-indigo-700 text-sm">{summary.inProgress}</span>
            <span className="text-[11px] text-indigo-600">In Progress</span>
          </div>

          <div className="w-px h-4 bg-stone-200"></div>

          <div className="flex items-center gap-1.5 text-emerald-700">
            <span className="font-bold text-emerald-700 text-sm">{summary.completed}</span>
            <span className="text-[11px] text-emerald-600">Completed</span>
          </div>
        </div>

        {/* Progress % Pill */}
        <div className="hidden sm:flex items-center gap-2 shrink-0">
          <div className="w-20 bg-stone-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${summary.completionRate}%` }}
            ></div>
          </div>
          <span className="text-[11px] font-semibold text-stone-700 font-mono">
            {summary.completionRate}%
          </span>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="p-4 sm:p-5 border-b border-stone-100 space-y-3">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-stone-400" />
          <input
            type="text"
            placeholder="Search tasks by title, category, or notes..."
            value={filters.search}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, search: e.target.value }))
            }
            className="w-full pl-10 pr-9 py-2 text-xs bg-stone-50 border border-stone-200/80 rounded-xl focus:bg-white focus:border-indigo-600 focus:outline-hidden text-stone-900 transition-colors placeholder:text-stone-400"
          />
          {filters.search && (
            <button
              type="button"
              onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}
              className="absolute right-3 top-2.5 text-stone-400 hover:text-stone-700 p-0.5 rounded cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Status Tabs */}
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-0.5 no-scrollbar">
          <div className="flex items-center gap-1">
            {filterTabs.map((tab) => {
              const isSelected = filters.status === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, status: tab.id }))
                  }
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                    isSelected
                      ? 'bg-stone-900 text-white shadow-2xs'
                      : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
                  }`}
                >
                  <span>{tab.label}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-medium ${
                      isSelected
                        ? 'bg-stone-700 text-stone-100'
                        : 'bg-stone-200/70 text-stone-600'
                    }`}
                  >
                    {tab.count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Secondary Filters: Category & Sorting */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Category selector */}
            {availableCategories.length > 0 && (
              <select
                aria-label="Filter by category"
                value={filters.category}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, category: e.target.value }))
                }
                className="px-2 py-1 text-xs rounded-lg border border-stone-200/80 bg-stone-50 text-stone-700 focus:outline-hidden focus:bg-white"
              >
                <option value="all">All Categories</option>
                {availableCategories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            )}

            {/* Sort selector */}
            <select
              aria-label="Sort tasks by"
              value={filters.sortBy}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  sortBy: e.target.value as 'dueDate' | 'priority' | 'createdAt' | 'title',
                }))
              }
              className="px-2 py-1 text-xs rounded-lg border border-stone-200/80 bg-stone-50 text-stone-700 focus:outline-hidden focus:bg-white"
            >
              <option value="dueDate">Sort: Due Date</option>
              <option value="priority">Sort: Priority</option>
              <option value="createdAt">Sort: Created</option>
              <option value="title">Sort: Title</option>
            </select>
          </div>
        </div>
      </div>

      {/* Task Cards Feed */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-3">
        {filteredAndSortedTasks.length === 0 ? (
          <div className="h-full min-h-[220px] flex flex-col items-center justify-center text-center p-6 rounded-2xl border-2 border-dashed border-stone-200">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
              <ListTodo className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-stone-800">
              {filters.search || filters.status !== 'all' || filters.priority !== 'all'
                ? 'No matching tasks found'
                : 'No tasks yet'}
            </h3>
            <p className="text-xs text-stone-500 max-w-xs mt-1 leading-relaxed">
              {filters.search || filters.status !== 'all' || filters.priority !== 'all'
                ? 'Try clearing your search or switching filters to see other tasks.'
                : 'Tell TaskMate what you want to accomplish or create your first task manually.'}
            </p>

            <div className="flex items-center gap-2 mt-4">
              {filters.search || filters.status !== 'all' || filters.priority !== 'all' ? (
                <button
                  type="button"
                  onClick={resetFilters}
                  className="px-3.5 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-semibold transition-colors cursor-pointer"
                >
                  Clear Filters
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={openNewTaskModal}
                    className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
                  >
                    Create your first task
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      sendMessage('Create a task to study Python tomorrow')
                    }
                    className="px-3.5 py-1.5 rounded-xl bg-stone-100 hover:bg-indigo-50 hover:text-indigo-700 text-stone-700 text-xs font-semibold border border-stone-200 transition-colors cursor-pointer"
                  >
                    Ask AI Assistant
                  </button>
                </>
              )}
            </div>
          </div>
        ) : (
          filteredAndSortedTasks.map((task: Task) => (
            <TaskCard key={task.id} task={task} />
          ))
        )}
      </div>
    </div>
  );
};
