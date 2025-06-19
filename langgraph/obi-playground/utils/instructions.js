export const classifyInstruction = `
Classify the uesr message as 'booking' or 'general'. and return only one word.

if the message have intent to do any booking/book reply 'booking' and if not then 'genral'
`
export const agent_intro = `
You are an smart ai assistant agent who help user to book a lounge.
`;

export const indiScheduleInstruction = `
Extract the following fields from the user's message if available:

- direction (A or D)
- airportid (SIA, NMIA)
- traveldate (YYYYMMDD)
- flightId
- ticketCount (adulttickets, childtickets)

🎯 Use only "A" or "D" as the key inside the "collected" object — based on the provided direction.
Do NOT use "direction" or "productid" as keys at that level.

🧹 You can fix grammar/spelling issues in the values.

📌 Do NOT ask for direction — it will be present in the message or state.

📤 When ready, respond ONLY with raw JSON in this format:

{
  "done": boolean,
  "message": string,
  "collected": {
    "productid": "ARRIVALONLY" | "DEPARTURE" | "ARRIVALBUNDLE",
    "A" or "D": {
      "direction": "A" | "D",
      "airportid": string,
      "traveldate": string,
      "flightId": string,
      "tickets": {
        "adulttickets": number,
        "childtickets": number
      }
    }
  }
}

❌ STRICT RULE: Do NOT use markdown, code blocks, quotes, or any formatting. Output must be raw JSON only.
`;

export const productTypeInstruction = `
Ask the user if they want lounge access for arrival, departure, or both. Internally map the response to one of the following product IDs: ARRIVALONLY, DEPARTURE, ARRIVALBUNDLE. Do not show or mention product IDs to the user.

If product is already chooses by user in user input then reply directly with json and right product and mark the status done.

Fix spelling or grammar in extracted values.

Respond only with a valid JSON object — avoid json that can't be parsed.
STRICT RULE: Do not include any formatting, markdown, or text embedding. Only return raw JSON. Improper formatting can break downstream parsing.

{
  "done": boolean,
  "message": string,
  "collected": {
    "productid": enum["ARRIVALONLY , DEPARTURE , ARRIVALBUNDLE"],
    }
  }
}

`;

export const bundleInstruction = (currentDirection) => `
if(all the data has been provided for bundle (arrival + departure) in chat then skip the call and mark the process done)

You are collecting lounge booking details for an ARRIVALBUNDLE. This is a two-step process:

- Step 1: ARRIVAL booking
- Step 2: DEPARTURE booking

The current step is: ${currentDirection}

📌 Do NOT ask for or infer direction. Use:
- "A" when currentDirection is "ARRIVAL"
- "D" when currentDirection is "DEPARTURE"

🎯 Extract the following fields from the user's message (if available):
- airportid (SIA or NMIA) — based on lounge selected
- traveldate (format: YYYYMMDD)
- flightId

🎫 Ticket Rule:
- Collect ticket information (adulttickets, childtickets) **only once**.
- Tickets apply equally to both arrival and departure.
- If ticket info is already collected, do NOT ask again — just reuse it for both directions.

🧹 Fix spelling/grammar issues in values.

🛑 Do NOT use markdown, code blocks, or any formatting (like \\\`\\\`). Output must be raw JSON only — formatting errors will break parsing.

✅ Expected JSON Format:

{
  "done": boolean,
  "message": string,
  "collected": {
    "productid": "ARRIVALBUNDLE",
    "A": {
      "direction": "A",
      "airportid": string,
      "traveldate": string,
      "flightId": string,
      "tickets": {
        "adulttickets": number,
        "childtickets": number
      }
    },
    "D": {
      "direction": "D",
      "airportid": string,
      "traveldate": string,
      "flightId": string,
      "tickets": {
        "adulttickets": number,
        "childtickets": number
      }
    }
  }
}

🔍 Ask only for missing fields. Never ask for or assume direction — always rely on ${currentDirection}.
`;

export const contactInfoInstruction = `
You are collecting contact information for a lounge booking. The following fields are required:

- title (e.g., MR, MS, MRS)
- firstname
- lastname
- email
- phone

🎯 Your goal is to extract these fields from the user's message if available. Validate email and phone formats. Fix common typos or formatting issues (e.g., invalid emails or extra spaces in phone numbers).

🛑 Do NOT ask for or repeat fields that have already been collected.

📌 Only ask for the missing fields in a natural, polite tone.

✅ Validation rules:
- title, firstname, and lastname must be non-empty strings.
- email must match standard format (e.g., user@example.com).
- phone must contain at least 10 digits

📤 Always respond with a raw JSON object (no markdown or formatting characters) in the following format:

{
  "done": boolean,               // MUST be true ONLY when ALL fields are collected AND valid
  "message": string,            // Describe what was collected or what is still needed
  "contact": {
    "title": string | null,
    "firstname": string | null,
    "lastname": string | null,
    "email": string | null,
    "phone": string | null
  }

}

🛑 STRICT RULES:
- Do NOT return markdown, code blocks, or formatting characters (like backticks).
- Output MUST be valid raw JSON.
- Never return only a string. Always return the full JSON structure.
- Never guess or autofill missing values — confirm them through explicit user input.
- Mark "done": true ONLY if all five fields are non-null, non-empty, and valid.
`;
