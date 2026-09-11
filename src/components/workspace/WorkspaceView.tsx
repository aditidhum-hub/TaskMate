import React from 'react';
import { useApp } from '../../context/AppContext';
import { AiAssistantPanel } from '../chat/AiAssistantPanel';
import { TaskPanel } from '../tasks/TaskPanel';
import { Bot, ListTodo } from 'lucide-react';

export const WorkspaceView: React.FC = () => {
  const { mobileTab, setMobileTab, summary } = useApp();

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4.25rem)] max-w-7xl w-full mx-auto p-3 sm:p-5 lg:p-6 gap-4">
      {/* Mobile Tab Switcher */}
      <div className="lg:hidden flex items-center justify-center">
        <div className="inline-flex p-1 rounded-xl bg-stone-200/70 border border-stone-300/60 shadow-2xs">
          <button
            type="button"
            onClick={() => setMobileTab('assistant')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              mobileTab === 'assistant'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>AI Assistant</span>
          </button>
          <button
            type="button"
            onClick={() => setMobileTab('tasks')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              mobileTab === 'tasks'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            <ListTodo className="w-4 h-4" />
            <span>My Tasks</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full font-medium bg-stone-100 text-stone-600">
              {summary.pending}
            </span>
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="flex-1 flex flex-col lg:flex-row gap-5 min-h-0 overflow-hidden">
        {/* Left Column: AI Assistant (~55% width on desktop) */}
        <div
          className={`flex-1 flex flex-col h-full min-h-0 ${
            mobileTab === 'assistant' ? 'flex' : 'hidden lg:flex'
          } lg:basis-[56%]`}
        >
          <AiAssistantPanel />
        </div>

        {/* Right Column: Task Management (~45% width on desktop) */}
        <div
          className={`flex-1 flex flex-col h-full min-h-0 ${
            mobileTab === 'tasks' ? 'flex' : 'hidden lg:flex'
          } lg:basis-[44%]`}
        >
          <TaskPanel />
        </div>
      </div>
    </div>
  );
};
