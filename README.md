# App User Behavior & Conversion Funnel Analysis

I've always been curious why some apps feel like they "leak" users at checkout even when signups look healthy — so I built this analysis to find exactly where a user base drops off between opening an app and actually buying something.

**Tools:** Python · SQLite · Pandas · Matplotlib

## What I Built

A simulated but realistic dataset of 6,000 app users moving through a 5-step funnel — **App Open → Signup → Browse Product → Add to Cart → Purchase** — tracked across acquisition channel (Organic, Paid Social, Referral, Email, Paid Search) and device (iOS, Android, Web). I loaded everything into a SQLite database and wrote SQL queries to answer the same questions a product team would actually ask.

## Key Findings

- **Biggest drop-off point:** the **Add to Cart → Purchase** step, where 37% of remaining users are lost — bigger than any other step in the funnel, including signup.
- **Referral users convert 3.4x better than Organic Search users** (51% vs 15%) — meaning acquisition channel matters far more than raw traffic volume.
- **iOS users convert at 42%**, compared to 26% on Android and under 19% on Web — a signal worth digging into for platform-specific UX issues.
- **Overall funnel conversion** from first app open to purchase: **32.4%**.

## How It Works

1. Generates synthetic user and event data with realistic, weighted conversion probabilities per channel/device (not random — designed to mimic real product behavior)
2. Loads it into a SQLite database
3. Runs 5 SQL queries: overall funnel, conversion by channel, conversion by device, step-by-step drop-off, and weekly signup/purchase trend
4. Builds a 6-chart dashboard summarizing everything

## Why This Matters

This is the exact kind of analysis a Product Analyst or Data Analyst does to answer "where are we losing users and why." Knowing where the biggest leak is (Add to Cart, not signup) tells a product team exactly where to focus — checkout friction, payment options, or trust signals — instead of guessing.

📁 [View the analysis script](./app_funnel_analysis.py)
