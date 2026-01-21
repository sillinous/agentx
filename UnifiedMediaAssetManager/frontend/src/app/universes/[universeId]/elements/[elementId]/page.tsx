'use client';

import { useState, useEffect, Suspense, lazy } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
    Universe,
    Element,
    AnyComponent,
    TextComponent,
    ImageComponent,
    VideoComponent,
    AudioComponent,
    Model3DComponent,
    AttributeComponent,
    RelationshipComponent,
    getUniverseById,
    addComponentToElement,
    generateSimpleImage
} from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';
import { useToast } from '@/context/ToastContext';
import { Skeleton, SkeletonText } from '@/components/Skeleton';
import { EmptyComponents } from '@/components/EmptyState';

// Dynamically import ModelViewer to avoid SSR issues with Three.js
const ModelViewer = lazy(() => import('@/components/ModelViewer'));

// Component Display Functions
function TextComponentDisplay({ component }: { component: TextComponent }) {
    return (
        <div>
            <h3 className="text-lg font-semibold text-gray-900">{component.data.field}</h3>
            <p className="mt-2 text-gray-700 whitespace-pre-wrap">{component.data.content}</p>
        </div>
    );
}

function ImageComponentDisplay({ component }: { component: ImageComponent }) {
    return (
        <div>
            <h3 className="text-lg font-semibold text-gray-900">{component.data.label}</h3>
            {component.data.prompt && (
                <p className="mt-1 text-sm text-gray-500 italic">Prompt: {component.data.prompt}</p>
            )}
            <img
                src={component.data.url}
                alt={component.data.label}
                className="mt-2 max-w-full h-auto rounded-md shadow-md"
                loading="lazy"
            />
        </div>
    );
}

function VideoComponentDisplay({ component }: { component: VideoComponent }) {
    return (
        <div>
            <h3 className="text-lg font-semibold text-gray-900">{component.data.label}</h3>
            <video
                src={component.data.url}
                controls
                className="mt-2 max-w-full h-auto rounded-md shadow-md"
            >
                Your browser does not support the video tag.
            </video>
        </div>
    );
}

function AudioComponentDisplay({ component }: { component: AudioComponent }) {
    return (
        <div>
            <h3 className="text-lg font-semibold text-gray-900">{component.data.label}</h3>
            <audio
                src={component.data.url}
                controls
                className="mt-2 w-full"
            >
                Your browser does not support the audio tag.
            </audio>
        </div>
    );
}

function Model3DComponentDisplay({ component }: { component: Model3DComponent }) {
    const [showViewer, setShowViewer] = useState(false);
    const isGLTF = component.data.url.endsWith('.gltf') || component.data.url.endsWith('.glb');

    return (
        <div>
            <h3 className="text-lg font-semibold text-gray-900">{component.data.label}</h3>
            {isGLTF ? (
                <>
                    <button
                        onClick={() => setShowViewer(!showViewer)}
                        className="mt-2 inline-flex items-center px-3 py-1.5 bg-yellow-600 text-white text-sm rounded-md hover:bg-yellow-700 transition-colors"
                    >
                        {showViewer ? 'Hide 3D Viewer' : 'View 3D Model'}
                    </button>
                    {showViewer && (
                        <div className="mt-4 h-96 bg-gray-100 rounded-lg overflow-hidden">
                            <Suspense fallback={
                                <div className="flex items-center justify-center h-full">
                                    <div className="w-8 h-8 border-4 border-yellow-200 border-t-yellow-600 rounded-full animate-spin"></div>
                                </div>
                            }>
                                <ModelViewer url={component.data.url} className="w-full h-full" />
                            </Suspense>
                        </div>
                    )}
                </>
            ) : (
                <p className="mt-2 text-gray-700">
                    3D Model: <a href={component.data.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">{component.data.url}</a>
                    <span className="ml-2 text-sm text-gray-500">(Only GLTF/GLB formats supported for preview)</span>
                </p>
            )}
        </div>
    );
}

function AttributeComponentDisplay({ component }: { component: AttributeComponent }) {
    return (
        <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Attributes</h3>
            <div className="grid grid-cols-2 gap-2">
                {Object.entries(component.data.attributes).map(([key, value]) => (
                    <div key={key} className="flex flex-col">
                        <span className="text-sm font-medium text-gray-600">{key}:</span>
                        <span className="text-gray-900">{String(value)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

function RelationshipComponentDisplay({ component }: { component: RelationshipComponent }) {
    return (
        <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Relationships</h3>
            <ul className="space-y-2">
                {component.data.relations.map((relation, index) => (
                    <li key={index} className="border-l-4 border-teal-500 pl-3">
                        <p className="text-sm font-medium text-gray-900">{relation.type}</p>
                        <p className="text-sm text-gray-600">Target: <span className="font-mono text-xs">{relation.target_element_id}</span></p>
                        {relation.description && (
                            <p className="text-sm text-gray-700 mt-1">{relation.description}</p>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}

// AI Quick Action configurations based on element type
const AI_QUICK_ACTIONS: Record<string, { label: string; prompt: string; icon: string }[]> = {
    Character: [
        { label: 'Generate Backstory', prompt: 'Write a detailed backstory for this character including their origins, motivations, and key life events.', icon: '📜' },
        { label: 'Describe Appearance', prompt: 'Write a vivid physical description of this character including their build, features, clothing style, and distinguishing marks.', icon: '👤' },
        { label: 'Create Dialogue Sample', prompt: 'Write a short dialogue sample that captures this character\'s unique voice, speech patterns, and personality.', icon: '💬' },
    ],
    Location: [
        { label: 'Describe Atmosphere', prompt: 'Write an atmospheric description of this location including sensory details like sounds, smells, lighting, and the overall mood.', icon: '🌅' },
        { label: 'Detail Architecture', prompt: 'Describe the architectural style, layout, and notable structural features of this location.', icon: '🏛️' },
        { label: 'Reveal History', prompt: 'Write about the history of this location - who built it, what events occurred here, and how it has changed over time.', icon: '📚' },
    ],
    Item: [
        { label: 'Describe Appearance', prompt: 'Write a detailed physical description of this item including its materials, craftsmanship, and any unique markings.', icon: '🔍' },
        { label: 'Reveal Origin', prompt: 'Write the origin story of this item - who created it, when, why, and how it came to be in its current state.', icon: '⚒️' },
        { label: 'List Properties', prompt: 'Describe the special properties, powers, or capabilities of this item and any conditions for their use.', icon: '✨' },
    ],
    Organization: [
        { label: 'Describe Structure', prompt: 'Write about the organizational structure, hierarchy, and key roles within this organization.', icon: '🏢' },
        { label: 'Reveal Purpose', prompt: 'Describe the core mission, goals, and methods of this organization.', icon: '🎯' },
        { label: 'Detail History', prompt: 'Write the founding story and key historical events that shaped this organization.', icon: '📜' },
    ],
    default: [
        { label: 'Generate Description', prompt: 'Write a comprehensive description of this element including key details and characteristics.', icon: '📝' },
        { label: 'Explore Significance', prompt: 'Write about the significance and role of this element within the larger story or world.', icon: '⭐' },
    ],
};

export default function ElementDetailPage() {
    const params = useParams();
    const { universeId, elementId } = params;
    const toast = useToast();

    const [universe, setUniverse] = useState<Universe | null>(null);
    const [element, setElement] = useState<Element | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isAddingComponent, setIsAddingComponent] = useState(false);
    const isClient = useIsClient();

    // Progressive disclosure state
    const [activeTab, setActiveTab] = useState<'description' | 'media' | 'data'>('description');
    const [isQuickActionRunning, setIsQuickActionRunning] = useState(false);

    // State for forms
    const [newComponentField, setNewComponentField] = useState('Description');
    const [newComponentContent, setNewComponentContent] = useState('');
    const [newImagePrompt, setNewImagePrompt] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);

    // States for other component forms
    const [newMediaLabel, setNewMediaLabel] = useState('');
    const [newMediaUrl, setNewMediaUrl] = useState('');

    const [newAttributeKey, setNewAttributeKey] = useState('');
    const [newAttributeValue, setNewAttributeValue] = useState('');

    const [newRelationType, setNewRelationType] = useState('');
    const [newRelationTargetId, setNewRelationTargetId] = useState('');
    const [newRelationDescription, setNewRelationDescription] = useState('');

    // Get AI quick actions for this element type
    const quickActions = element ? (AI_QUICK_ACTIONS[element.element_type] || AI_QUICK_ACTIONS.default) : [];

    // Handle AI quick action
    const handleQuickAction = async (prompt: string, label: string) => {
        if (!element || typeof universeId !== 'string' || typeof elementId !== 'string') return;

        setIsQuickActionRunning(true);
        try {
            // Use the narrative agent to generate content
            const fullPrompt = `For the ${element.element_type.toLowerCase()} named "${element.name}": ${prompt}`;

            // Create the text component with the AI-generated content
            // For now, we'll use a placeholder - this would call the narrative agent API
            const newComponentData: Omit<TextComponent, 'id'> = {
                type: "TextComponent",
                data: {
                    field: label.replace('Generate ', '').replace('Describe ', '').replace('Create ', '').replace('Reveal ', '').replace('Detail ', '').replace('List ', '').replace('Explore ', ''),
                    content: `[AI-generated ${label.toLowerCase()} will appear here. The narrative agent would process: "${fullPrompt}"]`
                }
            };

            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            toast.success(`${label} added! Edit the content to refine.`);
        } catch (err) {
            toast.error(`Failed to run ${label}. Please try again.`);
        } finally {
            setIsQuickActionRunning(false);
        }
    };

    useEffect(() => {
        if (isClient) {
            if (typeof universeId !== 'string') {
                setError('Invalid Universe ID.');
                setIsLoading(false);
                return;
            }

            async function loadData() {
                try {
                    setIsLoading(true);
                    const fetchedUniverse = await getUniverseById(universeId as string);
                    if (fetchedUniverse) {
                        setUniverse(fetchedUniverse);
                        const currentElement = fetchedUniverse.elements.find(el => el.id === elementId);
                        setElement(currentElement ?? null);
                        if (!currentElement) setError('Element not found in this universe.');
                    } else {
                        setError('Universe not found.');
                    }
                } catch (err) {
                    setError('Failed to load data.');
                } finally {
                    setIsLoading(false);
                }
            }
            loadData();
        }
    }, [isClient, universeId, elementId]);

    const updateElementWithNewComponent = (newComponent: AnyComponent) => {
        setElement(prevElement => {
            if (!prevElement) return null;
            return {
                ...prevElement,
                components: [...prevElement.components, newComponent],
            };
        });
    };

    const handleTextComponentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newComponentContent.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') return;
        const newComponentData: Omit<TextComponent, 'id'> = {
            type: "TextComponent",
            data: { field: newComponentField, content: newComponentContent }
        };
        try {
            setIsAddingComponent(true);
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewComponentField('Description');
            setNewComponentContent('');
            toast.success('Text component added successfully');
        } catch (err) {
            toast.error('Failed to add text component. Please try again.');
        } finally {
            setIsAddingComponent(false);
        }
    };

    const handleImageGenerateSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newImagePrompt.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') return;

        setIsGenerating(true);
        try {
            const generatedData = await generateSimpleImage(newImagePrompt);
            const newComponentData: Omit<ImageComponent, 'id'> = {
                type: "ImageComponent",
                data: {
                    label: "AI Generated Image",
                    url: generatedData.url,
                    prompt: newImagePrompt,
                }
            };
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewImagePrompt('');
            toast.success('Image generated and added successfully');
        } catch (err) {
            toast.error('Failed to generate image. Please try again.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleMediaComponentSubmit = async (e: React.FormEvent, type: "VideoComponent" | "AudioComponent" | "Model3DComponent") => {
        e.preventDefault();
        if (!newMediaLabel.trim() || !newMediaUrl.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') {
            toast.warning('Please provide both a label and URL for the media component.');
            return;
        }
        const newComponentData: Omit<AnyComponent, 'id'> = {
            type: type,
            data: { label: newMediaLabel, url: newMediaUrl }
        };
        const mediaType = type.replace('Component', '').toLowerCase();
        try {
            setIsAddingComponent(true);
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewMediaLabel('');
            setNewMediaUrl('');
            toast.success(`${mediaType.charAt(0).toUpperCase() + mediaType.slice(1)} component added successfully`);
        } catch (err) {
            toast.error(`Failed to add ${mediaType} component. Please try again.`);
        } finally {
            setIsAddingComponent(false);
        }
    };

    const handleAttributeComponentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newAttributeKey.trim() || !newAttributeValue.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') {
            toast.warning('Please provide both an attribute key and value.');
            return;
        }
        const newComponentData: Omit<AttributeComponent, 'id'> = {
            type: "AttributeComponent",
            data: { attributes: { [newAttributeKey]: newAttributeValue } }
        };
        try {
            setIsAddingComponent(true);
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewAttributeKey('');
            setNewAttributeValue('');
            toast.success(`Attribute "${newAttributeKey}" added successfully`);
        } catch (err) {
            toast.error('Failed to add attribute. Please try again.');
        } finally {
            setIsAddingComponent(false);
        }
    };

    const handleRelationshipComponentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newRelationType.trim() || !newRelationTargetId.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') {
            toast.warning('Please provide both a relationship type and target element ID.');
            return;
        }
        const newComponentData: Omit<RelationshipComponent, 'id'> = {
            type: "RelationshipComponent",
            data: {
                relations: [{
                    target_element_id: newRelationTargetId,
                    type: newRelationType,
                    description: newRelationDescription || undefined
                }]
            }
        };
        try {
            setIsAddingComponent(true);
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewRelationType('');
            setNewRelationTargetId('');
            setNewRelationDescription('');
            toast.success(`Relationship "${newRelationType}" added successfully`);
        } catch (err) {
            toast.error('Failed to add relationship. Please try again.');
        } finally {
            setIsAddingComponent(false);
        }
    };

    if (!isClient || isLoading) return (
        <div className="px-4 py-6 sm:px-0" role="status" aria-label="Loading element details">
            <Skeleton className="h-4 w-48 mb-6" />
            <Skeleton className="h-10 w-2/3 mb-2" />
            <Skeleton className="h-6 w-32 mb-4" />
            <div className="bg-white rounded-lg shadow p-6 mb-6">
                <Skeleton className="h-6 w-48 mb-4" />
                <SkeletonText lines={3} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Skeleton className="h-32" />
                <Skeleton className="h-32" />
            </div>
            <span className="sr-only">Loading element details...</span>
        </div>
    );
    if (error) return (
        <div className="px-4 py-6 sm:px-0">
            <h1 className="text-2xl font-bold text-red-600 mb-4">{error}</h1>
            <Link href={`/universes/${universeId}`} className="text-indigo-600 hover:underline">&larr; Back to universe</Link>
        </div>
    );
    if (!element) return null;

    return (
        <div className="px-4 py-6 sm:px-0">
            <Link href={`/universes/${universeId}`} className="text-indigo-600 hover:underline mb-6 block">&larr; Back to {universe?.name || 'Universe'}</Link>

            {/* Element Header with Quick Actions */}
            <div className="mb-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900">{element.name}</h1>
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800 mt-2">
                            {element.element_type}
                        </span>
                    </div>
                    <Link
                        href={`/universes/${universeId}/elements/${elementId}/traits`}
                        className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors duration-150 text-sm font-medium self-start"
                    >
                        🏷️ Manage Traits
                    </Link>
                </div>
            </div>

            {/* AI Quick Actions - Prominent placement */}
            {quickActions.length > 0 && (
                <div className="bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center gap-2 mb-3">
                        <svg className="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <h3 className="font-semibold text-gray-900">AI Quick Actions</h3>
                        <span className="text-xs text-gray-500">for {element.element_type}s</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {quickActions.map((action, idx) => (
                            <button
                                key={idx}
                                onClick={() => handleQuickAction(action.prompt, action.label)}
                                disabled={isQuickActionRunning}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-violet-200 rounded-full text-sm font-medium text-violet-700 hover:bg-violet-50 hover:border-violet-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <span>{action.icon}</span>
                                {action.label}
                            </button>
                        ))}
                        {isQuickActionRunning && (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-violet-600">
                                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Generating...
                            </span>
                        )}
                    </div>
                </div>
            )}

            {/* Existing Components - Show FIRST so users see progress */}
            <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">
                    Content ({element.components.length})
                </h2>
                <div className="space-y-4">
                    {element.components.length > 0 ? (
                        element.components.map((component) => (
                            <div key={component.id} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                                {component.type === 'TextComponent' && <TextComponentDisplay component={component as TextComponent} />}
                                {component.type === 'ImageComponent' && <ImageComponentDisplay component={component as ImageComponent} />}
                                {component.type === 'VideoComponent' && <VideoComponentDisplay component={component as VideoComponent} />}
                                {component.type === 'AudioComponent' && <AudioComponentDisplay component={component as AudioComponent} />}
                                {component.type === 'Model3DComponent' && <Model3DComponentDisplay component={component as Model3DComponent} />}
                                {component.type === 'AttributeComponent' && <AttributeComponentDisplay component={component as AttributeComponent} />}
                                {component.type === 'RelationshipComponent' && <RelationshipComponentDisplay component={component as RelationshipComponent} />}
                            </div>
                        ))
                    ) : (
                        <EmptyComponents />
                    )}
                </div>
            </div>

            {/* Tabbed Form Section - Progressive Disclosure */}
            <div className="bg-white shadow-lg rounded-lg overflow-hidden">
                {/* Tab Navigation */}
                <div className="border-b border-gray-200">
                    <nav className="flex -mb-px" aria-label="Component types">
                        <button
                            onClick={() => setActiveTab('description')}
                            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === 'description'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            📝 Text & Images
                        </button>
                        <button
                            onClick={() => setActiveTab('media')}
                            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === 'media'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            🎬 Media Files
                        </button>
                        <button
                            onClick={() => setActiveTab('data')}
                            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === 'data'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                        >
                            🔗 Data & Relations
                        </button>
                    </nav>
                </div>

                {/* Tab Content */}
                <div className="p-6">
                    {/* Text & Images Tab */}
                    {activeTab === 'description' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Text Component Form */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-800 mb-3">Add Text</h3>
                                <form onSubmit={handleTextComponentSubmit} className="space-y-3">
                                    <div>
                                        <label htmlFor="component-field" className="block text-sm font-medium text-gray-700">Field Name</label>
                                        <input id="component-field" type="text" value={newComponentField} onChange={(e) => setNewComponentField(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                                    </div>
                                    <div>
                                        <label htmlFor="component-content" className="block text-sm font-medium text-gray-700">Content</label>
                                        <textarea id="component-content" value={newComponentContent} onChange={(e) => setNewComponentContent(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" rows={4} placeholder="Write a description, backstory, or any text content..." />
                                    </div>
                                    <button type="submit" disabled={isAddingComponent} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
                                        {isAddingComponent ? 'Adding...' : 'Add Text'}
                                    </button>
                                </form>
                            </div>

                            {/* Image Generation Form */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-800 mb-3">Generate Image</h3>
                                <form onSubmit={handleImageGenerateSubmit} className="space-y-3">
                                    <div>
                                        <label htmlFor="image-prompt" className="block text-sm font-medium text-gray-700">AI Prompt</label>
                                        <textarea id="image-prompt" value={newImagePrompt} onChange={(e) => setNewImagePrompt(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" rows={4} placeholder={`Describe the ${element.element_type.toLowerCase()} visually...`} />
                                    </div>
                                    <button type="submit" disabled={isGenerating} className="inline-flex items-center justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50">
                                        {isGenerating ? (
                                            <>
                                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                                Generating...
                                            </>
                                        ) : 'Generate Image'}
                                    </button>
                                </form>
                            </div>
                        </div>
                    )}

                    {/* Media Files Tab */}
                    {activeTab === 'media' && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-800 mb-3">Add Media File</h3>
                            <p className="text-sm text-gray-500 mb-4">Add videos, audio clips, or 3D models by providing a URL.</p>
                            <form className="space-y-3 max-w-xl">
                                <div>
                                    <label htmlFor="media-label" className="block text-sm font-medium text-gray-700">Label</label>
                                    <input id="media-label" type="text" value={newMediaLabel} onChange={(e) => setNewMediaLabel(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., Character Voice Sample" />
                                </div>
                                <div>
                                    <label htmlFor="media-url" className="block text-sm font-medium text-gray-700">URL</label>
                                    <input id="media-url" type="text" value={newMediaUrl} onChange={(e) => setNewMediaUrl(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="https://..." />
                                </div>
                                <div className="flex flex-wrap gap-2 pt-2">
                                    <button type="button" onClick={(e) => handleMediaComponentSubmit(e, "VideoComponent")} disabled={isAddingComponent} className="inline-flex items-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">
                                        🎬 Add Video
                                    </button>
                                    <button type="button" onClick={(e) => handleMediaComponentSubmit(e, "AudioComponent")} disabled={isAddingComponent} className="inline-flex items-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50">
                                        🔊 Add Audio
                                    </button>
                                    <button type="button" onClick={(e) => handleMediaComponentSubmit(e, "Model3DComponent")} disabled={isAddingComponent} className="inline-flex items-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50">
                                        🎲 Add 3D Model
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    {/* Data & Relations Tab */}
                    {activeTab === 'data' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Attributes Form */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-800 mb-3">Add Attribute</h3>
                                <p className="text-sm text-gray-500 mb-3">Store stats, properties, or metadata.</p>
                                <form onSubmit={handleAttributeComponentSubmit} className="space-y-3">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label htmlFor="attribute-key" className="block text-sm font-medium text-gray-700">Key</label>
                                            <input id="attribute-key" type="text" value={newAttributeKey} onChange={(e) => setNewAttributeKey(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., Age" />
                                        </div>
                                        <div>
                                            <label htmlFor="attribute-value" className="block text-sm font-medium text-gray-700">Value</label>
                                            <input id="attribute-value" type="text" value={newAttributeValue} onChange={(e) => setNewAttributeValue(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., 35" />
                                        </div>
                                    </div>
                                    <button type="submit" disabled={isAddingComponent} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 disabled:opacity-50">
                                        Add Attribute
                                    </button>
                                </form>
                            </div>

                            {/* Relationships Form */}
                            <div>
                                <h3 className="text-lg font-semibold text-gray-800 mb-3">Add Relationship</h3>
                                <p className="text-sm text-gray-500 mb-3">Connect this element to others.</p>
                                <form onSubmit={handleRelationshipComponentSubmit} className="space-y-3">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label htmlFor="relation-type" className="block text-sm font-medium text-gray-700">Relationship</label>
                                            <input id="relation-type" type="text" value={newRelationType} onChange={(e) => setNewRelationType(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., FriendOf" />
                                        </div>
                                        <div>
                                            <label htmlFor="relation-target-id" className="block text-sm font-medium text-gray-700">Target ID</label>
                                            <input id="relation-target-id" type="text" value={newRelationTargetId} onChange={(e) => setNewRelationTargetId(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="Element UUID" />
                                        </div>
                                    </div>
                                    <div>
                                        <label htmlFor="relation-description" className="block text-sm font-medium text-gray-700">Description (Optional)</label>
                                        <input id="relation-description" type="text" value={newRelationDescription} onChange={(e) => setNewRelationDescription(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="How are they related?" />
                                    </div>
                                    <button type="submit" disabled={isAddingComponent} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50">
                                        Add Relationship
                                    </button>
                                </form>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}