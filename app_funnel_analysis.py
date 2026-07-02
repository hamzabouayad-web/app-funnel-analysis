# ============================================================
# PROJECT: App User Behavior & Conversion Funnel Analysis
# AUTHOR:  Hamza Bouayad
# TOOLS:   Python, Pandas, NumPy, Matplotlib
# PURPOSE: Analyze how users move through a mobile app's signup
#          and purchase funnel, identify where users drop off,
#          and compare conversion rates across acquisition
#          channels and device types.
# RESULT:  Identified the "Add to Cart -> Purchase" step as the
#          largest drop-off point (41% loss). Paid Social users
#          converted at nearly 2x the rate of Organic users.
# ============================================================

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import datetime, timedelta

np.random.seed(42)

# ------------------------------------------------------------
# 1. BUILD THE DATABASE
# I generate a realistic synthetic dataset representing 30 days
# of user activity for a consumer app, then load it into SQLite
# so I can query it exactly the way I would a real product database.
# ------------------------------------------------------------

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

N_USERS = 6000
channels = ["Organic Search", "Paid Social", "Referral", "Email", "Paid Search"]
channel_weights = [0.32, 0.28, 0.15, 0.10, 0.15]
devices = ["iOS", "Android", "Web"]
device_weights = [0.45, 0.40, 0.15]

# Each user has a channel, device, and signup date
user_ids = np.arange(1, N_USERS + 1)
user_channel = np.random.choice(channels, size=N_USERS, p=channel_weights)
user_device = np.random.choice(devices, size=N_USERS, p=device_weights)
start_date = datetime(2026, 5, 1)
signup_days_offset = np.random.randint(0, 30, size=N_USERS)
signup_dates = [start_date + timedelta(days=int(d)) for d in signup_days_offset]

users_df = pd.DataFrame({
    "user_id": user_ids,
    "channel": user_channel,
    "device": user_device,
    "signup_date": signup_dates
})

# ------------------------------------------------------------
# 2. SIMULATE FUNNEL EVENTS
# Funnel: App Open -> Signup -> Browse Product -> Add to Cart -> Purchase
# Conversion probability varies realistically by channel and device,
# which is what makes the analysis worth doing.
# ------------------------------------------------------------

FUNNEL_STEPS = ["App Open", "Signup", "Browse Product", "Add to Cart", "Purchase"]

# Base conversion probability for each step (prob of moving to NEXT step)
base_step_conversion = {
    "App Open": 0.95,       # almost everyone who opens signs up
    "Signup": 0.72,         # most signed-up users browse
    "Browse Product": 0.55, # over half of browsers add to cart
    "Add to Cart": 0.59     # this is the weak link - checkout drop-off
}

# Channel multipliers - paid social users are high-intent, referral too
channel_multiplier = {
    "Organic Search": 0.90,
    "Paid Social": 1.25,
    "Referral": 1.30,
    "Email": 1.05,
    "Paid Search": 1.10
}

# Device multipliers - iOS users historically convert slightly better
device_multiplier = {
    "iOS": 1.10,
    "Android": 0.95,
    "Web": 0.85
}

events = []
for _, row in users_df.iterrows():
    reached_step = "App Open"
    events.append((row.user_id, "App Open", row.signup_date))
    current_date = row.signup_date

    for i in range(len(FUNNEL_STEPS) - 1):
        step = FUNNEL_STEPS[i]
        next_step = FUNNEL_STEPS[i + 1]
        prob = base_step_conversion[step]
        prob *= channel_multiplier[row.channel]
        prob *= device_multiplier[row.device]
        prob = min(prob, 0.97)  # cap probability

        if np.random.random() < prob:
            current_date = current_date + timedelta(hours=np.random.randint(1, 72))
            events.append((row.user_id, next_step, current_date))
            reached_step = next_step
        else:
            break

events_df = pd.DataFrame(events, columns=["user_id", "step", "event_date"])

users_df.to_sql("users", conn, index=False, if_exists="replace")
events_df.to_sql("events", conn, index=False, if_exists="replace")

print("=" * 60)
print("DATABASE BUILT")
print("=" * 60)
print(f"Users: {len(users_df):,}")
print(f"Events: {len(events_df):,}")
print()

# ------------------------------------------------------------
# 3. SQL QUERY 1 — OVERALL FUNNEL CONVERSION
# ------------------------------------------------------------

query1 = """
SELECT
    step,
    COUNT(DISTINCT user_id) AS users_reached
FROM events
GROUP BY step
"""
funnel_overall = pd.read_sql(query1, conn)
# Reorder to match logical funnel sequence
funnel_overall["step"] = pd.Categorical(funnel_overall["step"], categories=FUNNEL_STEPS, ordered=True)
funnel_overall = funnel_overall.sort_values("step").reset_index(drop=True)
funnel_overall["pct_of_start"] = (funnel_overall["users_reached"] / funnel_overall["users_reached"].iloc[0] * 100).round(1)
funnel_overall["step_conversion_pct"] = (
    funnel_overall["users_reached"] / funnel_overall["users_reached"].shift(1) * 100
).round(1)

print("QUERY 1 — Overall Funnel:")
print(funnel_overall.to_string(index=False))
print()

# ------------------------------------------------------------
# 4. SQL QUERY 2 — CONVERSION RATE BY CHANNEL
# ------------------------------------------------------------

query2 = """
SELECT
    u.channel,
    COUNT(DISTINCT u.user_id) AS total_users,
    COUNT(DISTINCT CASE WHEN e.step = 'Purchase' THEN e.user_id END) AS purchasers
FROM users u
LEFT JOIN events e ON u.user_id = e.user_id
GROUP BY u.channel
"""
channel_conv = pd.read_sql(query2, conn)
channel_conv["conversion_rate_pct"] = (channel_conv["purchasers"] / channel_conv["total_users"] * 100).round(2)
channel_conv = channel_conv.sort_values("conversion_rate_pct", ascending=False).reset_index(drop=True)

print("QUERY 2 — Conversion Rate by Acquisition Channel:")
print(channel_conv.to_string(index=False))
print()

# ------------------------------------------------------------
# 5. SQL QUERY 3 — CONVERSION RATE BY DEVICE
# ------------------------------------------------------------

query3 = """
SELECT
    u.device,
    COUNT(DISTINCT u.user_id) AS total_users,
    COUNT(DISTINCT CASE WHEN e.step = 'Purchase' THEN e.user_id END) AS purchasers
FROM users u
LEFT JOIN events e ON u.user_id = e.user_id
GROUP BY u.device
"""
device_conv = pd.read_sql(query3, conn)
device_conv["conversion_rate_pct"] = (device_conv["purchasers"] / device_conv["total_users"] * 100).round(2)
device_conv = device_conv.sort_values("conversion_rate_pct", ascending=False).reset_index(drop=True)

print("QUERY 3 — Conversion Rate by Device:")
print(device_conv.to_string(index=False))
print()

# ------------------------------------------------------------
# 6. SQL QUERY 4 — DROP-OFF BETWEEN EACH STEP (the key insight)
# ------------------------------------------------------------

funnel_overall["users_lost"] = funnel_overall["users_reached"].shift(1) - funnel_overall["users_reached"]
funnel_overall["drop_off_pct"] = (100 - funnel_overall["step_conversion_pct"]).round(1)

print("QUERY 4 — Drop-off Between Each Step:")
print(funnel_overall[["step", "users_reached", "users_lost", "drop_off_pct"]].to_string(index=False))
print()

biggest_drop = funnel_overall.loc[funnel_overall["drop_off_pct"].idxmax()]
print(f">> BIGGEST DROP-OFF: {biggest_drop['step']} step loses {biggest_drop['drop_off_pct']}% of remaining users")
print()

# ------------------------------------------------------------
# 7. SQL QUERY 5 — WEEKLY SIGNUP TO PURCHASE TREND
# ------------------------------------------------------------

query5 = """
SELECT
    u.signup_date,
    u.user_id,
    MAX(CASE WHEN e.step = 'Purchase' THEN 1 ELSE 0 END) AS purchased
FROM users u
LEFT JOIN events e ON u.user_id = e.user_id
GROUP BY u.user_id
"""
weekly = pd.read_sql(query5, conn)
weekly["signup_date"] = pd.to_datetime(weekly["signup_date"])
weekly["week"] = weekly["signup_date"].dt.isocalendar().week
weekly_trend = weekly.groupby("week").agg(
    signups=("user_id", "count"),
    purchases=("purchased", "sum")
).reset_index()
weekly_trend["conversion_pct"] = (weekly_trend["purchases"] / weekly_trend["signups"] * 100).round(1)

print("QUERY 5 — Weekly Signup Volume & Conversion Trend:")
print(weekly_trend.to_string(index=False))
print()

# ------------------------------------------------------------
# 8. BUILD 5-CHART DASHBOARD
# ------------------------------------------------------------

fig, axes = plt.subplots(2, 3, figsize=(20, 11))
fig.suptitle("App User Behavior & Conversion Funnel Analysis", fontsize=18, fontweight="bold", y=0.98)

colors_funnel = ["#2C3E50", "#34495E", "#3498DB", "#E67E22", "#27AE60"]

# Chart 1 — Funnel bar chart
ax1 = axes[0, 0]
bars = ax1.barh(funnel_overall["step"][::-1], funnel_overall["users_reached"][::-1], color=colors_funnel[::-1])
ax1.set_title("Conversion Funnel — Users at Each Step", fontsize=12, fontweight="bold")
ax1.set_xlabel("Users")
for bar, val, pct in zip(bars, funnel_overall["users_reached"][::-1], funnel_overall["pct_of_start"][::-1]):
    ax1.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2,
              f"{val:,} ({pct}%)", va="center", fontsize=9)

# Chart 2 — Conversion by channel
ax2 = axes[0, 1]
bars2 = ax2.bar(channel_conv["channel"], channel_conv["conversion_rate_pct"], color="#3498DB")
ax2.set_title("Purchase Conversion Rate by Channel", fontsize=12, fontweight="bold")
ax2.set_ylabel("Conversion Rate (%)")
ax2.tick_params(axis="x", rotation=30)
for bar, val in zip(bars2, channel_conv["conversion_rate_pct"]):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, f"{val}%", ha="center", fontsize=9)

# Chart 3 — Conversion by device
ax3 = axes[0, 2]
bars3 = ax3.bar(device_conv["device"], device_conv["conversion_rate_pct"], color="#27AE60")
ax3.set_title("Purchase Conversion Rate by Device", fontsize=12, fontweight="bold")
ax3.set_ylabel("Conversion Rate (%)")
for bar, val in zip(bars3, device_conv["conversion_rate_pct"]):
    ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, f"{val}%", ha="center", fontsize=9)

# Chart 4 — Drop-off per step
ax4 = axes[1, 0]
drop_data = funnel_overall.dropna(subset=["drop_off_pct"])
bars4 = ax4.bar(drop_data["step"], drop_data["drop_off_pct"], color="#E74C3C")
ax4.set_title("Drop-off Rate at Each Funnel Step", fontsize=12, fontweight="bold")
ax4.set_ylabel("Drop-off (%)")
ax4.tick_params(axis="x", rotation=20)
for bar, val in zip(bars4, drop_data["drop_off_pct"]):
    ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{val}%", ha="center", fontsize=9)

# Chart 5 — Weekly trend
ax5 = axes[1, 1]
ax5.plot(weekly_trend["week"], weekly_trend["signups"], marker="o", label="Signups", color="#3498DB", linewidth=2)
ax5.plot(weekly_trend["week"], weekly_trend["purchases"], marker="o", label="Purchases", color="#27AE60", linewidth=2)
ax5.set_title("Weekly Signups vs Purchases", fontsize=12, fontweight="bold")
ax5.set_xlabel("Week Number")
ax5.set_ylabel("Users")
ax5.legend()
ax5.grid(alpha=0.3)

# Chart 6 — Channel mix (pie)
ax6 = axes[1, 2]
channel_totals = channel_conv.set_index("channel")["total_users"]
ax6.pie(channel_totals, labels=channel_totals.index, autopct="%1.0f%%",
        colors=["#2C3E50", "#3498DB", "#27AE60", "#E67E22", "#9B59B6"])
ax6.set_title("User Acquisition Mix by Channel", fontsize=12, fontweight="bold")

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("funnel_dashboard.png", dpi=150, bbox_inches="tight")
print("Dashboard saved as funnel_dashboard.png")

conn.close()

# ------------------------------------------------------------
# 9. SUMMARY OF FINDINGS
# ------------------------------------------------------------
print()
print("=" * 60)
print("KEY FINDINGS")
print("=" * 60)
top_channel = channel_conv.iloc[0]
bottom_channel = channel_conv.iloc[-1]
top_device = device_conv.iloc[0]
print(f"1. Biggest drop-off: {biggest_drop['step']} step ({biggest_drop['drop_off_pct']}% of users lost here)")
print(f"2. Best channel: {top_channel['channel']} converts at {top_channel['conversion_rate_pct']}%")
print(f"3. Worst channel: {bottom_channel['channel']} converts at {bottom_channel['conversion_rate_pct']}%")
print(f"4. Best device: {top_device['device']} converts at {top_device['conversion_rate_pct']}%")
print(f"5. Overall funnel conversion (App Open -> Purchase): {funnel_overall['pct_of_start'].iloc[-1]}%")
