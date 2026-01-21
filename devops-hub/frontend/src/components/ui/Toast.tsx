/* eslint-disable react-refresh/only-export-components */
/**
 * Toast - Elegant notification system with smooth animations
 *
 * Design: Refined with subtle motion and clear visual hierarchy
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { ReactNode } from 'react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  description?: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (type: ToastType, message: string, description?: string, duration?: number) => void;
  hideToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const hideToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (type: ToastType, message: string, description?: string, duration = 4000) => {
      const id = `toast-${Date.now()}-${Math.random()}`;
      const toast: Toast = { id, type, message, description, duration };

      setToasts((prev) => [...prev, toast]);

      if (duration > 0) {
        setTimeout(() => hideToast(id), duration);
      }
    },
    [hideToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, showToast, hideToast }}>
      {children}
      <ToastContainer toasts={toasts} onClose={hideToast} />
    </ToastContext.Provider>
  );
}

interface ToastContainerProps {
  toasts: Toast[];
  onClose: (id: string) => void;
}

function ToastContainer({ toasts, onClose }: ToastContainerProps) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-md">
      {toasts.map((toast, index) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={onClose}
          index={index}
        />
      ))}
    </div>
  );
}

interface ToastItemProps {
  toast: Toast;
  onClose: (id: string) => void;
  index: number;
}

function ToastItem({ toast, onClose, index }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false);

  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => onClose(toast.id), 200);
  }, [onClose, toast.id]);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose();
    }, toast.duration || 4000);

    return () => clearTimeout(timer);
  }, [toast.duration, handleClose]);

  const typeStyles = {
    success: {
      bg: 'bg-gradient-to-br from-emerald-50 to-green-50',
      border: 'border-emerald-200',
      icon: '✓',
      iconBg: 'bg-emerald-500',
      iconColor: 'text-white',
    },
    error: {
      bg: 'bg-gradient-to-br from-red-50 to-rose-50',
      border: 'border-red-200',
      icon: '✕',
      iconBg: 'bg-red-500',
      iconColor: 'text-white',
    },
    warning: {
      bg: 'bg-gradient-to-br from-amber-50 to-yellow-50',
      border: 'border-amber-200',
      icon: '!',
      iconBg: 'bg-amber-500',
      iconColor: 'text-white',
    },
    info: {
      bg: 'bg-gradient-to-br from-blue-50 to-indigo-50',
      border: 'border-blue-200',
      icon: 'i',
      iconBg: 'bg-blue-500',
      iconColor: 'text-white',
    },
  };

  const style = typeStyles[toast.type];
  const animationDelay = index * 0.05;

  return (
    <div
      className={`
        ${style.bg} ${style.border}
        border rounded-lg shadow-lg overflow-hidden
        transition-all duration-200 ease-out
        ${isExiting ? 'opacity-0 translate-x-8 scale-95' : 'opacity-100 translate-x-0 scale-100'}
      `}
      style={{
        animation: isExiting ? undefined : `slideInRight 0.3s ease-out ${animationDelay}s backwards`,
      }}
      role="alert"
    >
      <div className="flex items-start gap-3 p-4">
        {/* Icon */}
        <div className={`${style.iconBg} ${style.iconColor} rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 font-bold text-sm`}>
          {style.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 text-sm leading-tight">
            {toast.message}
          </p>
          {toast.description && (
            <p className="text-gray-600 text-sm mt-1 leading-snug">
              {toast.description}
            </p>
          )}
        </div>

        {/* Close button */}
        <button
          onClick={handleClose}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close notification"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Progress bar */}
      {toast.duration && toast.duration > 0 && (
        <div className="h-1 bg-gray-200 relative overflow-hidden">
          <div
            className={`h-full ${style.iconBg} absolute left-0 top-0`}
            style={{
              animation: `shrink ${toast.duration}ms linear`,
            }}
          />
        </div>
      )}
    </div>
  );
}

// Helper hooks for common toast types
export function useToastHelpers() {
  const { showToast } = useToast();

  return {
    success: (message: string, description?: string) =>
      showToast('success', message, description),
    error: (message: string, description?: string) =>
      showToast('error', message, description),
    warning: (message: string, description?: string) =>
      showToast('warning', message, description),
    info: (message: string, description?: string) =>
      showToast('info', message, description),
  };
}
