/**
 * Main rate limiter implementation.
 */

import { Decision } from './decision';
import { Policy, KeyStrategy, Algorithm, normalizePolicy } from './policy';
import {
    extractIp,
    extractUserId,
    extractApiKey,
    extractPath,
    isHealthCheck,
    isPrivateIp,
} from './extractors';
import { TokenBucket, TokenBucketState } from '../algorithms/token-bucket';
import { FixedWindow, FixedWindowState } from '../algorithms/fixed-window';
import { SlidingWindow, SlidingWindowState } from '../algorithms/sliding-window';
import { Store } from '../stores/memory';

type AlgorithmInstance = TokenBucket | FixedWindow | SlidingWindow;

export interface RateLimiterOptions {
    store: Store;
    policy: Policy;
    trustedProxies?: string[];
    exemptPrivateIps?: boolean;
}

export class RateLimiter {
    private store: Store;
    private policy: Required<Policy>;
    private trustedProxies: string[];
    private exemptPrivateIps: boolean;
    private algorithm: AlgorithmInstance;

    constructor(options: RateLimiterOptions) {
        this.store = options.store;
        this.policy = normalizePolicy(options.policy);
        this.trustedProxies = options.trustedProxies ?? [];
        this.exemptPrivateIps = options.exemptPrivateIps ?? true;

        // Initialize algorithm based on policy
        if (this.policy.algorithm === Algorithm.TOKEN_BUCKET) {
            this.algorithm = new TokenBucket(
                this.policy.burst,
                this.policy.limit,
                this.policy.window
            );
        } else if (this.policy.algorithm === Algorithm.FIXED_WINDOW) {
            this.algorithm = new FixedWindow(this.policy.limit, this.policy.window);
        } else if (this.policy.algorithm === Algorithm.SLIDING_WINDOW) {
            this.algorithm = new SlidingWindow(this.policy.limit, this.policy.window);
        } else if (this.policy.algorithm === Algorithm.LEAKY_BUCKET) {
            // Leaky bucket: leak_rate = limit / window (requests per second)
            const leakRate = this.policy.limit / this.policy.window;
            this.algorithm = new LeakyBucket(this.policy.burst, leakRate, this.policy.window);
        } else {
            throw new Error(`Algorithm ${this.policy.algorithm} not implemented`);
        }
    }

    /**
     * Check if request is allowed under rate limit.
     */
    check(request: any, cost?: number, algorithm?: Algorithm): Decision {
        const requestCost = cost ?? this.policy.cost;

        // Check exemptions
        if (this.isExempt(request)) {
            return {
                allowed: true,
                limit: this.policy.limit,
                remaining: this.policy.limit,
                resetAt: Math.floor(Date.now() / 1000 + this.policy.window),
            };
        }

        // Extract rate limit key
        const key = this.extractKey(request);
        if (!key) {
            // If we can't extract a key, allow the request
            return {
                allowed: true,
                limit: this.policy.limit,
                remaining: this.policy.limit,
                resetAt: Math.floor(Date.now() / 1000 + this.policy.window),
            };
        }

        // Add policy name prefix to key
        const storageKey = `halt:${this.policy.name}:${key}`;

        // Get current state from storage
        const state = this.store.get(storageKey);

        let decision: Decision;

        // Handle different algorithms
        if (this.algorithm instanceof TokenBucket) {
            let tokens: number;
            let lastRefill: number;

            if (!state) {
                const initialState = this.algorithm.initialState();
                tokens = initialState.tokens;
                lastRefill = initialState.lastRefill;
            } else {
                tokens = state.tokens;
                lastRefill = state.lastRefill;
            }

            const result = this.algorithm.checkAndConsume(tokens, lastRefill, requestCost);
            decision = result.decision;

            const ttl = this.policy.window * 2;
            this.store.set(storageKey, { tokens: result.newTokens, lastRefill: result.newLastRefill }, ttl);
        } else if (this.algorithm instanceof FixedWindow) {
            let count: number;
            let windowStart: number;

            if (!state) {
                const initialState = this.algorithm.initialState();
                count = initialState.count;
                windowStart = initialState.windowStart;
            } else {
                count = state.count;
                windowStart = state.windowStart;
            }

            const result = this.algorithm.checkAndConsume(count, windowStart, requestCost);
            decision = result.decision;

            const ttl = this.policy.window * 2;
            this.store.set(storageKey, { count: result.newCount, windowStart: result.newWindowStart }, ttl);
        } else if (this.algorithm instanceof SlidingWindow) {
            const buckets = state || this.algorithm.initialState();
            const result = this.algorithm.checkAndConsume(buckets, requestCost);
            decision = result.decision;

            const ttl = this.policy.window * 2;
            this.store.set(storageKey, result.newBuckets, ttl);
        } else if (this.algorithm instanceof LeakyBucket) {
            let level: number;
            let lastLeak: number;

            if (!state) {
                const initialState = this.algorithm.initialState();
                level = initialState.level;
                lastLeak = initialState.lastLeak;
            } else {
                level = state.level;
                lastLeak = state.lastLeak;
            }

            const result = this.algorithm.checkAndConsume(level, lastLeak, requestCost);
            decision = result.decision;

            const ttl = this.policy.window * 2;
            this.store.set(storageKey, { level: result.newLevel, lastLeak: result.newLastLeak }, ttl);
        } else {
            throw new Error(`Algorithm ${typeof this.algorithm} not supported`);
        }

        return decision;
    }

    /**
     * Extract rate limit key from request based on policy strategy.
     */
    private extractKey(request: any): string | null {
        // Use custom extractor if provided
        if (this.policy.keyExtractor) {
            return this.policy.keyExtractor(request);
        }

        // Use built-in strategies
        if (this.policy.keyStrategy === KeyStrategy.IP) {
            return extractIp(request, this.trustedProxies);
        }

        if (this.policy.keyStrategy === KeyStrategy.USER) {
            return extractUserId(request);
        }

        if (this.policy.keyStrategy === KeyStrategy.API_KEY) {
            return extractApiKey(request);
        }

        if (this.policy.keyStrategy === KeyStrategy.COMPOSITE) {
            // Composite: user:ip or api_key:ip
            const user = extractUserId(request);
            const apiKey = extractApiKey(request);
            const ip = extractIp(request, this.trustedProxies);

            if (user && ip) {
                return `${user}:${ip}`;
            } else if (apiKey && ip) {
                return `${apiKey}:${ip}`;
            } else if (user) {
                return user;
            } else if (apiKey) {
                return apiKey;
            } else {
                return ip;
            }
        }

        return null;
    }

    /**
     * Check if request is exempt from rate limiting.
     */
    private isExempt(request: any): boolean {
        // Check health check paths
        const path = extractPath(request);
        if (path && isHealthCheck(path)) {
            return true;
        }

        // Check custom exemptions
        if (path && this.policy.exemptions.includes(path)) {
            return true;
        }

        // Check private IPs
        if (this.exemptPrivateIps) {
            const ip = extractIp(request, this.trustedProxies);
            if (ip && isPrivateIp(ip)) {
                return true;
            }
        }

        // Check IP exemptions
        const ip = extractIp(request, this.trustedProxies);
        if (ip && this.policy.exemptions.includes(ip)) {
            return true;
        }

        return false;
    }
}
