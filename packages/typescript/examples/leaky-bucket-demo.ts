/**
 * Example demonstrating the Leaky Bucket algorithm for traffic shaping.
 */

import { RateLimiter, InMemoryStore, Policy, Algorithm, KeyStrategy } from '../src';

function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
    console.log('='.repeat(60));
    console.log('Leaky Bucket Algorithm - Traffic Shaping Demo');
    console.log('='.repeat(60));
    console.log('\nThe leaky bucket smooths out bursts by processing requests');
    console.log('at a constant rate. Think of it like a bucket with a hole:');
    console.log('- Requests fill the bucket');
    console.log('- The bucket leaks at a constant rate');
    console.log('- If the bucket overflows, requests are rejected\n');

    // Create a leaky bucket policy
    // 10 requests per minute (leak rate: 10/60 = 0.167 req/sec)
    // Capacity: 15 (can handle small bursts)
    const policy: Policy = {
        name: 'leaky_bucket_demo',
        limit: 10,
        window: 60,
        burst: 15,
        algorithm: Algorithm.LEAKY_BUCKET,
        keyStrategy: KeyStrategy.IP,
    };

    const limiter = new RateLimiter({
        store: new InMemoryStore(),
        policy,
    });

    // Mock request
    const request = {
        socket: { remoteAddress: '192.168.1.100' },
        headers: {},
    };

    console.log(`Policy: ${policy.limit} requests per ${policy.window} seconds`);
    console.log(`Capacity: ${policy.burst} requests`);
    console.log(`Leak rate: ${(policy.limit! / policy.window!).toFixed(3)} req/sec\n`);

    // Simulate burst traffic
    console.log('Simulating burst traffic (12 requests in quick succession):');
    console.log('-'.repeat(60));

    for (let i = 0; i < 12; i++) {
        const decision = limiter.check(request);

        const status = decision.allowed ? '✅ ALLOWED' : '❌ BLOCKED';
        const reqNum = String(i + 1).padStart(2);
        const remaining = String(decision.remaining).padStart(2);
        console.log(
            `Request ${reqNum}: ${status} | Remaining: ${remaining} | Reset: ${decision.resetAt}`
        );

        if (!decision.allowed && decision.retryAfter) {
            console.log(`           Retry after: ${decision.retryAfter}s`);
        }

        await sleep(100); // Small delay
    }

    console.log('\n' + '-'.repeat(60));
    console.log('\nWaiting 3 seconds for bucket to leak...');
    await sleep(3000);

    console.log('\nAfter waiting (bucket has leaked ~0.5 requests):');
    console.log('-'.repeat(60));

    for (let i = 0; i < 3; i++) {
        const decision = limiter.check(request);

        const status = decision.allowed ? '✅ ALLOWED' : '❌ BLOCKED';
        console.log(
            `Request ${i + 1}: ${status} | Remaining: ${decision.remaining} | Reset: ${decision.resetAt}`
        );
    }

    console.log('\n' + '='.repeat(60));
    console.log('Key Characteristics of Leaky Bucket:');
    console.log('='.repeat(60));
    console.log('✅ Smooth traffic shaping - processes at constant rate');
    console.log('✅ Handles small bursts within capacity');
    console.log('✅ Predictable behavior - no boundary issues');
    console.log('✅ Good for rate limiting APIs with strict QoS requirements');
    console.log('='.repeat(60));
}

main().catch(console.error);
