# Personal Finance Analysis 📊

A full-stack personal finance dashboard that parses UPI statements and visualizes your spending patterns.

**Live Demo:** [personal-finance-analysis-production-5f31.up.railway.app](https://personal-finance-analysis-production-5f31.up.railway.app/)

---

## Supported Statements
- ✅ Google Pay (GPay) PDF statements
- ✅ PhonePe PDF statements

---

## Features

- **Statement Upload** — Upload your GPay or PhonePe PDF statement directly
- **Spending Charts** — Daily debit and credit trends visualized as line charts
- **Top Payees** — Bar chart showing your most frequent transactions
- **Credit vs Debit Pie** — Category breakdown by Merchant and Person, switchable between credit and debit view
- **Net Flow Chart** — Select any person and see your financial relationship over time (credit vs debit net flow)
- **Smart Filters** — Filter by date range, category (Merchant/Person), and amount range
- **Biggest Transaction** — Instantly see your largest transaction at a glance
- **Inline Category Editing** — Reassign transaction categories directly in the table
- **Collapsible UI** — Filters and transaction table hidden by default for a clean dashboard experience

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask, Flask-SQLAlchemy |
| Database | SQLite |
| Frontend | HTML, CSS, Vanilla JS |
| Charts | Chart.js |
| Parsing | pandas |
| Deployment | Railway |

---

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/SID1014/Personal-Finance-Analysis.git
cd Personal-Finance-Analysis

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## How to Use

1. Download your **GPay or PhonePe** statement PDF from the app
2. Visit the Upload page and submit your statement
3. The dashboard will automatically parse and display your transactions
4. Use filters to analyze specific time periods, categories, or amounts
5. Select a person from the "Filter By Person" dropdown to see your net financial flow with them

> **Note:** Uploading a new statement replaces all existing data.

---

## Project Structure

```
Personal-Finance-Analysis/
├── main.py               # Flask routes and app config
├── models.py             # SQLAlchemy Transaction model
├── statement_parser.py   # PDF statement parser
├── Procfile              # Railway deployment config
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html        # Upload page
│   └── dashboard.html    # Main dashboard
└── static/
    ├── css/styles.css
    
```

---





## Author

**Siddhant Dakhore**  
[GitHub](https://github.com/SID1014) • [Portfolio](https://sid-info.netlify.app)