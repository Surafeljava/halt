/**
 * Apollo Server plugin adapter for Halt rate limiting.
 *
 * Usage:
 * const plugin = haltApolloPlugin({ limiter });
 * const server = new ApolloServer({ typeDefs, resolvers, plugins: [plugin] });
 */

import { RateLimiter } from '../core/limiter';

export interface ApolloHaltOptions {
    limiter: RateLimiter;
    /** Optional function to extract a resource name for per-field limits */
    resourceExtractor?: (request: any) => string | null;
}

export function haltApolloPlugin(options: ApolloHaltOptions) {
    const { limiter, resourceExtractor } = options;

    return {
        async requestDidStart() {
            return {
                async didResolveOperation(requestContext: any) {
                    try {
                        // Provide request object compatible with limiter.extractors
                        const req = requestContext.request?.http || {};
                        if (resourceExtractor) {
                            // Allow users to attach custom resource info
                            (req as any).resource = resourceExtractor(requestContext.request);
                        }

                        const decision = await limiter.check(req);

                        if (!decision.allowed) {
                            // Short-circuit the request by adding an error
                            requestContext.response = {
                                http: {
                                    status: 429,
                                    headers: {
                                        ...requestContext.response?.http?.headers,
                                        'Retry-After': String(decision.retryAfter ?? 0),
                                    },
                                },
                                errors: [
                                    new Error('rate_limit_exceeded: Too many requests. Please try again later.'),
                                ],
                            };
                        } else {
                            // Attach rate limit headers for downstream
                            requestContext.response = requestContext.response || {};
                            requestContext.response.http = requestContext.response.http || {};
                            requestContext.response.http.headers = {
                                ...requestContext.response.http.headers,
                                'RateLimit-Limit': String(decision.limit),
                                'RateLimit-Remaining': String(Math.max(0, decision.remaining)),
                                'RateLimit-Reset': String(decision.resetAt),
                            };
                        }
                    } catch (err) {
                        // Don't block on errors from limiter; surface as server error
                        requestContext.errors = requestContext.errors || [];
                        requestContext.errors.push(err as Error);
                    }
                },
            };
        },
    };
}
