---
name: garmin-status
description: Generate a comprehensive health, performance, and goals status report from Garmin data.
---

## What I do
I analyze your local Garmin data and compile a human-readable, comprehensive status report. I look at your physiological health markers, running performance history, and future race goals to tell you exactly where you stand.

## Trigger
Use this skill when the user asks something like: 
*"Review my activity report, and my goals, and print my health status and running performance status"*

## Workflow

### Step 1: Read the Data
Read the latest generated Garmin report and configuration:
```bash
cat garmin-analyzer/data/garmin_report.md
cat .env
```
*(If the report does not exist, instruct the user to run `python garmin.py collect` first).*

### Step 2: Generate the Output
Use the data from the report and configuration to format a response using the exact structure below. Be encouraging but realistic based on the data.

#### Structure Template:

### 📊 Health & General Status
- **Age/Profile:** [Extract from Profile]
- **VO2 Max:** [Extract from Profile]
- **HR Zones:** [Extract from `.env` or report]
- **Sleep, HRV, Training Readiness:** [Extract from report. State if no data is available]

### 🏃 Running Performance Status (Last [X] Days)
- **Total Distance:** [Extract from report]
- **Total Time:** [Extract from report]
- **Averages:** [Extract runs/week and km/week]
- **Average Heart Rate:** [Extract from report]

**Recent Trends:** 
[Analyze the "Recent Runs" table. Comment on their pace vs HR correlation. Are they keeping easy runs easy? Are they doing long runs?]

### 🎯 Goals & Race Context
- **Goal Race:** [Extract from `.env` or report]
- **Race Date:** [Extract from `.env` or report]
- **Goal Time:** [Extract from `.env` or report]
- **Historical Race Weather:** [If available, extract from weather data]

**Current Race Predictions (Based on current fitness):**
- [List 5K, 10K, Half, Marathon predictions from the report]

### Summary
[Write a 1-2 paragraph synthesis. Compare their current race prediction to their goal time. Advise them on what they need to focus on (e.g., sticking to Zone 2, building volume, hitting interval paces) to bridge the gap between their current fitness and their goal.]