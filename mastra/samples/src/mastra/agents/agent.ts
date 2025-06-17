import { openai } from '@ai-sdk/openai';
import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { LibSQLStore } from '@mastra/libsql';
import { BookingFlow, newWorkflow } from '../workflows/gpt-workflow';

export const bookingAgent = new Agent({
  name: 'Booking-Agent',
  instructions: 'trigger booking flow as soon as user comes in',
  workflows: { BookingFlow , newWorkflow },
  model: openai('gpt-4o-mini'),
  memory: new Memory({
    storage: new LibSQLStore({
      url: 'file:../mastra.db', // path is relative to the .mastra/output directory
    }),
  }),
});
