import { openai } from '@ai-sdk/openai';
import { Agent } from '@mastra/core/agent';
import { createStep, createWorkflow } from '@mastra/core/workflows';
import { z } from 'zod';

export const llm = openai('gpt-4o-mini');




const initialWorkflow = createWorkflow({
    id: 'lounge-booking-flow',
    inputSchema: z.object({
        Query: z.string()
    }),
    outputSchema: z.any(),
})