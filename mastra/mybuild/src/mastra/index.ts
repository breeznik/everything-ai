
import { Mastra } from '@mastra/core/mastra';
import { PinoLogger } from '@mastra/loggers';
import { LibSQLStore } from '@mastra/libsql';
import { bookingAgent } from './agents/obi-agent';
import { bookingworkflow } from './workflows/obi-workflow';
import { loungeBookingWorkflow } from './workflows/obi-workflow2';

export const mastra = new Mastra({
  workflows: { loungeBookingWorkflow  , bookingworkflow},
  agents: { bookingAgent },
  storage: new LibSQLStore({
    url: ":memory:",
  }),
  logger: new PinoLogger({
    name: 'Mastra',
    level: 'info',
  }),
});
