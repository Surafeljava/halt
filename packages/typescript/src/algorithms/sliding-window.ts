/**
 * Sliding window rate limiting algorithm.
 */

import { Decision } from '../core/decision';

export type SlidingWindowState = Record<number, number>;

export class SlidingWindow {
    private limit: number;
    private window: number;
    private precision: number;
    private bucketSize: number;

    constructor(limit: number, window: number, precision: number = 10) {
        this.limit = limit;
        this.window = window;
        this.precision = precision;
        this.bucketSize = window / precision;
    }

    /**
     * Check if request is allowed and update buckets.
     */
    checkAndConsume(
        buckets: SlidingWindowState,
        cost: number,
        now: number = Date.now() / 1000
    ): { decision: Decision; newBuckets: SlidingWindowState } {
        // Calculate current bucket
        const currentBucket = Math.floor(now / this.bucketSize);

        // Remove expired buckets (older than window)
        const cutoffBucket = currentBucket - this.precision;
        const newBuckets: SlidingWindowState = {};

        for (const [bucketIdStr, count] of Object.entries(buckets)) {
            const bucketId = parseInt(bucketIdStr, 10);
            if (bucketId > cutoffBucket) {
                newBuckets[bucketId] = count;
            }
        }

        // Count requests in sliding window
        const totalCount = Object.values(newBuckets).reduce((sum, count) => sum + count, 0);

        // Calculate reset time (when oldest bucket expires)
        const bucketIds = Object.keys(newBuckets).map((id) => parseInt(id, 10));
        const oldestBucket = bucketIds.length > 0 ? Math.min(...bucketIds) : currentBucket;
        const resetAt = Math.floor((oldestBucket + this.precision + 1) * this.bucketSize);

        // Check if we have capacity
        if (totalCount + cost <= this.limit) {
            // Allow request
            newBuckets[currentBucket] = (newBuckets[currentBucket] || 0) + cost;
            const remaining = this.limit - (totalCount + cost);

            return {
                decision: {
                    allowed: true,
                    limit: this.limit,
                    remaining,
                    resetAt,
                },
                newBuckets,
            };
        } else {
            // Block request
            const retryAfter = Math.floor(this.bucketSize) + 1;

            return {
                decision: {
                    allowed: false,
                    limit: this.limit,
                    remaining: 0,
                    resetAt,
                    retryAfter,
                },
                newBuckets,
            };
        }
    }

    /**
     * Get initial state for a new key.
     */
    initialState(): SlidingWindowState {
        return {};
    }
}
