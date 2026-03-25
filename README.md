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
│
├── .env                       # API keys (never commit this to GitHub!)
├── .gitignore                 # Excludes .env and temp files
├── requirements.txt           # All Python dependencies
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
    Sends values to Gemini AI → returns structured JSON analysis
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
  "targets": ["Testosterone"],
  "direction": "Low",
  "dosage": "100-200mg every 1-2 weeks",
  "notes": "Standard HRT testosterone replacement",
  "within_hrt_scope": true
}
```

To add new medicines, simply add entries to `medicines.json` — no code changes needed.

---

## 🧪 Supported Blood Markers

| Category   | Markers                                          |
|------------|--------------------------------------------------|
| Hormones   | Testosterone, Estradiol, FSH, LH, DHEA, Progesterone, Cortisol |
| Thyroid    | TSH, Free T3, Free T4                            |
| Metabolic  | Glucose, HbA1c, Creatinine, Sodium, Potassium   |
| Liver      | ALT, AST                                         |
| Lipids     | Cholesterol, HDL, LDL, Triglycerides            |
| CBC        | Hemoglobin, Hematocrit, WBC, RBC, Platelets     |

---

## 🛠️ Tech Stack

| Tool                  | Purpose                        |
|-----------------------|--------------------------------|
| Python 3.10+          | Core language                  |
| pdfplumber            | PDF text extraction            |
| google-genai          | Gemini AI API                  |
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
