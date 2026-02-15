/**
 * Utility functions for extracting rate limit keys from requests.
 */

// Default health check paths
export const HEALTH_CHECK_PATHS = new Set([
    '/health',
    '/ping',
    '/ready',
    '/healthz',
    '/livez',
]);

// Private IP ranges (CIDR notation)
const PRIVATE_IP_PATTERNS = [
    /^127\./,
    /^10\./,
    /^172\.(1[6-9]|2\d|3[01])\./,
    /^192\.168\./,
    /^::1$/,
    /^fc00:/,
];

/**
 * Extract client IP from request, respecting X-Forwarded-For if from trusted proxy.
 */
export function extractIp(request: any, trustedProxies: string[] = []): string | null {
    let clientIp: string | null = null;

    // Try different request object patterns
    if (request.socket?.remoteAddress) {
        // Node.js/Express
        clientIp = request.socket.remoteAddress;
    } else if (request.ip) {
        // Express with trust proxy
        clientIp = request.ip;
    } else if (request.connection?.remoteAddress) {
        // Older Node.js
        clientIp = request.connection.remoteAddress;
    }

    if (!clientIp) {
        return null;
    }

    // Clean IPv6-mapped IPv4 addresses
    clientIp = clientIp.replace(/^::ffff:/, '');

    // Check if we should trust X-Forwarded-For
    if (trustedProxies.length > 0 && isTrustedProxy(clientIp, trustedProxies)) {
        const forwarded = getForwardedFor(request);
        if (forwarded) {
            return forwarded;
        }
    }

    return clientIp;
}

/**
 * Extract first IP from X-Forwarded-For header.
 */
function getForwardedFor(request: any): string | null {
    const headers = request.headers || {};
    const forwarded = headers['x-forwarded-for'] || headers['X-Forwarded-For'];

    if (forwarded) {
        // Take the first IP (client IP)
        return forwarded.split(',')[0].trim();
    }

    return null;
}

/**
 * Check if IP is in trusted proxy list.
 */
function isTrustedProxy(ip: string, trustedProxies: string[]): boolean {
    return trustedProxies.some((proxy) => {
        if (proxy.includes('/')) {
            // CIDR notation - simplified check
            return ip.startsWith(proxy.split('/')[0].split('.').slice(0, -1).join('.'));
        }
        return ip === proxy;
    });
}

/**
 * Check if IP is in private range.
 */
export function isPrivateIp(ip: string): boolean {
    return PRIVATE_IP_PATTERNS.some((pattern) => pattern.test(ip));
}

/**
 * Check if path is a health check endpoint.
 */
export function isHealthCheck(path: string): boolean {
    return HEALTH_CHECK_PATHS.has(path);
}

/**
 * Extract user ID from request.
 */
export function extractUserId(request: any): string | null {
    // Try common patterns
    if (request.user?.id) {
        return String(request.user.id);
    }

    if (request.userId) {
        return String(request.userId);
    }

    return null;
}

/**
 * Extract API key from request headers.
 */
export function extractApiKey(request: any): string | null {
    const headers = request.headers || {};

    // Try common header names
    const apiKey =
        headers['x-api-key'] ||
        headers['X-API-Key'] ||
        headers['authorization'] ||
        headers['Authorization'];

    if (apiKey) {
        // Handle Bearer tokens
        if (apiKey.startsWith('Bearer ')) {
            return apiKey.substring(7);
        }
        return apiKey;
    }

    return null;
}

/**
 * Extract path from request.
 */
export function extractPath(request: any): string | null {
    // Next.js
    if (request.nextUrl?.pathname) {
        return request.nextUrl.pathname;
    }

    // Express
    if (request.path) {
        return request.path;
    }

    if (request.url) {
        try {
            const url = new URL(request.url, 'http://localhost');
            return url.pathname;
        } catch {
            return request.url;
        }
    }

    return null;
}
