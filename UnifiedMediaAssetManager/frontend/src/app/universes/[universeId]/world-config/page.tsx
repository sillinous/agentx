'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  WorldConfig,
  getWorldConfig,
  createWorldConfig,
  updateWorldConfig,
  deleteWorldConfig,
} from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';
import { useToast } from '@/context/ToastContext';
import { ConfirmModal } from '@/components/Modal';
import { Skeleton } from '@/components/Skeleton';

export default function WorldConfigPage() {
  const params = useParams();
  const router = useRouter();
  const { universeId } = params;
  const toast = useToast();

  const [config, setConfig] = useState<WorldConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const isClient = useIsClient();

  // Delete confirmation modal
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Form state
  const [genre, setGenre] = useState('');
  const [physics, setPhysics] = useState('');
  const [magicSystem, setMagicSystem] = useState('');
  const [techLevel, setTechLevel] = useState('');
  const [tone, setTone] = useState('');
  const [artStyleNotes, setArtStyleNotes] = useState('');
  const [primaryColor, setPrimaryColor] = useState('');
  const [secondaryColor, setSecondaryColor] = useState('');
  const [accentColor, setAccentColor] = useState('');

  useEffect(() => {
    if (isClient) {
      if (typeof universeId !== 'string') {
        setError('Invalid Universe ID.');
        setIsLoading(false);
        return;
      }

      async function loadWorldConfig() {
        try {
          setIsLoading(true);
          const fetchedConfig = await getWorldConfig(universeId as string);
          if (fetchedConfig) {
            setConfig(fetchedConfig);
            // Populate form fields
            setGenre(fetchedConfig.genre || '');
            setPhysics(fetchedConfig.physics || '');
            setMagicSystem(fetchedConfig.magic_system || '');
            setTechLevel(fetchedConfig.tech_level || '');
            setTone(fetchedConfig.tone || '');
            setArtStyleNotes(fetchedConfig.art_style_notes || '');

            // Populate color palette
            if (fetchedConfig.color_palette) {
              setPrimaryColor(fetchedConfig.color_palette.primary || '');
              setSecondaryColor(fetchedConfig.color_palette.secondary || '');
              setAccentColor(fetchedConfig.color_palette.accent || '');
            }
          }
        } catch (err) {
          console.error('Failed to load world config:', err);
        } finally {
          setIsLoading(false);
        }
      }
      loadWorldConfig();
    }
  }, [isClient, universeId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!genre.trim() || typeof universeId !== 'string') {
      toast.warning('Please select a genre for your world.');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

      const colorPalette: { [key: string]: string } = {};
      if (primaryColor) colorPalette.primary = primaryColor;
      if (secondaryColor) colorPalette.secondary = secondaryColor;
      if (accentColor) colorPalette.accent = accentColor;

      const configData = {
        genre,
        physics: physics || undefined,
        magic_system: magicSystem || undefined,
        tech_level: techLevel || undefined,
        tone: tone || undefined,
        color_palette: Object.keys(colorPalette).length > 0 ? colorPalette : undefined,
        art_style_notes: artStyleNotes || undefined,
      };

      if (config) {
        // Update existing config
        const updatedConfig = await updateWorldConfig(universeId, configData);
        setConfig(updatedConfig);
        toast.success('World configuration updated successfully!');
      } else {
        // Create new config
        const newConfig = await createWorldConfig(universeId, configData);
        setConfig(newConfig);
        toast.success('World configuration created successfully!');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to save world configuration. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!config || typeof universeId !== 'string') return;

    try {
      setIsDeleting(true);
      await deleteWorldConfig(universeId);
      setConfig(null);
      // Reset form
      setGenre('');
      setPhysics('');
      setMagicSystem('');
      setTechLevel('');
      setTone('');
      setArtStyleNotes('');
      setPrimaryColor('');
      setSecondaryColor('');
      setAccentColor('');
      toast.success('World configuration deleted successfully!');
      setDeleteModalOpen(false);
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete world configuration.');
    } finally {
      setIsDeleting(false);
    }
  };

  // Render loading state
  if (!isClient || isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <p className="text-gray-600">Loading world configuration...</p>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0 max-w-4xl mx-auto">
      <Link href={`/universes/${universeId}`} className="text-indigo-600 hover:underline mb-6 block">
        &larr; Back to Universe
      </Link>

      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">World Configuration</h1>
        <p className="text-lg text-gray-600 mt-2">
          Define the rules, aesthetics, and atmosphere of your universe
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

      {/* World Configuration Form */}
      <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Genre (Required) */}
          <div>
            <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-1">
              Genre <span className="text-red-500">*</span>
            </label>
            <select
              id="genre"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              required
            >
              <option value="">Select a genre...</option>
              <option value="Cyberpunk">Cyberpunk</option>
              <option value="Fantasy">Fantasy</option>
              <option value="Sci-Fi">Sci-Fi</option>
              <option value="Historical">Historical</option>
              <option value="Horror">Horror</option>
              <option value="Mystery">Mystery</option>
              <option value="Romance">Romance</option>
              <option value="Western">Western</option>
              <option value="Post-Apocalyptic">Post-Apocalyptic</option>
              <option value="Steampunk">Steampunk</option>
              <option value="Urban Fantasy">Urban Fantasy</option>
              <option value="Space Opera">Space Opera</option>
            </select>
          </div>

          {/* Physics System */}
          <div>
            <label htmlFor="physics" className="block text-sm font-medium text-gray-700 mb-1">
              Physics System
            </label>
            <select
              id="physics"
              value={physics}
              onChange={(e) => setPhysics(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="">Select physics system...</option>
              <option value="Standard">Standard (Real-world physics)</option>
              <option value="Alternative">Alternative (Modified physics)</option>
              <option value="Hybrid">Hybrid (Mix of real and alternative)</option>
              <option value="Fantastical">Fantastical (Magic-based physics)</option>
            </select>
          </div>

          {/* Magic System */}
          <div>
            <label htmlFor="magic-system" className="block text-sm font-medium text-gray-700 mb-1">
              Magic System
            </label>
            <select
              id="magic-system"
              value={magicSystem}
              onChange={(e) => setMagicSystem(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="">Select magic system...</option>
              <option value="None">None</option>
              <option value="Traditional">Traditional (Spells, potions)</option>
              <option value="Digital Surrealism">Digital Surrealism (Tech-based magic)</option>
              <option value="Elemental">Elemental (Fire, water, earth, air)</option>
              <option value="Psychic">Psychic (Mind powers)</option>
              <option value="Divine">Divine (Religious/godly powers)</option>
              <option value="Chaos">Chaos (Unpredictable magic)</option>
            </select>
          </div>

          {/* Tech Level */}
          <div>
            <label htmlFor="tech-level" className="block text-sm font-medium text-gray-700 mb-1">
              Technology Level
            </label>
            <select
              id="tech-level"
              value={techLevel}
              onChange={(e) => setTechLevel(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="">Select technology level...</option>
              <option value="Stone Age">Stone Age</option>
              <option value="Medieval">Medieval</option>
              <option value="Renaissance">Renaissance</option>
              <option value="Industrial">Industrial</option>
              <option value="Modern">Modern</option>
              <option value="Near Future">Near Future</option>
              <option value="Far Future">Far Future</option>
              <option value="Post-Scarcity">Post-Scarcity</option>
            </select>
          </div>

          {/* Tone */}
          <div>
            <label htmlFor="tone" className="block text-sm font-medium text-gray-700 mb-1">
              Tone & Atmosphere
            </label>
            <select
              id="tone"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="">Select tone...</option>
              <option value="Gritty">Gritty</option>
              <option value="Neon">Neon</option>
              <option value="Melancholy">Melancholy</option>
              <option value="Hopeful">Hopeful</option>
              <option value="Dark">Dark</option>
              <option value="Whimsical">Whimsical</option>
              <option value="Epic">Epic</option>
              <option value="Mysterious">Mysterious</option>
            </select>
          </div>

          {/* Color Palette */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Visual Style</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label htmlFor="primary-color" className="block text-sm font-medium text-gray-700 mb-1">
                  Primary Color
                </label>
                <input
                  id="primary-color"
                  type="text"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="#FF5733 or Deep Crimson"
                />
              </div>
              <div>
                <label htmlFor="secondary-color" className="block text-sm font-medium text-gray-700 mb-1">
                  Secondary Color
                </label>
                <input
                  id="secondary-color"
                  type="text"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="#33A1FF or Azure Blue"
                />
              </div>
              <div>
                <label htmlFor="accent-color" className="block text-sm font-medium text-gray-700 mb-1">
                  Accent Color
                </label>
                <input
                  id="accent-color"
                  type="text"
                  value={accentColor}
                  onChange={(e) => setAccentColor(e.target.value)}
                  className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="#FFD700 or Golden"
                />
              </div>
            </div>

            <div>
              <label htmlFor="art-style-notes" className="block text-sm font-medium text-gray-700 mb-1">
                Art Style Notes
              </label>
              <textarea
                id="art-style-notes"
                value={artStyleNotes}
                onChange={(e) => setArtStyleNotes(e.target.value)}
                rows={4}
                className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Describe the visual aesthetic, art direction, and style references for this world..."
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={isSaving}
              className="inline-flex justify-center py-2 px-6 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving...' : config ? 'Update Configuration' : 'Create Configuration'}
            </button>

            {config && (
              <button
                type="button"
                onClick={() => setDeleteModalOpen(true)}
                disabled={isSaving}
                className="inline-flex justify-center py-2 px-6 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Delete Configuration
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Configuration Preview */}
      {config && (
        <div className="bg-gray-50 shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Current Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Genre:</span>
              <span className="ml-2 text-gray-600">{config.genre}</span>
            </div>
            {config.physics && (
              <div>
                <span className="font-medium text-gray-700">Physics:</span>
                <span className="ml-2 text-gray-600">{config.physics}</span>
              </div>
            )}
            {config.magic_system && (
              <div>
                <span className="font-medium text-gray-700">Magic System:</span>
                <span className="ml-2 text-gray-600">{config.magic_system}</span>
              </div>
            )}
            {config.tech_level && (
              <div>
                <span className="font-medium text-gray-700">Tech Level:</span>
                <span className="ml-2 text-gray-600">{config.tech_level}</span>
              </div>
            )}
            {config.tone && (
              <div>
                <span className="font-medium text-gray-700">Tone:</span>
                <span className="ml-2 text-gray-600">{config.tone}</span>
              </div>
            )}
          </div>

          {config.color_palette && Object.keys(config.color_palette).length > 0 && (
            <div className="mt-4">
              <span className="font-medium text-gray-700">Color Palette:</span>
              <div className="flex gap-2 mt-2">
                {config.color_palette.primary && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600">Primary:</span>
                    <span className="px-2 py-1 bg-gray-200 rounded text-xs">{config.color_palette.primary}</span>
                  </div>
                )}
                {config.color_palette.secondary && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600">Secondary:</span>
                    <span className="px-2 py-1 bg-gray-200 rounded text-xs">{config.color_palette.secondary}</span>
                  </div>
                )}
                {config.color_palette.accent && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-600">Accent:</span>
                    <span className="px-2 py-1 bg-gray-200 rounded text-xs">{config.color_palette.accent}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="mt-4 text-xs text-gray-500">
            <p>Created: {new Date(config.created_at).toLocaleString()}</p>
            <p>Updated: {new Date(config.updated_at).toLocaleString()}</p>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={handleDelete}
        title="Delete World Configuration"
        message="Are you sure you want to delete this world configuration? This action cannot be undone and will remove all settings for this universe's world."
        confirmText="Delete Configuration"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}
