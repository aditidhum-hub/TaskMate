import React from 'react';
import { useApp } from '../../context/AppContext';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export const Toast: React.FC = () => {
  const { toast } = useApp();

  if (!toast) return null;

  return (
    <div
      id="taskmate-toast"
      role="alert"
      className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 bg-stone-900 text-stone-50 rounded-2xl shadow-xl border border-stone-800 text-xs sm:text-sm animate-in fade-in slide-in-from-bottom-3 duration-200 max-w-sm"
    >
      {toast.type === 'success' && (
        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
      )}
      {toast.type === 'error' && (
        <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
      )}
      {toast.type === 'info' && (
        <Info className="w-4 h-4 text-blue-400 shrink-0" />
      )}

      <span className="font-medium text-stone-100 flex-1">{toast.message}</span>
    </div>
  );
};
