"use client";

import { useSyncExternalStore } from 'react';

// Simple external store that always returns true on client, false on server
const subscribe = () => () => {};
const getSnapshot = () => true;
const getServerSnapshot = () => false;

/**
 * A custom hook that returns `true` once the component has mounted on the client.
 * This is useful for preventing hydration mismatches by ensuring that
 * components that depend on client-side APIs or state are only rendered on the client.
 */
export function useIsClient() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
