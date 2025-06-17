import { createWorkflow, createStep } from "@mastra/core/workflows";
import { z } from "zod";
import { getSchedule, reserveCart } from "../tools/obi-tools";

// Step 1: Fetch lounges (outputs lounge names)
const fetchLoungesStep = createStep({
    id: "fetch-lounges",
    inputSchema: z.object({}),
    outputSchema: z.object({
        NMIA: z.string(),
        SIA: z.string(),
    }),
    execute: async () => ({
        NMIA: "Club Kingston / Norman Manley Intl",
        SIA: "Club Mobay / Sangster Intl",
    }),
});

// Shared schema for the rest
const bookingInputSchema = z.object({
    airportid: z.enum(["NMIA", "SIA"]),
    direction: z.enum(["A", "D"]),
    traveldate: z.string().regex(/^\d{8}$/),
    flightId: z.string(),
    adulttickets: z.number(),
    childtickets: z.number(),
    productid: z.enum(["DEPARTURELOUNGE", "ARRIVALONLY", "ARRIVALBUNDLE"]),
});

const scheduleInputSchedma = z.object({
    airportid: z.enum(["NMIA", "SIA"]),
    direction: z.enum(["A", "D"]),
    traveldate: z.string().regex(/^\d{8}$/),
    flightId: z.string(),
})

// Step 2: Human input collection — input = lounges, output = full booking data
const humanInputStep = createStep({
    id: "collect-booking-details",
    inputSchema: z.object({
        NMIA: z.string(),
        SIA: z.string()
    }),
    outputSchema: scheduleInputSchedma,
    resumeSchema: scheduleInputSchedma,
    suspendSchema: z.any(),
    execute: async ({ inputData, resumeData, suspend }) => {
        if (!resumeData) {
            // suspend() must throw or never resolve, so we await it and return its result
            return await suspend({ message: 'please enter the booking details for schedule' }) as any;
        }
        return resumeData;
    },
});

// Step 3: Fetch schedule using complete input
const getScheduleStep = createStep({
    id: "get-schedule",
    inputSchema: scheduleInputSchedma,
    outputSchema: z.any(),
    execute: async ({ inputData }) => {
        return await getSchedule(inputData);
    },
});

// Step 4: Reserve lounge using same booking data
const reserveStep = createStep({
    id: "reserve-lounge",
    inputSchema: z.any(),
    outputSchema: z.any(),
    execute: async ({ inputData }) => {
        // return await reserveCart(inputData);
        return { message: 'reservation confirmed with the data : ', inputData }
    },
});

// Final booking workflow
export const loungeBookingWorkflow = createWorkflow({
    id: "lounge-booking",
    inputSchema: z.object({}), // can be extended for initial user query
    outputSchema: z.any(),
})
    .then(fetchLoungesStep)
    .then(humanInputStep)
    .then(getScheduleStep)
    .then(reserveStep)
    .commit();
