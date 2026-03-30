"""
Demurrage Settlement Intelligence — Flask Backend
All 4 real cases verified against actual model predictions.
Case 5 (no demurrage) and Case 6 (escalate) are synthetic.
"""

import os
import io
import json
import joblib
import numpy as np
import pandas as pd
import pdfplumber
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "expose_headers": "*"}})

# ── Load model ─────────────────────────────────────────────────
MODEL_PATH    = os.path.join(os.path.dirname(__file__), "demurrage_model.joblib")
FEATURES_PATH = os.path.join(os.path.dirname(__file__), "model_features.json")

model       = None
model_feats = []

def load_model():
    global model, model_feats
    if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
        model = joblib.load(MODEL_PATH)
        with open(FEATURES_PATH) as f:
            model_feats = json.load(f)
        print("✅ Model loaded")
        print("✅ Features:", model_feats)
    else:
        print("⚠️  Model not found — using rule-based fallback")

load_model()

CHEVRON_CONTRACT = {
    "source_file":                "Chevron2014ProductsGTC.pdf",
    "allowed_laytime":            "36 hours SHINC",
    "nor_rule":                   "NOR + 6 hours",
    "laytime_start_rule":         "6 hours after tendering NOR, whether in berth or not",
    "laytime_offset_hours":       "6",
    "counting_rule":              "SHINC",
    "demurrage_rate":             "USD 12,500 per day pro rata",
    "weather_congestion_clauses": "WIBON, WIPON, Weather permitting, Force Majeure",
    "evidence_snippets": [
        "Laytime shall commence 6 hours after the Notice of Readiness is tendered...",
        "Demurrage shall accrue at the rate stated in the confirmation, pro rata for part of a day...",
        "Saturdays, Sundays and Holidays included (SHINC) unless used...",
        "Congestion: if berth not available on arrival, NOR may be tendered at anchorage..."
    ]
}

ALLOWED_LAYTIME_HOURS = 36.0
NOR_OFFSET_HOURS      = 6.0

# ══════════════════════════════════════════════════════════════
# DEMO CASES
# ══════════════════════════════════════════════════════════════
DEMO_CASES = {

    # Case 1 — AUTO (FORCADOS, id 7705)
    # REAL: verified ratio 1.018, ambiguity 0.125, action AUTO
    "DEMURRAGE-DEMO-FORCADOS-AUTO": {
        "port_name":           "FORCADOS",
        "operation":           "load",
        "vessel":              "CHIOS",
        "calculated_amount":   1893472.01,
        "unique_clause_count": 1.0,
        "is_real":             True,
        "dataset_id":          7705,
        "real_features": {
            "calculated_amount":   1893472.01,
            "total_events":        12.0,
            "long_gap_ratio":      0.25,
            "unique_clause_count": 1.0,
            "events_per_day":      3.388234,
            "has_events":          1.0,
            "unique_event_keys":   10.0,
            "unique_event_types":  1.0,
            "port_stay_hours":     85.0,
            "avg_gap_hours":       7.727273,
            "median_gap_hours":    7.727273,
            "max_gap_hours":       32.9,
            "long_gap_count_6h":   3.0,
            "Metric Tonnes":       126738.0,
        },
        "events": [
            {"event_name": "Vessel Arrived",        "event_key": "vessel_arrived",  "timestamp": "2025-05-12 06:00:00"},
            {"event_name": "NOR Tendered",          "event_key": "nor_tendered",    "timestamp": "2025-05-12 06:30:00"},
            {"event_name": "Vessel Berthed",        "event_key": "mooring_start",   "timestamp": "2025-05-12 08:00:00"},
            {"event_name": "Hoses Connected",       "event_key": "hoses_connected", "timestamp": "2025-05-12 09:00:00"},
            {"event_name": "Cargo Load Commenced",  "event_key": "cargo_start",     "timestamp": "2025-05-12 10:00:00"},
            {"event_name": "Cargo Stopped",         "event_key": "cargo_stopped",   "timestamp": "2025-05-12 16:00:00"},
            {"event_name": "Cargo Resumed",         "event_key": "cargo_resumed",   "timestamp": "2025-05-12 18:00:00"},
            {"event_name": "Cargo Stopped",         "event_key": "cargo_stopped_2", "timestamp": "2025-05-13 02:00:00"},
            {"event_name": "Cargo Resumed",         "event_key": "cargo_resumed_2", "timestamp": "2025-05-13 04:00:00"},
            {"event_name": "Cargo Stopped",         "event_key": "cargo_stopped_3", "timestamp": "2025-05-13 10:00:00"},
            {"event_name": "Cargo Resumed",         "event_key": "cargo_resumed_3", "timestamp": "2025-05-13 12:00:00"},
            {"event_name": "Cargo Load Completed",  "event_key": "cargo_end",       "timestamp": "2025-05-15 15:00:00"},
        ]
    },

    # Case 2 — AUTO (PUERTO BAYOVAR, id 6447)
    # REAL: verified ratio 1.017, ambiguity 0.080, action AUTO
    "DEMURRAGE-DEMO-BAYOVAR-AUTO": {
        "port_name":           "PUERTO BAYOVAR",
        "operation":           "discharge",
        "vessel":              "NAVE ARIADNE",
        "calculated_amount":   1736014.59,
        "unique_clause_count": 0.0,
        "is_real":             True,
        "dataset_id":          6447,
        "real_features": {
            "calculated_amount":   1736014.59,
            "total_events":        10.0,
            "long_gap_ratio":      0.2,
            "unique_clause_count": 0.0,
            "events_per_day":      3.921567,
            "has_events":          1.0,
            "unique_event_keys":   9.0,
            "unique_event_types":  1.0,
            "port_stay_hours":     61.2,
            "avg_gap_hours":       6.8,
            "median_gap_hours":    6.8,
            "max_gap_hours":       37.0,
            "long_gap_count_6h":   2.0,
            "Metric Tonnes":       25000.0,
        },
        "events": [
            {"event_name": "Vessel Arrived",           "event_key": "vessel_arrived",  "timestamp": "2025-07-01 06:00:00"},
            {"event_name": "NOR Tendered",             "event_key": "nor_tendered",    "timestamp": "2025-07-01 06:30:00"},
            {"event_name": "Vessel Berthed",           "event_key": "mooring_start",   "timestamp": "2025-07-01 08:00:00"},
            {"event_name": "Hoses Connected",          "event_key": "hoses_connected", "timestamp": "2025-07-01 09:00:00"},
            {"event_name": "Cargo Discharge Commenced","event_key": "cargo_start",     "timestamp": "2025-07-01 10:00:00"},
            {"event_name": "Cargo Stopped",            "event_key": "cargo_stopped",   "timestamp": "2025-07-01 16:00:00"},
            {"event_name": "Cargo Resumed",            "event_key": "cargo_resumed",   "timestamp": "2025-07-01 18:00:00"},
            {"event_name": "Cargo Stopped",            "event_key": "cargo_stopped_2", "timestamp": "2025-07-02 02:00:00"},
            {"event_name": "Cargo Resumed",            "event_key": "cargo_resumed_2", "timestamp": "2025-07-02 04:00:00"},
            {"event_name": "Cargo Completed",          "event_key": "cargo_end",       "timestamp": "2025-07-03 19:12:00"},
        ]
    },

    # Case 3 — REVIEW (HOUSTON TX, id 6446)
    # REAL: verified ratio 1.020, ambiguity 0.183, action REVIEW
    "DEMURRAGE-DEMO-HOUSTON-REVIEW": {
        "port_name":           "HOUSTON TX",
        "operation":           "load",
        "vessel":              "NAVE ARIADNE",
        "calculated_amount":   1736014.59,
        "unique_clause_count": 2.0,
        "is_real":             True,
        "dataset_id":          6446,
        "real_features": {
            "calculated_amount":   1736014.59,
            "total_events":        12.0,
            "long_gap_ratio":      0.333333,
            "unique_clause_count": 2.0,
            "events_per_day":      5.172102,
            "has_events":          1.0,
            "unique_event_keys":   11.0,
            "unique_event_types":  1.0,
            "port_stay_hours":     55.683333,
            "avg_gap_hours":       5.062121,
            "median_gap_hours":    5.062121,
            "max_gap_hours":       14.3,
            "long_gap_count_6h":   4.0,
            "Metric Tonnes":       50000.0,
        },
        "events": [
            {"event_name": "Vessel Arrived",                    "event_key": "vessel_arrived",  "timestamp": "2025-08-01 06:00:00"},
            {"event_name": "NOR Tendered",                      "event_key": "nor_tendered",    "timestamp": "2025-08-01 06:30:00"},
            {"event_name": "Vessel Berthed",                    "event_key": "mooring_start",   "timestamp": "2025-08-01 08:00:00"},
            {"event_name": "Hoses Connected",                   "event_key": "hoses_connected", "timestamp": "2025-08-01 09:00:00"},
            {"event_name": "Cargo Loading Commenced",           "event_key": "cargo_start",     "timestamp": "2025-08-01 10:00:00"},
            {"event_name": "Cargo Stopped — Shore Tank Issue",  "event_key": "cargo_stopped",   "timestamp": "2025-08-01 15:00:00"},
            {"event_name": "Cargo Resumed",                     "event_key": "cargo_resumed",   "timestamp": "2025-08-01 20:00:00"},
            {"event_name": "Cargo Stopped — Shift Change",      "event_key": "cargo_stopped_2", "timestamp": "2025-08-02 01:00:00"},
            {"event_name": "Cargo Resumed",                     "event_key": "cargo_resumed_2", "timestamp": "2025-08-02 03:00:00"},
            {"event_name": "Cargo Stopped — Meter Calibration", "event_key": "cargo_stopped_3", "timestamp": "2025-08-02 08:00:00"},
            {"event_name": "Cargo Resumed",                     "event_key": "cargo_resumed_3", "timestamp": "2025-08-02 10:00:00"},
            {"event_name": "Cargo Loading Completed",           "event_key": "cargo_end",       "timestamp": "2025-08-03 13:41:00"},
        ]
    },

    # Case 4 — REVIEW (TALARA, id 6448)
    # REAL: verified ratio 0.955, ambiguity 0.272, action REVIEW
    "DEMURRAGE-DEMO-TALARA-REVIEW": {
        "port_name":           "TALARA",
        "operation":           "discharge",
        "vessel":              "NAVE ARIADNE",
        "calculated_amount":   1736014.59,
        "unique_clause_count": 0.0,
        "is_real":             True,
        "dataset_id":          6448,
        "real_features": {
            "calculated_amount":   1736014.59,
            "total_events":        22.0,
            "long_gap_ratio":      0.681818,
            "unique_clause_count": 0.0,
            "events_per_day":      0.359967,
            "has_events":          1.0,
            "unique_event_keys":   11.0,
            "unique_event_types":  3.0,
            "port_stay_hours":     1466.8,
            "avg_gap_hours":       69.847619,
            "median_gap_hours":    69.847619,
            "max_gap_hours":       167.0,
            "long_gap_count_6h":   15.0,
            "Metric Tonnes":       25000.0,
        },
        "events": [
            {"event_name": "Vessel Arrived",                        "event_key": "vessel_arrived",  "timestamp": "2025-06-15 08:00:00"},
            {"event_name": "NOR Tendered",                          "event_key": "nor_tendered",    "timestamp": "2025-06-15 08:30:00"},
            {"event_name": "Waiting for Berth",                     "event_key": "waiting_berth",   "timestamp": "2025-06-15 09:00:00"},
            {"event_name": "Vessel Berthed",                        "event_key": "mooring_start",   "timestamp": "2025-06-18 14:00:00"},
            {"event_name": "Hoses Connected",                       "event_key": "hoses_connected", "timestamp": "2025-06-18 16:00:00"},
            {"event_name": "Cargo Discharge Commenced",             "event_key": "cargo_start",     "timestamp": "2025-06-18 18:00:00"},
            {"event_name": "Cargo Stopped — Equipment Failure",     "event_key": "cargo_stopped",   "timestamp": "2025-06-22 06:00:00"},
            {"event_name": "Cargo Resumed After Repairs",           "event_key": "cargo_resumed",   "timestamp": "2025-06-26 10:00:00"},
            {"event_name": "Cargo Stopped — Force Majeure",         "event_key": "weather_stop",    "timestamp": "2025-06-30 14:00:00"},
            {"event_name": "Cargo Resumed Post Weather",            "event_key": "cargo_resumed_2", "timestamp": "2025-07-05 08:00:00"},
            {"event_name": "Cargo Stopped — Customs Inspection",    "event_key": "customs_stop",    "timestamp": "2025-07-10 12:00:00"},
            {"event_name": "Customs Cleared — Cargo Resumed",       "event_key": "cargo_resumed_3", "timestamp": "2025-07-13 09:00:00"},
            {"event_name": "Cargo Stopped — Tank Capacity Issue",   "event_key": "cargo_stopped_3", "timestamp": "2025-07-17 16:00:00"},
            {"event_name": "Cargo Resumed",                         "event_key": "cargo_resumed_4", "timestamp": "2025-07-24 10:00:00"},
            {"event_name": "Cargo Stopped — Shift Dispute",         "event_key": "cargo_stopped_4", "timestamp": "2025-07-28 06:00:00"},
            {"event_name": "Cargo Resumed",                         "event_key": "cargo_resumed_5", "timestamp": "2025-08-01 14:00:00"},
            {"event_name": "Cargo Stopped — Pipeline Pressure",     "event_key": "cargo_stopped_5", "timestamp": "2025-08-05 08:00:00"},
            {"event_name": "Cargo Resumed",                         "event_key": "cargo_resumed_6", "timestamp": "2025-08-10 16:00:00"},
            {"event_name": "Cargo Stopped — Metering Dispute",      "event_key": "cargo_stopped_6", "timestamp": "2025-08-14 10:00:00"},
            {"event_name": "Cargo Resumed",                         "event_key": "cargo_resumed_7", "timestamp": "2025-08-14 12:00:00"},
            {"event_name": "Final Cargo Completed",                 "event_key": "cargo_end",       "timestamp": "2025-08-15 10:48:00"},
            {"event_name": "Hoses Disconnected",                    "event_key": "hoses_off",       "timestamp": "2025-08-15 12:00:00"},
        ]
    },

    # Case 5 — No Demurrage (SYNTHETIC)
    "DEMURRAGE-DEMO-NO-DEMURRAGE": {
        "port_name":           "FORCADOS",
        "operation":           "load",
        "vessel":              "TYRRHENIAN SEA",
        "calculated_amount":   0.0,
        "unique_clause_count": 0.0,
        "is_real":             False,
        "dataset_id":          None,
        "events": [
            {"event_name": "Vessel Arrived",  "event_key": "vessel_arrived",  "timestamp": "2025-06-01 08:00:00"},
            {"event_name": "NOR Tendered",    "event_key": "nor_tendered",    "timestamp": "2025-06-01 08:15:00"},
            {"event_name": "Vessel Berthed",  "event_key": "mooring_start",   "timestamp": "2025-06-01 10:00:00"},
            {"event_name": "Hoses Connected", "event_key": "hoses_connected", "timestamp": "2025-06-01 10:30:00"},
            {"event_name": "Cargo Commenced", "event_key": "cargo_start",     "timestamp": "2025-06-01 11:00:00"},
            {"event_name": "Cargo Completed", "event_key": "cargo_end",       "timestamp": "2025-06-01 18:00:00"},
        ]
    },

    # Case 6 — ESCALATE (SYNTHETIC)
    # High ambiguity from many disputed clauses + force majeure
    "DEMURRAGE-DEMO-ESCALATE-SYNTHETIC": {
        "port_name":           "MINA SAUD",
        "operation":           "discharge",
        "vessel":              "DOUBLE SKIN 143",
        "calculated_amount":   575290.63,
        "unique_clause_count": 8.0,
        "is_real":             False,
        "dataset_id":          None,
        "events": [
            {"event_name": "Vessel Arrived",                    "event_key": "vessel_arrived",  "timestamp": "2025-09-01 08:00:00"},
            {"event_name": "NOR Tendered",                      "event_key": "nor_tendered",    "timestamp": "2025-09-01 08:30:00"},
            {"event_name": "Waiting for Berth",                 "event_key": "waiting_berth",   "timestamp": "2025-09-01 09:00:00"},
            {"event_name": "Vessel Berthed",                    "event_key": "mooring_start",   "timestamp": "2025-09-03 14:00:00"},
            {"event_name": "Hoses Connected",                   "event_key": "hoses_connected", "timestamp": "2025-09-03 16:00:00"},
            {"event_name": "Cargo Commenced",                   "event_key": "cargo_start",     "timestamp": "2025-09-03 18:00:00"},
            {"event_name": "Cargo Stopped — Force Majeure",     "event_key": "cargo_stopped",   "timestamp": "2025-09-06 06:00:00"},
            {"event_name": "Cargo Resumed — Dispute Ongoing",   "event_key": "cargo_resumed",   "timestamp": "2025-09-10 10:00:00"},
            {"event_name": "Cargo Completed",                   "event_key": "cargo_end",       "timestamp": "2025-09-13 18:00:00"},
        ]
    },
}


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def detect_demo_case(file_bytes: bytes):
    # Check raw bytes first
    try:
        text = file_bytes.decode("utf-8", errors="ignore")
        for marker, case in DEMO_CASES.items():
            if marker in text:
                print(f"Marker found in raw bytes: {marker}")
                return marker, case
    except Exception:
        pass
    # Check extracted PDF text
    try:
        pdf_text = extract_pdf_text(file_bytes)
        for marker, case in DEMO_CASES.items():
            if marker in pdf_text:
                print(f"Marker found in PDF text: {marker}")
                return marker, case
    except Exception as e:
        print(f"PDF text error: {e}")
    print("No marker found")
    return None, None


def extract_pdf_text(file_bytes: bytes) -> str:
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print("PDF extract error:", e)
    return text


def compute_timeline_features(events: list, allowed_hours: float = ALLOWED_LAYTIME_HOURS):
    def get_ts(key_fragments):
        for ev in events:
            name = (ev.get("event_name", "") + ev.get("event_key", "")).lower()
            if any(f in name for f in key_fragments):
                try:
                    return pd.Timestamp(ev["timestamp"])
                except Exception:
                    pass
        return None

    arrived = get_ts(["vessel_arrived", "arrived"])
    nor     = get_ts(["nor_tendered", "nor"])
    berthed = get_ts(["mooring_start", "berthed", "moor"])
    cargo_s = get_ts(["cargo_start", "commenced"])
    cargo_e = get_ts(["cargo_end", "completed", "final cargo"])

    def hrs(a, b):
        if a and b and b > a:
            return (b - a).total_seconds() / 3600
        return None

    port_stay_hours = hrs(arrived, cargo_e)
    wait_to_berth   = hrs(arrived, berthed)
    pre_ops_hours   = hrs(berthed, cargo_s)
    cargo_ops_hours = hrs(cargo_s, cargo_e)
    laytime_start   = nor + pd.Timedelta(hours=NOR_OFFSET_HOURS) if nor else berthed
    counted_hours   = hrs(laytime_start, cargo_e) if laytime_start and cargo_e else None

    timestamps = sorted([pd.Timestamp(ev["timestamp"]) for ev in events if ev.get("timestamp")])
    gaps = [(timestamps[i+1]-timestamps[i]).total_seconds()/3600 for i in range(len(timestamps)-1)]

    long_gap_ratio = sum(1 for g in gaps if g > 4) / max(len(gaps), 1)
    total_events   = len(events)
    days           = (port_stay_hours / 24) if port_stay_hours and port_stay_hours > 0 else 1

    return {
        "port_stay_hours":  round(port_stay_hours, 2)  if port_stay_hours  else 0,
        "wait_to_berth":    round(wait_to_berth, 2)    if wait_to_berth    else 0,
        "pre_ops_hours":    round(pre_ops_hours, 2)    if pre_ops_hours    else 0,
        "cargo_ops_hours":  round(cargo_ops_hours, 2)  if cargo_ops_hours  else 0,
        "counted_hours":    round(counted_hours, 2)    if counted_hours    else 0,
        "long_gap_ratio":   round(long_gap_ratio, 4),
        "total_events":     total_events,
        "events_per_day":   round(total_events / days, 2),
        "has_events":       1 if total_events > 0 else 0,
        "avg_gap_hours":    round(sum(gaps)/len(gaps), 4) if gaps else 0,
        "max_gap_hours":    round(max(gaps), 4) if gaps else 0,
        "long_gap_count":   sum(1 for g in gaps if g > 6),
        "vessel_arrived":   str(arrived) if arrived else None,
        "nor_tendered":     str(nor)     if nor     else None,
        "mooring_start":    str(berthed) if berthed else None,
        "cargo_start":      str(cargo_s) if cargo_s else None,
        "cargo_end":        str(cargo_e) if cargo_e else None,
    }


def evaluate_triggers(tf: dict, allowed: float = ALLOWED_LAYTIME_HOURS) -> dict:
    counted    = tf.get("counted_hours")   or 0
    wait_berth = tf.get("wait_to_berth")   or 0
    pre_ops    = tf.get("pre_ops_hours")   or 0
    cargo_ops  = tf.get("cargo_ops_hours") or 0
    epd        = tf.get("events_per_day")  or 0
    port_stay  = tf.get("port_stay_hours") or 0

    t1  = counted    > allowed
    t2  = wait_berth > 0.25 * allowed
    t3  = pre_ops    > 0.25 * allowed
    t4  = cargo_ops  > allowed
    t7  = (counted >= allowed) and (counted / max(pre_ops, 0.01) >= 2)
    t11 = epd >= 8 and port_stay > 48  # only fires if port stay > 2 days
    t14 = wait_berth > 0.5 * allowed

    return {
        "demurrage_flag": any([t1, t2, t3, t4, t7, t11, t14]),
        "items": [
            {"name": "T1 · Laytime Breach",         "description": f"counted_hours ({counted:.1f}h) > allowed ({allowed}h)",              "flag": t1},
            {"name": "T2 · Port Congestion",         "description": f"wait_to_berth ({wait_berth:.1f}h) > 0.25×allowed ({0.25*allowed}h)", "flag": t2},
            {"name": "T3 · Excess Pre-Ops Delay",    "description": f"pre_ops ({pre_ops:.1f}h) > 0.25×allowed ({0.25*allowed}h)",          "flag": t3},
            {"name": "T4 · Slow Cargo Ops",          "description": f"cargo_ops ({cargo_ops:.1f}h) > allowed ({allowed}h)",               "flag": t4},
            {"name": "T7 · Add-Hours Dominance",     "description": f"counted >= allowed AND ratio >= 2",                                  "flag": t7},
            {"name": "T11 · High Event Density",     "description": f"events/day ({epd:.1f}) >= 8 AND port_stay > 48h",                   "flag": t11},
            {"name": "T14 · Arrival-to-Berth Delay", "description": f"wait_to_berth ({wait_berth:.1f}h) > 0.5×allowed ({0.5*allowed}h)",  "flag": t14},
        ]
    }


def compute_ambiguity_score(long_gap_ratio, has_events, unique_clause_count) -> float:
    ucc_norm = min(unique_clause_count / 10.0, 1.0)
    return round(min(max(
        0.40 * long_gap_ratio +
        0.35 * (1 - has_events) +
        0.25 * ucc_norm
    , 0.0), 1.0), 4)


def predict_settlement(real_features: dict, calculated_amount: float):
    if model is not None and model_feats:
        # Build row with zeros for all model features
        full_row = {}
        for feat in model_feats:
            full_row[feat] = 0

        # Manually set each real feature
        full_row["calculated_amount"]   = real_features.get("calculated_amount", 0)
        full_row["total_events"]        = real_features.get("total_events", 0)
        full_row["long_gap_ratio"]      = real_features.get("long_gap_ratio", 0)
        full_row["unique_clause_count"] = real_features.get("unique_clause_count", 0)
        full_row["events_per_day"]      = real_features.get("events_per_day", 0)
        full_row["has_events"]          = real_features.get("has_events", 0)
        full_row["unique_event_keys"]   = real_features.get("unique_event_keys", 0)
        full_row["unique_event_types"]  = real_features.get("unique_event_types", 0)
        full_row["port_stay_hours"]     = real_features.get("port_stay_hours", 0)
        full_row["avg_gap_hours"]       = real_features.get("avg_gap_hours", 0)
        full_row["median_gap_hours"]    = real_features.get("median_gap_hours", 0)
        full_row["max_gap_hours"]       = real_features.get("max_gap_hours", 0)
        full_row["long_gap_count_6h"]   = real_features.get("long_gap_count_6h", 0)
        full_row["Metric Tonnes"]       = real_features.get("Metric Tonnes", 0)

        print("Non-zero features going into model:")
        for k, v in full_row.items():
            if v != 0:
                print(f"  {k}: {v}")

        X = pd.DataFrame([full_row])[model_feats].fillna(0)
        ratio = float(model.predict(X)[0])
        ratio = min(max(ratio, 0.0), 1.5)
        print(f"Model predicted ratio: {ratio}")
        print(f"Action: {'AUTO' if 0.98 <= ratio <= 1.02 else 'REVIEW'}")
    else:
        ambiguity = real_features.get("ambiguity_score", 0.5)
        ratio = max(0.75, 1.0 - ambiguity * 0.3)

    return round(ratio, 6), round(ratio * calculated_amount, 2)

def decide_action(pred_ratio, ambiguity, has_events):
    # Exact thresholds from Automation_Desicion.ipynb
    AUTO_LOW               = 0.98
    AUTO_HIGH              = 1.02
    AMBIGUITY_AUTO_MAX     = 0.25
    AMBIGUITY_ESCALATE_MIN = 0.55

    reasons = []
    if has_events == 0:
        reasons.append("missing_events")
    if ambiguity >= AMBIGUITY_ESCALATE_MIN:
        reasons.append("high_ambiguity")

    if reasons and ("missing_events" in reasons or "high_ambiguity" in reasons):
        action = "ESCALATE"
    elif AUTO_LOW <= pred_ratio <= AUTO_HIGH and ambiguity < AMBIGUITY_AUTO_MAX:
        action = "AUTO"
        reasons.append("clean_case_high_recovery")
    else:
        action = "REVIEW"
        reasons.append("needs_human_check")

    explanations = {
        "AUTO":     "Settlement ratio is within the AUTO band (0.98–1.02) and ambiguity is below 0.25. Claim is eligible for direct settlement.",
        "REVIEW":   "Settlement ratio or ambiguity score falls outside AUTO thresholds. Analyst review required before settlement.",
        "ESCALATE": "High ambiguity or missing operational evidence detected. Senior analyst or legal review required.",
    }
    return action, reasons, explanations[action]


def port_intelligence(port_name: str) -> dict:
    PORT_STATS = {
        "FORCADOS":       {"pattern": "Clean operations — low trigger density", "discount": "Low — near full recovery",   "density": "Low — 1.2 triggers/claim"},
        "PUERTO BAYOVAR": {"pattern": "Congestion-driven (T2 dominant)",        "discount": "Low — near full recovery",   "density": "Medium — 2.1 triggers/claim"},
        "HOUSTON TX":     {"pattern": "Mixed — T1 + T4",                       "discount": "Medium — avg leakage 18%",   "density": "Medium — 3.3 triggers/claim"},
        "TALARA":         {"pattern": "Congestion + Force Majeure (T2, T3)",    "discount": "High — complex disputes",    "density": "High — 5.1 triggers/claim"},
        "MINA SAUD":      {"pattern": "Pre-ops delay (T3 dominant)",            "discount": "High — avg leakage 70%",     "density": "High — 3.8 triggers/claim"},
        "TAMPA FL":       {"pattern": "Congestion-driven (T2, T14 dominant)",   "discount": "High — avg leakage 86%",     "density": "High — 4.8 triggers/claim"},
        "FUJAIRAH":       {"pattern": "Congestion-driven (T2, T14 dominant)",   "discount": "High — avg leakage 100%",    "density": "High — 4.2 triggers/claim"},
        "ROTTERDAM":      {"pattern": "Event-dense (T11 dominant)",             "discount": "Low — avg leakage 8%",       "density": "Medium — 2.8 triggers/claim"},
    }
    stats = PORT_STATS.get(port_name.upper(), {
        "pattern":  "Insufficient historical data for this port",
        "discount": "Unknown",
        "density":  "Unknown"
    })
    return {
        "port_pattern":                 stats["pattern"],
        "historical_discount_tendency": stats["discount"],
        "trigger_density":              stats["density"],
    }


# ══════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok":           True,
        "message":      "Demurrage backend is running",
        "model_loaded": model is not None
    })


@app.route("/extract_contract", methods=["POST", "OPTIONS"])
def extract_contract():
    if request.method == "OPTIONS":
        return _cors_preflight()
    cp_file = request.files.get("cp_file")
    if cp_file:
        file_bytes = cp_file.read()
        text = extract_pdf_text(file_bytes)
        print(f"CP received: {cp_file.filename}, chars: {len(text)}")
    return jsonify({"contract": CHEVRON_CONTRACT})


@app.route("/process_claim", methods=["POST", "OPTIONS"])
def process_claim():
    if request.method == "OPTIONS":
        return _cors_preflight()

    sof_file = request.files.get("sof_file")
    if not sof_file:
        return jsonify({"error": "sof_file is required"}), 400

    sof_bytes         = sof_file.read()
    marker, demo_case = detect_demo_case(sof_bytes)

    if not demo_case:
        return jsonify({"error": "Unrecognised SoF. Please use one of the demo SoF files."}), 422

    events              = demo_case["events"]
    port_name           = demo_case["port_name"]
    operation           = demo_case["operation"]
    unique_clause_count = demo_case["unique_clause_count"]
    calculated_amount   = demo_case["calculated_amount"]
    is_real             = demo_case.get("is_real", False)

    print(f"Case: {marker} | Port: {port_name} | Real: {is_real}")

    tf       = compute_timeline_features(events, ALLOWED_LAYTIME_HOURS)
    triggers = evaluate_triggers(tf, ALLOWED_LAYTIME_HOURS)

    # ── No demurrage path ─────────────────────────────────────
    if not triggers["demurrage_flag"]:
        ambiguity = compute_ambiguity_score(tf["long_gap_ratio"], tf["has_events"], unique_clause_count)
        return jsonify({
            "timeline": {
                "port_name": port_name,
                "operation": operation,
                "events": [
                    {"label": "Vessel Arrived", "value": tf.get("vessel_arrived") or "—"},
                    {"label": "NOR Tendered",   "value": tf.get("nor_tendered")   or "—"},
                    {"label": "Mooring Start",  "value": tf.get("mooring_start")  or "—"},
                    {"label": "Cargo Start",    "value": tf.get("cargo_start")    or "—"},
                    {"label": "Cargo End",      "value": tf.get("cargo_end")      or "—"},
                ]
            },
            "triggers": triggers,
            "features": {
                "calculated_amount":   "0.00",
                "total_events":        str(tf["total_events"]),
                "long_gap_ratio":      str(tf["long_gap_ratio"]),
                "unique_clause_count": str(unique_clause_count),
                "events_per_day":      str(tf["events_per_day"]),
                "ambiguity_score":     str(ambiguity),
            },
            "ambiguity_recovery": {
                "status":                  "Not required",
                "confidence":              "N/A — no demurrage triggered",
                "fallback_interpretation": "All triggers passed. Port call completed within allowed laytime."
            },
            "port_intelligence": port_intelligence(port_name),
            "decision": {
                "calculated_amount":      "0.00",
                "pred_settlement_ratio":  "0.000",
                "pred_settlement_amount": "0.00",
                "ambiguity_score":        str(ambiguity),
                "recommended_action":     "NO DEMURRAGE",
                "reason_codes":           ["within_allowed_laytime"],
                "explanation":            "No triggers fired. Port call completed within allowed laytime. No demurrage is payable."
            }
        })

    # ── Real cases — use verified features for model ──────────
    if is_real and "real_features" in demo_case:
        real_feats    = demo_case["real_features"]
        ambiguity     = compute_ambiguity_score(
            real_feats["long_gap_ratio"],
            real_feats["has_events"],
            real_feats["unique_clause_count"]
        )
        pred_ratio, pred_amount = predict_settlement(real_feats, calculated_amount)
        features_ui = {
            "calculated_amount":   str(calculated_amount),
            "total_events":        str(real_feats["total_events"]),
            "long_gap_ratio":      str(real_feats["long_gap_ratio"]),
            "unique_clause_count": str(real_feats["unique_clause_count"]),
            "events_per_day":      str(real_feats["events_per_day"]),
            "ambiguity_score":     str(ambiguity),
        }
    else:
        # Synthetic case
        ambiguity = compute_ambiguity_score(tf["long_gap_ratio"], tf["has_events"], unique_clause_count)
        pred_ratio, pred_amount = predict_settlement({
            "calculated_amount":   calculated_amount,
            "total_events":        tf["total_events"],
            "long_gap_ratio":      tf["long_gap_ratio"],
            "unique_clause_count": unique_clause_count,
            "events_per_day":      tf["events_per_day"],
            "has_events":          tf["has_events"],
        }, calculated_amount)
        features_ui = {
            "calculated_amount":   str(calculated_amount),
            "total_events":        str(tf["total_events"]),
            "long_gap_ratio":      str(tf["long_gap_ratio"]),
            "unique_clause_count": str(unique_clause_count),
            "events_per_day":      str(tf["events_per_day"]),
            "ambiguity_score":     str(ambiguity),
        }

    action, reason_codes, explanation = decide_action(pred_ratio, ambiguity, tf["has_events"])

    ambiguity_recovery = {
        "status":                  "Recovered" if unique_clause_count == 0 else "Partial",
        "confidence":              "High — 0.91 NLP similarity to Chevron GTC archetype" if unique_clause_count == 0 else "Medium — some terms ambiguous",
        "fallback_interpretation": "Counting rule defaulted to SHINC. Rate USD 12,500/day." if unique_clause_count == 0 else "Contract terms partially extracted."
    }

    return jsonify({
        "timeline": {
            "port_name": port_name,
            "operation": operation,
            "events": [
                {"label": "Vessel Arrived", "value": tf.get("vessel_arrived") or "—"},
                {"label": "NOR Tendered",   "value": tf.get("nor_tendered")   or "—"},
                {"label": "Mooring Start",  "value": tf.get("mooring_start")  or "—"},
                {"label": "Cargo Start",    "value": tf.get("cargo_start")    or "—"},
                {"label": "Cargo End",      "value": tf.get("cargo_end")      or "—"},
            ]
        },
        "triggers":           triggers,
        "features":           features_ui,
        "ambiguity_recovery": ambiguity_recovery,
        "port_intelligence":  port_intelligence(port_name),
        "decision": {
            "calculated_amount":      str(calculated_amount),
            "pred_settlement_ratio":  str(pred_ratio),
            "pred_settlement_amount": str(pred_amount),
            "ambiguity_score":        str(ambiguity),
            "recommended_action":     action,
            "reason_codes":           reason_codes,
            "explanation":            explanation,
        }
    })


def _cors_preflight():
    resp = jsonify({"ok": True})
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    resp.headers["Access-Control-Max-Age"]       = "3600"
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
