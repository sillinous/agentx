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
    generateImage
} from '@/services/api';
import { useIsClient } from '@/hooks/useIsClient';

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
                        <span className="text-gray-900">{value}</span>
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

export default function ElementDetailPage() {
    const params = useParams();
    const { universeId, elementId } = params;

    const [universe, setUniverse] = useState<Universe | null>(null);
    const [element, setElement] = useState<Element | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const isClient = useIsClient();

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
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewComponentField('Description');
            setNewComponentContent('');
        } catch (err) { alert('Failed to add text component.'); }
    };

    const handleImageGenerateSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newImagePrompt.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') return;
        
        setIsGenerating(true);
        try {
            const generatedData = await generateImage(newImagePrompt);
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
        } catch (err) {
            alert('Failed to generate or add image component.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleMediaComponentSubmit = async (e: React.FormEvent, type: "VideoComponent" | "AudioComponent" | "Model3DComponent") => {
        e.preventDefault();
        if (!newMediaLabel.trim() || !newMediaUrl.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') {
            alert('Label and URL cannot be empty.');
            return;
        }
        const newComponentData: Omit<AnyComponent, 'id'> = {
            type: type,
            data: { label: newMediaLabel, url: newMediaUrl }
        };
        try {
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewMediaLabel('');
            setNewMediaUrl('');
        } catch (err) {
            alert(`Failed to add ${type.replace('Component', '').toLowerCase()} component.`);
        }
    };

    const handleAttributeComponentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newAttributeKey.trim() || !newAttributeValue.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') {
            alert('Attribute key and value cannot be empty.');
            return;
        }
        const newComponentData: Omit<AttributeComponent, 'id'> = {
            type: "AttributeComponent",
            data: { attributes: { [newAttributeKey]: newAttributeValue } }
        };
        try {
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewAttributeKey('');
            setNewAttributeValue('');
        } catch (err) {
            alert('Failed to add attribute component.');
        }
    };

    const handleRelationshipComponentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newRelationType.trim() || !newRelationTargetId.trim() || typeof universeId !== 'string' || typeof elementId !== 'string') {
            alert('Relationship type and target ID cannot be empty.');
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
            const addedComponent = await addComponentToElement(universeId, elementId, newComponentData);
            updateElementWithNewComponent(addedComponent);
            setNewRelationType('');
            setNewRelationTargetId('');
            setNewRelationDescription('');
        } catch (err) {
            alert('Failed to add relationship component.');
        }
    };

    if (!isClient || isLoading) return (
        <div className="px-4 py-6 sm:px-0">
            <p className="text-gray-600">Loading...</p>
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

            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900">{element.name}</h1>
                <p className="text-lg text-gray-500 font-mono mt-2">{element.element_type}</p>
                <div className="mt-4">
                    <Link
                        href={`/universes/${universeId}/elements/${elementId}/traits`}
                        className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors duration-150 text-sm font-medium"
                    >
                        🏷️ Manage Entity Traits
                    </Link>
                </div>
            </div>

            {/* Forms Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                {/* Add Text Component Form */}
                <div className="bg-white shadow-lg rounded-lg p-6">
                    <h2 className="text-2xl font-semibold text-gray-800 mb-4">Add Text Component</h2>
                    <form onSubmit={handleTextComponentSubmit} className="space-y-4">
                        <div>
                            <label htmlFor="component-field" className="block text-sm font-medium text-gray-700">Field Name</label>
                            <input id="component-field" type="text" value={newComponentField} onChange={(e) => setNewComponentField(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                        </div>
                        <div>
                            <label htmlFor="component-content" className="block text-sm font-medium text-gray-700">Content</label>
                            <textarea id="component-content" value={newComponentContent} onChange={(e) => setNewComponentContent(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" rows={5} />
                        </div>
                        <button type="submit" className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out">Add Text</button>
                    </form>
                </div>

                {/* Add Image Component Form */}
                <div className="bg-white shadow-lg rounded-lg p-6">
                    <h2 className="text-2xl font-semibold text-gray-800 mb-4">Generate Image Component</h2>
                    <form onSubmit={handleImageGenerateSubmit} className="space-y-4">
                        <div>
                            <label htmlFor="image-prompt" className="block text-sm font-medium text-gray-700">AI Prompt</label>
                            <textarea id="image-prompt" value={newImagePrompt} onChange={(e) => setNewImagePrompt(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" rows={5} placeholder="e.g., A photorealistic portrait of a starship captain..." />
                        </div>
                        <button type="submit" disabled={isGenerating} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition duration-150 ease-in-out">
                            {isGenerating ? 'Generating...' : 'Generate Image'}
                        </button>
                    </form>
                </div>

                {/* Add Media Component Form (Video, Audio, 3D Model) */}
                <div className="bg-white shadow-lg rounded-lg p-6">
                    <h2 className="text-2xl font-semibold text-gray-800 mb-4">Add Media Component</h2>
                    <form className="space-y-4">
                        <div>
                            <label htmlFor="media-label" className="block text-sm font-medium text-gray-700">Label</label>
                            <input id="media-label" type="text" value={newMediaLabel} onChange={(e) => setNewMediaLabel(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., Intro Video" />
                        </div>
                        <div>
                            <label htmlFor="media-url" className="block text-sm font-medium text-gray-700">URL</label>
                            <input id="media-url" type="text" value={newMediaUrl} onChange={(e) => setNewMediaUrl(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., https://example.com/video.mp4" />
                        </div>
                        <div className="flex space-x-4">
                            <button type="button" onClick={(e) => handleMediaComponentSubmit(e, "VideoComponent")} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out">Add Video</button>
                            <button type="button" onClick={(e) => handleMediaComponentSubmit(e, "AudioComponent")} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition duration-150 ease-in-out">Add Audio</button>
                            <button type="button" onClick={(e) => handleMediaComponentSubmit(e, "Model3DComponent")} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 transition duration-150 ease-in-out">Add 3D Model</button>
                        </div>
                    </form>
                </div>

                {/* Add Attribute Component Form */}
                <div className="bg-white shadow-lg rounded-lg p-6">
                    <h2 className="text-2xl font-semibold text-gray-800 mb-4">Add Attribute</h2>
                    <form onSubmit={handleAttributeComponentSubmit} className="space-y-4">
                        <div>
                            <label htmlFor="attribute-key" className="block text-sm font-medium text-gray-700">Key</label>
                            <input id="attribute-key" type="text" value={newAttributeKey} onChange={(e) => setNewAttributeKey(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., Strength" />
                        </div>
                        <div>
                            <label htmlFor="attribute-value" className="block text-sm font-medium text-gray-700">Value</label>
                            <input id="attribute-value" type="text" value={newAttributeValue} onChange={(e) => setNewAttributeValue(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., 10" />
                        </div>
                        <button type="submit" className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 transition duration-150 ease-in-out">Add Attribute</button>
                    </form>
                </div>

                {/* Add Relationship Component Form */}
                <div className="bg-white shadow-lg rounded-lg p-6">
                    <h2 className="text-2xl font-semibold text-gray-800 mb-4">Add Relationship</h2>
                    <form onSubmit={handleRelationshipComponentSubmit} className="space-y-4">
                        <div>
                            <label htmlFor="relation-type" className="block text-sm font-medium text-gray-700">Type</label>
                            <input id="relation-type" type="text" value={newRelationType} onChange={(e) => setNewRelationType(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., ParentOf" />
                        </div>
                        <div>
                            <label htmlFor="relation-target-id" className="block text-sm font-medium text-gray-700">Target Element ID</label>
                            <input id="relation-target-id" type="text" value={newRelationTargetId} onChange={(e) => setNewRelationTargetId(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="e.g., a1b2c3d4-e5f6-7890-1234-567890abcdef" />
                        </div>
                        <div>
                            <label htmlFor="relation-description" className="block text-sm font-medium text-gray-700">Description (Optional)</label>
                            <textarea id="relation-description" value={newRelationDescription} onChange={(e) => setNewRelationDescription(e.target.value)} className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" rows={2} />
                        </div>
                        <button type="submit" className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition duration-150 ease-in-out">Add Relationship</button>
                    </form>
                </div>
            </div>

            {/* Existing Components List */}
            <div className="bg-white shadow-lg rounded-lg p-6">
                <h2 className="text-2xl font-semibold text-gray-800 mb-4">Components</h2>
                <div className="space-y-6">
                    {element.components.length > 0 ? (
                        element.components.map((component) => (
                            <div key={component.id} className="p-4 border border-gray-200 rounded-md">
                                {component.type === 'TextComponent' && <TextComponentDisplay component={component as TextComponent} />}
                                {component.type === 'ImageComponent' && <ImageComponentDisplay component={component as ImageComponent} />}
                                {component.type === 'VideoComponent' && <VideoComponentDisplay component={component as VideoComponent} />}
                                {component.type === 'AudioComponent' && <AudioComponentDisplay component={component as AudioComponent} />}
                                {component.type === 'Model3DComponent' && <Model3DComponentDisplay component={component as Model3DComponent} />}
                                {component.type === 'AttributeComponent' && <AttributeComponentDisplay component={component as AttributeComponent} />}
                                {component.type === 'RelationshipComponent' && <RelationshipComponentDisplay component={component as RelationshipComponent} />}
                                <p className="text-xs text-gray-400 mt-2 font-mono">Type: {component.type}</p>
                            </div>
                        ))
                    ) : (
                        <p className="text-gray-500">No components added yet.</p>
                    )}
                </div>
            </div>
        </div>
    );
}