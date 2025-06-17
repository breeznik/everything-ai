import { createTool } from "@mastra/core/tools";
import axios from 'axios';
import z from 'zod';

export const getLoungeDeclaration = createTool({
    id: 'get-lounge',
    description: 'server lounge option for selection',
    inputSchema: z.string(),
    outputSchema: z.any(),
    execute: async () => {
        return {
            NMIA: "Club Kingston / Norman Manley Intl",
            SIA: "Club Mobay / Sangster Intl",
        };
    }
})

export const getScheduleDeclration = createTool({
    id: 'get-schedule',
    description: 'Serves the avaialable schedule based on flight information',
    inputSchema: z.object({
        direction: z.enum(['A', 'D']),
        airportid: z.enum(['NMIA', 'SIA']),
        traveldate: z.string().regex(/^\d{8}$/, {
            message: "traveldate must be in yyyymmdd format (e.g. 20250531)",
        }),
        flightId: z.string()
    }),
    execute: async ({ context }) => {
        return await getSchedule(context)
    }
})

export const reservationDecleration = createTool({
    id: 'get-reservation',
    description: 'will provide lounge reservation status',
    inputSchema: z.object({
        adulttickets: z.number(),
        childtickets: z.number(),
        airportid: z.string(),
        flightId: z.string(),
        traveldate: z.string().regex(/^\d{8}$/, {
            message: "traveldate must be in yyyymmdd format (e.g. 20250531)",
        }),
        productid: z.enum(["DEPARTURELOUNGE", "ARRIVALONLY", "ARRIVALBUNDLE"])
    }),
    outputSchema: z.any(),
    execute: async ({ context }) => {
        return await reserveCart(context)
    }
})

export async function getSchedule({
    direction, airportid, traveldate, flightId, productid
}: any) {
    console.log('hey from get schedule')
    const request = {
        username: process.env.STATIC_USERNAME,
        sessionid: process.env.STATIC_SESSIONID,
        failstatus: 0,
        request: {
            direction: direction,
            airportid: airportid,
            traveldate: traveldate,
        },
    };
    try {
        const response = await axios.post(`${process.env.DEVSERVER}/getschedule`, request);
        console.log(response)
        const result = response.data.data.flightschedule.filter((flightDetail) => flightDetail.flightId === flightId);
        return result;
    } catch (error) {
        console.log(error)
    }
    return { message: "we have an error" }
}

export async function reserveCart({
    adulttickets,
    childtickets,
    airportid,
    traveldate,
    flightId,
    productid
}: {
    adulttickets: number,
    childtickets: number,
    airportid: string,
    traveldate: string,
    flightId: string
    productid: "DEPARTURELOUNGE" | "ARRIVALONLY" | "ARRIVALBUNDLE",
}) {
    // console.log("hey from reserved Cart")
    // let arrivalscheduleid = 0, departurescheduleid = 0;
    // if (productid === "ARRIVALONLY") {
    //     const resultFromgetSchedule = await getSchedule({ direction: "A", airportid, traveldate, flightId })
    //     console.log(resultFromgetSchedule, "result from schedule id")
    //     arrivalscheduleid = resultFromgetSchedule[0].scheduleId
    // } else if (productid === "DEPARTURELOUNGE") {
    //     const resultFromgetSchedule = await getSchedule({ direction: "D", airportid, traveldate, flightId })
    //     departurescheduleid = resultFromgetSchedule[0].scheduleId
    // } else {
    //     let resultFromgetSchedule = await getSchedule({ direction: "A", airportid, traveldate, flightId })
    //     arrivalscheduleid = resultFromgetSchedule[0].scheduleId
    //     resultFromgetSchedule = await getSchedule({ direction: "D", airportid, traveldate, flightId })
    //     departurescheduleid = resultFromgetSchedule[0].scheduleId
    // }
    // const request = {
    //     failstatus: 0,
    //     sessionid: process.env.STATIC_SESSIONID,
    //     username: process.env.STATIC_USERNAME,
    //     request: {
    //         adulttickets: adulttickets,
    //         arrivalscheduleid: arrivalscheduleid,
    //         cartitemid: 0,
    //         childtickets: childtickets,
    //         departurescheduleid: departurescheduleid,
    //         distributorid: "",
    //         paymenttype: "GUESTCARD",
    //         productid: productid,
    //         ticketsrequested: adulttickets + childtickets
    //     }
    // }
    // try {
    //     console.log('check before network call', request)
    //     const response = await axios.post(`${process.env.devServer}/reservecartitem`, request);
    //     console.log(response.data, "response from Reserve Cart")
    //     return response.data.data;
    // } catch (error) {
    //     console.log(error)
    // }
    // return { message: "we have an error in reserving cart" }
    return {message:'reservation confirmed'}
}