# 🩺 HRT Blood Report AI System

An AI-powered blood report analysis tool built for HRT (Hormone Replacement Therapy) clinics.
Extracts lab values from PDF reports, analyzes them using Google Gemini AI, matches findings
to an internal medicine database, and checks doctor prescriptions — all inside a clean web dashboard.

> ⚠️ **Disclaimer:** This project is for educational and portfolio purposes only.
> It is NOT a medical device and must NOT be used for real clinical decisions.

---

## 📸 Features

- 📄 **PDF Extraction** — Reads blood report PDFs and pulls out lab values automatically
- 🧠 **AI Analysis** — Uses Google Gemini to flag High/Low values with plain-English explanations
- 💊 **Medicine Suggestions** — Recommends only from an internal product database (no external suggestions)
- 📋 **Prescription Checker** — Compares doctor's prescription against AI findings with a match score
- 📊 **Dashboard** — Full Streamlit web UI with charts, tabs, and progress tracking
- 🔒 **Scope Enforcement** — Automatically flags issues outside HRT scope as "Refer to Specialist"

---

## 🗂️ Project Structure

```
blood-report-ai/
│
├── app.py                     # Phase 5 — Streamlit web dashboard
├── pdf_extractor.py           # Phase 1 — PDF reading & value extraction
├── ai_analyzer.py             # Phase 2 — Google Gemini AI analysis
├── medicine_db.py             # Phase 3 — Internal medicine database logic
├── prescription_checker.py    # Phase 4 — Prescription vs AI comparison
│
├── medicines.json             # Internal medicine/product database
├── main.py                    # Terminal pipeline (runs all phases)
├── generate_sample_report.py  # Generates a fake blood report PDF for testing
├── tests/                     # pytest test suite
│
├── .env                       # API keys (never commit this to GitHub!)
├── .gitignore                 # Excludes .env and temp files
├── requirements.txt           # All Python dependencies
├── requirements-dev.txt       # Dependencies + pytest
└── README.md                  # This file
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/blood-report-ai.git
cd blood-report-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a free Gemini API key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key

### 4. Create your `.env` file

Create a file named `.env` in the project root:

```bash
GEMINI_API_KEY=AIzaSy_paste_your_key_here
```

> ⚠️ Never commit your `.env` file to GitHub. It is already listed in `.gitignore`.

### 5. Generate a sample blood report (optional)

```bash
python generate_sample_report.py
```

This creates `sample_blood_report.pdf` for testing.

### 6. Run the tests (optional)

```bash
pip install -r requirements-dev.txt
pytest
```

The tests never call the Gemini API, so no API key is needed.

---

## 🚀 Running the App

### Option A — Web Dashboard (recommended)

```bash
streamlit run app.py
```

Opens at `http://localhost:8501` in your browser.

### Option B — Terminal Pipeline

```bash
python main.py sample_blood_report.pdf
```

Prints full analysis directly in the terminal.

---

## 🔄 How It Works — Pipeline

```
PDF Upload
    │
    ▼
Phase 1: pdf_extractor.py
    Reads PDF text → finds lab values → calculates High/Low/Normal
    │
    ▼
Phase 2: ai_analyzer.py
    Sends values + patient age/sex to Gemini AI → JSON checked against a schema
    │
    ▼
Phase 3: medicine_db.py
    Matches flagged values → suggests from internal medicines.json only
    │
    ▼
Phase 4: prescription_checker.py
    Compares doctor's prescription → calculates match score
    │
    ▼
Phase 5: app.py (Streamlit)
    Displays everything in a web dashboard with charts
```

---

## 💊 Medicine Database

Medicines are stored in `medicines.json`. Each entry looks like:

```json
{
  "id": "MED001",
  "name": "Testosterone Cypionate",
  "type": "injection",
  "targets": {"Testosterone": "Low"},
  "dosage": "100-200mg every 1-2 weeks",
  "notes": "Standard HRT testosterone replacement",
  "within_hrt_scope": true
}
```

`targets` maps each blood marker to the result it treats (`"High"` or `"Low"`), so one
medicine can treat different directions for different markers — e.g. Levothyroxine is
`{"TSH": "High", "Free T3": "Low", "Free T4": "Low"}`. Marker names must match the names in
the table below (the test suite checks this).

To add new medicines, simply add entries to `medicines.json` — no code changes needed.

The prescription match score is per flagged issue: an issue counts as covered when the
doctor prescribed **any** of the options suggested for it.

---

## 🧪 Supported Blood Markers

| Category   | Markers                                          |
|------------|--------------------------------------------------|
| Hormones   | Testosterone, Free Testosterone, Estradiol, FSH, LH, DHEA (DHEA-S), Progesterone, Cortisol |
| Thyroid    | TSH, Free T3, Free T4                            |
| Metabolic  | Glucose, HbA1c, Creatinine, Sodium, Potassium   |
| Liver      | ALT, AST                                         |
| Lipids     | Cholesterol, HDL, LDL, Triglycerides            |
| CBC        | Hemoglobin, Hematocrit, WBC, RBC, Platelets     |
| Vitamins   | Vitamin D (25-OH)                               |

Common lab spellings are recognised too (e.g. "Hemoglobin A1c", "LDL Cholesterol", "SGOT",
"Estradiol (E2)").

**Reference ranges.** The report's own printed range is always used when there is one.
Otherwise a built-in adult range is used, adjusted for:

- **Sex** — read from the report ("Gender: Female", "Sex: M"), or set in the app's sidebar.
  Female ranges are used for testosterone, hemoglobin, hematocrit, RBC, creatinine, HDL and
  DHEA. Estradiol, progesterone, FSH and LH depend on the menstrual cycle, so for women they
  need the report's own range. If sex isn't found, the general (male) ranges are used and the
  app shows a warning.
- **Units** — common SI units are converted (e.g. glucose in mmol/L, testosterone in nmol/L,
  creatinine in µmol/L).

When there's no safe range (an unknown unit, Free Testosterone without a printed range, or a
cycle-dependent hormone for a woman) the test is shown with status **Unknown** (grey) and is
never flagged High or Low.

---

## 🛠️ Tech Stack

| Tool                  | Purpose                        |
|-----------------------|--------------------------------|
| Python 3.10+          | Core language                  |
| pdfplumber            | PDF text extraction            |
| google-genai          | Gemini AI API                  |
| pydantic              | Validates the AI's JSON reply  |
| Streamlit             | Web dashboard                  |
| Plotly                | Interactive charts             |
| Pandas                | Data handling                  |
| reportlab             | Sample PDF generation          |
| python-dotenv         | Environment variable management|

---

## 🔐 Environment Variables

| Variable         | Description                    | Required |
|------------------|--------------------------------|----------|
| `GEMINI_API_KEY` | Google AI Studio API key       | ✅ Yes   |
| `GROQ_API_KEY`   | Groq API key (optional backup) | ❌ No    |

---

## 📝 .gitignore

Make sure your `.gitignore` contains:

```
.env
__pycache__/
*.pyc
temp_*.pdf
*.egg-info/
.venv/
```

---

## 🧠 What I Learned Building This

- Extracting structured data from unstructured PDF text using `pdfplumber` and `regex`
- Prompt engineering — writing precise prompts to get structured JSON from an LLM
- Connecting multiple Python modules into a clean pipeline
- Building a full web app with `Streamlit` without any HTML/CSS knowledge
- Handling free AI API rate limits and model deprecation
- Designing a scoped medical AI system with referral logic

---

## 📈 Future Improvements

- [ ] Patient history tracking — compare old vs new blood reports over time
- [ ] Progress charts — show improvement/decline after treatment
- [ ] PDF report export — download the full analysis as a PDF
- [ ] Multi-patient support — manage multiple patient records
- [ ] Authentication — login system for clinic staff
- [ ] Better PDF parsing — handle more blood report formats

---

## 👤 Author

Built as a learning project to understand AI integration, PDF processing, and full-stack Python development.

---

## 📄 License

MIT License — free to use and modify for educational purposes.
