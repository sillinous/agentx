'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Universe, getUniverseById, addElementToUniverse } from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';

export default function UniverseDetailPage() {
  const params = useParams();
  const { universeId } = params;

  const [universe, setUniverse] = useState<Universe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newElementName, setNewElementName] = useState('');
  const [newElementType, setNewElementType] = useState('');
  const isClient = useIsClient();

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
          } else {
            setError('Universe not found.');
          }
        } catch (err) {
          setError('Failed to load universe data.');
        } finally {
          setIsLoading(false);
        }
      }
      loadUniverse();
    }
  }, [isClient, universeId]);

  const handleElementSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newElementName.trim() || !universeId || typeof universeId !== 'string') {
      alert('Element name cannot be empty.');
      return;
    }
    try {
      const newElement = await addElementToUniverse(universeId, {
        name: newElementName,
        element_type: newElementType || 'Generic',
      });
      // Update the universe state to include the new element
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
    } catch (err) {
      alert('Failed to add element. Please try again.');
    }
  };

  // Render loading/error states
  if (!isClient || isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <p className="text-gray-600">Loading...</p>
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

      {/* Phase 1 Quick Links */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">World Building Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href={`/universes/${universeId}/world-config`}
            className="flex flex-col p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow duration-200 border border-indigo-100 hover:border-indigo-300"
          >
            <div className="text-2xl mb-2">🌍</div>
            <h3 className="text-lg font-semibold text-gray-900">World Configuration</h3>
            <p className="text-sm text-gray-600 mt-1">
              Define genre, physics, magic systems, and visual style
            </p>
          </Link>

          <Link
            href={`/universes/${universeId}/timeline`}
            className="flex flex-col p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow duration-200 border border-purple-100 hover:border-purple-300"
          >
            <div className="text-2xl mb-2">📅</div>
            <h3 className="text-lg font-semibold text-gray-900">Timeline</h3>
            <p className="text-sm text-gray-600 mt-1">
              Manage chronological events and story milestones
            </p>
          </Link>

          <div className="flex flex-col p-4 bg-white rounded-lg shadow border border-gray-100">
            <div className="text-2xl mb-2">🏷️</div>
            <h3 className="text-lg font-semibold text-gray-900">Entity Traits</h3>
            <p className="text-sm text-gray-600 mt-1">
              Add traits to elements from their detail pages
            </p>
          </div>
        </div>
      </div>

      {/* Media Generation Tools */}
      <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-3">Media Generation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            href={`/universes/${universeId}/video`}
            className="flex flex-col p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow duration-200 border border-blue-100 hover:border-blue-300"
          >
            <div className="text-2xl mb-2">🎬</div>
            <h3 className="text-lg font-semibold text-gray-900">Video Generation</h3>
            <p className="text-sm text-gray-600 mt-1">
              Create AI-generated videos with mood-based strategies
            </p>
          </Link>

          <Link
            href={`/universes/${universeId}/audio`}
            className="flex flex-col p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow duration-200 border border-green-100 hover:border-green-300"
          >
            <div className="text-2xl mb-2">🔊</div>
            <h3 className="text-lg font-semibold text-gray-900">Audio Processing</h3>
            <p className="text-sm text-gray-600 mt-1">
              Text-to-speech, transcription, and audio analysis
            </p>
          </Link>
        </div>
      </div>

      {/* Add Element Form */}
      <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Add a New Element</h2>
        <form onSubmit={handleElementSubmit} className="space-y-4">
          <div>
            <label htmlFor="element-name" className="block text-sm font-medium text-gray-700">Element Name</label>
            <input
              id="element-name"
              type="text"
              value={newElementName}
              onChange={(e) => setNewElementName(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="e.g., Captain Eva Rostova"
            />
          </div>
          <div>
            <label htmlFor="element-type" className="block text-sm font-medium text-gray-700">Element Type</label>
            <input
              id="element-type"
              type="text"
              value={newElementType}
              onChange={(e) => setNewElementType(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="e.g., Character"
            />
          </div>
          <button
            type="submit"
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out"
          >
            Add Element
          </button>
        </form>
      </div>

      {/* Element List */}
      <div className="bg-white shadow-lg rounded-lg p-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Elements in this Universe</h2>
        <ul className="space-y-4">
          {universe.elements.length > 0 ? (
            universe.elements.map((element) => (
              <Link key={element.id} href={`/universes/${universe.id}/elements/${element.id}`} passHref>
                <li className="block p-4 border border-gray-200 rounded-md hover:bg-gray-50 hover:border-indigo-400 cursor-pointer transition-all duration-200 ease-in-out">
                  <h3 className="text-xl font-bold text-indigo-700">{element.name}</h3>
                  <p className="text-gray-500 font-mono text-sm mt-1">{element.element_type}</p>
                </li>
              </Link>
            ))
          ) : (
            <p className="text-gray-500">No elements found in this universe. Add one to get started!</p>
          )}
        </ul>
      </div>
    </div>
  );
}
