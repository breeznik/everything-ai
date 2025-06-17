import { createWorkflow, createStep } from "@mastra/core/workflows";
import z from "zod";

// --- Sample Tools (Mock Logic) ---
const sampleScheduleCall = async (input: any) => ({
    availableSlots: ["10:00 AM", "2:00 PM", "6:00 PM"],
    status: "ok",
});
const sampleReserveCart = async (input: any) => ({
    reservationId: "RES12345",
    status: "reserved",
});
const sampleSetContact = async (input: any) => ({ contactSaved: true });
const samplePayment = async (input: any) => ({
    paymentStatus: "success",
    transactionId: "TXN98765",
});

// --- Step Definitions ---
// LLM Call Step

export const llmCall = createStep({
    id: "llmCall",
    description: "LLM decides if user's query is related to lounge booking",
    inputSchema: z.object({
        query: z.string(),
    }),
    outputSchema: z.object({
        shouldBook: z.union([z.string(), z.boolean()]),
    }),
    execute: async ({ inputData, mastra }) => {
        const agent = mastra.getAgent("bookingAgent");
        console.log('step triggered')

        const systemPrompt = `
        You are a smart assistant. Based on the user's query, decide if it is about lounge booking. 
        If yes, respond with only "true".
        If not, answer the user query.
        `;

        const response = await agent.stream([
            { role: "system", content: systemPrompt },
            { role: "user", content: inputData.query },
        ]);
        let responseText = "";

        for await (const chunk of response.textStream) {
            process.stdout.write(chunk); // Logs to server terminal
            responseText += chunk;
        }
        console.log('response')
        const shouldBook = responseText.trim().toLowerCase();
        return { shouldBook };
    },
});

const scheduleCall = createStep({
    id: "scheduleCall",
    inputSchema: z.object({
        airportid: z.enum(["NMIA", "SIA"]),
        direction: z.enum(["A", "D"]),
        travelDate: z.string(),
        flightId: z.string(),
    }),
    outputSchema: z.object({
        availableSlots: z.array(z.string()),
        status: z.string(),
    }),
    execute: sampleScheduleCall,
});

const reservationStep = createStep({
    id: "reserveLounge",
    inputSchema: z.object({
        adulttickets: z.number(),
        childtickets: z.number(),
        productid: z.string(),
    }),
    outputSchema: z.object({
        reservationId: z.string(),
        status: z.string(),
    }),
    execute: sampleReserveCart,
});

const contactInfoStep = createStep({
    id: "setContactInfo",
    inputSchema: z.object({
        email: z.string().email(),
        firstname: z.string(),
        lastname: z.string(),
        phone: z.string(),
    }),
    outputSchema: z.object({ contactSaved: z.boolean() }),
    execute: sampleSetContact,
});

const paymentStep = createStep({
    id: "makePayment",
    inputSchema: z.object({
        cardHolder: z.string(),
        cardNumber: z.string(),
        cardType: z.enum(["VISA", "MASTERCARD"]),
        cvv: z.string(),
        expiryDate: z.string(),
        email: z.string().email(),
    }),
    outputSchema: z.object({
        paymentStatus: z.string(),
        transactionId: z.string(),
    }),
    execute: samplePayment,
});

const finalStep = createStep({
    id: "finalOutput",
    inputSchema: paymentStep.outputSchema,
    outputSchema: z.object({ result: z.string() }),
    execute: async ({ inputData }) => ({
        result: `Booking complete. Transaction ID: ${inputData.transactionId}`,
    }),
});

const fallbackStep = createStep({
    id: "fallback",
    inputSchema: llmCall.outputSchema,
    outputSchema: z.object({ result: z.any() }),
    execute: async ({ inputData }) => ({ result: inputData.shouldBook }),
});

const fallInStep = createStep({
    id: "FallIn",
    inputSchema: llmCall.outputSchema,
    outputSchema: z.object({ result: z.any() }),
    execute: async ({ inputData }) => ({ result: inputData.shouldBook }),
});

const humanInputStep = createStep({
    id: "humna-input",
    inputSchema: llmCall.outputSchema,
    outputSchema: scheduleCall.inputSchema,
    resumeSchema: scheduleCall.inputSchema,
    suspendSchema: z.object({
        messsage: z.string().describe('message to user for sharing schedule info')
    }),
    execute: async ({ resumeData, suspend }) => {
        if (!resumeData) {
            await suspend({
                messsage: 'please share your schedule information'
            })
            return {
                airportid: '',
                direction: '',
                travelDate: '',
                flightId: '',
            }
        }

        return resumeData
    }
})

export const newWorkflow = createWorkflow({
    id: 'test-worflow',
    description: 'this is test nested workflow',
    inputSchema: llmCall.outputSchema,
    outputSchema: z.object({ result: z.any() }),
}).then(humanInputStep).then(scheduleCall).commit()

// --- Workflow Definition ---
export const BookingFlow = createWorkflow({
    id: "BookingFlow",
    description: "Chained lounge booking workflow with LLM-based branching",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: z.any({}),
})
    .then(llmCall)
    .branch([
        [async ({ inputData }) => inputData.shouldBook === 'true', newWorkflow],
        [async ({ inputData }) => inputData.shouldBook !== 'true', fallbackStep],
    ])
    .commit();

