// Shared types and utilities for Unified Media Ecosystem

// ============================================
// User Management
// ============================================
export interface User {
  id: string;
  email: string;
  name?: string;
  role?: 'admin' | 'user' | 'guest';
  createdAt?: Date;
  updatedAt?: Date;
}

// ============================================
// Media Assets
// ============================================
export type MediaType = 'image' | 'video' | 'audio' | '3d' | 'text';

export interface MediaAsset {
  id: string;
  type: MediaType;
  url: string;
  thumbnailUrl?: string;
  metadata?: Record<string, any>;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface MediaGenerationRequest {
  type: MediaType;
  prompt: string;
  provider?: string;
  parameters?: Record<string, any>;
}

// ============================================
// Universe/Project System
// ============================================
export interface Universe {
  id: string;
  name: string;
  description?: string;
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
  settings?: UniverseSettings;
}

export interface UniverseSettings {
  isPublic?: boolean;
  collaborators?: string[];
  tags?: string[];
}

// ============================================
// Element System (Characters, Locations, etc.)
// ============================================
export interface Element {
  id: string;
  universeId: string;
  name: string;
  type: ElementType;
  description?: string;
  attributes?: Record<string, any>;
  relationships?: ElementRelationship[];
  assets?: MediaAsset[];
  createdAt?: Date;
  updatedAt?: Date;
}

export type ElementType = 
  | 'character' 
  | 'location' 
  | 'prop' 
  | 'event' 
  | 'concept'
  | 'item'
  | 'faction'
  | 'custom';

export interface ElementRelationship {
  targetElementId: string;
  relationshipType: string;
  metadata?: Record<string, any>;
}

// ============================================
// Timeline System
// ============================================
export interface TimelineEvent {
  id: string;
  universeId: string;
  title: string;
  description?: string;
  timestamp?: Date | string;
  linkedElements?: string[];
  metadata?: Record<string, any>;
}

// ============================================
// HITL (Human-in-the-Loop) System
// ============================================
export interface HITLRequest {
  id: string;
  type: 'review' | 'approval' | 'feedback';
  status: 'pending' | 'approved' | 'rejected' | 'needs_revision';
  content: any;
  metadata?: Record<string, any>;
  createdAt: Date;
  resolvedAt?: Date;
  resolvedBy?: string;
}

// ============================================
// Common API Response Types
// ============================================
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata?: {
    timestamp: Date;
    requestId?: string;
  };
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// ============================================
// Utility Types
// ============================================
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type ID = string | number;

// ============================================
// Constants
// ============================================
export const MEDIA_TYPES: ReadonlyArray<MediaType> = [
  'image',
  'video',
  'audio',
  '3d',
  'text'
] as const;

export const ELEMENT_TYPES: ReadonlyArray<ElementType> = [
  'character',
  'location',
  'prop',
  'event',
  'concept',
  'item',
  'faction',
  'custom'
] as const;
