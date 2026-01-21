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
        attributes: Record<string, unknown>;
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
/**
 * Fetches all universes with optional pagination and search.
 * @param options - Pagination and search options
 */
export async function getAllUniverses(options?: {
    limit?: number;
    offset?: number;
    search?: string;
}): Promise<Universe[]> {
    try {
        const params = new URLSearchParams();
        if (options?.limit) params.append('limit', options.limit.toString());
        if (options?.offset) params.append('offset', options.offset.toString());
        if (options?.search) params.append('search', options.search);
        
        const url = `${API_BASE_URL}/universes${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
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
 * Gets elements in a universe with optional pagination and filtering.
 * @param universeId The ID of the universe.
 * @param options - Pagination and filter options
 */
export async function getElementsInUniverse(universeId: string, options?: {
    limit?: number;
    offset?: number;
    search?: string;
    element_type?: string;
}): Promise<Element[]> {
    try {
        const params = new URLSearchParams();
        if (options?.limit) params.append('limit', options.limit.toString());
        if (options?.offset) params.append('offset', options.offset.toString());
        if (options?.search) params.append('search', options.search);
        if (options?.element_type) params.append('element_type', options.element_type);
        
        const url = `${API_BASE_URL}/universes/${universeId}/elements${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch elements for universe ${universeId}:`, error);
        return [];
    }
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

// =============================================================================
// Universe CRUD Operations
// =============================================================================

/**
 * Updates an existing universe.
 * @param universeId The ID of the universe to update.
 * @param updateData The data to update (name, description).
 */
export async function updateUniverse(universeId: string, updateData: { name?: string; description?: string }): Promise<Universe> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(updateData),
    });
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT, { detail: { status: response.status } }));
        }
        const error = await response.json().catch(() => ({ detail: 'Update failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Deletes a universe and all its contents.
 * @param universeId The ID of the universe to delete.
 */
export async function deleteUniverse(universeId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT, { detail: { status: response.status } }));
        }
        const error = await response.json().catch(() => ({ detail: 'Delete failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
}

// =============================================================================
// Element CRUD Operations
// =============================================================================

/**
 * Gets a single element by its ID.
 * @param universeId The ID of the universe containing the element.
 * @param elementId The ID of the element to fetch.
 */
export async function getElementById(universeId: string, elementId: string): Promise<Element | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements/${elementId}`);
        if (!response.ok) {
            if (response.status === 404) {
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch element ${elementId}:`, error);
        return null;
    }
}

/**
 * Updates an existing element.
 * @param universeId The ID of the universe containing the element.
 * @param elementId The ID of the element to update.
 * @param updateData The data to update (name, element_type).
 */
export async function updateElement(universeId: string, elementId: string, updateData: { name?: string; element_type?: string }): Promise<Element> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements/${elementId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(updateData),
    });
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT, { detail: { status: response.status } }));
        }
        const error = await response.json().catch(() => ({ detail: 'Update failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Deletes an element and all its components.
 * @param universeId The ID of the universe containing the element.
 * @param elementId The ID of the element to delete.
 */
export async function deleteElement(universeId: string, elementId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements/${elementId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT, { detail: { status: response.status } }));
        }
        const error = await response.json().catch(() => ({ detail: 'Delete failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
}

// =============================================================================
// Component CRUD Operations
// =============================================================================

/**
 * Gets all components for an element.
 * @param universeId The ID of the universe.
 * @param elementId The ID of the element.
 * @param componentType Optional filter by component type.
 */
export async function getComponentsForElement(universeId: string, elementId: string, componentType?: string): Promise<AnyComponent[]> {
    try {
        const params = new URLSearchParams();
        if (componentType) params.append('component_type', componentType);

        const url = `${API_BASE_URL}/universes/${universeId}/elements/${elementId}/components${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch components for element ${elementId}:`, error);
        return [];
    }
}

/**
 * Gets a single component by its ID.
 * @param universeId The ID of the universe.
 * @param elementId The ID of the element.
 * @param componentId The ID of the component to fetch.
 */
export async function getComponentById(universeId: string, elementId: string, componentId: string): Promise<AnyComponent | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements/${elementId}/components/${componentId}`);
        if (!response.ok) {
            if (response.status === 404) {
                return null;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch component ${componentId}:`, error);
        return null;
    }
}

/**
 * Updates an existing component.
 * @param universeId The ID of the universe.
 * @param elementId The ID of the element.
 * @param componentId The ID of the component to update.
 * @param updateData The data to update (type, data).
 */
export async function updateComponent(
    universeId: string,
    elementId: string,
    componentId: string,
    updateData: { type?: string; data?: Record<string, unknown> }
): Promise<AnyComponent> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements/${elementId}/components/${componentId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify(updateData),
    });
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT, { detail: { status: response.status } }));
        }
        const error = await response.json().catch(() => ({ detail: 'Update failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Deletes a component.
 * @param universeId The ID of the universe.
 * @param elementId The ID of the element.
 * @param componentId The ID of the component to delete.
 */
export async function deleteComponent(universeId: string, elementId: string, componentId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/universes/${universeId}/elements/${elementId}/components/${componentId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT, { detail: { status: response.status } }));
        }
        const error = await response.json().catch(() => ({ detail: 'Delete failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
}

/**
 * Calls the AI service to generate a simple image from a prompt.
 * @param prompt The text prompt for the image generation.
 * @deprecated Use generateImage with ImageGenerateRequest for full functionality
 */
export async function generateSimpleImage(prompt: string): Promise<{ url: string }> {
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
// 3D Model Upload API Functions
// =============================================================================

export interface Model3DUploadResponse {
    model_id: string;
    filename: string;
    url: string;
    file_size: number;
    format: string;
}

export interface Model3DInfo {
    model_id: string;
    filename: string;
    url: string;
    file_size: number;
    format: string;
    universe_id: string | null;
}

/**
 * Upload a 3D model file (GLTF/GLB).
 * @param file The 3D model file to upload
 * @param universeId Optional universe ID to associate the model with
 */
export async function uploadModel(file: File, universeId?: string): Promise<Model3DUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    let url = `${API_BASE_URL}/api/models/upload`;
    if (universeId) {
        url += `?universe_id=${encodeURIComponent(universeId)}`;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers: authHeaders(),
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

/**
 * Get information about an uploaded 3D model.
 * @param modelId The model ID
 */
export async function getModelInfo(modelId: string): Promise<Model3DInfo | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/models/${modelId}`, {
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
        console.error(`Failed to get model info for ${modelId}:`, error);
        return null;
    }
}

/**
 * Delete an uploaded 3D model.
 * @param modelId The model ID to delete
 */
export async function deleteModel(modelId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/models/${modelId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
}

/**
 * List uploaded 3D models.
 * @param options Filter and pagination options
 */
export async function listModels(options?: {
    universeId?: string;
    limit?: number;
    offset?: number;
}): Promise<{ models: Model3DInfo[]; total: number; has_more: boolean }> {
    const params = new URLSearchParams();
    if (options?.universeId) params.append('universe_id', options.universeId);
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());

    const url = `${API_BASE_URL}/api/models/?${params.toString()}`;
    const response = await fetch(url, {
        headers: authHeaders(),
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
    agent_job_id?: string;

    // Request parameters
    generation_type: string;
    prompt: string;
    negative_prompt?: string;
    reference_image_url?: string;

    // Strategy parameters
    mood_category?: string;
    camera_movement?: string;
    aspect_ratio?: string;
    duration?: number;

    // Provider details
    provider?: string;
    provider_job_id?: string;
    provider_status?: string;

    // LTX-2 specific parameters
    ltx_model?: string;
    ltx_resolution?: string;
    ltx_fps?: number;
    audio_sync_enabled?: boolean;
    ltx_request_id?: string;

    // Generated content
    video_url?: string;
    output_video_url?: string;  // Legacy alias for video_url
    thumbnail_url?: string;
    local_path?: string;
    file_size?: number;

    // Metadata
    status: string;
    error_message?: string;
    extra_metadata?: Record<string, unknown>;
    created_at?: string;
    started_at?: string;
    completed_at?: string;
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
    
    // Provider selection
    provider?: string;
    
    // LTX-2 specific parameters
    ltx_model?: string;
    ltx_resolution?: string;
    ltx_fps?: number;
    audio_sync_enabled?: boolean;
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
    provider?: string;
    limit?: number;
    offset?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
}): Promise<{ jobs: VideoJob[]; total: number; has_more: boolean }> {
    try {
        const params = new URLSearchParams();
        if (filters?.universe_id) params.append('universe_id', filters.universe_id);
        if (filters?.status) params.append('status', filters.status);
        if (filters?.provider) params.append('provider', filters.provider);
        if (filters?.limit) params.append('limit', filters.limit.toString());
        if (filters?.offset) params.append('offset', filters.offset.toString());
        if (filters?.sort_by) params.append('sort_by', filters.sort_by);
        if (filters?.sort_order) params.append('sort_order', filters.sort_order);

        const url = `${API_BASE_URL}/api/video/jobs${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url, { headers: authHeaders() });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch video jobs:', error);
        return { jobs: [], total: 0, has_more: false };
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
// Video Transcoding API Functions
// =============================================================================

export interface TranscodeProfile {
    name: string;
    resolution: string;
    codec: string;
    bitrate: string;
    container: string;
    description: string;
}

export interface TranscodeVariant {
    success: boolean;
    platform: string;
    profile?: string;
    output_path?: string;
    public_url?: string;
    file_size?: number;
    width?: number;
    height?: number;
    bitrate?: string;
    codec?: string;
    container?: string;
    error?: string;
}

export interface TranscodeResult {
    job_id: string;
    success_count: number;
    failure_count: number;
    variants: TranscodeVariant[];
}

/**
 * Transcode a video to multiple platform formats.
 */
export async function transcodeVideo(
    jobId: string,
    platforms: string[]
): Promise<TranscodeResult> {
    const response = await fetch(`${API_BASE_URL}/api/video/jobs/${jobId}/transcode`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify({ platforms }),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Get all encoding variants for a video job.
 */
export async function getVideoVariants(jobId: string): Promise<{
    job_id: string;
    original_url: string | null;
    original_path: string | null;
    variants: TranscodeVariant[];
}> {
    const response = await fetch(`${API_BASE_URL}/api/video/jobs/${jobId}/variants`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Get available transcoding profiles.
 */
export async function getTranscodeProfiles(): Promise<{ profiles: TranscodeProfile[] }> {
    const response = await fetch(`${API_BASE_URL}/api/video/transcode/profiles`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Get detailed video file information.
 */
export async function getVideoFileInfo(jobId: string): Promise<{
    job_id: string;
    video_info: {
        format?: string;
        duration?: number;
        file_size?: number;
        bit_rate?: number;
        video?: {
            codec?: string;
            width?: number;
            height?: number;
            fps?: string;
        };
        audio?: {
            codec?: string;
            sample_rate?: string;
            channels?: number;
        };
        error?: string;
    };
}> {
    const response = await fetch(`${API_BASE_URL}/api/video/jobs/${jobId}/info`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// =============================================================================
// Phase 4: Audio Processing API Functions
// =============================================================================

// Response from /api/audio/tts and /api/audio/transcribe endpoints
export interface AudioJob {
    job_id: string;
    status: string;
    error?: string;  // Top-level error for failed jobs
    result?: {
        success: boolean;
        transcription?: string;
        audio_url?: string;
        duration?: number;
        error?: string;
    };
}

// Full audio job details from /api/audio/jobs and /api/audio/jobs/{id}
export interface AudioJobDetails {
    id: string;
    universe_id?: string;
    generation_type: string;
    prompt?: string;
    status: string;
    provider?: string;
    voice_id?: string;
    language?: string;
    audio_url?: string;
    local_path?: string;
    file_size?: number;
    duration?: number;
    transcription?: Record<string, unknown>;
    created_at?: string;
    completed_at?: string;
    error_message?: string;
    error?: string;  // Alias for error_message for convenience
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

/**
 * Lists audio jobs with filtering and pagination.
 */
export async function listAudioJobs(filters?: {
    universe_id?: string;
    generation_type?: string;
    provider?: string;
    status?: string;
    limit?: number;
    offset?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
}): Promise<{ jobs: AudioJobDetails[]; total: number; limit: number; offset: number; has_more: boolean }> {
    try {
        const params = new URLSearchParams();
        if (filters?.universe_id) params.append('universe_id', filters.universe_id);
        if (filters?.generation_type) params.append('generation_type', filters.generation_type);
        if (filters?.provider) params.append('provider', filters.provider);
        if (filters?.status) params.append('status', filters.status);
        if (filters?.limit) params.append('limit', filters.limit.toString());
        if (filters?.offset) params.append('offset', filters.offset.toString());
        if (filters?.sort_by) params.append('sort_by', filters.sort_by);
        if (filters?.sort_order) params.append('sort_order', filters.sort_order);

        const url = `${API_BASE_URL}/api/audio/jobs${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url, { headers: authHeaders() });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch audio jobs:', error);
        return { jobs: [], total: 0, limit: 20, offset: 0, has_more: false };
    }
}

/**
 * Gets a specific audio job by ID.
 */
export async function getAudioJobDetails(jobId: string): Promise<AudioJobDetails | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/audio/jobs/${jobId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch audio job ${jobId}:`, error);
        return null;
    }
}

// --- Story Deconstruction Types ---

export interface CharacterStub {
    name: string;
    description: string;
    role: string;
    traits: {
        physical?: string;
        personality?: string;
        background?: string;
        motivations?: string;
        relationships?: string;
    };
    first_appearance?: string;
    significance: string;
}

export interface TimelineEventStub {
    title: string;
    description: string;
    participants: string[];
    location?: string;
    event_type: string;
    significance: string;
    sequence_order: number;
}

export interface LocationStub {
    name: string;
    description: string;
    location_type: string;
    atmosphere?: string;
    significance?: string;
}

export interface ItemStub {
    name: string;
    description: string;
    item_type: string;
    owner?: string;
    significance?: string;
}

export interface WorldContextStub {
    genre?: string;
    tone?: string;
    themes?: string[];
    tech_level?: string;
    magic_system?: string;
    time_period?: string;
}

export interface DeconstructionResult {
    characters: CharacterStub[];
    timeline: TimelineEventStub[];
    locations: LocationStub[];
    items: ItemStub[];
    world_context: WorldContextStub;
    metadata: {
        model: string;
        tokens_used: number;
        story_length: number;
        extraction_targets: string[];
        detail_level: string;
    };
}

export interface DeconstructionJob {
    job_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    confidence_score?: number;
    human_review_required?: boolean;
    created_at?: string;
    completed_at?: string;
    result?: DeconstructionResult;
    error?: string;
}

export interface ImportResult {
    success: boolean;
    characters_created: number;
    timeline_events_created: number;
    locations_created: number;
    items_created: number;
    world_config_updated: boolean;
    errors: string[];
}

// --- Story Deconstruction API Functions ---

/**
 * Deconstruct a story into structured elements.
 */
export async function deconstructStory(request: {
    story_text: string;
    extraction_targets?: string[];
    detail_level?: 'minimal' | 'standard' | 'comprehensive';
}): Promise<DeconstructionJob> {
    const response = await fetch(`${API_BASE_URL}/api/deconstruction/analyze`, {
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
 * Get deconstruction job status and results.
 */
export async function getDeconstructionJob(jobId: string): Promise<DeconstructionJob> {
    const response = await fetch(`${API_BASE_URL}/api/deconstruction/jobs/${jobId}`, {
        method: 'GET',
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * List all deconstruction jobs.
 */
export async function listDeconstructionJobs(options?: {
    limit?: number;
    offset?: number;
}): Promise<{
    jobs: DeconstructionJob[];
    total: number;
    limit: number;
    offset: number;
}> {
    const params = new URLSearchParams();
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());

    const response = await fetch(`${API_BASE_URL}/api/deconstruction/jobs?${params.toString()}`, {
        method: 'GET',
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Import deconstruction results into a universe.
 */
export async function importDeconstruction(
    universeId: string,
    request: {
        job_id: string;
        import_characters?: boolean;
        import_timeline?: boolean;
        import_locations?: boolean;
        import_items?: boolean;
        apply_world_context?: boolean;
    }
): Promise<ImportResult> {
    const response = await fetch(`${API_BASE_URL}/api/deconstruction/universes/${universeId}/import`, {
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

// ============================================================================
// Provider Health API
// ============================================================================

export interface ProviderHealthStatus {
    status: 'ok' | 'error' | 'not_configured';
    message?: string;
    provider?: string;
    subscription?: string;
    models?: string[];
}

export interface AllProvidersHealth {
    status: 'ok' | 'partial' | 'no_providers_configured';
    providers: {
        runway?: ProviderHealthStatus;
        ltx?: ProviderHealthStatus;
        elevenlabs?: ProviderHealthStatus;
        openai_whisper?: ProviderHealthStatus;
    };
}

export interface ProviderStatusConfig {
    video: {
        mode: string;
        active_provider: string;
        providers: {
            runway: { configured: boolean };
            ltx: { configured: boolean };
        };
    };
    audio_tts: {
        mode: string;
        provider: string;
        configured: boolean;
    };
    audio_transcribe: {
        mode: string;
        provider: string;
        configured: boolean;
    };
}

export interface Voice {
    id: string;
    name: string;
    category: string;
    labels?: Record<string, string>;
    preview_url?: string;
}

/**
 * Check health of all providers.
 */
export async function checkAllProvidersHealth(): Promise<AllProvidersHealth> {
    const response = await fetch(`${API_BASE_URL}/api/providers/health`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Check health of a specific provider.
 */
export async function checkProviderHealth(providerName: string): Promise<ProviderHealthStatus> {
    const response = await fetch(`${API_BASE_URL}/api/providers/health/${providerName}`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Get current provider configuration status.
 */
export async function getProviderStatus(): Promise<ProviderStatusConfig> {
    const response = await fetch(`${API_BASE_URL}/api/providers/status`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * List available TTS voices.
 */
export async function listVoices(): Promise<Voice[]> {
    const response = await fetch(`${API_BASE_URL}/api/providers/voices`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

// =============================================================================
// Universe Templates API Functions
// =============================================================================

// Template summary for listing
export interface UniverseTemplate {
    id: string;
    name: string;
    description: string;
    icon: string;
    category: string;
    tags: string[];
    element_count: number;
    event_count: number;
    is_system: boolean;
    use_count: number;
    rating?: number;
    created_at?: string;
}

// Full template detail with all data
export interface UniverseTemplateDetail extends UniverseTemplate {
    world_config: Record<string, unknown>;
    elements: Array<{
        name: string;
        element_type: string;
        description?: string;
        traits?: Record<string, unknown>;
    }>;
    timeline_events: Array<{
        event_name: string;
        event_time: string;
        event_description?: string;
        event_type?: string;
        importance?: number;
    }>;
    is_public: boolean;
    created_by?: string;
    updated_at?: string;
}

// Template creation/update payload
export interface TemplateCreatePayload {
    name: string;
    description?: string;
    icon?: string;
    category?: string;
    tags?: string[];
    world_config?: Record<string, unknown>;
    elements?: Array<{
        name: string;
        element_type: string;
        description?: string;
        traits?: Record<string, unknown>;
    }>;
    timeline_events?: Array<{
        event_name: string;
        event_time: string;
        event_description?: string;
        event_type?: string;
        importance?: number;
    }>;
    is_public?: boolean;
}

export interface TemplateUpdatePayload {
    name?: string;
    description?: string;
    icon?: string;
    category?: string;
    tags?: string[];
    world_config?: Record<string, unknown>;
    elements?: Array<{
        name: string;
        element_type: string;
        description?: string;
        traits?: Record<string, unknown>;
    }>;
    timeline_events?: Array<{
        event_name: string;
        event_time: string;
        event_description?: string;
        event_type?: string;
        importance?: number;
    }>;
    is_public?: boolean;
}

export interface CreateFromTemplateResult {
    success: boolean;
    universe_id: string;
    universe_name: string;
    template_used: string;
    elements_created: number;
    events_created: number;
    message: string;
}

/**
 * List all available universe templates with optional filtering.
 */
export async function getTemplates(options?: {
    category?: string;
    search?: string;
    tags?: string[];
}): Promise<UniverseTemplate[]> {
    const params = new URLSearchParams();
    if (options?.category) params.append('category', options.category);
    if (options?.search) params.append('search', options.search);
    if (options?.tags && options.tags.length > 0) params.append('tags', options.tags.join(','));

    const url = `${API_BASE_URL}/api/templates/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Get all unique template categories.
 */
export async function getTemplateCategories(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/api/templates/categories`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Get full details of a specific template.
 */
export async function getTemplateById(templateId: string): Promise<UniverseTemplateDetail | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            if (response.status === 404) return null;
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch template ${templateId}:`, error);
        return null;
    }
}

/**
 * Create a new custom template.
 */
export async function createTemplate(data: TemplateCreatePayload): Promise<UniverseTemplateDetail> {
    const response = await fetch(`${API_BASE_URL}/api/templates/`, {
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
 * Update an existing template.
 */
export async function updateTemplate(templateId: string, data: TemplateUpdatePayload): Promise<UniverseTemplateDetail> {
    const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}`, {
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
 * Delete a custom template.
 */
export async function deleteTemplate(templateId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
}

/**
 * Duplicate an existing template.
 */
export async function duplicateTemplate(templateId: string, newName?: string): Promise<UniverseTemplateDetail> {
    const params = newName ? `?new_name=${encodeURIComponent(newName)}` : '';
    const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}/duplicate${params}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Create a universe from a template.
 */
export async function createUniverseFromTemplate(
    templateId: string,
    universeName: string
): Promise<CreateFromTemplateResult> {
    const response = await fetch(
        `${API_BASE_URL}/api/templates/${templateId}/create?universe_name=${encodeURIComponent(universeName)}`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...authHeaders(),
            },
        }
    );
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

/**
 * Seed system templates (admin function).
 */
export async function seedTemplates(): Promise<{ success: boolean; templates_added: number; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/templates/seed`, {
        method: 'POST',
        headers: authHeaders(),
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
    }
    return await response.json();
}

// =============================================================================
// Analytics API Functions
// =============================================================================

export interface AnalyticsOverview {
    entities: {
        universes: number;
        elements: number;
    };
    video_jobs: Record<string, number>;
    audio_jobs: Record<string, number>;
    agent_jobs: Record<string, number>;
    timestamp: string;
}

export interface JobStats {
    period_days: number;
    video_jobs: {
        by_day: Array<{ date: string; status: string; count: number }>;
        total: number;
        success_count: number;
        success_rate: number;
    };
    audio_jobs: {
        by_day: Array<{ date: string; status: string; count: number }>;
        total: number;
        success_count: number;
        success_rate: number;
    };
    agent_jobs: {
        by_day: Array<{ date: string; status: string; count: number }>;
        total: number;
        success_count: number;
        success_rate: number;
    };
}

export interface ProviderUsage {
    period_days: number;
    video_providers: Array<{
        provider: string;
        job_count: number;
        total_bytes: number;
    }>;
    audio_providers: Array<{
        provider: string;
        job_count: number;
        total_bytes: number;
    }>;
    agent_types: Array<{
        agent_type: string;
        job_count: number;
    }>;
}

export interface ProcessingTimes {
    period_days: number;
    video_generation: {
        average_seconds: number;
        min_seconds: number;
        max_seconds: number;
        sample_size: number;
    };
    audio_processing: {
        average_seconds: number;
        min_seconds: number;
        max_seconds: number;
        sample_size: number;
    };
    agent_execution: {
        average_seconds: number;
        min_seconds: number;
        max_seconds: number;
        sample_size: number;
    };
}

export interface RecentActivity {
    activities: Array<{
        type: 'video' | 'audio' | 'agent';
        id: string;
        status: string;
        provider?: string;
        job_type?: string;
        agent_type?: string;
        prompt?: string;
        created_at: string;
    }>;
}

/**
 * Get high-level platform statistics.
 */
export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/overview`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Get job statistics for the last N days.
 */
export async function getJobStats(days: number = 7): Promise<JobStats> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/jobs/stats?days=${days}`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Get provider usage statistics.
 */
export async function getProviderUsage(days: number = 30): Promise<ProviderUsage> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/providers/usage?days=${days}`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Get average processing times.
 */
export async function getProcessingTimes(days: number = 7): Promise<ProcessingTimes> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/processing/times?days=${days}`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

/**
 * Get recent activity feed.
 */
export async function getRecentActivity(limit: number = 20): Promise<RecentActivity> {
    const response = await fetch(`${API_BASE_URL}/api/analytics/recent-activity?limit=${limit}`, {
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// =============================================================================
// Image Generation API Functions
// =============================================================================

export interface ImageJob {
    id: string;
    status: string;
    generation_type: string;
    prompt: string;
    negative_prompt?: string;
    width: number;
    height: number;
    num_inference_steps?: number;
    guidance_scale?: number;
    seed?: number;
    style_preset?: string;
    provider?: string;
    model?: string;
    image_url?: string;
    local_path?: string;
    file_size?: number;
    error_message?: string;
    created_at: string;
    completed_at?: string;
}

export interface ImageGenerateRequest {
    prompt: string;
    negative_prompt?: string;
    width?: number;
    height?: number;
    num_inference_steps?: number;
    guidance_scale?: number;
    seed?: number;
    style_preset?: string;
    provider?: string;
    universe_id?: string;
    element_id?: string;
}

export interface StylePreset {
    name: string;
    description: string;
}

export interface ImageSize {
    name: string;
    width: number;
    height: number;
}

/**
 * Generate an image using AI.
 */
export async function generateImage(request: ImageGenerateRequest): Promise<ImageJob> {
    const response = await fetch(`${API_BASE_URL}/api/image/generate`, {
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
 * List image generation jobs with filtering.
 */
export async function listImageJobs(filters?: {
    universe_id?: string;
    element_id?: string;
    status?: string;
    page?: number;
    page_size?: number;
}): Promise<{ jobs: ImageJob[]; total: number; page: number; page_size: number }> {
    try {
        const params = new URLSearchParams();
        if (filters?.universe_id) params.append('universe_id', filters.universe_id);
        if (filters?.element_id) params.append('element_id', filters.element_id);
        if (filters?.status) params.append('status', filters.status);
        if (filters?.page) params.append('page', filters.page.toString());
        if (filters?.page_size) params.append('page_size', filters.page_size.toString());

        const url = `${API_BASE_URL}/api/image/jobs${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url, { headers: authHeaders() });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch image jobs:', error);
        return { jobs: [], total: 0, page: 1, page_size: 20 };
    }
}

/**
 * Get a specific image job by ID.
 */
export async function getImageJob(jobId: string): Promise<ImageJob | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/image/jobs/${jobId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch image job ${jobId}:`, error);
        return null;
    }
}

/**
 * Delete an image job.
 */
export async function deleteImageJob(jobId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/image/jobs/${jobId}`, {
        method: 'DELETE',
        headers: authHeaders(),
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
}

/**
 * Get available style presets.
 */
export async function getImageStyles(): Promise<StylePreset[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/image/styles`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch image styles:', error);
        return [];
    }
}

/**
 * Get recommended image sizes.
 */
export async function getImageSizes(): Promise<ImageSize[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/image/sizes`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch image sizes:', error);
        return [];
    }
}

/**
 * Get available image generation providers.
 */
export async function getImageProviders(): Promise<{ providers: string[]; default: string }> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/image/providers`, {
            headers: authHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch image providers:', error);
        return { providers: ['mock'], default: 'mock' };
    }
}
