/**
 * Fixed window rate limiting algorithm.
 */

import { Decision } from '../core/decision';

export interface FixedWindowState {
    count: number;
    windowStart: number;
}

export class FixedWindow {
    private limit: number;
    private window: number;

    constructor(limit: number, window: number) {
        this.limit = limit;
        this.window = window;
    }

    /**
     * Check if request is allowed and increment counter.
     */
    checkAndConsume(
        currentCount: number,
        windowStart: number,
        cost: number,
        now: number = Date.now() / 1000
    ): { decision: Decision; newCount: number; newWindowStart: number } {
        // Check if we're in a new window
        const timeSinceStart = now - windowStart;
        if (timeSinceStart >= this.window) {
            // New window - reset counter
            currentCount = 0;
            windowStart = now;
        }

        // Calculate reset time (end of current window)
        const resetAt = Math.floor(windowStart + this.window);

        // Check if we have capacity
        if (currentCount + cost <= this.limit) {
            // Allow request
            const newCount = currentCount + cost;
            const remaining = this.limit - newCount;

            return {
                decision: {
                    allowed: true,
                    limit: this.limit,
                    remaining,
                    resetAt,
                },
                newCount,
                newWindowStart: windowStart,
            };
        } else {
            // Block request
            const retryAfter = Math.floor(resetAt - now) + 1;

            return {
                decision: {
                    allowed: false,
                    limit: this.limit,
                    remaining: 0,
                    resetAt,
                    retryAfter,
                },
                newCount: currentCount,
                newWindowStart: windowStart,
            };
        }
    }

    /**
     * Get initial state for a new key.
     */
    initialState(now: number = Date.now() / 1000): FixedWindowState {
        return {
            count: 0,
            windowStart: now,
        };
    }
}
