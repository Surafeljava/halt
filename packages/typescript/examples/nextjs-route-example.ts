// app/api/route.ts
import { withHalt } from 'halt/next';
import { InMemoryStore, presets } from 'halt';

const store = new InMemoryStore();

async function handler(req: Request) {
    return Response.json({
        message: 'Hello World',
        info: 'Rate limited to 100 req/min',
    });
}

export const GET = withHalt(handler, {
    store,
    policy: presets.PUBLIC_API,
});
