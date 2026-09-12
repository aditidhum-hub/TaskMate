import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { NavView } from '../../types';
import {
  CheckSquare,
  Sparkles,
  LayoutDashboard,
  Bot,
  ListTodo,
  Columns2,
  Layers,
  Bell,
  User,
  LogOut,
  LogIn,
  Settings,
  ShieldCheck,
  Check,
  ExternalLink,
} from 'lucide-react';

export const Header: React.FC = () => {
  const {
    currentUser,
    activeNavView,
    setActiveNavView,
    openAuthModal,
    signOut,
    signInDemoUser,
    tasks,
    summary,
  } = useApp();

  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setIsNotificationsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems: { id: NavView; label: string; icon: React.ReactNode }[] = [
    { id: 'workspace', label: 'Workspace', icon: <Columns2 className="w-4 h-4" /> },
    { id: 'kanban', label: 'Kanban', icon: <Layers className="w-4 h-4" /> },
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'assistant', label: 'AI Assistant', icon: <Bot className="w-4 h-4" /> },
    { id: 'tasks', label: 'Tasks', icon: <ListTodo className="w-4 h-4" /> },
  ];

  return (
    <header
      id="taskmate-header"
      className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-stone-200/80 transition-colors"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Left: Brand / Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={() => setActiveNavView('workspace')}
            className="flex items-center gap-2.5 group cursor-pointer focus:outline-hidden"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform duration-200">
              <CheckSquare className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div className="text-left">
              <div className="flex items-center gap-1.5">
                <span className="text-base font-bold text-stone-900 tracking-tight">
                  TaskMate
                </span>
                <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  AI Online
                </span>
              </div>
              <span className="text-[11px] text-stone-500 block -mt-0.5">
                AI Task Assistant
              </span>
            </div>
          </button>
        </div>

        {/* Center: Main Navigation */}
        <nav
          id="taskmate-nav"
          aria-label="Primary Navigation"
          className="hidden md:flex items-center gap-1 bg-stone-100/80 p-1 rounded-xl border border-stone-200/60"
        >
          {navItems.map((item) => {
            const isActive = activeNavView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveNavView(item.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${
                  isActive
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-stone-600 hover:text-stone-900 hover:bg-stone-200/50'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
                {(item.id === 'tasks' || item.id === 'kanban') && tasks.length > 0 && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-medium ${
                      isActive
                        ? 'bg-indigo-100 text-indigo-800'
                        : 'bg-stone-200/80 text-stone-600'
                    }`}
                  >
                    {summary.pending}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Side: Notifications & User Profile */}
        <div className="flex items-center gap-2">
          {/* Notifications button & popover */}
          <div className="relative" ref={notifRef}>
            <button
              type="button"
              id="notifications-button"
              aria-label="Notifications"
              onClick={() => setIsNotificationsOpen((prev) => !prev)}
              className="w-9 h-9 rounded-xl text-stone-600 hover:text-stone-900 hover:bg-stone-100 flex items-center justify-center transition-colors relative cursor-pointer"
            >
              <Bell className="w-4 h-4" />
              {summary.highPriorityPending > 0 && (
                <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>
              )}
            </button>

            {isNotificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-stone-200 p-4 z-50 animate-in fade-in zoom-in-95 duration-150">
                <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                  <h4 className="text-xs font-bold text-stone-900">Notifications</h4>
                  <span className="text-[10px] text-stone-500 font-medium">
                    {summary.pending} tasks pending
                  </span>
                </div>
                <div className="divide-y divide-stone-100 max-h-60 overflow-y-auto mt-2">
                  {summary.highPriorityPending > 0 ? (
                    <div className="py-2.5 text-xs">
                      <div className="flex items-start gap-2">
                        <span className="w-2 h-2 rounded-full bg-rose-500 mt-1.5 shrink-0"></span>
                        <div>
                          <p className="font-semibold text-stone-800">High Priority Action</p>
                          <p className="text-stone-500 text-[11px] mt-0.5">
                            You have {summary.highPriorityPending} high-priority task(s) awaiting your attention today.
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="py-4 text-center text-xs text-stone-500">
                      No urgent alerts. Everything is on track!
                    </div>
                  )}
                  <div className="py-2.5 text-xs flex items-start gap-2">
                    <span className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5 shrink-0"></span>
                    <div>
                      <p className="font-semibold text-stone-800">AI Assistant Ready</p>
                      <p className="text-stone-500 text-[11px] mt-0.5">
                        Ask TaskMate to schedule, breakdown chapters, or plan milestones.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Menu */}
          <div className="relative" ref={profileRef}>
            {currentUser ? (
              <button
                type="button"
                id="user-profile-button"
                onClick={() => setIsProfileOpen((prev) => !prev)}
                className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-stone-100 transition-colors cursor-pointer focus:outline-hidden"
              >
                <img
                  src={currentUser.avatar}
                  alt={currentUser.name}
                  referrerPolicy="no-referrer"
                  className="w-8 h-8 rounded-lg object-cover ring-1 ring-stone-200"
                />
                <span className="hidden lg:inline text-xs font-semibold text-stone-800 max-w-[100px] truncate">
                  {currentUser.name}
                </span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => openAuthModal('signin')}
                className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
              >
                <LogIn className="w-3.5 h-3.5" /> Sign In
              </button>
            )}

            {/* Profile Dropdown Menu */}
            {isProfileOpen && currentUser && (
              <div className="absolute right-0 mt-2 w-60 bg-white rounded-2xl shadow-xl border border-stone-200 py-2 z-50 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-4 py-2.5 border-b border-stone-100">
                  <p className="text-xs font-bold text-stone-900">{currentUser.name}</p>
                  <p className="text-[11px] text-stone-500 truncate">{currentUser.email}</p>
                </div>

                <div className="py-1 text-xs text-stone-700">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveNavView('dashboard');
                      setIsProfileOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-stone-50 flex items-center gap-2 cursor-pointer"
                  >
                    <LayoutDashboard className="w-3.5 h-3.5 text-stone-500" />
                    Productivity Dashboard
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveNavView('kanban');
                      setIsProfileOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-stone-50 flex items-center gap-2 cursor-pointer"
                  >
                    <Layers className="w-3.5 h-3.5 text-stone-500" />
                    Kanban Board
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      signInDemoUser();
                      setIsProfileOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-stone-50 flex items-center gap-2 cursor-pointer"
                  >
                    <User className="w-3.5 h-3.5 text-stone-500" />
                    Reset to Demo Account
                  </button>
                </div>

                <div className="pt-1 border-t border-stone-100">
                  <button
                    type="button"
                    onClick={() => {
                      signOut();
                      setIsProfileOpen(false);
                    }}
                    className="w-full px-4 py-2 text-left text-xs font-semibold text-rose-600 hover:bg-rose-50 flex items-center gap-2 cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Navigation bar */}
      <div className="md:hidden border-t border-stone-200 px-3 py-2 bg-stone-50 flex items-center justify-around text-xs overflow-x-auto">
        {navItems.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setActiveNavView(item.id)}
            className={`flex items-center gap-1 py-1 px-2 rounded-lg font-semibold transition-colors cursor-pointer shrink-0 ${
              activeNavView === item.id
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            {item.icon}
            <span className="text-[10px]">{item.label}</span>
          </button>
        ))}
      </div>
    </header>
  );
};
