# Personal Life Operating System (PLOS) - Hybrid Master Spec

## 1. User Baseline

This system is designed for one primary user and should optimize for sustainable, measurable life improvement across health, fitness, food, sleep, finance, social connection, career growth, habits, and mental wellness.

### Current Baseline

- Current weight: 118 kg
- Current BP medication: Tazloc CT 40
- Primary health goals:
  - Reduce weight sustainably.
  - Improve BP through lifestyle changes.
  - Reduce medication dependency only under doctor supervision.
  - Improve physical fitness, consistency, discipline, and mental wellness.

### Primary Outcomes

1. Reduce weight sustainably.
2. Improve BP health naturally while keeping all medication decisions under doctor supervision.
3. Improve consistency and discipline.
4. Improve physical fitness.
5. Improve mental wellness.
6. Improve social engagement.
7. Improve financial health and net worth visibility.
8. Build lifelong habits.
9. Create measurable progress across all major life dimensions.

---

## 2. Safety Rules

PLOS must behave like a life improvement system, not a doctor, therapist, financial advisor, lawyer, tax advisor, or investment advisor.

### Health Safety Rules

- Never recommend starting, stopping, increasing, reducing, or changing medication.
- Never claim to diagnose BP, diabetes, obesity, anxiety, depression, sleep disorders, or any other medical condition.
- Always advise doctor consultation for medication decisions, unusual readings, severe symptoms, fasting concerns, chest pain, fainting, severe dizziness, extreme BP readings, or repeated abnormal health patterns.
- Treat BP, sugar, fasting, exercise, weight loss, pranayama, yoga, meditation, and sleep recommendations as general wellness support.
- Prefer conservative target progression. Avoid extreme diets, extreme fasting, overtraining, or punishment-based coaching.
- If the user reports severe symptoms, the AI coach must prioritize urgent medical help over ordinary coaching.

### Finance Safety Rules

- Do not provide regulated investment, insurance, legal, tax, or trading advice as a professional recommendation.
- Do not recommend specific trades, aggressive options strategies, leverage, or concentrated bets.
- For asset allocation, insurance purchases, property decisions, tax planning, legal matters, or trading strategy changes, suggest consulting qualified professionals.
- Prioritize capital protection, liquidity, emergency funds, debt awareness, and risk visibility before profit targets.
- Finance insights should be framed as tracking observations, reminders, risk flags, and educational guidance.

### Coaching Safety Rules

- Tone must be firm, practical, direct, and non-shaming.
- Reward honest logging even when behavior is poor.
- If performance drops, reduce friction before increasing pressure.
- The AI coach should never use guilt, fear, insults, or humiliation.
- The system should optimize sustainability over perfection.

---

## 3. Product Vision

Create an AI-powered Personal Life Operating System that combines:

- Web app tracking and dashboards.
- AI daily coaching and accountability.
- Habit scoring and progress reviews.
- Health, finance, social, career, and lifestyle pattern detection.
- Telegram reminders with low notification fatigue.
- Long-term measurable improvement across life dimensions.

The system should act as:

- Personal coach
- Accountability partner
- Health assistant
- Performance optimizer
- Habit builder
- Finance tracker
- Life dashboard

The web app is the system of record. The AI coach reads logged data and produces coaching, reviews, reminders, risk flags, and next actions.

---

## 4. Phase 1 Scope

Phase 1 should be focused but complete enough to be useful every day.

### Phase 1 Includes

- Manual data entry.
- Core life logging.
- Health metrics tracking.
- Food and fasting tracking.
- Exercise and mind habit tracking.
- Sleep tracking.
- Finance and net worth tracking.
- Career and social tracking.
- Bad habit tracking.
- North Star dashboard.
- Finance dashboard.
- Capped Life Score from 0 to 1000.
- Separate AI Accountability Score.
- Daily AI coach check-in.
- Weekly AI review.
- Telegram reminders.
- Compact daily reports and deeper weekly/monthly reports.

### Phase 1 Excludes

- Bank API integrations.
- PF API integrations.
- Broker API integrations.
- Google Fit integration.
- Apple Health integration.
- Smartwatch integration.
- OCR food logging.
- Voice logging.
- Automated medical interpretation.
- Automated investment or trading advice.

---

## 5. Web App Requirements

The web app should provide structured logging, dashboards, scores, trends, reports, and AI coach outputs.

### Technology Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python
- Database Phase 1: SQLite
- Database Phase 2: PostgreSQL
- Authentication: user account with email/password
- AI layer: OpenAI primary, Claude optional
- Notifications: Telegram bot
- Deployment Phase 1: local laptop
- Deployment Phase 2: Oracle Cloud Infrastructure Always Free

### Core Screens

- North Star Dashboard
- Daily Check-in
- Health Log
- Food and Fasting Log
- Exercise and Mind Log
- Sleep Log
- Finance Dashboard
- Finance Logs
- Social and Career Log
- Bad Habits Log
- Reports
- Settings and Targets

### North Star Dashboard

The North Star Dashboard is the primary screen.

Show:

- Current weight
- Weight trend
- BP trend
- Current BP medication reference
- Life Score from 0 to 1000
- AI Accountability Score
- Consistency score
- Current streaks
- Goal completion rate
- Health score
- Food score
- Exercise score
- Sleep score
- Finance score
- Social score
- Career/Growth score
- Top 3 risks
- Top 3 next actions

---

## 6. AI Coach Behavior

The AI coach should use all logged app data for holistic coaching.

### Operating Style

- Be firm, practical, and direct.
- Keep daily output compact.
- Focus on actions the user can complete today.
- Praise consistency and honest logging, not perfection.
- Detect patterns across categories.
- Recommend conservative target changes based on 1-2 weeks of data.
- Ask for missing high-impact logs only.

### Daily Coach Output

Every daily check-in should include:

- Wins: what went well.
- Risks: what is falling behind.
- Score snapshot: Life Score and key category scores.
- Missing logs: only the highest-impact missing data.
- Next actions: 1 to 3 concrete actions for today.

### Weekly Coach Output

Every weekly review should include:

- Biggest wins.
- Biggest bottlenecks.
- Most improved category.
- Worst performing category.
- What helped weight loss.
- What increased BP risk.
- Food, sleep, exercise, and stress patterns.
- Finance progress and risk flags.
- Social and career consistency.
- One focus area for next week.
- Recommended target adjustments.

### Monthly Coach Output

Every monthly review should include:

- Life Score trend.
- Category score trends.
- Weight and BP trends.
- Habit streaks.
- Finance and net worth trend.
- Expense and investment trend.
- Insurance renewal or policy gaps.
- Career and social progress.
- Top 3 lessons.
- Top 3 priorities for next month.

---

## 7. Data Model

Phase 1 data entry is manual. Store structured snapshots and logs so the AI coach can analyze trends without requiring external integrations.

### User Profile

Store:

- Name
- Age if provided
- Height if provided
- Current weight
- Target weight milestones
- BP medication reference
- Health constraints
- Preferred coaching tone
- Reminder preferences
- Target settings

### Daily Check-in

Store:

- Date
- Mood
- Energy
- Stress
- Overall day rating
- Notes
- Completed habits
- Missed habits
- AI summary

### Health Metrics

Track daily when available:

- BP
- Blood sugar
- Weight
- BMI
- Body fat percentage
- Muscle percentage
- Visceral fat
- Body age
- RMR/BMR
- Health notes

### Exercise and Mind

Daily targets:

- Walking: 5300 steps
- Pranayama: 15 minutes
- Meditation: 15 minutes
- Yoga: 15 minutes

Weekly targets:

- Strength training: 60 minutes, 3 times per week
- Preferred strength days: Monday, Wednesday, Friday
- Weekend cardio: 1 session per week
- Weekend cardio options: running, cycling, long walk
- Weekend cardio duration: 60 minutes

Track:

- Activity type
- Duration
- Intensity
- Steps
- Distance
- Completion status
- Notes

### Food and Nutrition

Track:

- Food item
- Quantity in grams
- Meal type
- Meal time
- Calories
- Protein
- Carbs
- Fat
- Fibre
- Food quality score from 0 to 100
- Processed food flag
- Direct sugar flag
- Refined food flag

Nutrition goals:

- Low carb diet
- Calorie deficit
- Weight reduction
- Higher food quality
- Reduced direct sugar
- Reduced processed and refined food

Fasting progression:

- Start: 14:10
- Progress to: 16:8
- Then: 18:6
- AI should recommend progression only when adherence and health context look stable.

### Sleep

Track:

- Sleep duration
- Sleep quality
- Bed time
- Wake time
- Sleep consistency
- Sleep notes

Sleep should contribute significantly to health, BP risk, and consistency insights.

### Social

Targets:

- Call friend: daily
- Meet friend/cousin: monthly
- Bike ride: 20 km per week

Track:

- Activity type
- Person or group
- Duration
- Date
- Notes
- Social energy impact

### Career and Growth

Target:

- 1 interview per month

Track:

- Applications
- Interviews scheduled
- Interviews completed
- Learning sessions
- Resume updates
- Networking actions
- Career notes

### Bad Habits

Track:

- Direct sugar
- Processed food
- Refined food
- Smoking
- Alcohol
- Social media

Targets:

- Direct sugar: zero
- Processed food: zero
- Refined food: zero
- Smoking: zero
- Alcohol: maximum 180 ml per month
- Social media: maximum 30 minutes per day

### Out of Comfort Zone

Target:

- 1 activity per week

Examples:

- Solo bike ride
- Solo movie
- Solo train travel
- Coffee with friend
- AI suggested challenge

Track:

- Activity
- Date
- Difficulty
- Emotional impact
- Notes

---

## 8. Finance Tracker

The finance tracker should provide a full net worth and financial health view through manual snapshots in Phase 1.

### Properties

Track:

- Property name
- Property type
- Location
- Estimated value
- Ownership share
- Purchase price if provided
- Loan status
- Outstanding loan amount
- EMI
- Interest rate if provided
- Rental income
- Maintenance cost
- Property notes

### Bank Accounts

Track:

- Bank name
- Account type
- Balance snapshot
- Purpose
- Minimum balance
- Interest rate if relevant
- Last updated date
- Notes

### Investments

Track:

- SIPs
- Stocks
- Mutual funds
- ETFs
- FDs
- Bonds
- Gold
- Crypto if applicable
- Current value
- Monthly contribution
- Goal or purpose
- Risk category
- Last updated date

Primary investment target:

- Increase investments by Rs 50,000 per month.

### PF and Retirement

Track:

- EPF
- PPF
- NPS
- Employer PF
- Pension balances
- Contribution amounts
- Maturity or lock-in notes
- Last updated date

### Insurance

Track:

- Term life insurance
- Health insurance
- Vehicle insurance
- Property insurance
- Personal accident insurance
- Policy number or reference
- Insurer
- Coverage amount
- Premium
- Renewal date
- Nominee
- Policy notes

### Liabilities

Track:

- Home loan
- Personal loan
- Credit card dues
- Vehicle loan
- Other debts
- Interest rate
- EMI
- Outstanding balance
- Due date
- Last updated date

### Expenses

Track:

- Expenses above Rs 2,000
- Optional recurring expenses
- Category
- Amount
- Reason
- Need/want flag
- Date
- Payment account

Generate AI insights about high expenses, recurring leaks, and avoidable wants.

### Trading

Current strategy:

- Options selling

Initial target:

- Rs 5,000 per month

Track:

- Trades
- Win rate
- Monthly P&L
- Drawdown
- Risk per trade
- Margin usage
- Losses
- Notes

The AI coach must prioritize risk metrics and capital protection over profit targets.

### Finance Dashboard

Show:

- Total net worth
- Total assets
- Total liabilities
- Liquid assets
- Illiquid assets
- Property value
- Bank balance total
- Investment value total
- PF/retirement total
- Insurance coverage overview
- Insurance renewal calendar
- Debt outstanding
- Monthly investment amount
- Monthly expenses
- Emergency fund coverage
- Finance goal progress
- Trading P&L and risk summary

### AI Finance Behavior

The AI coach should:

- Provide trend insights.
- Highlight missing snapshots.
- Remind about insurance renewals.
- Flag high debt, high expenses, poor emergency fund coverage, and trading risk.
- Track monthly investment consistency.
- Compare net worth trend month over month.
- Avoid professional financial advice.

---

## 9. Scoring Model

### Life Score

Life Score range:

- Minimum: 0
- Maximum: 1000

Category weights:

- Health: 30%
- Food: 25%
- Exercise: 20%
- Sleep: 10%
- Finance: 5%
- Social: 5%
- Career/Growth: 5%

Rules:

- Score must always stay between 0 and 1000.
- Streak bonuses must be capped.
- Negative penalties must be capped.
- One poor behavior should reduce score but should not destroy motivation.
- Honest logging should be rewarded through the AI Accountability Score.

### AI Accountability Score

Separate from Life Score.

Purpose:

- Measure tracking discipline and data completeness.

Factors:

- Logging consistency
- Daily check-ins
- Missing entries
- Data completeness
- Honest logging
- Continuous tracking

Penalties:

- Missing entries
- Incomplete records
- Repeated skipped check-ins

### Streak Bonuses

Use capped streak bonuses:

- 7 days: small bonus
- 30 days: moderate bonus
- 90 days: strong bonus
- 180 days: milestone bonus

Bonuses should improve motivation without making the score unrealistic.

### Negative Signals

Track negative signals:

- Smoking
- Processed food
- Direct sugar
- Excess alcohol
- Missed logging
- Repeated poor sleep
- Repeated missed workouts
- Excess social media
- High discretionary expenses
- Excessive trading risk

Penalties should be bounded and paired with recovery actions.

---

## 10. Target Progression

Targets should adapt conservatively based on 1-2 weeks of performance.

### If User Succeeds

- Increase targets gradually.
- Prefer one small change at a time.
- Keep workload sustainable.
- Do not increase health targets aggressively after a short streak.

### If User Struggles

- Reduce the target slightly.
- Reduce friction.
- Suggest easier alternatives.
- Prioritize restarting consistency.
- Avoid shame or all-or-nothing framing.

### Examples

- Steps: increase only after consistent completion.
- Meditation: move from 15 minutes to 20 minutes only after stable adherence.
- Fasting: progress from 14:10 to 16:8 only when adherence and health context are stable.
- Strength training: improve consistency before increasing load or frequency.
- Finance: ask for missing snapshots before giving trend insights.

---

## 11. Workflows

### Daily Workflow

1. User enters daily logs.
2. Web app updates scores and dashboard.
3. AI coach identifies wins, risks, missing data, and next actions.
4. Telegram reminders are scheduled only when helpful.
5. User receives compact daily coaching.

### Weekly Workflow

1. Aggregate all category logs.
2. Compute Life Score and category score trends.
3. Detect patterns.
4. Identify bottlenecks.
5. Recommend one focus area.
6. Suggest conservative target adjustments.
7. Review finance snapshots and renewal reminders.

### Monthly Workflow

1. Review health, weight, BP, habit, sleep, finance, career, and social trends.
2. Compare net worth and investment progress.
3. Review insurance renewals and debt status.
4. Identify major wins and repeated blockers.
5. Set next month priorities.

### Quarterly Workflow

1. Review long-term progress.
2. Reassess goals and targets.
3. Review finance, insurance, property, career, and health direction.
4. Identify whether Phase 2 integrations or app improvements are needed.

---

## 12. Pattern Detection

The AI coach should detect patterns such as:

- User skips meditation on Mondays.
- User eats processed food on weekends.
- Weight drops when strength training is completed 3 times per week.
- Sleep quality impacts BP.
- High social media usage reduces sleep.
- Missing food logs correlate with poor weight progress.
- Large expenses cluster around weekends.
- Insurance renewals are approaching.
- Trading risk increases after losses.
- Social activity improves mood and consistency.

Pattern insights should be practical and tied to a specific next action.

---

## 13. Prediction Engine

Prediction should be cautious and clearly labeled as an estimate.

Generate when enough data exists:

- 30-day weight estimate
- 60-day weight estimate
- 90-day weight estimate
- BP trend estimate
- Consistency estimate
- Finance trend estimate
- Net worth trend estimate
- Probability of maintaining key habits

Rules:

- Do not overstate certainty.
- Do not predict medication reduction.
- Do not imply medical outcomes are guaranteed.
- Mention when data is insufficient.
- Use predictions to guide behavior, not to create pressure.

---

## 14. Risk Detection

Detect and flag:

- Weight increasing for 3 consecutive weeks.
- Sleep deterioration.
- Increasing social isolation.
- Increasing stress.
- Excessive social media usage.
- Finance goals slipping.
- Repeated missed workouts.
- Repeated poor food quality.
- Repeated missed BP or weight logs.
- Rising discretionary expenses.
- Missing insurance renewal dates.
- High debt or EMI burden.
- Trading drawdown or repeated losses.

Each risk alert should include:

- Risk name
- Why it matters
- Evidence from logs
- Suggested next action
- Safety disclaimer when relevant

---

## 15. Reminder Rules

Telegram integration should support reminders without notification fatigue.

Reminder types:

- Meditation reminder
- Workout reminder
- Food logging reminder
- Friend call reminder
- Sleep reminder
- Expense tracking reminder
- Finance snapshot reminder
- Insurance renewal reminder
- BP/weight logging reminder

Rules:

- Reminders should be timely and useful.
- Avoid excessive frequency.
- AI should adjust timing based on completion history.
- Critical reminders, such as insurance renewal or missing health logs, may receive higher priority.
- The user should be able to mute or reduce reminders.

---

## 16. Reporting

### Daily Report

Keep compact:

- Life Score
- Key category scores
- Wins
- Risks
- Missing logs
- 1 to 3 next actions

### Weekly Report

Include:

- Life Score trend
- Category score trend
- Weight trend
- BP trend
- Food quality trend
- Exercise consistency
- Sleep consistency
- Habit streaks
- Finance summary
- Social and career progress
- AI insights
- Recommended focus area

### Monthly Report

Include:

- Life Score trend
- Category score trends
- Goal scores
- Weight trend
- BP trend
- Habit trends
- Streaks
- Prediction trends
- Net worth trend
- Expense trend
- Investment progress
- Insurance renewal status
- Debt status
- AI insights
- Recommendations

### Quarterly and Yearly Reports

Include:

- Long-term progress summary
- Health and weight milestones
- Finance and net worth milestones
- Social and career progress
- Biggest behavior patterns
- Best habit systems
- Weakest life areas
- Strategic recommendations

---

## 17. Gamification

Gamification should support consistency without encouraging unhealthy extremes.

### Levels

- Bronze
- Silver
- Gold
- Platinum
- Diamond

### Achievements

- 7-day meditation streak
- 30-day no direct sugar
- 5 kg weight loss
- 10 kg weight loss
- 100 workouts
- Monthly investment milestone
- Insurance renewal completed
- Emergency fund milestone
- Net worth milestone
- Consistency milestone
- Social connection milestone
- Career growth milestone

Rules:

- Achievements should reward consistency, recovery, and sustainable behavior.
- Avoid achievements that encourage unsafe fasting, overtraining, excessive trading, or unhealthy restriction.

---

## 18. Acceptance Test Scenarios

The redesigned PLOS system should satisfy these scenarios:

- Daily check-in with complete data produces concise scores, risks, and next actions.
- Daily check-in with missing data asks only for high-impact missing fields.
- Weekly review detects patterns across sleep, BP, food, exercise, finance, and social behavior.
- Finance dashboard computes assets, liabilities, and net worth from manual snapshots.
- Insurance renewal reminders trigger before due dates.
- AI refuses medication-change advice and redirects to doctor supervision.
- AI refuses regulated financial advice and provides general insights only.
- Scoring remains capped between 0 and 1000.
- Phase 1 works without bank APIs, PF APIs, broker integrations, Google Fit, Apple Health, OCR, or voice logging.
- Target progression remains conservative even after strong streaks.
- Poor performance produces recovery suggestions instead of shame.

---

## 19. Roadmap

### Phase 2

- PostgreSQL migration
- OCI deployment
- Enhanced reporting
- Improved reminder preferences
- CSV import for finance and expenses
- Optional broker statement import
- Food database improvements
- Better trend charts

### Future Roadmap

- Google Fit integration
- Apple Health integration
- Smartwatch integration
- OCR food logging
- Voice logging
- AI meal planning
- AI exercise planning
- Advanced weight prediction engine
- Advanced BP trend engine
- Financial goal prediction
- Life Score forecasting
- AI health coach improvements
- AI financial coach improvements
- AI accountability agent
- Multi-agent architecture

---

## 20. Master Instruction For The AI Coach

You are the PLOS AI Coach. Your job is to help the user improve life outcomes through consistent tracking, practical accountability, and conservative behavior change.

Use the web app data as the source of truth. When data is missing, ask for the smallest useful amount of information. Keep daily coaching compact and action-oriented. Use weekly and monthly reviews for deeper analysis.

Always follow health and finance safety rules. Do not give medication-change advice, diagnosis, regulated financial advice, tax advice, legal advice, insurance advice, or specific trading recommendations. Provide observations, general education, reminders, and practical next actions.

Optimize for sustainable progress, not perfection.
