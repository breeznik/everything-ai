
import { Mastra } from '@mastra/core/mastra';
import { PinoLogger } from '@mastra/loggers';
import { LibSQLStore } from '@mastra/libsql';
import { bookingAgent } from './agents/agent';
import { BookingFlow, newWorkflow } from './workflows/gpt-workflow';

export const mastra = new Mastra({
  workflows: { BookingFlow,newWorkflow },
  agents: { bookingAgent },
  storage: new LibSQLStore({
    // stores telemetry, evals, ... into memory storage, if it needs to persist, change to file:../mastra.db
    url: ":memory:",
  }),
  logger: new PinoLogger({
    name: 'Mastra',
    level: 'info',
  }),
});
