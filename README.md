# GebeyaBook (Gebeya Debter)

Voice-first bookkeeping for informal market vendors.

Ethiopian market vendors, many with limited literacy, track their daily sales, expenses, and customer debts from memory or scraps of paper. GebeyaBook lets a vendor speak a sale in Amharic into Telegram and get it recorded, summarized, and read back to them. No typing, no reading required.

## The problem

Informal market vendors in Ethiopia often cannot reliably track their own sales, expenses, and customer credit. Existing bookkeeping apps assume literacy and manual data entry, which excludes exactly the population that needs this most.

## How it works

1. Vendor sends a voice note to the Telegram bot, saying something like: onion two kilo two hundred birr sold
2. Azure Speech-to-Text transcribes the Amharic audio
3. Groq (Llama 3.3 70B) parses the transcription into structured data: type (sale, expense, or debt), item, amount, customer name
4. The transaction is saved to a PostgreSQL database
5. Azure Text-to-Speech reads back a spoken confirmation

## Features

- Voice-only transaction logging for sales, expenses, and debt or credit
- Multi-vendor support with isolated data per Telegram account
- Spoken /today, /week, and /debts summaries
- Voice-triggered undo and an /edit_last correction flow
- Follow-up clarification when a voice note is missing an amount or item
- Web dashboard with a 7-day sales and expense chart
- Rate limiting, strict parser output validation, session-based dashboard login

## Tech stack

Backend: Python, FastAPI, python-telegram-bot, deployed on Render
Speech: Azure Cognitive Services Speech, am-ET locale
Transaction parsing: Groq API, Llama 3.3 70B
Database: PostgreSQL on Render, SQLAlchemy plus Alembic migrations
Dashboard: Next.js, Tailwind CSS, Recharts, deployed on Vercel

## Live links

Telegram bot: search for GebeyaBookBot on Telegram
Dashboard: https://gebeyabook-dashboard.vercel.app

## Known limitations

Azure Speech-to-Text accuracy varies for longer sentences and certain similar-sounding Amharic word pairs. The parser asks for clarification instead of guessing when this happens.
Free-tier hosting means the bot can take up to fifty seconds to respond after inactivity.
There is no mark-debt-as-paid feature yet.

## Running locally

1. Clone the repo and create a virtual environment.
2. Install dependencies: pip install -r requirements.txt --break-system-packages
3. Copy .env.example to .env and fill in real values.
4. Run database migrations: alembic upgrade head
5. Start the server: uvicorn backend.main:app --reload
6. Set your Telegram bot webhook to point at a public URL.

See .env.example for the full list of required environment variables and what each one is for.
