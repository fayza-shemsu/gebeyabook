# Day 13 — Pilot Day Notes

## Vendor 1
- Who: Returning vendor from Day 1
- Sells: Vegetables (tomatoes, onions, potatoes)
- Moments of confusion:
  - Opened Telegram without any problem.
  - Didn't know whether to type or send a voice message after pressing Start.
  - Asked: "Should I say everything in one voice note or one sale at a time?"
- Bot misunderstandings:
  - Vendor said: "I sold two kilos of onions for 180 birr."
  - Bot recorded 80 birr instead of 180 birr.
- Did they use undo/correction naturally?
  - No. They asked "How do I fix it?" — had to be shown.
- "Would you use this tomorrow without me?"
  - "Yes, if it understands my voice better."
- Overall reaction:
  - Smiled after seeing the sales summary.
  - Said speaking is easier than writing in a notebook.

## Vendor 2
- Who: New vendor
- Sells: Coffee and tea
- Moments of confusion:
  - Found Telegram easily.
  - Didn't understand what "/today" meant.
  - Expected the bot to ask questions automatically.
- Bot misunderstandings:
  - Understood every sale correctly. No speech recognition errors.
- Did they use undo/correction naturally?
  - Yes. After making a mistake, typed "undo" without being told.
- "Would you use this tomorrow without me?"
  - "Maybe. I need to practice once or twice."
- Overall reaction:
  - Liked that everything was saved automatically.
  - Suggested showing today's total in larger text.

## Vendor 3
- Who: Returning vendor
- Sells: Shoes
- Moments of confusion:
  - Didn't know whether to record debts separately from sales.
  - Asked if customer names were required.
- Bot misunderstandings:
  - Vendor said: "Customer will pay tomorrow."
  - Bot recorded it as a normal sale instead of a debt.
- Did they use undo/correction naturally?
  - Needed help.
- "Would you use this tomorrow without me?"
  - "Yes, but I want it in Amharic."
- Overall reaction:
  - Very interested. Said it could save time during busy hours.
  - Asked if it works without internet.

## Patterns across all vendors

Most common confusion:
- People understood Telegram itself fine.
- Unsure exactly what to say in the voice message / how to phrase a sale.
- "/today" and "/debts" were not immediately obvious — nobody was told these commands exist.

Most common bot error:
- Numbers above 100 were sometimes recognized incorrectly (180 → 80).
- The bot occasionally confused debt phrasing ("will pay tomorrow") with a completed sale, since it didn't use the expected "በዱቤ" keyword.

Feature requests:
- Full Amharic interface (all bot messages, not just confirmations).
- Expense tracking made more visible.
- Profit calculation.
- Monthly reports.
- Offline capability.
- Easier, more discoverable way to correct mistakes.

Overall verdict:
- All vendors liked the idea of speaking instead of writing — this is the core value proposition, and it landed.
- Nobody had trouble opening Telegram or getting started.
- Biggest improvements needed: (1) numeric transcription accuracy on 3-digit amounts, (2) recognizing debt phrasing beyond the "በዱቤ" keyword, (3) making bot commands and capabilities discoverable without prior explanation.
