"""
Example demonstrating the Leaky Bucket algorithm for traffic shaping.
"""

from halt import RateLimiter, InMemoryStore, Policy, Algorithm, KeyStrategy
import time


def main():
    print("="*60)
    print("Leaky Bucket Algorithm - Traffic Shaping Demo")
    print("="*60)
    print("\nThe leaky bucket smooths out bursts by processing requests")
    print("at a constant rate. Think of it like a bucket with a hole:")
    print("- Requests fill the bucket")
    print("- The bucket leaks at a constant rate")
    print("- If the bucket overflows, requests are rejected\n")
    
    # Create a leaky bucket policy
    # 10 requests per minute (leak rate: 10/60 = 0.167 req/sec)
    # Capacity: 15 (can handle small bursts)
    policy = Policy(
        name="leaky_bucket_demo",
        limit=10,
        window=60,
        burst=15,
        algorithm=Algorithm.LEAKY_BUCKET,
        key_strategy=KeyStrategy.IP,
    )
    
    limiter = RateLimiter(store=InMemoryStore(), policy=policy)
    
    # Mock request
    class MockRequest:
        def __init__(self):
            self.client = type('obj', (object,), {'host': '192.168.1.100'})
    
    request = MockRequest()
    
    print(f"Policy: {policy.limit} requests per {policy.window} seconds")
    print(f"Capacity: {policy.burst} requests")
    print(f"Leak rate: {policy.limit / policy.window:.3f} req/sec\n")
    
    # Simulate burst traffic
    print("Simulating burst traffic (12 requests in quick succession):")
    print("-" * 60)
    
    for i in range(12):
        decision = limiter.check(request)
        
        status = "✅ ALLOWED" if decision.allowed else "❌ BLOCKED"
        print(f"Request {i+1:2d}: {status} | Remaining: {decision.remaining:2d} | Reset: {decision.reset_at}")
        
        if not decision.allowed and decision.retry_after:
            print(f"           Retry after: {decision.retry_after}s")
        
        time.sleep(0.1)  # Small delay
    
    print("\n" + "-" * 60)
    print("\nWaiting 3 seconds for bucket to leak...")
    time.sleep(3)
    
    print("\nAfter waiting (bucket has leaked ~0.5 requests):")
    print("-" * 60)
    
    for i in range(3):
        decision = limiter.check(request)
        
        status = "✅ ALLOWED" if decision.allowed else "❌ BLOCKED"
        print(f"Request {i+1}: {status} | Remaining: {decision.remaining} | Reset: {decision.reset_at}")
    
    print("\n" + "="*60)
    print("Key Characteristics of Leaky Bucket:")
    print("="*60)
    print("✅ Smooth traffic shaping - processes at constant rate")
    print("✅ Handles small bursts within capacity")
    print("✅ Predictable behavior - no boundary issues")
    print("✅ Good for rate limiting APIs with strict QoS requirements")
    print("="*60)


if __name__ == "__main__":
    main()
