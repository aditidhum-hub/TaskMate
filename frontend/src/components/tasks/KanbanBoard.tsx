import React, { useMemo } from 'react';
import { useApp } from '../../context/AppContext';
import { Task, TaskPriority, TaskStatus, KanbanColumn } from '../../types';
import {
  Plus,
  Search,
  CheckCircle2,
  Clock,
  PlayCircle,
  Flag,
  Calendar,
  Tag,
  ArrowRight,
  ArrowLeft,
  Edit2,
  Trash2,
  X,
  Layers,
} from 'lucide-react';

const KANBAN_COLUMNS: KanbanColumn[] = [
  {
    id: 'pending',
    title: 'Pending',
    description: 'Tasks waiting to be tackled',
  },
  {
    id: 'in_progress',
    title: 'In Progress',
    description: 'Active work currently in flight',
  },
  {
    id: 'completed',
    title: 'Completed',
    description: 'Finished goals and milestones',
  },
];

export const KanbanBoard: React.FC = () => {
  const {
    tasks,
    filters,
    setFilters,
    resetFilters,
    moveTaskStatus,
    openNewTaskModal,
    openEditTaskModal,
    deleteTask,
  } = useApp();

  // Filter tasks based on active search, priority, category
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (filters.priority !== 'all' && task.priority !== filters.priority) {
        return false;
      }
      if (filters.category !== 'all' && task.category !== filters.category) {
        return false;
      }
      if (filters.search.trim()) {
        const q = filters.search.toLowerCase();
        const matchesTitle = task.title.toLowerCase().includes(q);
        const matchesDesc = (task.description || '').toLowerCase().includes(q);
        const matchesCat = (task.category || '').toLowerCase().includes(q);
        if (!matchesTitle && !matchesDesc && !matchesCat) return false;
      }
      return true;
    });
  }, [tasks, filters]);

  // Extract available categories
  const availableCategories = useMemo(() => {
    const set = new Set<string>();
    tasks.forEach((t) => {
      if (t.category) set.add(t.category);
    });
    return Array.from(set);
  }, [tasks]);

  const getPriorityStyle = (priority: TaskPriority) => {
    switch (priority) {
      case 'high':
        return 'bg-rose-50 text-rose-700 border-rose-200/80';
      case 'medium':
        return 'bg-amber-50 text-amber-700 border-amber-200/80';
      case 'low':
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200/80';
    }
  };

  const getColumnIcon = (colId: TaskStatus) => {
    switch (colId) {
      case 'pending':
        return <Clock className="w-4 h-4 text-amber-500" />;
      case 'in_progress':
        return <PlayCircle className="w-4 h-4 text-indigo-500" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
    }
  };

  const getColumnBadgeStyle = (colId: TaskStatus) => {
    switch (colId) {
      case 'pending':
        return 'bg-amber-100/70 text-amber-800 border-amber-200/60';
      case 'in_progress':
        return 'bg-indigo-100/70 text-indigo-800 border-indigo-200/60';
      case 'completed':
        return 'bg-emerald-100/70 text-emerald-800 border-emerald-200/60';
    }
  };

  return (
    <div
      id="kanban-board-container"
      className="flex-1 flex flex-col h-full bg-white rounded-2xl border border-stone-200/80 shadow-xs overflow-hidden"
    >
      {/* Kanban Top Toolbar */}
      <div className="p-4 sm:p-5 border-b border-stone-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-stone-50/50">
        <div>
          <h2 className="text-lg font-bold text-stone-900 tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            <span>Kanban Board</span>
          </h2>
          <p className="text-xs text-stone-500 mt-0.5">
            Visualize workflow, track progress, and shift task states
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          {/* Search Input */}
          <div className="relative flex-1 sm:w-48">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-stone-400" />
            <input
              type="text"
              placeholder="Search board..."
              value={filters.search}
              onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
              className="w-full pl-8 pr-7 py-1.5 text-xs bg-white border border-stone-200 rounded-xl focus:border-indigo-600 focus:outline-hidden text-stone-900 placeholder:text-stone-400"
            />
            {filters.search && (
              <button
                type="button"
                onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}
                className="absolute right-2 top-2 text-stone-400 hover:text-stone-700"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Priority filter */}
          <select
            aria-label="Filter Kanban by priority"
            value={filters.priority}
            onChange={(e) => setFilters((prev) => ({ ...prev, priority: e.target.value as 'all' | TaskPriority }))}
            className="px-2.5 py-1.5 text-xs rounded-xl border border-stone-200 bg-white text-stone-700 focus:outline-hidden"
          >
            <option value="all">All Priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          {/* Category filter */}
          {availableCategories.length > 0 && (
            <select
              aria-label="Filter Kanban by category"
              value={filters.category}
              onChange={(e) => setFilters((prev) => ({ ...prev, category: e.target.value }))}
              className="px-2.5 py-1.5 text-xs rounded-xl border border-stone-200 bg-white text-stone-700 focus:outline-hidden"
            >
              <option value="all">All Categories</option>
              {availableCategories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          )}

          {/* Add Task Button */}
          <button
            type="button"
            id="kanban-add-task-btn"
            onClick={openNewTaskModal}
            className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1 shadow-xs transition-colors cursor-pointer shrink-0"
          >
            <Plus className="w-4 h-4" />
            <span>Add Task</span>
          </button>
        </div>
      </div>

      {/* 3-Column Grid */}
      <div className="flex-1 overflow-x-auto p-4 sm:p-5 bg-stone-100/60">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-full min-w-[760px]">
          {KANBAN_COLUMNS.map((column) => {
            const columnTasks = filteredTasks.filter((t) => t.status === column.id);

            return (
              <div
                key={column.id}
                id={`kanban-column-${column.id}`}
                className="flex flex-col bg-white rounded-2xl border border-stone-200/90 shadow-2xs overflow-hidden h-full max-h-[calc(100vh-13rem)]"
              >
                {/* Column Header */}
                <div className="p-3.5 sm:p-4 border-b border-stone-100 flex items-center justify-between bg-stone-50/60">
                  <div className="flex items-center gap-2">
                    {getColumnIcon(column.id)}
                    <span className="text-xs sm:text-sm font-bold text-stone-900">
                      {column.title}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${getColumnBadgeStyle(
                        column.id
                      )}`}
                    >
                      {columnTasks.length}
                    </span>
                  </div>

                  {column.id === 'pending' && (
                    <button
                      type="button"
                      onClick={openNewTaskModal}
                      title="Add task to Pending"
                      className="p-1 rounded-lg text-stone-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Column Task Cards */}
                <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
                  {columnTasks.length === 0 ? (
                    <div className="h-40 flex flex-col items-center justify-center text-center p-4 border border-dashed border-stone-200 rounded-xl">
                      <p className="text-xs font-medium text-stone-400">
                        No {column.title.toLowerCase()} tasks
                      </p>
                      <p className="text-[11px] text-stone-400 mt-0.5">
                        {column.description}
                      </p>
                    </div>
                  ) : (
                    columnTasks.map((task: Task) => (
                      <div
                        key={task.id}
                        id={`kanban-card-${task.id}`}
                        className="p-3.5 rounded-xl bg-stone-50/80 hover:bg-white border border-stone-200/80 hover:border-indigo-200 hover:shadow-xs transition-all space-y-2 group"
                      >
                        {/* Card Header: Category & Priority */}
                        <div className="flex items-center justify-between gap-1.5">
                          <span className="text-[10px] font-medium text-stone-500 bg-stone-100 px-2 py-0.5 rounded-md flex items-center gap-1">
                            <Tag className="w-2.5 h-2.5" />
                            <span>{task.category || 'General'}</span>
                          </span>

                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-md uppercase font-bold border flex items-center gap-1 ${getPriorityStyle(
                              task.priority
                            )}`}
                          >
                            <Flag className="w-2.5 h-2.5" />
                            <span>{task.priority}</span>
                          </span>
                        </div>

                        {/* Title */}
                        <h4
                          className={`text-xs font-semibold text-stone-900 leading-snug break-words ${
                            task.status === 'completed' ? 'line-through text-stone-400' : ''
                          }`}
                        >
                          {task.title}
                        </h4>

                        {/* Description (if present) */}
                        {task.description && (
                          <p className="text-[11px] text-stone-500 line-clamp-2 leading-relaxed">
                            {task.description}
                          </p>
                        )}

                        {/* Due Date & Timestamp */}
                        {task.due_date && (
                          <div className="flex items-center gap-1 text-[11px] text-stone-500">
                            <Calendar className="w-3 h-3 text-stone-400" />
                            <span>Due: {task.due_date}</span>
                          </div>
                        )}

                        {/* Card Action Controls */}
                        <div className="pt-2 border-t border-stone-200/60 flex items-center justify-between text-xs">
                          {/* Shift Left (Move Backward) */}
                          <div>
                            {column.id === 'in_progress' && (
                              <button
                                type="button"
                                onClick={() => moveTaskStatus(task.id, 'pending')}
                                title="Move back to Pending"
                                className="px-2 py-1 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-600 text-[11px] font-medium flex items-center gap-1 transition-colors cursor-pointer"
                              >
                                <ArrowLeft className="w-3 h-3" />
                                <span>Pending</span>
                              </button>
                            )}
                            {column.id === 'completed' && (
                              <button
                                type="button"
                                onClick={() => moveTaskStatus(task.id, 'in_progress')}
                                title="Move back to In Progress"
                                className="px-2 py-1 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-600 text-[11px] font-medium flex items-center gap-1 transition-colors cursor-pointer"
                              >
                                <ArrowLeft className="w-3 h-3" />
                                <span>In Progress</span>
                              </button>
                            )}
                          </div>

                          {/* Center: Edit & Delete */}
                          <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                            <button
                              type="button"
                              onClick={() => openEditTaskModal(task)}
                              title="Edit Task"
                              className="p-1 rounded-md text-stone-400 hover:text-indigo-600 hover:bg-stone-200/60 transition-colors cursor-pointer"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                            <button
                              type="button"
                              onClick={() => deleteTask(task.id)}
                              title="Delete Task"
                              className="p-1 rounded-md text-stone-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>

                          {/* Shift Right (Advance Forward) */}
                          <div>
                            {column.id === 'pending' && (
                              <button
                                type="button"
                                onClick={() => moveTaskStatus(task.id, 'in_progress')}
                                title="Advance to In Progress"
                                className="px-2 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-semibold flex items-center gap-1 transition-colors cursor-pointer"
                              >
                                <span>Start</span>
                                <ArrowRight className="w-3 h-3" />
                              </button>
                            )}
                            {column.id === 'in_progress' && (
                              <button
                                type="button"
                                onClick={() => moveTaskStatus(task.id, 'completed')}
                                title="Mark Completed"
                                className="px-2 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-[11px] font-semibold flex items-center gap-1 transition-colors cursor-pointer"
                              >
                                <span>Done</span>
                                <CheckCircle2 className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
