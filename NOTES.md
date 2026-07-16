# Day 2 — STT/TTS Engine Decision

## Speech-to-Text (STT)

### Groq whisper-large-v3
Score: 1/5
- With language="am" forced: hallucinated Cyrillic, Burmese, and mixed scripts — completely unusable
- Without language param (auto-detect): improved slightly, phonetically close on 2/5 clips, but outputs Latin/Arabic/Urdu transliteration instead of real Amharic script
- Verdict: not usable for this project — no real Amharic script support

### Azure Speech-to-Text (am-ET)
Score: 5/5
- All 5 test clips transcribed accurately into real Amharic script
- Correctly handled numbers (converted to digits, e.g. "ሁለት መቶ" → "200") — a bonus, makes parsing easier later
- Minor: dropped the "ኝ" suffix in "ሸጥኩኝ" → "ሸጥኩ" once, negligible

## DECISION: STT
**Azure Speech-to-Text (am-ET)** — chosen for production use.
Groq whisper-large-v3 does not reliably support Amharic script and is not usable for this project.
## Text-to-Speech (TTS)

### Azure TTS (am-ET-MekdesNeural)
Score: 5/5 (clear, natural)
- Generated audio for test sentence, sounded clear and understandable
- Free tier available, dedicated Amharic voices

### ElevenLabs
Score: N/A — blocked
- Free tier does not allow API access to voices at all (402 payment_required)
- Would require paid subscription; Amharic is not an officially strong-supported language for ElevenLabs anyway
- Not worth paying to test given Azure already performs well and is free

## DECISION: TTS
**Azure TTS (am-ET-MekdesNeural)** — chosen for production use.