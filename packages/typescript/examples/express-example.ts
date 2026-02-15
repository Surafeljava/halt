import express from 'express';
import { RateLimiter, InMemoryStore, presets } from '../src';
import { haltMiddleware } from '../src/adapters/express';

const app = express();

// Create rate limiter with in-memory store
const limiter = new RateLimiter({
    store: new InMemoryStore(),
    policy: presets.PUBLIC_API,
});

// Add middleware
app.use(haltMiddleware({ limiter }));

app.get('/', (req, res) => {
    res.json({ message: 'Hello World', info: 'Rate limited to 100 req/min' });
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
