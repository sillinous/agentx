// A simple API client for interacting with the backend.

// Default to the backend's uvicorn port (8000). Override with `NEXT_PUBLIC_API_URL`.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// Auth error event for cross-component communication
export const AUTH_ERROR_EVENT = 'auth:error';

// --- Type Definitions (mirroring backend Pydantic models) ---

export interface BaseComponent {
    id: string;
    type: string;
}

export interface TextComponent extends BaseComponent {
    type: "TextComponent";
    data: {
        field: string;
        content: string;
    };
}

export interface ImageComponent extends BaseComponent {
    type: "ImageComponent";
    data: {
        label: string;
        url: string;
        prompt: string;
    };
}

export interface VideoComponent extends BaseComponent {
    type: "VideoComponent";
    data: {
        label: string;
        url: string;
    };
}

export interface AudioComponent extends BaseComponent {
    type: "AudioComponent";
    data: {
        label: string;
        url: string;
    };
}

export interface Model3DComponent extends BaseComponent {
    type: "Model3DComponent";
    data: {
        label: string;
        url: string;
    };
}

export interface AttributeComponent extends BaseComponent {
    type: "AttributeComponent";
    data: {
        attributes: { [key: string]: any };
    };
}

export interface RelationshipComponent extends BaseComponent {
    type: "RelationshipComponent";
    data: {
        relations: Array<{
            target_element_id: string;
            type: string;
            description?: string;
        }>;
    };
}

export type AnyComponent = TextComponent | ImageComponent | VideoComponent | AudioComponent | Model3DComponent | AttributeComponent | RelationshipComponent; // Expanded union

export interface Universe {
    id: string; // UUIDs are strings in JSON
    name: string;
    description: string;
    elements: Element[];
}

export interface Element {
    id: string;
    universe_id: string;
    name: string;
    element_type: string;
    entity_subtype?: string; // Phase 1: character, location, item, etc.
    components: AnyComponent[];
}

// --- Phase 1: World Building Types ---

export interface WorldConfig {
    id: string;
    universe_id: string;
    genre: string;
    physics?: string;
    magic_system?: string;
    tech_level?: string;
    tone?: string;
    color_palette?: { [key: string]: string };
    art_style_notes?: string;
    reference_images?: string[];
    created_at: string;
    updated_at: string;
}

export interface EntityTrait {
    id: string;
    element_id: string;
    trait_key: string;
    trait_value?: string;
    trait_type?: string;
    trait_category?: string;
    display_order: number;
    is_ai_visible: boolean;
    created_at: string;
    updated_at: string;
}

export interface TraitTemplate {
    key: string;
    label: string;
    type: string;
    category: string;
    description?: string;
    placeholder?: string;
}

export interface TimelineEvent {
    id: string;
    universe_id: string;
    title: string;
    description?: string;
    event_timestamp: string;
    event_type?: string;
    participants?: string[];
    location_id?: string;
    significance?: string;
    consequences?: string;
    created_at: string;
    updated_at: string;
}

// --- API Functions ---

function getAuthToken(): string | null {
    // Prefer runtime-localStorage, fallback to build-time env var
    try {
        if (typeof window !== 'undefined') {
            const t = window.localStorage.getItem('UMAM_TOKEN');
            if (t) return t;
        }
    } catch {
        // ignore
    }
    return process.env.NEXT_PUBLIC_AUTH_TOKEN || null;
}

function authHeaders(): Record<string, string> {
    const token = getAuthToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Fetches all universes from the backend.
 */
export async function getAllUniverses(): Promise<Universe[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/universes`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch universes:", error);
        return []; // Return an empty array on error
    }
}

/**
 * Fetches a single universe by its ID.
 * @param universeId The ID of the universe to fetch.
 */
export async function getUniverseById(universeId: string): Promise<Universe | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/universes/${universeId}`);
        if (!response.ok) {
            if (response.status === 404) {
                return null; // Handle not found gracefully
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch universe with ID ${universeId}:`, error);
        return null;
    }
}


/**
 * Creates a new universe.
 * @param universeData - The data for the new universe.
 */
export async function createUniverse(universeData: { name: string; description: string }): Promise<Universe> {
    const response = await fetch(`${API_BASE_URL}/universes`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(universeData),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Adds a new element to a universe.
 * @param universeId The ID of the universe.
 * @param elementData The data for the new element.
 */
export async function addElementToUniverse(universeId: string, elementData: { name: string; element_type: string }): Promise<Element> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(elementData),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Adds a new component to an element.
 * @param universeId The ID of the universe containing the element.
 * @param elementId The ID of the element.
 * @param component The component data to add.
 */
export async function addComponentToElement(universeId: string, elementId: string, component: Omit<AnyComponent, 'id'>): Promise<AnyComponent> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements/${elementId}/components`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(component),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Calls the AI service to generate an image from a prompt.
 * @param prompt The text prompt for the image generation.
 */
export async function generateImage(prompt: string): Promise<{ url: string }> {
    const response = await fetch(`${API_BASE_URL}/ai/generate/image`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify({ prompt }),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// =============================================================================
// Phase 1: World Configuration API Functions
// =============================================================================

/**
 * Gets world configuration for a universe.
 */
export async function getWorldConfig(universeId: string): Promise<WorldConfig | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/universes/${universeId}/world-config`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            if (response.status === 404) {
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch world config for universe ${universeId}:`, error);
        return null;
    }
}

/**
 * Creates world configuration for a universe.
 */
export async function createWorldConfig(universeId: string, data: Omit<WorldConfig, 'id' | 'universe_id' | 'created_at' | 'updated_at'>): Promise<WorldConfig> {
    const response = await fetch(`${API_BASE_URL}/api/universes/${universeId}/world-config`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Updates world configuration for a universe.
 */
export async function updateWorldConfig(universeId: string, data: Partial<Omit<WorldConfig, 'id' | 'universe_id' | 'created_at' | 'updated_at'>>): Promise<WorldConfig> {
    const response = await fetch(`${API_BASE_URL}/api/universes/${universeId}/world-config`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Deletes world configuration for a universe.
 */
export async function deleteWorldConfig(universeId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/universes/${universeId}/world-config`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
}

// =============================================================================
// Phase 1: Entity Traits API Functions
// =============================================================================

/**
 * Gets trait templates for an entity type.
 */
export async function getTraitTemplates(entityType: string): Promise<{ entity_type: string; templates: TraitTemplate[] }> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/entity-types/${entityType}/traits`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch trait templates for ${entityType}:`, error);
        return { entity_type: entityType, templates: [] };
    }
}

/**
 * Lists all traits for an element.
 */
export async function listTraits(elementId: string, category?: string): Promise<EntityTrait[]> {
    try {
        const url = category
            ? `${API_BASE_URL}/api/elements/${elementId}/traits?category=${encodeURIComponent(category)}`
            : `${API_BASE_URL}/api/elements/${elementId}/traits`;
        const response = await fetch(url, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch traits for element ${elementId}:`, error);
        return [];
    }
}

/**
 * Gets a specific trait by ID.
 */
export async function getTrait(elementId: string, traitId: string): Promise<EntityTrait | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/elements/${elementId}/traits/${traitId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            if (response.status === 404) {
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch trait ${traitId}:`, error);
        return null;
    }
}

/**
 * Adds a new trait to an element.
 */
export async function addTrait(elementId: string, trait: Omit<EntityTrait, 'id' | 'element_id' | 'created_at' | 'updated_at'>): Promise<EntityTrait> {
    const response = await fetch(`${API_BASE_URL}/api/elements/${elementId}/traits`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(trait),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Updates an existing trait.
 */
export async function updateTrait(elementId: string, traitId: string, data: Partial<Omit<EntityTrait, 'id' | 'element_id' | 'created_at' | 'updated_at'>>): Promise<EntityTrait> {
    const response = await fetch(`${API_BASE_URL}/api/elements/${elementId}/traits/${traitId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Deletes a trait.
 */
export async function deleteTrait(elementId: string, traitId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/elements/${elementId}/traits/${traitId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
}

// =============================================================================
// Phase 1: Timeline Events API Functions
// =============================================================================

/**
 * Lists timeline events for a universe with optional filtering.
 */
export async function listTimelineEvents(
    universeId: string,
    filters?: {
        start_date?: string;
        end_date?: string;
        event_type?: string;
        significance?: string;
        limit?: number;
    }
): Promise<TimelineEvent[]> {
    try {
        const params = new URLSearchParams();
        if (filters?.start_date) params.append('start_date', filters.start_date);
        if (filters?.end_date) params.append('end_date', filters.end_date);
        if (filters?.event_type) params.append('event_type', filters.event_type);
        if (filters?.significance) params.append('significance', filters.significance);
        if (filters?.limit) params.append('limit', filters.limit.toString());

        const url = `${API_BASE_URL}/api/universes/${universeId}/timeline${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch timeline events for universe ${universeId}:`, error);
        return [];
    }
}

/**
 * Gets a specific timeline event by ID.
 */
export async function getTimelineEvent(eventId: string): Promise<TimelineEvent | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/timeline/${eventId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            if (response.status === 404) {
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch timeline event ${eventId}:`, error);
        return null;
    }
}

/**
 * Creates a new timeline event.
 */
export async function createTimelineEvent(universeId: string, event: Omit<TimelineEvent, 'id' | 'universe_id' | 'created_at' | 'updated_at'>): Promise<TimelineEvent> {
    const response = await fetch(`${API_BASE_URL}/api/universes/${universeId}/timeline`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(event),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Updates a timeline event.
 */
export async function updateTimelineEvent(eventId: string, data: Partial<Omit<TimelineEvent, 'id' | 'universe_id' | 'created_at' | 'updated_at'>>): Promise<TimelineEvent> {
    const response = await fetch(`${API_BASE_URL}/api/timeline/${eventId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Deletes a timeline event.
 */
export async function deleteTimelineEvent(eventId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/timeline/${eventId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
}

/**
 * Gets participant details for a timeline event.
 */
export async function getEventParticipants(eventId: string): Promise<{ event_id: string; participants: Array<{ id: string; name: string; element_type: string; entity_subtype?: string }> }> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/timeline/${eventId}/participants`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch participants for event ${eventId}:`, error);
        return { event_id: eventId, participants: [] };
    }
}

// =============================================================================
// Phase 4: Video Generation API Functions
// =============================================================================

export interface VideoJob {
    id: string;
    universe_id?: string;
    generation_type: string;
    prompt: string;
    status: string;
    provider?: string;
    provider_job_id?: string;
    mood_category?: string;
    camera_movement?: string;
    output_video_url?: string;
    created_at?: string;
    completed_at?: string;
    error_message?: string;
}

export interface VideoGenerateRequest {
    universe_id?: string;
    generation_type?: string;
    prompt: string;
    negative_prompt?: string;
    reference_image_url?: string;
    mood?: number;
    aspect_ratio?: string;
    duration?: number;
}

export interface VideoStrategyVariation {
    mood_category: string;
    camera_movement: string;
    enriched_prompt: string;
    pacing: string;
    lighting: string;
    color_grading: string;
}

/**
 * Creates a video generation job.
 */
export async function generateVideo(request: VideoGenerateRequest): Promise<{
    job_id: string;
    status: string;
    provider_job_id?: string;
    strategy: { mood_category: string; camera_movement: string; enriched_prompt: string };
}> {
    const response = await fetch(`${API_BASE_URL}/api/video/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(request),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Lists video generation jobs.
 */
export async function listVideoJobs(filters?: {
    universe_id?: string;
    status?: string;
    limit?: number;
}): Promise<{ jobs: VideoJob[]; total: number }> {
    try {
        const params = new URLSearchParams();
        if (filters?.universe_id) params.append('universe_id', filters.universe_id);
        if (filters?.status) params.append('status', filters.status);
        if (filters?.limit) params.append('limit', filters.limit.toString());

        const url = `${API_BASE_URL}/api/video/jobs${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url, { headers: authHeaders() });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch video jobs:', error);
        return { jobs: [], total: 0 };
    }
}

/**
 * Gets a specific video job with status update.
 */
export async function getVideoJob(jobId: string): Promise<VideoJob | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/video/jobs/${jobId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch video job ${jobId}:`, error);
        return null;
    }
}

/**
 * Generates video strategy variations without creating a job.
 */
export async function generateVideoStrategy(request: {
    prompt: string;
    mood?: number;
    platform?: string;
    num_variations?: number;
}): Promise<{
    success: boolean;
    variations: VideoStrategyVariation[];
    mood_category: string;
}> {
    const response = await fetch(`${API_BASE_URL}/api/video/strategy`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(request),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

// =============================================================================
// Phase 4: Audio Processing API Functions
// =============================================================================

export interface AudioJob {
    job_id: string;
    status: string;
    result?: {
        success: boolean;
        transcription?: string;
        audio_url?: string;
        duration?: number;
        error?: string;
    };
}

/**
 * Transcribes audio to text.
 */
export async function transcribeAudio(request: {
    audio_url: string;
    universe_id?: string;
    provider?: string;
}): Promise<AudioJob> {
    const response = await fetch(`${API_BASE_URL}/api/audio/transcribe`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(request),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Converts text to speech.
 */
export async function textToSpeech(request: {
    text: string;
    voice?: string;
    universe_id?: string;
    provider?: string;
}): Promise<AudioJob> {
    const response = await fetch(`${API_BASE_URL}/api/audio/tts`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(request),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Analyzes audio characteristics.
 */
export async function analyzeAudio(request: {
    audio_url: string;
    universe_id?: string;
    provider?: string;
}): Promise<{
    success: boolean;
    analysis?: {
        duration: number;
        format: string;
        sample_rate: number;
        channels: number;
    };
}> {
    const response = await fetch(`${API_BASE_URL}/api/audio/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(request),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}


