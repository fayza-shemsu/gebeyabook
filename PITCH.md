# GebeyaBook (Gebeya Debter) - One Pager

## The problem

Informal market vendors in Ethiopia, many with limited literacy, have no reliable way to track daily sales, expenses, and customer credit. Existing bookkeeping tools assume typing and reading, which excludes exactly the population that needs this most. Vendors currently rely on memory or scraps of paper, and money owed by customers on credit is especially easy to lose track of.

## The solution

GebeyaBook is a voice-only bookkeeping assistant that works entirely over Telegram. A vendor speaks a sale, expense, or debt in Amharic, and the system transcribes it, extracts the structured transaction, saves it, and reads a spoken confirmation back. No typing, no reading, no new app to install. A companion web dashboard gives a visual view of the same data for anyone who wants it.

## Validation

Interviewed real market vendors before writing any code to confirm the pain point and collect real spoken phrasing patterns. After building the core pipeline, ran a real pilot day with three vendors selling vegetables, coffee and tea, and shoes, using the live product for real transactions. All three vendors said they preferred speaking over writing. Two of three said they would keep using it without supervision. The pilot surfaced two real bugs, a compound-number parsing error and overly narrow debt-phrase detection, both fixed and verified using the vendors' own real phrasing afterward.

## What is next

Three realistic next features, in priority order:

1. SMS fallback for vendors without a smartphone or reliable data, so the voice pipeline is not the only way in
2. Direct logging of Telebirr or CBE Birr mobile payment confirmations, so digital payments do not need to be spoken manually
3. Additional language support, starting with Oromiffa and Tigrinya, since informal vendors nationwide are not exclusively Amharic speakers

## Current status

Live, working, and pilot-tested. Telegram bot deployed on Render, web dashboard deployed on Vercel, PostgreSQL database with proper migrations, real error handling and rate limiting in place.
