import pandas as pd
from models import db,Transaction
import re
import csv
import sys
import os
from datetime import datetime
import spacy
import pdfplumber
from collections import defaultdict


nlp = spacy.load("en_core_web_sm")
def is_person(name): 
    clean_name = str(name).title() 
    if clean_name.isdigit():
        return "Recharge"
    doc = nlp(clean_name)
    
    for entity in doc.ents:
        if entity.label_ == "PERSON":  
            return "Person"
        
    return "Merchant"


def group_words_into_rows(words: list[dict], y_tolerance: int = 5) -> dict:
    
    buckets: dict[int, list] = defaultdict(list)
    for w in words:
        key = round(w["top"] / y_tolerance) * y_tolerance
        buckets[key].append(w)
    return {k: sorted(buckets[k], key=lambda w: w["x0"]) for k in sorted(buckets)}
 
 

 
def parse_amount(raw: str) -> str:
    """'₹1,240.36'  →  '1240.36'"""
    cleaned = raw.replace("₹", "").replace(",", "").strip()
    try:
        return f"{float(cleaned):.2f}"
    except ValueError:
        return cleaned
 
_GPAY_DATE_MAX    = 110   
_GPAY_DETAILS_MAX = 520   
 

_GPAY_DATE_RE = re.compile(r'^\d{2}\w{3},\d{4}$')
 

_GPAY_UPI_RE = re.compile(r'UPITransactionID[:\s]+(\d+)')

_GPAY_PAID_TO   = "Paidto"
_GPAY_RCVD_FROM = "Receivedfrom"
 
def _gpay_col(x0: float) -> str:
    if x0 < _GPAY_DATE_MAX:    return "date"
    if x0 < _GPAY_DETAILS_MAX: return "details"
    return "amount"
 
def _gpay_split_camel(name: str) -> str:
    
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)  
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)  
    return s.strip()
 
def _gpay_parse_date(raw: str) -> str:
    try:
        return datetime.strptime(raw, "%d%b,%Y").strftime("%Y-%m-%d")
    except ValueError:
        return raw
 
def parse_gpay(pdf_path: str) -> list[dict]:
    
    transactions = []
 
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=True)
            if not words:
                continue
 
            visual_rows = group_words_into_rows(words)
            row_list = list(visual_rows.values()) 
            i = 0
            while i < len(row_list):
                row = row_list[i]
 
                
                cols: dict[str, list] = defaultdict(list)
                for w in row:
                    cols[_gpay_col(w["x0"])].append(w["text"])
 
                date_text    = " ".join(cols["date"]).strip()
                details_text = " ".join(cols["details"]).strip()
                amount_text  = " ".join(cols["amount"]).strip()
 
              
                if not _GPAY_DATE_RE.match(date_text):
                    i += 1
                    continue
 
                if details_text.startswith(_GPAY_RCVD_FROM):
                    txn_type = "credit"
                    raw_name = details_text[len(_GPAY_RCVD_FROM):]
                elif details_text.startswith(_GPAY_PAID_TO):
                    txn_type = "debit"
                    raw_name = details_text[len(_GPAY_PAID_TO):]
                else:
                    txn_type = "unknown"
                    raw_name = details_text
 
                payee = _gpay_split_camel(raw_name)
                category = is_person(payee)
 
                
                time_str, ref_no = "", ""
 
                if i + 1 < len(row_list):
                    sub_cols: dict[str, list] = defaultdict(list)
                    for w in row_list[i + 1]:
                        sub_cols[_gpay_col(w["x0"])].append(w["text"])
                    sub_date    = " ".join(sub_cols["date"]).strip()
                    sub_details = " ".join(sub_cols["details"]).strip()
 
                   
                    if re.match(r"^\d{2}:\d{2}", sub_date):
                        time_str = sub_date
                        upi_m = _GPAY_UPI_RE.search(sub_details)
                        if upi_m:
                            ref_no = upi_m.group(1)
 
                transactions.append({
                    "date":   _gpay_parse_date(date_text),
                    "payee":  payee,
                    "type":   txn_type,
                    "amount": parse_amount(amount_text),
                    "category": category,
                })
                i += 1
    df = pd.DataFrame(transactions)
    return df           
                
    
 
 
  
_PP_DATE_MAX    = 110   # date column:    0  ≤ x < 110
_PP_DETAILS_MAX = 415   # details column: 110 ≤ x < 415
_PP_TYPE_MAX    = 500   # type column:    415 ≤ x < 500
#                         amount column:  x ≥ 500
 
# Matches the date token on a PhonePe transaction row
# Handles standard months ('Jan', 'Feb', …) and 'Sept'
_PP_DATE_RE = re.compile(
    r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}$'
)
 
# UTR number on the sub-row  e.g. 'UTR No. 494968570716'
_PP_UTR_RE = re.compile(r'^UTR No\.\s+(\S+)')
 
# Action prefixes to strip from payee names
_PP_PREFIX_RE = re.compile(
    r'^(?:Paid to|Payment to|Received from|Mobile recharged)\s*', re.IGNORECASE
)
 
# Lines that are definitely NOT a payee continuation
_PP_NON_PAYEE = re.compile(
    r'^(?:Transaction ID|UTR No\.|Paid by|Credited to|Page \d|This is)'
)
 
def _pp_col(x0: float) -> str:
    if x0 < _PP_DATE_MAX:    return "date"
    if x0 < _PP_DETAILS_MAX: return "details"
    if x0 < _PP_TYPE_MAX:    return "type"
    return "amount"
 
def _pp_parse_date(raw: str) -> str:
    """'Mar 12, 2026' or 'Sept 22, 2025'  →  '2026-03-12'"""
    raw = raw.replace("Sept ", "Sep ")
    for fmt in ("%b %d, %Y", "%b  %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return raw
 
def parse_phonepe(pdf_path: str) -> list[dict]:
    """
    Extract transactions from a PhonePe PDF using column bucketing.
 
    Column layout per visual row:
        date  │  details (payee / UTR / account)  │  type  │  amount
 
    A new transaction starts when the date column contains a valid
    PhonePe date string AND the type column contains DEBIT or CREDIT.
 
    Edge case — split payee:
        Row N:   date="Jan 21, 2026"  details="Paid to"  type="DEBIT"  amount="₹500"
        Row N+1: date="08:25 pm"      details="Indian Oil Petrol Pump - ..."
    If the details on the main row reduces to an empty string after
    stripping the prefix, the very next row's details (which starts
    at the same x as the details column) is used as the payee,
    provided it doesn't look like a Transaction ID / UTR line.
    """
    transactions = []
 
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=True)
            if not words:
                continue
 
            visual_rows = group_words_into_rows(words)
            row_list = list(visual_rows.values())
 
            i = 0
            while i < len(row_list):
                row = row_list[i]
 
                cols: dict[str, list] = defaultdict(list)
                for w in row:
                    cols[_pp_col(w["x0"])].append(w["text"])
 
                date_text    = " ".join(cols["date"]).strip()
                details_text = " ".join(cols["details"]).strip()
                type_text    = " ".join(cols["type"]).strip()
                amount_text  = " ".join(cols["amount"]).strip()
 
                # Is this a transaction row?
                if not _PP_DATE_RE.match(date_text):
                    i += 1
                    continue
                if type_text not in ("DEBIT", "CREDIT"):
                    i += 1
                    continue
 
                # ── parse payee ──
                payee = _PP_PREFIX_RE.sub("", details_text).strip()
 
                # ── handle split-payee edge case ──
                # If payee is blank after stripping the prefix, look at the
                # NEXT row's details column for the continuation.
                if payee == "" and i + 1 < len(row_list):
                    next_cols: dict[str, list] = defaultdict(list)
                    for w in row_list[i + 1]:
                        next_cols[_pp_col(w["x0"])].append(w["text"])
                    next_details = " ".join(next_cols["details"]).strip()
                    if next_details and not _PP_NON_PAYEE.match(next_details):
                        payee = next_details
                category = is_person(payee)
                # ── extract time from the time sub-row ──
                time_str, ref_no = "", ""
 
                # The time sub-row has a clock string in the date column
                # and the Transaction ID in the details column.
                # Scan up to 5 sub-rows ahead.
                for j in range(i + 1, min(i + 6, len(row_list))):
                    sub_cols: dict[str, list] = defaultdict(list)
                    for w in row_list[j]:
                        sub_cols[_pp_col(w["x0"])].append(w["text"])
                    sub_date    = " ".join(sub_cols["date"]).strip()
                    sub_details = " ".join(sub_cols["details"]).strip()
 
                    # Time line: date column holds 'HH:MM am/pm'
                    if re.match(r"^\d{2}:\d{2} (?:am|pm)$", sub_date) and not time_str:
                        time_str = sub_date
 
                    # UTR line
                    utr_m = _PP_UTR_RE.match(sub_details)
                    if utr_m:
                        ref_no = utr_m.group(1)
                        break  # UTR is the last useful sub-row
 
                transactions.append({
                    "date":   _pp_parse_date(date_text),
                    
                    "payee":  payee,
                    "type":   type_text.lower(),
                    "amount": parse_amount(amount_text),
                    "category":category
                    
                })
                i += 1
    df = pd.DataFrame(transactions)
 
    return df
 
 
  
def detect_format(pdf_name: str) -> str:
    pdf_path = os.path.join('uploads/',pdf_name)
    with pdfplumber.open(pdf_path) as pdf:
        first_line = pdf.pages[0].extract_text().split('\n')[0].strip()
 
    if first_line.startswith("Transaction Statement for"):
        return parse_phonepe(pdf_path)
    elif first_line.lower().startswith("transaction statement"):
        return parse_gpay(pdf_path)
    else:
        raise ValueError(
            f"Unrecognised PDF format.\n"
            f"  First line: {first_line!r}\n"
            f"  Expected:   'Transaction statement' (GPay)\n"
            f"              'Transaction Statement for ...' (PhonePe)"
        )
 
        
def parse_dataframe(filename):
    df = pd.read_csv(os.path.join('uploads/',filename) , skiprows= 8 )
    columns = ['Date', 'Remarks', 'Debit', 'Credit', 'Balance Amount']
    if not all(col in df.columns for col in columns):
        raise ValueError("The columns are not expected")
    df['Category'] = df['Remarks'].str.split('/').str[3]
    return df

def save_in_db(df):
    Transaction.query.delete()
    db.session.commit() 
    for _,row in df.iterrows():
        if not pd.isna(row['date']):
            entry = Transaction(
            date = pd.to_datetime(row['date'], format='%Y-%m-%d').date(),
            payee = row['payee'],
            type = row['type'],
            amount = row['amount'],
            category = row['category'])
            db.session.add(entry)
    db.session.commit()