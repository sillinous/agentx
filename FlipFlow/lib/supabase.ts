/**
 * Server-side Supabase utilities
 * This file should only be imported in server components and API routes
 */

import { createClient } from '@supabase/supabase-js';
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import type { Database } from './types';

// Get environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Legacy client for API routes (uses anon key, RLS enforced)
// Returns null during build if env vars not available
export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient<Database>(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
      },
    })
  : (null as any);

// Server client for server components and route handlers
export async function createSupabaseServerClient() {
  const cookieStore = await cookies();

  return createServerClient<Database>(
    supabaseUrl,
    supabaseAnonKey,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
        set(name: string, value: string, options: any) {
          try {
            cookieStore.set({ name, value, ...options });
          } catch (error) {
            // Handle cookie setting errors in middleware
          }
        },
        remove(name: string, options: any) {
          try {
            cookieStore.set({ name, value: '', ...options });
          } catch (error) {
            // Handle cookie removal errors in middleware
          }
        },
      },
    }
  );
}

// Server-side Supabase client (uses service key, bypasses RLS)
// Only use this in API routes where you need admin access
export function getServiceSupabase() {
  const serviceKey = process.env.SUPABASE_SERVICE_KEY;

  if (!serviceKey) {
    throw new Error('SUPABASE_SERVICE_KEY is not set');
  }

  return createClient<Database>(supabaseUrl, serviceKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });
}

// Admin client with service role key (use carefully!)
export function createSupabaseAdminClient() {
  return getServiceSupabase();
}

// Helper to get current user session
export async function getCurrentUser() {
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error) {
    console.error('Error getting session:', error);
    return null;
  }

  return session?.user ?? null;
}

// Helper to check if user is authenticated
export async function requireAuth() {
  const user = await getCurrentUser();

  if (!user) {
    throw new Error('Authentication required');
  }

  return user;
}
