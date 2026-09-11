import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { SUGGESTED_PROMPT_CHIPS } from '../../data/mockData';
import {
  Send,
  Sparkles,
  Bot,
  User,
  CheckCircle2,
  Trash2,
  Clock,
  ArrowRight,
  ListTodo,
  Calendar,
  Layers,
} from 'lucide-react';

export const AiAssistantPanel: React.FC = () => {
  const {
    currentUser,
    messages,
    sendMessage,
    isAiThinking,
    aiStatusText,
    clearChat,
    toggleTaskStatus,
  } = useApp();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAiThinking]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isAiThinking) return;
    const text = input;
    setInput('');
    await sendMessage(text);
  };

  const handleChipClick = (prompt: string) => {
    sendMessage(prompt);
  };

  // Dynamic greeting based on user's current local hour
  const getGreeting = () => {
    const hour = new Date().getHours();
    const name = currentUser?.name ? currentUser.name.split(' ')[0] : 'there';
    if (hour < 12) return `Good morning, ${name}`;
    if (hour < 18) return `Good afternoon, ${name}`;
    return `Good evening, ${name}`;
  };

  return (
    <div
      id="ai-assistant-panel"
      className="flex-1 flex flex-col h-full bg-white rounded-2xl border border-stone-200/80 shadow-xs overflow-hidden"
    >
      {/* AI Header with Greeting & Suggested Chips */}
      <div className="p-5 sm:p-6 border-b border-stone-100 bg-gradient-to-b from-stone-50/70 to-white">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
                <Sparkles className="w-4 h-4" />
              </span>
              <h2 className="text-lg sm:text-xl font-bold text-stone-900 tracking-tight">
                {getGreeting()}
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-stone-500 mt-1">
              What would you like to get done today?
            </p>
          </div>

          <button
            type="button"
            onClick={clearChat}
            title="Clear Chat Conversation"
            className="p-2 rounded-xl text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition-colors text-xs cursor-pointer"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* Suggested Prompt Chips */}
        <div className="mt-4 flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
          {SUGGESTED_PROMPT_CHIPS.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleChipClick(chip)}
              disabled={isAiThinking}
              className="px-3 py-1.5 rounded-xl bg-stone-100/90 hover:bg-indigo-50 hover:text-indigo-700 text-stone-700 text-xs font-medium border border-stone-200/60 whitespace-nowrap transition-all duration-150 cursor-pointer disabled:opacity-50 active:scale-95 shrink-0"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] sm:max-w-[78%] space-y-2 ${
                  isUser ? 'items-end' : 'items-start'
                }`}
              >
                {/* Safe tool activity badge if executed */}
                {msg.tool_activity && (
                  <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60 mb-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>{msg.tool_activity}</span>
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`p-3.5 sm:p-4 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap break-words ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-tr-xs shadow-xs'
                      : 'bg-stone-100/90 text-stone-800 rounded-tl-xs border border-stone-200/60 shadow-xs'
                  }`}
                >
                  {msg.content}
                </div>

                {/* Interactive Mini Task Preview if AI created a task */}
                {msg.created_task && (
                  <div className="p-3 rounded-xl bg-indigo-50/80 border border-indigo-100 text-xs text-stone-800 space-y-1.5 shadow-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-semibold text-indigo-950">
                        <ListTodo className="w-4 h-4 text-indigo-600" />
                        <span>Task Created</span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-white text-indigo-700 border border-indigo-200/60">
                        {msg.created_task.priority}
                      </span>
                    </div>
                    <p className="font-medium text-stone-900">{msg.created_task.title}</p>
                    {msg.created_task.due_date && (
                      <div className="flex items-center gap-1 text-[11px] text-stone-500">
                        <Calendar className="w-3 h-3" />
                        <span>Due: {msg.created_task.due_date}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Suggested follow-up prompt chips */}
                {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {msg.suggestedActions.map((action, aIdx) => (
                      <button
                        key={aIdx}
                        type="button"
                        onClick={() => sendMessage(action)}
                        disabled={isAiThinking}
                        className="px-2.5 py-1 rounded-lg bg-white hover:bg-indigo-50 hover:text-indigo-700 text-stone-600 text-[11px] font-medium border border-stone-200 transition-colors cursor-pointer flex items-center gap-1 active:scale-95 disabled:opacity-50"
                      >
                        <span>{action}</span>
                        <ArrowRight className="w-3 h-3 opacity-60" />
                      </button>
                    ))}
                  </div>
                )}

                <div
                  className={`text-[10px] text-stone-400 px-1 ${
                    isUser ? 'text-right' : 'text-left'
                  }`}
                >
                  {new Date(msg.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-xl bg-stone-200 text-stone-700 flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                  {currentUser?.avatar ? (
                    <img
                      src={currentUser.avatar}
                      alt={currentUser.name}
                      referrerPolicy="no-referrer"
                      className="w-full h-full rounded-xl object-cover"
                    />
                  ) : (
                    <User className="w-4 h-4" />
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* AI Thinking / Tool Activity Indicator */}
        {isAiThinking && (
          <div className="flex items-start gap-3 justify-start animate-in fade-in duration-200">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs">
              <Bot className="w-4 h-4 animate-spin" />
            </div>

            <div className="p-3.5 rounded-2xl rounded-tl-xs bg-stone-100/80 border border-stone-200/60 shadow-xs flex items-center gap-3 text-xs text-stone-600">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-bounce"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-bounce [animation-delay:0.4s]"></span>
              </div>
              <span className="font-medium text-stone-700">{aiStatusText}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Premium Chat Message Composer */}
      <div className="p-4 border-t border-stone-200/80 bg-white">
        <form onSubmit={handleSend} className="relative flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            id="taskmate-chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isAiThinking}
            placeholder="Ask TaskMate anything..."
            className="w-full pl-4 pr-12 py-3 text-xs sm:text-sm bg-stone-100/70 hover:bg-stone-100 focus:bg-white text-stone-900 rounded-xl border border-stone-200/80 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 focus:outline-hidden transition-all placeholder:text-stone-400"
          />

          <button
            type="submit"
            id="taskmate-send-button"
            disabled={!input.trim() || isAiThinking}
            aria-label="Send message"
            className="absolute right-2.5 p-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-xs transition-all duration-150 hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-[11px] text-stone-400 text-center mt-2">
          TaskMate automatically schedules, plans, and organizes your tasks.
        </p>
      </div>
    </div>
  );
};
