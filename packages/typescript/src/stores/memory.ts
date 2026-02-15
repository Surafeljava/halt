/**
 * In-memory storage backend for rate limiting.
 */

export interface Store {
    get(key: string): any;
    set(key: string, value: any, ttl?: number): void;
    increment(key: string, delta?: number, ttl?: number): number;
    delete(key: string): void;
}

interface StoreEntry {
    value: any;
    expiry?: number;
}

export class InMemoryStore implements Store {
    private data: Map<string, StoreEntry> = new Map();

    get(key: string): any {
        this.cleanupExpired(key);
        const entry = this.data.get(key);
        return entry?.value ?? null;
    }

    set(key: string, value: any, ttl?: number): void {
        const entry: StoreEntry = { value };

        if (ttl !== undefined) {
            entry.expiry = Date.now() + ttl * 1000;
        }

        this.data.set(key, entry);
    }

    increment(key: string, delta: number = 1, ttl?: number): number {
        this.cleanupExpired(key);
        const entry = this.data.get(key);
        const current = typeof entry?.value === 'number' ? entry.value : 0;
        const newValue = current + delta;

        const newEntry: StoreEntry = { value: newValue };

        // Set TTL only if key didn't exist
        if (!entry && ttl !== undefined) {
            newEntry.expiry = Date.now() + ttl * 1000;
        } else if (entry?.expiry) {
            newEntry.expiry = entry.expiry;
        }

        this.data.set(key, newEntry);
        return newValue;
    }

    delete(key: string): void {
        this.data.delete(key);
    }

    private cleanupExpired(key: string): void {
        const entry = this.data.get(key);
        if (entry?.expiry && Date.now() >= entry.expiry) {
            this.data.delete(key);
        }
    }

    /**
     * Clean up all expired keys.
     */
    cleanupAllExpired(): number {
        const now = Date.now();
        let count = 0;

        for (const [key, entry] of this.data.entries()) {
            if (entry.expiry && now >= entry.expiry) {
                this.data.delete(key);
                count++;
            }
        }

        return count;
    }
}
