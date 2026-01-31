/**
 * Centralized API layer for multi-environment support
 * Automatically detects K8s (proxied) vs Amplify (direct) environments
 * 
 * Environment behavior:
 * - Local K8s / EKS: NEXT_PUBLIC_API_URL not set → uses '/api/python' → Ingress proxy
 * - Serverless/Amplify: NEXT_PUBLIC_API_URL set → uses API Gateway URL + '/api/python' prefix
 * 
 * Note: API Gateway routes are defined with /api/python prefix (e.g., /api/python/search/list)
 */

// Auto-detect API base URL - handles removing duplicates
const API_BASE = (() => {
    let url = process.env.NEXT_PUBLIC_API_URL;

    // 1. No Env Var -> Default to relative path (for K8s/Local proxy)
    if (!url) {
        return '/api/python';
    }

    // 2. Env Var equals the relative path (misconfiguration prevention)
    if (url === '/api/python') {
        return '/api/python';
    }

    // 3. Remove trailing slashes
    if (url.endsWith('/')) {
        url = url.slice(0, -1);
    }

    // 4. If URL already ends with /api/python, return as is (prevent duplication)
    if (url.endsWith('/api/python')) {
        return url;
    }

    // 5. Append /api/python for standard domains (Amplify)
    return `${url}/api/python`;
})();

/**
 * Get the API base URL for use in components
 * Use this instead of hardcoding '/api/python'
 */
export function getApiUrl(endpoint: string = ''): string {
    // Ensure endpoint starts with / if provided
    const normalizedEndpoint = endpoint && !endpoint.startsWith('/') ? `/${endpoint}` : endpoint;
    return `${API_BASE}${normalizedEndpoint}`;
}

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(endpoint: string, options?: RequestInit) {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
}

/**
 * Tasting Notes API
 */
export const notesAPI = {
    /**
     * Get all public notes
     */
    getAll: async (limit = 50) => {
        return apiFetch(`/notes?limit=${limit}`);
    },

    /**
     * Get notes by user ID
     */
    getByUserId: async (userId: string) => {
        return apiFetch(`/notes/user/${userId}`);
    },

    /**
     * Get notes by liquor ID
     */
    getByLiquorId: async (liquorId: number) => {
        return apiFetch(`/notes/liquor/${liquorId}`);
    },

    /**
     * Create a new note
     */
    create: async (data: any) => {
        return apiFetch('/notes', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    /**
     * Update an existing note
     */
    update: async (noteId: string, data: any) => {
        return apiFetch(`/notes/${noteId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    /**
     * Delete a note
     */
    delete: async (noteId: string) => {
        return apiFetch(`/notes/${noteId}`, {
            method: 'DELETE',
        });
    },

    /**
     * Toggle like on a note
     */
    toggleLike: async (noteId: string, userId: string) => {
        return apiFetch(`/notes/${noteId}/like`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId }),
        });
    },
};

/**
 * Search API
 */
export const searchAPI = {
    /**
     * Search for liquors
     */
    search: async (query: string) => {
        return apiFetch('/search', {
            method: 'POST',
            body: JSON.stringify({ query }),
        });
    },

    /**
     * Get online products by drink name
     */
    getProducts: async (drinkName: string) => {
        return apiFetch(`/search/products/${encodeURIComponent(drinkName)}`);
    },

    /**
     * Get drink by ID
     */
    getDrinkById: async (id: number) => {
        return apiFetch(`/drink/${id}`);
    },

    /**
     * Get drinks by region
     */
    getDrinksByRegion: async (region: string) => {
        return apiFetch('/drinks/region', {
            method: 'POST',
            body: JSON.stringify({ region }),
        });
    },

    /**
     * Get drinks with filters
     */
    getDrinksWithFilters: async (filters: any) => {
        return apiFetch('/drinks/filter', {
            method: 'POST',
            body: JSON.stringify(filters),
        });
    },
};

/**
 * Chatbot API
 */
export const chatbotAPI = {
    /**
     * Send message to chatbot
     */
    sendMessage: async (message: string, conversationId?: string) => {
        return apiFetch('/chatbot', {
            method: 'POST',
            body: JSON.stringify({
                message,
                conversation_id: conversationId
            }),
        });
    },
};

/**
 * OCR API
 */
export const ocrAPI = {
    /**
     * Process OCR image
     */
    processImage: async (imageData: string) => {
        return apiFetch('/ocr', {
            method: 'POST',
            body: JSON.stringify({ image: imageData }),
        });
    },
};

/**
 * Statistics API
 */
export const statsAPI = {
    /**
     * Get statistics
     */
    getStats: async () => {
        return apiFetch('/stats');
    },
};

/**
 * Favorites API
 */
export const favoritesAPI = {
    /**
     * Toggle favorite status (add or remove)
     */
    toggle: async (userId: string, drinkId: number, drinkName: string, imageUrl?: string) => {
        return apiFetch('/favorites/toggle', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                drink_id: drinkId,
                drink_name: drinkName,
                image_url: imageUrl
            }),
        });
    },

    /**
     * Get all favorites for a user
     */
    getByUserId: async (userId: string) => {
        return apiFetch(`/favorites/user/${userId}`);
    },

    /**
     * Check if a drink is favorited
     */
    check: async (userId: string, drinkId: number) => {
        return apiFetch(`/favorites/check/${userId}/${drinkId}`);
    },

    /**
     * Remove a favorite
     */
    remove: async (userId: string, drinkId: number) => {
        return apiFetch(`/favorites/${drinkId}`, {
            method: 'DELETE',
            body: JSON.stringify({ user_id: userId }),
        });
    },
};

// Export all APIs as a single object
export const api = {
    notes: notesAPI,
    search: searchAPI,
    chatbot: chatbotAPI,
    ocr: ocrAPI,
    stats: statsAPI,
    favorites: favoritesAPI,
};

export default api;

