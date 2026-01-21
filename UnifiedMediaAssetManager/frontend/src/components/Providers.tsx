'use client';

import { AuthProvider } from '@/context/AuthContext';
import { ToastProvider } from '@/context/ToastContext';
import { OnboardingProvider } from '@/context/OnboardingContext';
import { ToastContainer } from '@/components/Toast';
import { OnboardingWizard, OnboardingHelpButton } from '@/components/OnboardingWizard';
import { KeyboardShortcutsProvider } from '@/components/KeyboardShortcuts';

export default function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ToastProvider>
            <AuthProvider>
                <OnboardingProvider>
                    <KeyboardShortcutsProvider>
                        {children}
                        <ToastContainer />
                        <OnboardingWizard />
                        <OnboardingHelpButton />
                    </KeyboardShortcutsProvider>
                </OnboardingProvider>
            </AuthProvider>
        </ToastProvider>
    );
}
