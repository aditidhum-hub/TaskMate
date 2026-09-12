import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Header } from './components/layout/Header';
import { WorkspaceView } from './components/workspace/WorkspaceView';
import { KanbanBoard } from './components/tasks/KanbanBoard';
import { DashboardView } from './components/dashboard/DashboardView';
import { AiAssistantPanel } from './components/chat/AiAssistantPanel';
import { TaskPanel } from './components/tasks/TaskPanel';
import { TaskModal } from './components/modals/TaskModal';
import { AuthModal } from './components/modals/AuthModal';
import { Toast } from './components/ui/Toast';

const TaskMateApp: React.FC = () => {
  const { activeNavView } = useApp();

  return (
    <div className="min-h-screen flex flex-col bg-stone-100/70 text-stone-900 font-sans antialiased selection:bg-indigo-100 selection:text-indigo-900">
      {/* SaaS Navigation Header */}
      <Header />

      {/* Main Content Router */}
      <main className="flex-1 flex flex-col min-h-0">
        {activeNavView === 'workspace' && <WorkspaceView />}
        {activeNavView === 'kanban' && (
          <div className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-5 lg:p-6 flex flex-col h-[calc(100vh-4.25rem)]">
            <KanbanBoard />
          </div>
        )}
        {activeNavView === 'dashboard' && <DashboardView />}
        {activeNavView === 'assistant' && (
          <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 flex flex-col h-[calc(100vh-4.25rem)]">
            <AiAssistantPanel />
          </div>
        )}
        {activeNavView === 'tasks' && (
          <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 flex flex-col h-[calc(100vh-4.25rem)]">
            <TaskPanel />
          </div>
        )}
      </main>

      {/* Modals & Floating Components */}
      <TaskModal />
      <AuthModal />
      <Toast />
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <TaskMateApp />
    </AppProvider>
  );
}
