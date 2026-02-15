/**
 * Leaky bucket rate limiting algorithm.
 */

import { Decision } from '../core/decision';

export interface LeakyBucketState {
    level: number;
    lastLeak: number;
}

export class LeakyBucket {
    private capacity: number;
    private leakRate: number;
    private window: number;

    constructor(capacity: number, leakRate: number, window: number) {
        this.capacity = capacity;
        this.leakRate = leakRate; // requests per second
        this.window = window;
    }

    /**
     * Check if request is allowed and update bucket level.
     */
    checkAndConsume(
        currentLevel: number,
        lastLeak: number,
        cost: number,
        now: number = Date.now() / 1000
    ): { decision: Decision; newLevel: number; newLastLeak: number } {
        // Calculate how much has leaked since last check
        const elapsed = now - lastLeak;
        const leaked = elapsed * this.leakRate;

        // Update bucket level (can't go below 0)
        let newLevel = Math.max(0, currentLevel - leaked);

        // Calculate when bucket will be empty
        let resetAt: number;
        if (newLevel > 0) {
            const timeToEmpty = newLevel / this.leakRate;
            resetAt = Math.floor(now + timeToEmpty);
        } else {
            resetAt = Math.floor(now);
        }

        // Check if we have capacity
        if (newLevel + cost <= this.capacity) {
            // Allow request - add to bucket
            newLevel += cost;
            const remaining = Math.floor(this.capacity - newLevel);

            return {
                decision: {
                    allowed: true,
                    limit: this.capacity,
                    remaining,
                    resetAt,
                },
                newLevel,
                newLastLeak: now,
            };
        } else {
            // Block request - bucket is full
            // Calculate when there will be enough capacity
            const spaceNeeded = newLevel + cost - this.capacity;
            const retryAfter = Math.floor(spaceNeeded / this.leakRate) + 1;

            return {
                decision: {
                    allowed: false,
                    limit: this.capacity,
                    remaining: 0,
                    resetAt,
                    retryAfter,
                },
                newLevel,
                newLastLeak: now,
            };
        }
    }

    /**
     * Get initial state for a new key.
     */
    initialState(now: number = Date.now() / 1000): LeakyBucketState {
        return {
            level: 0,
            lastLeak: now,
        };
    }
}
