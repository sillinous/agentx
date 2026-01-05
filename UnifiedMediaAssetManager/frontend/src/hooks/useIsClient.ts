"use client";

import { useState, useEffect } from 'react';

/**
 * A custom hook that returns `true` once the component has mounted on the client.
 * This is useful for preventing hydration mismatches by ensuring that
 * components that depend on client-side APIs or state are only rendered on the client.
 */
export function useIsClient() {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return isClient;
}
