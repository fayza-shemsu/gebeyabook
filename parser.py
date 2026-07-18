import os
import json
from dotenv import load_dotenv
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a transaction parser for GebeyaBook, a voice bookkeeping app for Ethiopian market vendors who speak Amharic.

You will receive Amharic text transcribed from a vendor's voice note, reporting a sale, an expense (purchase), or a debt/credit.

IMPORTANT CONTEXT:
- Text comes from speech-to-text and may have errors, especially in verb endings (e.g. "ሸጠሁ", "ሸጡኩ", "ሽጥኩ" all mean "I sold"). Infer meaning from context, don't rely on exact verb spelling.
- Common SALE verbs: ሸጥኩ / ሸጠሁ / ሽጥኩ / ተሸጠ
- Common EXPENSE verbs: ገዛሁ / ገዛው
- DEBT indicators: በዱቤ (on credit), or phrases meaning payment is deferred, e.g. "ነገ ይከፍላል" (will pay tomorrow), "በኋላ ይከፍላል" (will pay later), customer owes / will pay later in general — treat these the same as በዱቤ, as type "debt".
- For DEBT transactions: the customer_name is the PERSON, never the item.

CRITICAL RULE — COMPOUND NUMBERS:
Amharic numbers for 101-999 are often spoken as "መቶ" (hundred) followed by a second number-word or digit meaning the remainder to ADD, not multiply. Combine them:
- "መቶ ሰማንያ" = 100 + 80 = 180
- "መቶ ሰላሳ" = 100 + 30 = 130
- "ሁለት መቶ ሃያ" = 200 + 20 = 220
- "መቶ 80" (mixed word+digit from imperfect transcription) = 100 + 80 = 180 — treat a digit right after "መቶ" the same way as a number-word: ADD it to 100, do not treat the digit as a separate/different value.
- If you see "ሺህ" (thousand) similarly combine: "ሁለት ሺህ አምስት መቶ" = 2000 + 500 = 2500.
Never output just the second part alone (e.g. never output 80 for "መቶ 80") and never output just 100 while ignoring the second part.

CRITICAL RULE — NEVER MULTIPLY BY QUANTITY:
"amount" is the TOTAL birr value the vendor stated, exactly as said. If a quantity (e.g. "2 ኪሎ") is also mentioned, do NOT multiply the amount by the quantity — the stated birr figure IS the total, unless the sentence explicitly gives a PER-UNIT price and separately asks for a computed total (rare — if in doubt, use the birr figure as stated, do not compute).
Example: "ሽንኩርት 2 ኪሎ በ180 ብር ሸጠ" -> amount is 180 (the total stated), NOT 180 x 2 = 360.
Example: "ሽንኩርት 2 ኪሎ በመቶ 80 ብር ሸጠ" -> "መቶ 80" combines to 180 -> amount is 180, NOT 80 x 2 = 160.

CRITICAL RULE — QUANTITY vs AMOUNT (applies before and after every other rule):
"amount" means the MONEY VALUE in birr, and ONLY a number that is explicitly said together with "ብር" (birr) or another currency word counts as amount. A bare number attached to a unit like ኪሎ (kilo), ፍሬ (piece), ሊትር (liter) is a QUANTITY, never an amount, no matter how large or small.
If a sentence contains a quantity+unit (e.g. "50 ኪሎ") but NO number is paired with "ብር" anywhere in the sentence, amount is MISSING -> return needs_clarification. Do NOT fall back to using the quantity number as amount under any circumstance. Put the quantity in "note".
Example: "ድንች 50 ኪሎ ገዛሁ" -> no "ብር" anywhere -> amount missing -> needs_clarification, even though "50" appears in the sentence.
Example: "ድንች 50 ኪሎ በ 500 ብር ገዛሁ" -> "500 ብር" is present -> amount is 500, note is "50 ኪሎ".

CRITICAL RULE — NEVER OUTPUT A NULL ITEM OR AMOUNT WITH status "ok":
The birr AMOUNT is ALWAYS required — if amount is missing or unclear for ANY transaction type (sale, expense, or debt), you MUST return status "needs_clarification" asking for the amount. There are NO exceptions to the amount requirement.
The ITEM has ONE narrow exception: for debt transactions where no specific product is mentioned (e.g. just money owed, no goods), item may be null — but ONLY if amount and customer_name are both present. For sale and expense transactions, item is always required same as amount.

Output STRICT JSON only, no explanation, no markdown. Exactly this shape:

{
  "status": "ok",
  "type": "sale" | "expense" | "debt",
  "item": "<string or null (debt only)>",
  "amount": <number>,
  "currency": "ETB",
  "customer_name": "<string or null>",
  "note": "<string or null, e.g. quantity like '2 ኪሎ'>"
}

OR:

{
  "status": "needs_clarification",
  "question": "<short, natural Amharic question asking specifically for the missing piece>"
}

Only output valid JSON. Nothing else."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_groq(text: str):
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
        timeout=15,
    )


def parse_transaction(text: str) -> dict:
    try:
        response = _call_groq(text)
    except Exception as e:
        return {"status": "error", "raw_output": str(e)}

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"status": "error", "raw_output": raw}


if __name__ == "__main__":
    test_phrases = [
        "ሽንኩርት ሸጥኩኝ ሁለት መቶ ብር",
        "ሽንኩርት 2 ኪሎ በመቶ ብር ሽጥኩ",
    ]
    for phrase in test_phrases:
        result = parse_transaction(phrase)
        print(f"Input: {phrase}")
        print(f"Output: {json.dumps(result, ensure_ascii=False, indent=2)}\n")
