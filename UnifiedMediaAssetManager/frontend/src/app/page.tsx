"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Universe, getAllUniverses, createUniverse } from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';

export default function Home() {
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isClient = useIsClient();

  useEffect(() => {
    // Only run the effect on the client
    if (isClient) {
      async function loadUniverses() {
        try {
          setIsLoading(true);
          const fetchedUniverses = await getAllUniverses();
          setUniverses(fetchedUniverses);
        } catch (err) {
          setError('Failed to load universes. Make sure the backend is running.');
        } finally {
          setIsLoading(false);
        }
      }
      loadUniverses();
    }
  }, [isClient]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) {
      alert('Universe name cannot be empty.');
      return;
    }
    try {
      const newUniverse = await createUniverse({ name: newName, description: newDescription });
      setUniverses([...universes, newUniverse]);
      setNewName('');
      setNewDescription('');
    } catch (err) {
      setError('Failed to create universe.');
    }
  };

  // Prevent server-side rendering of the component's body to avoid hydration mismatch
  if (!isClient) {
    return null;
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <h1 className="text-3xl font-extrabold text-gray-900 mb-6">Your Universes</h1>

      {/* Create Universe Form */}
      <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Create a New Universe</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">Name</label>
            <input
              id="name"
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="e.g., Starfall Chronicles"
            />
          </div>
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              id="description"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="A brief summary of your universe"
              rows={3}
            />
          </div>
          <button
            type="submit"
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out"
          >
            Create Universe
          </button>
        </form>
      </div>

      {/* Universe List */}
      <div className="bg-white shadow-lg rounded-lg p-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Existing Universes</h2>
        {error && <p className="text-red-600 bg-red-50 p-3 rounded-md mb-4">{error}</p>}
        {isLoading ? (
          <p className="text-gray-600">Loading universes...</p>
        ) : (
          <ul className="space-y-4">
            {universes.length > 0 ? (
              universes.map((universe) => (
                <Link key={universe.id} href={`/universes/${universe.id}`} passHref>
                  <li className="block p-4 border border-gray-200 rounded-md hover:bg-gray-50 hover:border-indigo-400 cursor-pointer transition-all duration-200 ease-in-out">
                    <h3 className="text-xl font-bold text-indigo-700">{universe.name}</h3>
                    <p className="text-gray-600 mt-1">{universe.description}</p>
                  </li>
                </Link>
              ))
            ) : (
              <p className="text-gray-500">No universes found. Create one to get started!</p>
            )}
          </ul>
        )}
      </div>
    </div>
  );
}