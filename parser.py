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
- Numbers may appear as Amharic words or digits.
- Common SALE verbs: ሸጥኩ / ሸጠሁ / ሽጥኩ / ተሸጠ
- Common EXPENSE verbs: ገዛሁ / ገዛው
- DEBT indicator: በዱቤ (on credit)
- For DEBT transactions: the customer_name is the PERSON, never the item. A person's name in a debt sentence (e.g. "ከበደ ሶስት መቶ ብር በዱቤ ወሰደ" - Kebede took 300 birr on credit) should be extracted as customer_name, NOT as item. If no specific product/item is mentioned in a debt sentence, item should be null, not the customer name.

CRITICAL RULE — QUANTITY vs AMOUNT:
"amount" means the MONEY VALUE in birr — how much was paid or received. It is NOT the quantity of goods (kilos, pieces, liters). If a sentence mentions a quantity (e.g. "50 ኪሎ") but never states a birr price, the amount is MISSING — do not use the quantity number as the amount.
Example: "ድንች 50 ኪሎ ገዛሁ" has a quantity (50 kilo) but NO price -> amount is missing -> needs_clarification.
Example: "ድንች 50 ኪሎ በ 500 ብር ገዛሁ" -> amount is 500 (the birr value), NOT 50.

CRITICAL RULE — NEVER OUTPUT A NULL ITEM OR AMOUNT WITH status "ok":
If you cannot confidently identify BOTH the item AND the birr amount, you MUST return status "needs_clarification" — never return status "ok" with item or amount set to null. There are no exceptions to this rule. (Exception: for debt transactions with no product mentioned, item may be null as long as customer_name and amount are both present.)

Output STRICT JSON only, no explanation, no markdown. Exactly this shape:

{
  "status": "ok",
  "type": "sale" | "expense" | "debt",
  "item": "<string or null (debt only)>",
  "amount": <number>,
  "currency": "ETB",
  "customer_name": "<string or null>",
  "note": "<string or null, e.g. quantity like '50 ኪሎ'>"
}

OR, if item or amount is missing/unclear:

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
