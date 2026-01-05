'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Element,
  EntityTrait,
  getUniverseById,
  getTraitTemplates,
  listTraits,
  addTrait,
  updateTrait,
  deleteTrait,
} from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';

interface TraitTemplate {
  key: string;
  label: string;
  type: string;
  category: string;
  description?: string;
  placeholder?: string;
}

export default function EntityTraitsPage() {
  const params = useParams();
  const router = useRouter();
  const { universeId, elementId } = params;

  const [element, setElement] = useState<Element | null>(null);
  const [traits, setTraits] = useState<EntityTrait[]>([]);
  const [templates, setTemplates] = useState<TraitTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const isClient = useIsClient();

  // Form state for new trait
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTraitKey, setNewTraitKey] = useState('');
  const [newTraitValue, setNewTraitValue] = useState('');
  const [newTraitType, setNewTraitType] = useState('string');
  const [newTraitCategory, setNewTraitCategory] = useState('core');
  const [newTraitAiVisible, setNewTraitAiVisible] = useState(true);

  // Edit state
  const [editingTrait, setEditingTrait] = useState<EntityTrait | null>(null);
  const [editTraitValue, setEditTraitValue] = useState('');
  const [editTraitType, setEditTraitType] = useState('string');
  const [editTraitCategory, setEditTraitCategory] = useState('core');
  const [editTraitAiVisible, setEditTraitAiVisible] = useState(true);

  // Filter state
  const [filterCategory, setFilterCategory] = useState<string>('');

  useEffect(() => {
    if (isClient) {
      if (typeof universeId !== 'string' || typeof elementId !== 'string') {
        setError('Invalid Universe or Element ID.');
        setIsLoading(false);
        return;
      }

      async function loadData() {
        try {
          setIsLoading(true);

          // Load element info
          const fetchedUniverse = await getUniverseById(universeId as string);
          if (fetchedUniverse) {
            const currentElement = fetchedUniverse.elements.find(el => el.id === elementId);
            if (currentElement) {
              setElement(currentElement);

              // Load trait templates for this element type
              const entityType = currentElement.element_type.toLowerCase();
              const templatesData = await getTraitTemplates(entityType);
              setTemplates(templatesData.templates || []);
            } else {
              setError('Element not found in this universe.');
            }
          } else {
            setError('Universe not found.');
          }

          // Load existing traits
          await loadTraits();
        } catch (err) {
          console.error('Failed to load data:', err);
          setError('Failed to load entity traits.');
        } finally {
          setIsLoading(false);
        }
      }
      loadData();
    }
  }, [isClient, universeId, elementId]);

  const loadTraits = async () => {
    try {
      const fetchedTraits = await listTraits(
        elementId as string,
        filterCategory || undefined
      );
      setTraits(fetchedTraits);
    } catch (err) {
      console.error('Failed to load traits:', err);
    }
  };

  useEffect(() => {
    if (isClient && elementId) {
      loadTraits();
    }
  }, [filterCategory, isClient, elementId]);

  const handleAddTrait = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTraitKey.trim() || typeof elementId !== 'string') {
      alert('Trait key is required.');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

      const newTrait = await addTrait(elementId, {
        trait_key: newTraitKey,
        trait_value: newTraitValue || undefined,
        trait_type: newTraitType,
        trait_category: newTraitCategory,
        is_ai_visible: newTraitAiVisible,
        display_order: traits.length,
      });

      setTraits([...traits, newTrait]);
      setSuccessMessage('Trait added successfully!');

      // Reset form
      setNewTraitKey('');
      setNewTraitValue('');
      setNewTraitType('string');
      setNewTraitCategory('core');
      setNewTraitAiVisible(true);
      setShowAddForm(false);
    } catch (err: any) {
      setError(err.message || 'Failed to add trait. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdateTrait = async (traitId: string) => {
    if (!editingTrait || typeof elementId !== 'string') return;

    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

      const updatedTrait = await updateTrait(elementId, traitId, {
        trait_value: editTraitValue || undefined,
        trait_type: editTraitType,
        trait_category: editTraitCategory,
        is_ai_visible: editTraitAiVisible,
      });

      setTraits(traits.map(t => (t.id === traitId ? updatedTrait : t)));
      setSuccessMessage('Trait updated successfully!');
      setEditingTrait(null);
    } catch (err: any) {
      setError(err.message || 'Failed to update trait.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteTrait = async (traitId: string) => {
    if (typeof elementId !== 'string') return;

    const confirmed = window.confirm(
      'Are you sure you want to delete this trait? This action cannot be undone.'
    );

    if (!confirmed) return;

    try {
      setIsSaving(true);
      await deleteTrait(elementId, traitId);
      setTraits(traits.filter(t => t.id !== traitId));
      setSuccessMessage('Trait deleted successfully!');
    } catch (err: any) {
      setError(err.message || 'Failed to delete trait.');
    } finally {
      setIsSaving(false);
    }
  };

  const startEditingTrait = (trait: EntityTrait) => {
    setEditingTrait(trait);
    setEditTraitValue(trait.trait_value || '');
    setEditTraitType(trait.trait_type || 'string');
    setEditTraitCategory(trait.trait_category || 'core');
    setEditTraitAiVisible(trait.is_ai_visible);
  };

  const cancelEditing = () => {
    setEditingTrait(null);
  };

  const useTemplate = (template: TraitTemplate) => {
    setNewTraitKey(template.key);
    setNewTraitType(template.type);
    setNewTraitCategory(template.category);
    setShowAddForm(true);
  };

  // Render loading state
  if (!isClient || isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <p className="text-gray-600">Loading entity traits...</p>
      </div>
    );
  }

  if (error && !element) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-2xl font-bold text-red-600 mb-4">{error}</h1>
        <Link href={`/universes/${universeId}`} className="text-indigo-600 hover:underline">
          &larr; Back to Universe
        </Link>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0 max-w-6xl mx-auto">
      <Link
        href={`/universes/${universeId}/elements/${elementId}`}
        className="text-indigo-600 hover:underline mb-6 block"
      >
        &larr; Back to Element
      </Link>

      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">Entity Traits</h1>
        <p className="text-lg text-gray-600 mt-2">
          {element?.name} ({element?.element_type})
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Add type-specific attributes and characteristics to enrich AI context
        </p>
      </div>

      {/* Success/Error Messages */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-6">
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Trait Templates Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white shadow-lg rounded-lg p-6 sticky top-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Trait Templates</h2>
            <p className="text-sm text-gray-600 mb-4">
              Click a template to quickly add common traits for {element?.element_type}s
            </p>
            <div className="space-y-2">
              {templates.length > 0 ? (
                templates.map((template, index) => (
                  <button
                    key={index}
                    onClick={() => useTemplate(template)}
                    className="w-full text-left px-3 py-2 border border-gray-200 rounded-md hover:bg-indigo-50 hover:border-indigo-300 transition-colors duration-150"
                  >
                    <div className="font-medium text-sm text-gray-900">{template.label}</div>
                    <div className="text-xs text-gray-500 mt-1">{template.description}</div>
                    <div className="flex gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                        {template.category}
                      </span>
                      <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                        {template.type}
                      </span>
                    </div>
                  </button>
                ))
              ) : (
                <p className="text-sm text-gray-500">No templates available for this entity type.</p>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Filter and Add Button */}
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <label htmlFor="filter-category" className="text-sm font-medium text-gray-700">
                Filter by Category:
              </label>
              <select
                id="filter-category"
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
              >
                <option value="">All Categories</option>
                <option value="core">Core</option>
                <option value="physical">Physical</option>
                <option value="behavioral">Behavioral</option>
                <option value="historical">Historical</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors duration-150 text-sm font-medium"
            >
              {showAddForm ? 'Cancel' : '+ Add Custom Trait'}
            </button>
          </div>

          {/* Add Trait Form */}
          {showAddForm && (
            <div className="bg-white shadow-lg rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Add New Trait</h2>
              <form onSubmit={handleAddTrait} className="space-y-4">
                <div>
                  <label htmlFor="trait-key" className="block text-sm font-medium text-gray-700 mb-1">
                    Trait Key <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="trait-key"
                    type="text"
                    value={newTraitKey}
                    onChange={(e) => setNewTraitKey(e.target.value)}
                    className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., personality, backstory, powers"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="trait-value" className="block text-sm font-medium text-gray-700 mb-1">
                    Trait Value
                  </label>
                  <textarea
                    id="trait-value"
                    value={newTraitValue}
                    onChange={(e) => setNewTraitValue(e.target.value)}
                    rows={3}
                    className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Describe the trait value..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="trait-type" className="block text-sm font-medium text-gray-700 mb-1">
                      Type
                    </label>
                    <select
                      id="trait-type"
                      value={newTraitType}
                      onChange={(e) => setNewTraitType(e.target.value)}
                      className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="boolean">Boolean</option>
                      <option value="text">Text</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="trait-category" className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      id="trait-category"
                      value={newTraitCategory}
                      onChange={(e) => setNewTraitCategory(e.target.value)}
                      className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    >
                      <option value="core">Core</option>
                      <option value="physical">Physical</option>
                      <option value="behavioral">Behavioral</option>
                      <option value="historical">Historical</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    id="trait-ai-visible"
                    type="checkbox"
                    checked={newTraitAiVisible}
                    onChange={(e) => setNewTraitAiVisible(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="trait-ai-visible" className="ml-2 block text-sm text-gray-700">
                    Visible to AI (Include in AI context generation)
                  </label>
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors duration-150 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSaving ? 'Adding...' : 'Add Trait'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors duration-150 text-sm font-medium"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Traits List */}
          <div className="bg-white shadow-lg rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Current Traits ({traits.length})
            </h2>

            {traits.length > 0 ? (
              <div className="space-y-4">
                {traits.map((trait) => (
                  <div key={trait.id} className="border border-gray-200 rounded-lg p-4">
                    {editingTrait?.id === trait.id ? (
                      // Edit Mode
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          handleUpdateTrait(trait.id);
                        }}
                        className="space-y-3"
                      >
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Trait Key
                          </label>
                          <input
                            type="text"
                            value={trait.trait_key}
                            disabled
                            className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 text-sm"
                          />
                          <p className="text-xs text-gray-500 mt-1">Trait key cannot be changed</p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Trait Value
                          </label>
                          <textarea
                            value={editTraitValue}
                            onChange={(e) => setEditTraitValue(e.target.value)}
                            rows={3}
                            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                            <select
                              value={editTraitType}
                              onChange={(e) => setEditTraitType(e.target.value)}
                              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                            >
                              <option value="string">String</option>
                              <option value="number">Number</option>
                              <option value="boolean">Boolean</option>
                              <option value="text">Text</option>
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Category
                            </label>
                            <select
                              value={editTraitCategory}
                              onChange={(e) => setEditTraitCategory(e.target.value)}
                              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                            >
                              <option value="core">Core</option>
                              <option value="physical">Physical</option>
                              <option value="behavioral">Behavioral</option>
                              <option value="historical">Historical</option>
                              <option value="custom">Custom</option>
                            </select>
                          </div>
                        </div>

                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={editTraitAiVisible}
                            onChange={(e) => setEditTraitAiVisible(e.target.checked)}
                            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                          />
                          <label className="ml-2 block text-sm text-gray-700">
                            Visible to AI
                          </label>
                        </div>

                        <div className="flex gap-2 pt-2">
                          <button
                            type="submit"
                            disabled={isSaving}
                            className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                          >
                            {isSaving ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            type="button"
                            onClick={cancelEditing}
                            className="px-3 py-1.5 border border-gray-300 text-gray-700 rounded text-sm font-medium hover:bg-gray-50"
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : (
                      // Display Mode
                      <>
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900">
                              {trait.trait_key}
                            </h3>
                            <div className="flex gap-2 mt-1">
                              <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                                {trait.trait_category || 'core'}
                              </span>
                              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                                {trait.trait_type || 'string'}
                              </span>
                              {trait.is_ai_visible && (
                                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">
                                  AI Visible
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => startEditingTrait(trait)}
                              className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDeleteTrait(trait.id)}
                              className="text-sm text-red-600 hover:text-red-800 font-medium"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                        {trait.trait_value && (
                          <p className="text-gray-700 mt-2 whitespace-pre-wrap">{trait.trait_value}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-2">
                          Updated: {new Date(trait.updated_at).toLocaleString()}
                        </p>
                      </>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">
                No traits added yet. Use templates or add custom traits to get started!
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
