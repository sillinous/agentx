'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Universe, getUniverseById, addElementToUniverse, getElementsInUniverse, Element } from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';
import { useToast } from '@/context/ToastContext';
import { SkeletonUniverseDetail, SkeletonElementList } from '@/components/Skeleton';
import { EmptyElements } from '@/components/EmptyState';

export default function UniverseDetailPage() {
  const params = useParams();
  const { universeId } = params;

  const [universe, setUniverse] = useState<Universe | null>(null);
  const [elements, setElements] = useState<Element[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingElements, setIsLoadingElements] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newElementName, setNewElementName] = useState('');
  const [newElementType, setNewElementType] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [showAdvancedTools, setShowAdvancedTools] = useState(false);
  const isClient = useIsClient();
  const toast = useToast();
  const nameInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load elements with search/filter
  const loadElements = useCallback(async (search?: string, type?: string) => {
    if (typeof universeId !== 'string') return;
    
    try {
      setIsLoadingElements(true);
      const fetchedElements = await getElementsInUniverse(universeId, {
        search: search || undefined,
        element_type: type || undefined,
        limit: 100
      });
      setElements(fetchedElements);
    } catch (err) {
      toast.error('Failed to load elements.');
    } finally {
      setIsLoadingElements(false);
    }
  }, [universeId, toast]);

  // Handle search with debouncing
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      loadElements(value, filterType);
    }, 300);
  };

  // Handle filter change
  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setFilterType(value);
    loadElements(searchQuery, value);
  };

  // Clear search and filter
  const clearFilters = () => {
    setSearchQuery('');
    setFilterType('');
    loadElements('', '');
  };

  useEffect(() => {
    if (isClient) {
      if (typeof universeId !== 'string') {
        setError('Invalid Universe ID.');
        setIsLoading(false);
        return;
      }

      async function loadUniverse() {
        try {
          setIsLoading(true);
          const fetchedUniverse = await getUniverseById(universeId as string);
          if (fetchedUniverse) {
            setUniverse(fetchedUniverse);
            // Load elements separately
            loadElements();
          } else {
            setError('Universe not found.');
            toast.error('Universe not found.');
          }
        } catch (err) {
          setError('Failed to load universe data.');
          toast.error('Failed to load universe. Please check your connection.');
        } finally {
          setIsLoading(false);
        }
      }
      loadUniverse();
    }
  }, [isClient, universeId, toast, loadElements]);

  const handleElementSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setNameError(null);
    
    if (!newElementName.trim()) {
      setNameError('Element name is required');
      nameInputRef.current?.focus();
      return;
    }
    
    if (!universeId || typeof universeId !== 'string') {
      toast.error('Invalid universe ID.');
      return;
    }
    
    try {
      setIsCreating(true);
      const newElement = await addElementToUniverse(universeId, {
        name: newElementName,
        element_type: newElementType || 'Generic',
      });
      
      // Add to elements list
      setElements(prev => [newElement, ...prev]);
      
      // Update universe element count
      setUniverse(prevUniverse => {
        if (!prevUniverse) return null;
        return {
          ...prevUniverse,
          elements: [...prevUniverse.elements, newElement],
        };
      });
      
      // Clear form
      setNewElementName('');
      setNewElementType('');
      toast.success(`Element "${newElement.name}" created successfully!`);
    } catch (err) {
      toast.error('Failed to add element. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  // Render loading/error states
  if (!isClient || isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <SkeletonUniverseDetail />
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-2xl font-bold text-red-600 mb-4">{error}</h1>
        <Link href="/" className="text-indigo-600 hover:underline">
          &larr; Back to all universes
        </Link>
      </div>
    );
  }

  if (!universe) {
    return null; // Should be covered by error state, but good practice
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <Link href="/" className="text-indigo-600 hover:underline mb-6 block">
        &larr; Back to all universes
      </Link>

      {/* Universe Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">{universe.name}</h1>
        <p className="text-lg text-gray-600 mt-2">{universe.description}</p>
      </div>

      {/* Quick Start Guide - Only show when no elements exist */}
      {elements.length === 0 && !isLoadingElements && (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-lg p-6 mb-8">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Get Started</h2>
              <p className="text-gray-600 text-sm mb-3">
                Start by adding your first element below. Elements are the building blocks of your universe: characters, locations, items, and more.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                  1. Create elements
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                  2. Add descriptions & media
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                  3. Generate AI content
                </span>
              </div>
            </div>
          </div>

          {/* Quick import option */}
          <div className="mt-4 pt-4 border-t border-emerald-200">
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-medium">Have an existing story?</span> Import characters and locations automatically.
            </p>
            <Link
              href={`/universes/${universeId}/deconstruct`}
              className="inline-flex items-center text-sm font-medium text-emerald-700 hover:text-emerald-800"
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Import from Story
            </Link>
          </div>
        </div>
      )}

      {/* Advanced Tools - Collapsible Section */}
      <div className="mb-8">
        <button
          onClick={() => setShowAdvancedTools(!showAdvancedTools)}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors duration-200"
        >
          <div className="flex items-center gap-3">
            <div className="flex -space-x-1">
              <span className="text-lg">🌍</span>
              <span className="text-lg">🎬</span>
              <span className="text-lg">📖</span>
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-gray-900">Advanced Tools</h3>
              <p className="text-sm text-gray-500">World building, timeline, media generation & more</p>
            </div>
          </div>
          <svg
            className={`w-5 h-5 text-gray-400 transform transition-transform duration-200 ${showAdvancedTools ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Expandable Content */}
        {showAdvancedTools && (
          <div className="mt-4 space-y-4">
            {/* World Building Tools */}
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">World Building</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                <Link
                  href={`/universes/${universeId}/world-config`}
                  className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-indigo-100 hover:border-indigo-300"
                >
                  <span className="text-xl">🌍</span>
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">World Config</h4>
                    <p className="text-xs text-gray-500">Genre, physics, magic</p>
                  </div>
                </Link>

                <Link
                  href={`/universes/${universeId}/timeline`}
                  className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-purple-100 hover:border-purple-300"
                >
                  <span className="text-xl">📅</span>
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">Timeline</h4>
                    <p className="text-xs text-gray-500">Events & milestones</p>
                  </div>
                </Link>

                <Link
                  href={`/universes/${universeId}/deconstruct`}
                  className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-pink-100 hover:border-pink-300"
                >
                  <span className="text-xl">📖</span>
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">Story Import</h4>
                    <p className="text-xs text-gray-500">Extract from text</p>
                  </div>
                </Link>

                <div className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm border border-gray-100">
                  <span className="text-xl">🏷️</span>
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">Entity Traits</h4>
                    <p className="text-xs text-gray-500">Via element pages</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Media Generation Tools */}
            <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Media Generation</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <Link
                  href={`/universes/${universeId}/video`}
                  className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-blue-100 hover:border-blue-300"
                >
                  <span className="text-xl">🎬</span>
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">Video Generation</h4>
                    <p className="text-xs text-gray-500">AI-generated videos with mood strategies</p>
                  </div>
                </Link>

                <Link
                  href={`/universes/${universeId}/audio`}
                  className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border border-green-100 hover:border-green-300"
                >
                  <span className="text-xl">🔊</span>
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">Audio Processing</h4>
                    <p className="text-xs text-gray-500">TTS, transcription, analysis</p>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Element Form */}
      <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">Add a New Element</h2>
        <p className="text-gray-500 text-sm mb-4">Elements are the building blocks of your universe: characters, locations, items, and more.</p>
        <form onSubmit={handleElementSubmit} className="space-y-4">
          <div>
            <label htmlFor="element-name" className="block text-sm font-medium text-gray-700">
              Element Name <span className="text-red-500">*</span>
            </label>
            <input
              ref={nameInputRef}
              id="element-name"
              type="text"
              value={newElementName}
              onChange={(e) => {
                setNewElementName(e.target.value);
                if (nameError) setNameError(null);
              }}
              className={`mt-1 block w-full px-4 py-2 border rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                nameError ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., Captain Eva Rostova"
              aria-invalid={!!nameError}
              aria-describedby={nameError ? 'name-error' : undefined}
            />
            {nameError && (
              <p id="name-error" className="mt-1 text-sm text-red-600">{nameError}</p>
            )}
          </div>
          <div>
            <label htmlFor="element-type" className="block text-sm font-medium text-gray-700">Element Type</label>
            <select
              id="element-type"
              value={newElementType}
              onChange={(e) => setNewElementType(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="">Select type (optional)</option>
              <option value="Character">Character</option>
              <option value="Location">Location</option>
              <option value="Item">Item</option>
              <option value="Prop">Prop</option>
              <option value="Organization">Organization</option>
              <option value="Concept">Concept</option>
              <option value="Event">Event</option>
              <option value="Generic">Generic</option>
            </select>
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
              'Add Element'
            )}
          </button>
        </form>
      </div>

      {/* Element List */}
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-4">
          <h2 className="text-2xl font-semibold text-gray-800">
            Elements ({elements.length})
          </h2>
          
          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-2 flex-1 sm:max-w-2xl">
            {/* Search */}
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search elements..."
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
            
            {/* Filter by type */}
            <select
              value={filterType}
              onChange={handleFilterChange}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white"
            >
              <option value="">All Types</option>
              <option value="Character">Character</option>
              <option value="Location">Location</option>
              <option value="Item">Item</option>
              <option value="Prop">Prop</option>
              <option value="Organization">Organization</option>
              <option value="Concept">Concept</option>
              <option value="Event">Event</option>
              <option value="Generic">Generic</option>
            </select>
            
            {(searchQuery || filterType) && (
              <button
                onClick={clearFilters}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 whitespace-nowrap"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
        
        {isLoadingElements ? (
          <SkeletonElementList count={5} />
        ) : elements.length > 0 ? (
          <>
            {(searchQuery || filterType) && (
              <p className="text-sm text-gray-500 mb-3">
                Found {elements.length} {elements.length === 1 ? 'element' : 'elements'}
                {searchQuery && ` matching "${searchQuery}"`}
                {filterType && ` of type "${filterType}"`}
              </p>
            )}
            <ul className="space-y-3">
              {elements.map((element) => (
                <Link key={element.id} href={`/universes/${universe.id}/elements/${element.id}`} passHref>
                  <li className="block p-4 border border-gray-200 rounded-md hover:bg-gray-50 hover:border-indigo-400 cursor-pointer transition-all duration-200 ease-in-out">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-indigo-700">{element.name}</h3>
                        <p className="text-gray-500 text-sm mt-1">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                            {element.element_type}
                          </span>
                        </p>
                      </div>
                      <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </li>
                </Link>
              ))}
            </ul>
          </>
        ) : (
          (searchQuery || filterType) ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
              <p className="mt-1 text-sm text-gray-500">No elements match your search criteria</p>
              <button
                onClick={clearFilters}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Clear filters
              </button>
            </div>
          ) : (
            <EmptyElements />
          )
        )}
      </div>
    </div>
  );
}
