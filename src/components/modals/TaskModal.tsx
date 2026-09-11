import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Task, TaskPriority, TaskStatus } from '../../types';
import { X, Calendar, Flag, Tag, Check, Sparkles } from 'lucide-react';

export const TaskModal: React.FC = () => {
  const {
    isNewTaskModalOpen,
    closeNewTaskModal,
    editingTask,
    closeEditTaskModal,
    createTask,
    updateTask,
  } = useApp();

  const isOpen = isNewTaskModalOpen || Boolean(editingTask);
  const isEditing = Boolean(editingTask);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('Today');
  const [priority, setPriority] = useState<TaskPriority>('medium');
  const [status, setStatus] = useState<TaskStatus>('pending');
  const [category, setCategory] = useState('Work');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (editingTask) {
      setTitle(editingTask.title);
      setDescription(editingTask.description || '');
      setDueDate(editingTask.due_date || 'Today');
      setPriority(editingTask.priority);
      setStatus(editingTask.status);
      setCategory(editingTask.category || 'Work');
    } else {
      setTitle('');
      setDescription('');
      setDueDate('Today');
      setPriority('medium');
      setStatus('pending');
      setCategory('Work');
    }
  }, [editingTask, isNewTaskModalOpen]);

  if (!isOpen) return null;

  const handleClose = () => {
    if (isEditing) {
      closeEditTaskModal();
    } else {
      closeNewTaskModal();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      if (isEditing && editingTask) {
        await updateTask(editingTask.id, {
          title: title.trim(),
          description: description.trim(),
          due_date: dueDate,
          priority,
          status,
          category,
        });
        closeEditTaskModal();
      } else {
        await createTask({
          title: title.trim(),
          description: description.trim(),
          due_date: dueDate,
          priority,
          category,
        });
        closeNewTaskModal();
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const commonDueDates = ['Today', 'Tomorrow', 'Next Week', 'Sep 15, 2026'];
  const commonCategories = ['Work', 'Study', 'Health', 'Personal', 'Finance'];

  return (
    <div
      id="task-modal-backdrop"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div
        id="task-modal-content"
        className="bg-white rounded-3xl p-6 border border-stone-200 shadow-2xl max-w-lg w-full space-y-5 animate-in zoom-in-95 duration-150"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
              <Sparkles className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-stone-900">
              {isEditing ? 'Edit Task' : 'Create New Task'}
            </h3>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Task Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Task Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              autoFocus
              placeholder="e.g. Study Python, Prepare client review slides..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-stone-50 border border-stone-200 rounded-xl focus:bg-white focus:border-indigo-600 focus:outline-hidden text-stone-900 transition-colors"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Short Description (optional)
            </label>
            <textarea
              rows={2}
              placeholder="Add key milestones or notes..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 text-xs bg-stone-50 border border-stone-200 rounded-xl focus:bg-white focus:border-indigo-600 focus:outline-hidden text-stone-900 transition-colors"
            />
          </div>

          {/* Priority Selection */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Priority
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['low', 'medium', 'high'] as TaskPriority[]).map((p) => {
                const isSelected = priority === p;
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriority(p)}
                    className={`py-2 px-3 rounded-xl font-semibold capitalize border transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                      isSelected
                        ? p === 'high'
                          ? 'bg-rose-50 border-rose-400 text-rose-700 shadow-2xs'
                          : p === 'medium'
                          ? 'bg-amber-50 border-amber-400 text-amber-700 shadow-2xs'
                          : 'bg-blue-50 border-blue-400 text-blue-700 shadow-2xs'
                        : 'bg-stone-50 border-stone-200 text-stone-600 hover:bg-stone-100'
                    }`}
                  >
                    <Flag className="w-3 h-3" />
                    <span>{p}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Due Date */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Due Date
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {commonDueDates.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDueDate(d)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                    dueDate === d
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-stone-50 text-stone-600 border-stone-200 hover:bg-stone-100'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
            <input
              type="text"
              placeholder="Or enter custom date/time (e.g. Next Friday, Sep 20)..."
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-stone-50 border border-stone-200 rounded-xl focus:bg-white focus:border-indigo-600 focus:outline-hidden text-stone-900"
            />
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Category
            </label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {commonCategories.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCategory(c)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                    category === c
                      ? 'bg-stone-900 text-white border-stone-900'
                      : 'bg-stone-50 text-stone-600 border-stone-200 hover:bg-stone-100'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
            <input
              type="text"
              placeholder="Or type custom category..."
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-1.5 text-xs bg-stone-50 border border-stone-200 rounded-xl focus:bg-white focus:border-indigo-600 focus:outline-hidden text-stone-900"
            />
          </div>

          {/* If Editing, allow Status change */}
          {isEditing && (
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                Task Status
              </label>
              <select
                aria-label="Task Status"
                value={status}
                onChange={(e) => setStatus(e.target.value as TaskStatus)}
                className="w-full px-3 py-2 text-xs bg-stone-50 border border-stone-200 rounded-xl text-stone-900 focus:bg-white focus:outline-hidden"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-3 border-t border-stone-100 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-xl text-stone-600 hover:bg-stone-100 font-semibold text-xs transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-xs transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting
                ? 'Saving...'
                : isEditing
                ? 'Save Changes'
                : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
