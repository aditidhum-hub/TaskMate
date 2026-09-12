import React from 'react';
import { Task, TaskPriority, TaskStatus } from '../../types';
import { useApp } from '../../context/AppContext';
import {
  Check,
  Calendar,
  Clock,
  Pencil,
  Trash2,
  Tag,
  AlertCircle,
  CheckCircle2,
  Circle,
} from 'lucide-react';

interface TaskCardProps {
  task: Task;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task }) => {
  const { toggleTaskStatus, deleteTask, openEditTaskModal } = useApp();

  const isCompleted = task.status === 'completed';
  const isInProgress = task.status === 'in_progress';

  const priorityStyles: Record<TaskPriority, { bg: string; text: string; border: string }> = {
    high: {
      bg: 'bg-rose-50',
      text: 'text-rose-700',
      border: 'border-rose-200/80',
    },
    medium: {
      bg: 'bg-amber-50',
      text: 'text-amber-700',
      border: 'border-amber-200/80',
    },
    low: {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-200/80',
    },
  };

  const statusStyles: Record<TaskStatus, { label: string; badge: string }> = {
    pending: { label: 'Pending', badge: 'bg-stone-100 text-stone-600' },
    in_progress: { label: 'In Progress', badge: 'bg-indigo-50 text-indigo-700 border border-indigo-200/60' },
    completed: { label: 'Completed', badge: 'bg-emerald-50 text-emerald-700 border border-emerald-200/60' },
  };

  const priorityConfig = priorityStyles[task.priority] || priorityStyles.medium;
  const statusConfig = statusStyles[task.status] || statusStyles.pending;

  return (
    <div
      id={`task-card-${task.id}`}
      className={`group relative p-4 rounded-2xl border transition-all duration-200 ${
        isCompleted
          ? 'bg-stone-50/60 border-stone-200/60 opacity-80'
          : isInProgress
          ? 'bg-white border-indigo-200 shadow-xs ring-1 ring-indigo-50'
          : 'bg-white border-stone-200/80 hover:border-stone-300 shadow-xs hover:shadow-sm'
      }`}
    >
      <div className="flex items-start gap-3.5">
        {/* Custom Animated Checkbox */}
        <button
          type="button"
          role="checkbox"
          aria-checked={isCompleted}
          aria-label={`Mark task ${task.title} as ${isCompleted ? 'pending' : 'completed'}`}
          onClick={() => toggleTaskStatus(task.id)}
          className={`mt-0.5 w-5 h-5 rounded-lg border flex items-center justify-center transition-all duration-150 cursor-pointer shrink-0 ${
            isCompleted
              ? 'bg-emerald-600 border-emerald-600 text-white shadow-xs'
              : 'border-stone-300 hover:border-indigo-600 hover:bg-indigo-50/40 text-transparent'
          }`}
        >
          <Check
            className={`w-3.5 h-3.5 stroke-[3] transition-transform duration-150 ${
              isCompleted ? 'scale-100' : 'scale-0'
            }`}
          />
        </button>

        {/* Task Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4
              className={`text-sm font-semibold leading-snug transition-all duration-150 break-words ${
                isCompleted
                  ? 'line-through text-stone-400 font-normal'
                  : 'text-stone-900'
              }`}
            >
              {task.title}
            </h4>

            {/* Actions (Pencil / Trash) */}
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150 shrink-0">
              <button
                type="button"
                onClick={() => openEditTaskModal(task)}
                aria-label="Edit task"
                className="p-1 rounded-md text-stone-400 hover:text-indigo-600 hover:bg-stone-100 transition-colors cursor-pointer"
              >
                <Pencil className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => deleteTask(task.id)}
                aria-label="Delete task"
                className="p-1 rounded-md text-stone-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Short Description */}
          {task.description && (
            <p
              className={`text-xs mt-1 leading-relaxed line-clamp-2 ${
                isCompleted ? 'text-stone-400 line-through' : 'text-stone-600'
              }`}
            >
              {task.description}
            </p>
          )}

          {/* Badges & Meta Row */}
          <div className="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-stone-100">
            {/* Priority Badge */}
            <span
              className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border ${priorityConfig.bg} ${priorityConfig.text} ${priorityConfig.border}`}
            >
              {task.priority}
            </span>

            {/* Status Badge */}
            <span
              className={`px-2 py-0.5 rounded-md text-[10px] font-semibold ${statusConfig.badge}`}
            >
              {statusConfig.label}
            </span>

            {/* Category / Tag */}
            {task.category && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium bg-stone-100 text-stone-600">
                <Tag className="w-2.5 h-2.5" />
                {task.category}
              </span>
            )}

            {/* Due Date */}
            {task.due_date && (
              <span
                className={`inline-flex items-center gap-1 text-[11px] font-medium ml-auto ${
                  isCompleted
                    ? 'text-stone-400'
                    : task.due_date.toLowerCase() === 'today'
                    ? 'text-rose-600 font-semibold'
                    : 'text-stone-500'
                }`}
              >
                <Clock className="w-3 h-3" />
                {task.due_date}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
