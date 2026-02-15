/**
 * Decision model for rate limiting results.
 */

export interface Decision {
    /** Whether the request is allowed */
    allowed: boolean;
    /** Maximum number of requests allowed in the window */
    limit: number;
    /** Number of requests remaining in the current window */
    remaining: number;
    /** Unix timestamp when the limit resets */
    resetAt: number;
    /** Seconds to wait before retrying (only set when blocked) */
    retryAfter?: number;
}

/**
 * Convert decision to standard rate limit headers.
 */
export function toHeaders(decision: Decision): Record<string, string> {
    const headers: Record<string, string> = {
        'RateLimit-Limit': String(decision.limit),
        'RateLimit-Remaining': String(Math.max(0, decision.remaining)),
        'RateLimit-Reset': String(decision.resetAt),
    };

    if (!decision.allowed && decision.retryAfter !== undefined) {
        headers['Retry-After'] = String(decision.retryAfter);
    }

    return headers;
}
