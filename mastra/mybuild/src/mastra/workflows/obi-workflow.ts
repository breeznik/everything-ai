import { createStep, createWorkflow } from "@mastra/core/workflows";
import z from 'zod';
import { getSchedule, reserveCart } from "../tools/obi-tools";

// Lounge schedule input (for getSchedule)
const scheduleInputSchema = z.object({
    airportid: z.enum(["NMIA", "SIA"]),
    direction: z.enum(["A", "D"]).describe('THE A and D represents ARRIVAL and DEPARTURE'),
    traveldate: z.string().regex(/^\d{8}$/, {
        message: "traveldate must be in yyyymmdd format (e.g. 20250627)",
    }),
    flightId: z.string()
});

// Lounge declaration output
const getLoungeOutputSchema = z.object({
    NMIA: z.string(),
    SIA: z.string(),
});

// Lounge selection step (static return)
const getLoungeStep = createStep({
    id: 'get-lounge',
    description: 'Serves available lounges for selection',
    inputSchema: z.object({
        input: z.string().describe('User asks for lounge booking')
    }),
    outputSchema: getLoungeOutputSchema,
    execute: async () => {
        return {
            NMIA: "Club Kingston / Norman Manley Intl",
            SIA: "Club Mobay / Sangster Intl",
        };
    }
});

// Flight info prompt step
const humanStep = createStep({
    id: "human-step",
    description: "Prompts user to provide schedule information",
    inputSchema: z.object({
        input: z.string().describe('Query for booking the lounge')
    }),
    outputSchema: scheduleInputSchema,
    resumeSchema: scheduleInputSchema,
    suspendSchema: z.object({ message: z.string() }),
    execute: async ({ resumeData, suspend }) => {
        if (!resumeData) {
            await suspend({ message: 'please provide schedule data' });
            // Throw to ensure function never returns an invalid object
            throw new Error('Execution suspended');
        }
        // Type assertion to satisfy the output schema
        return resumeData as z.infer<typeof scheduleInputSchema>;
    }
});

// Lounge schedule fetch step
const getScheduleStep = createStep({
    id: 'get-schedule',
    description: 'Fetches available lounge schedule based on flight info',
    inputSchema: scheduleInputSchema,
    outputSchema: z.any(), // You can tighten this based on your actual response
    execute: async ({ inputData }) => {
        console.log('Fetching schedule with:', inputData);
        return await getSchedule(inputData);
    }
});

// Reservation step (not used in flow yet, keep for later)
const reservationStep = createStep({
    id: 'get-reservation',
    description: 'Makes lounge reservation',
    inputSchema: z.object({
        adulttickets: z.number(),
        childtickets: z.number(),
        airportid: z.string(),
        flightId: z.string(),
        traveldate: z.string().regex(/^\d{8}$/, {
            message: "traveldate must be in yyyymmdd format (e.g. 20250627)",
        }),
        productid: z.enum(["DEPARTURELOUNGE", "ARRIVALONLY", "ARRIVALBUNDLE"])
    }),
    outputSchema: z.any(),
    execute: async ({ inputData }) => {
        return await reserveCart(inputData);
    }
});

// Booking workflow chain
const bookingworkflow = createWorkflow({
    id: 'booking-workflow',
    inputSchema: z.object({
        input: z.string().describe('Query for booking the lounge')
    }),
    outputSchema: z.any()
})
    .then(humanStep)
    .then(getScheduleStep);

// Register the workflow
bookingworkflow.commit();

export { bookingworkflow };
