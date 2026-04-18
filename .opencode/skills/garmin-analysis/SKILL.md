---
name: garmin-analysis
description: Analyze Garmin workouts, show data tables, and generate a comprehensive coaching status report
---

## What I do
I combine raw data analysis (via the CLI) with an intelligent coaching summary to give the user a complete picture of their training status, progress towards their goals, and actionable advice on how to adjust their plan.

## Usage / Trigger
Use this skill when the user asks to analyze their data, review their activity report, or check their health/performance status.

## Workflow

### Step 1: Run Data Analysis (CLI)
Run the analysis command to see the raw workout tables, weather, and weekly volume:
```bash
python3 garmin.py analyze -d 30
```
*(Use `--json` if you need the output for strict programmatic parsing).*

### Step 2: Read Context Files
Read the latest generated Garmin report and configuration to understand the user's physiological status and goals:
```bash
cat garmin-analyzer/data/garmin_report.md
cat .env
```
*(If `garmin_report.md` does not exist, instruct the user to run `python garmin.py collect` first).*

### Step 3: Generate the Output
Use the data from the CLI output and context files to format a conversational coaching response using the exact structure below. Be encouraging but realistic.

#### Structure Template:

### 📊 Health & General Status
- **Age/Profile:** [Extract from Profile]
- **VO2 Max:** [Extract from Profile]
- **HR Zones:** [Extract from `.env` or report]
- **Sleep, HRV, Training Readiness:** [Extract from report. State if no data is available]

### 🏃 Running Performance Status (Last X Days)
- **Total Distance & Time:** [Extract from report]
- **Averages:** [Extract runs/week and km/week]
- **Recent Trends:** [Analyze the recent runs. Comment on pace vs HR correlation. Are they keeping easy runs easy? Are they doing long runs?]

### 🎯 Goals & Race Context
- **Goal Race:** [Extract from `.env` or report]
- **Goal Date & Time:** [Extract from `.env` or report]
- **Historical Race Weather:** [If available, extract from weather data]
- **Current Race Predictions:** [List predictions from the report based on current fitness]

### 💡 Summary & Plan Adjustments
[Write a 1-2 paragraph synthesis. Compare their current race prediction to their goal time. **Crucially: You MUST explicitly state what needs to change in the current training plan or execution in order to reach the goal. (e.g., "To bridge the gap to your goal, you need to increase your training days from 3 to 4, cap your easy run HR strictly at 155, and add a dedicated tempo session each week.")**]