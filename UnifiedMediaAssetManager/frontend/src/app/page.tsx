"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Universe, getAllUniverses, createUniverse, getTemplates, createUniverseFromTemplate, UniverseTemplate } from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';
import { useToast } from '@/context/ToastContext';
import { SkeletonUniverseList } from '@/components/Skeleton';
import { EmptyUniverses } from '@/components/EmptyState';

export default function Home() {
  const router = useRouter();
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Template state
  const [templates, setTemplates] = useState<UniverseTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [templateName, setTemplateName] = useState('');
  const [isCreatingFromTemplate, setIsCreatingFromTemplate] = useState(false);

  const isClient = useIsClient();
  const toast = useToast();
  const nameInputRef = useRef<HTMLInputElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced search function
  const performSearch = useCallback(async (query: string) => {
    try {
      setIsSearching(true);
      const fetchedUniverses = await getAllUniverses({ 
        search: query || undefined,
        limit: 100 
      });
      setUniverses(fetchedUniverses);
    } catch (err) {
      toast.error('Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  }, [toast]);

  // Handle search input with debouncing
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    
    // Clear existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Set new timeout for debounced search
    searchTimeoutRef.current = setTimeout(() => {
      performSearch(value);
    }, 300);
  };

  // Clear search
  const clearSearch = () => {
    setSearchQuery('');
    performSearch('');
  };

  useEffect(() => {
    if (isClient) {
      async function loadData() {
        try {
          setIsLoading(true);
          const [fetchedUniverses, fetchedTemplates] = await Promise.all([
            getAllUniverses(),
            getTemplates().catch(() => []) // Templates are optional
          ]);
          setUniverses(fetchedUniverses);
          setTemplates(fetchedTemplates);
        } catch (err) {
          toast.error('Unable to load universes. Please check that the backend server is running.');
        } finally {
          setIsLoading(false);
        }
      }
      loadData();
    }
  }, [isClient, toast]);

  // Handle creating universe from template
  const handleCreateFromTemplate = async () => {
    if (!selectedTemplate || !templateName.trim()) {
      toast.warning('Please select a template and provide a name');
      return;
    }

    try {
      setIsCreatingFromTemplate(true);
      const result = await createUniverseFromTemplate(selectedTemplate, templateName);
      toast.success(result.message);
      // Navigate to the new universe
      router.push(`/universes/${result.universe_id}`);
    } catch (err) {
      toast.error('Failed to create universe from template. Please try again.');
    } finally {
      setIsCreatingFromTemplate(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setNameError(null);

    if (!newName.trim()) {
      setNameError('Universe name is required');
      nameInputRef.current?.focus();
      return;
    }

    try {
      setIsCreating(true);
      const newUniverse = await createUniverse({ name: newName, description: newDescription });
      setUniverses([...universes, newUniverse]);
      setNewName('');
      setNewDescription('');
      toast.success(`Universe "${newUniverse.name}" created successfully!`);
    } catch (err) {
      toast.error('Failed to create universe. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const scrollToForm = () => {
    nameInputRef.current?.focus();
  };

  // Prevent server-side rendering of the component's body to avoid hydration mismatch
  if (!isClient) {
    return null;
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-extrabold text-gray-900 mb-6">Your Universes</h1>

      {/* Quick Start with Templates */}
      {templates.length > 0 && (
        <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 border border-indigo-200 rounded-lg p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900">Quick Start with Templates</h2>
          </div>
          <p className="text-gray-600 text-sm mb-4">
            Jump-start your creative project with a pre-built universe including characters, locations, and timeline events.
          </p>

          {/* Template Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => {
                  setSelectedTemplate(template.id);
                  setTemplateName(template.name);
                }}
                className={`p-3 rounded-lg border-2 text-left transition-all ${
                  selectedTemplate === template.id
                    ? 'border-indigo-500 bg-indigo-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-indigo-300 hover:shadow-sm'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">{template.icon}</span>
                  <span className="font-semibold text-gray-900 text-sm">{template.name}</span>
                </div>
                <p className="text-xs text-gray-500 line-clamp-2 mb-2">{template.description}</p>
                <div className="flex gap-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700">
                    {template.element_count} elements
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
                    {template.event_count} events
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Template Name & Create */}
          {selectedTemplate && (
            <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-indigo-200">
              <div className="flex-1">
                <label htmlFor="template-name" className="sr-only">Universe Name</label>
                <input
                  id="template-name"
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="Name your universe..."
                  className="block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <button
                onClick={handleCreateFromTemplate}
                disabled={isCreatingFromTemplate || !templateName.trim()}
                className="inline-flex items-center justify-center px-6 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {isCreatingFromTemplate ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create from Template
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  setSelectedTemplate(null);
                  setTemplateName('');
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}

      {/* Create Universe Form (Manual) */}
      <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">
          {templates.length > 0 ? 'Or Start from Scratch' : 'Create a New Universe'}
        </h2>
        <p className="text-gray-500 text-sm mb-4">
          {templates.length > 0
            ? 'Create a blank universe and build your world from the ground up.'
            : 'A universe is a container for your story world, its characters, locations, and events.'}
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              ref={nameInputRef}
              id="name"
              type="text"
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value);
                if (nameError) setNameError(null);
              }}
              className={`mt-1 block w-full px-4 py-2 border rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                nameError ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., Starfall Chronicles"
              aria-invalid={!!nameError}
              aria-describedby={nameError ? 'name-error' : undefined}
            />
            {nameError && (
              <p id="name-error" className="mt-1 text-sm text-red-600">{nameError}</p>
            )}
          </div>
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              id="description"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="A brief summary of your universe (optional)"
              rows={3}
            />
          </div>
          <button
            type="submit"
            disabled={isCreating}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isCreating ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </>
            ) : (
              'Create Universe'
            )}
          </button>
        </form>
      </div>

      {/* Universe List */}
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-4">
          <h2 className="text-2xl font-semibold text-gray-800">
            {universes.length > 0 ? `Your Universes (${universes.length})` : 'Your Universes'}
          </h2>
          
          {/* Search Bar */}
          <div className="relative flex-1 sm:max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search universes..."
              className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                aria-label="Clear search"
              >
                <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
            {isSearching && (
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg className="animate-spin h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            )}
          </div>
        </div>
        
        {isLoading ? (
          <SkeletonUniverseList count={3} />
        ) : universes.length > 0 ? (
          <>
            {searchQuery && (
              <p className="text-sm text-gray-500 mb-3">
                Found {universes.length} {universes.length === 1 ? 'universe' : 'universes'} matching &quot;{searchQuery}&quot;
              </p>
            )}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {universes.map((universe) => (
                <Link key={universe.id} href={`/universes/${universe.id}`} passHref>
                  <div className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-indigo-400 hover:shadow-md cursor-pointer transition-all duration-200 ease-in-out h-full">
                    <h3 className="text-lg font-bold text-indigo-700 mb-2">{universe.name}</h3>
                    <p className="text-gray-600 text-sm line-clamp-2">{universe.description || 'No description'}</p>
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <span className="text-xs text-gray-400">Click to explore</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </>
        ) : (
          searchQuery ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
              <p className="mt-1 text-sm text-gray-500">No universes match &quot;{searchQuery}&quot;</p>
              <button
                onClick={clearSearch}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Clear search
              </button>
            </div>
          ) : (
            <EmptyUniverses onCreateClick={scrollToForm} />
          )
        )}
      </div>
    </div>
  );
}