# Day 4 — Transcription Test Log

| # | What I said | Azure transcribed | Accurate? | Notes |
|---|---|---|---|---|
| 1 | ሁለት መቶ ብር | 200 ብር | ✅ | digit conversion, correct |
| 2 | ሶስት ሺህ ብር | 3000 ብር | ✅ | correct |
| 3 | ቲማቲም | ቲማቲም | ✅ | correct |
| 4 | ቡና | ቡና | ✅ | correct |
| 5 | ሽንኩርት ሁለት ኪሎ በመቶ ብር ሸጥኩኝ | ሽንኩርት 2 ኪሎ በመቶ ብር ሽጥኩ | ✅ | minor spelling drift, ኝ suffix dropped |
| 6 | ቲማቲም ሶስት ኪሎ ሁለት መቶ ብር ሸጠሁ | ቲማቲም ሦስት ኪሎ 200 ብር ሸጡኩ | ✅ | correct on retry (first attempt had wrong verb form) |
| 7 | ቡና አንድ ኪሎ አምስት መቶ ብር ተሸጠ | ቡና 1 ኪሎ 500 ብር ተሸጠ | ✅ | correct |
| 8 | ድንች ሃምሳ ኪሎ ገዛሁ | ድንች, 50 ኪሎ ገዛሁ | ✅ | correct on retry (first attempt misheard as "ደኖች") |
| 9 | ስኳር አስር ኪሎ ገዛሁ በሁለት መቶ ብር | ስኳር 10 ኪሎ ገዛሁ በ 200 ብር | ✅ | correct on retry (first attempt dropped "ሁለት") |
| 10 | ለትራንስፖርት አርባ ብር ከፈልኩ | ለትራንስፖርት 40 ብር ከፍ አልኩ | ⚠️ | close but verb slightly off ("ከፍ አልኩ" vs "ከፈልኩ") — meaning still understandable |

## Repeated mistakes observed
1. **Inconsistency on retry** — the same sentence spoken twice can transcribe differently; several "errors" on first attempt disappeared on a clean retry. Suggests accuracy is sensitive to pace/clarity, not a fundamental model limitation.
2. **Verb endings are the least reliable part** — first-person past tense verbs (ሸጠሁ, ገዛሁ, ከፈልኩ) are where most remaining variation shows up, even after retries (#10).
3. **Numbers, item names, and short phrases are highly reliable** — near-perfect across all attempts.
4. **Two-number sentences** (amount + price) can occasionally drop or merge a number on a rushed take — worth double-checking, not designing around as a certainty.

## Why this matters for Day 5
The parser should not depend on an exact verb match to detect sale vs. purchase — since verb transcription varies most, the prompt should use flexible/contextual matching. Item and number extraction can be trusted more heavily since they're consistently accurate.