# app.py
# WHAT THIS FILE DOES:
# Builds a web dashboard using Streamlit
# User uploads a blood report PDF
# Shows AI analysis, medicine suggestions, prescription checker
# All in a clean visual interface - no HTML/CSS needed!

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json

from pdf_extractor        import process_blood_report
from ai_analyzer          import analyze_blood_report
from medicine_db          import load_medicines, get_medicine_suggestions
from prescription_checker import check_prescription

# ── Page config (must be first Streamlit command)
st.set_page_config(
    page_title="HRT Blood Report AI",
    page_icon="🩺",
    layout="wide"
)

# ── Custom CSS for cleaner look
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: bold; color: #1f77b4; }
    .status-good    { background-color: #d4edda; padding: 10px; border-radius: 8px; }
    .status-warning { background-color: #fff3cd; padding: 10px; border-radius: 8px; }
    .status-urgent  { background-color: #f8d7da; padding: 10px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


def render_match_score_gauge(score):
    """Creates a gauge chart for prescription match score using Plotly"""
    color = "#28a745" if score >= 80 else "#ffc107" if score >= 50 else "#dc3545"
    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = score,
        title = {"text": "Prescription Match Score"},
        gauge = {
            "axis": {"range": [0, 100]},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,  50],  "color": "#f8d7da"},
                {"range": [50, 80],  "color": "#fff3cd"},
                {"range": [80, 100], "color": "#d4edda"},
            ]
        }
    ))
    fig.update_layout(height=300)
    return fig


def render_blood_values_chart(blood_values):
    """Creates a bar chart showing blood values vs reference ranges"""
    names, values, colors_list, refs = [], [], [], []

    for test, data in blood_values.items():
        names.append(test)
        values.append(data["value"])
        refs.append(data.get("ref_range", "N/A"))

        # Color bars by status
        status = data.get("status", "unknown").lower()
        if status == "high":
            colors_list.append("#dc3545")   # red
        elif status == "low":
            colors_list.append("#fd7e14")   # orange
        else:
            colors_list.append("#28a745")   # green

    fig = go.Figure(go.Bar(
        x=names, y=values,
        marker_color=colors_list,
        text=[f"{v} ({s})" for v, s in zip(values, [d.get("status","?") for d in blood_values.values()])],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Value: %{y}<br><extra></extra>"
    ))
    fig.update_layout(
        title="Blood Test Results Overview",
        xaxis_tickangle=-45,
        height=450,
        showlegend=False
    )
    return fig


# ════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════

st.markdown('<div class="main-header">🩺 HRT Blood Report AI System</div>', unsafe_allow_html=True)
st.markdown("Upload a blood report PDF to get AI-powered analysis, medicine suggestions, and prescription review.")
st.divider()

# ── Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.info("This tool is for **educational/demo purposes** only. Not for medical use.")
    st.divider()
    st.markdown("**How to use:**")
    st.markdown("1. Upload a blood report PDF")
    st.markdown("2. View AI analysis")
    st.markdown("3. Check medicine suggestions")
    st.markdown("4. Enter doctor's prescription")
    st.markdown("5. See match score")

# ── File Upload
uploaded_file = st.file_uploader(
    "📂 Upload Blood Report PDF",
    type=["pdf"],
    help="Upload a patient blood report in PDF format"
)

if uploaded_file:

    # Save uploaded file temporarily
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ── Run Phase 1
    with st.spinner("📄 Extracting blood values from PDF..."):
        extracted = process_blood_report(temp_path)

    if not extracted or not extracted["blood_values"]:
        st.error("❌ Could not extract blood values. Please check your PDF format.")
        st.stop()

    blood_values = extracted["blood_values"]

    # ════════════════════════
    # TAB LAYOUT
    # ════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Blood Values",
        "🧠 AI Analysis",
        "💊 Medicine Suggestions",
        "📋 Prescription Checker"
    ])

    # ── TAB 1: Blood Values
    with tab1:
        st.subheader("📊 Extracted Blood Values")

        # Summary metrics
        total   = len(blood_values)
        high    = sum(1 for d in blood_values.values() if d["status"] == "High")
        low     = sum(1 for d in blood_values.values() if d["status"] == "Low")
        normal  = total - high - low

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tests",    total)
        col2.metric("🔴 High",        high)
        col3.metric("🟠 Low",         low)
        col4.metric("🟢 Normal",      normal)

        # Chart
        st.plotly_chart(render_blood_values_chart(blood_values), use_container_width=True)

        # Data table
        st.subheader("Raw Values Table")
        df = pd.DataFrame([
            {
                "Test":       name,
                "Value":      data["value"],
                "Unit":       data["unit"],
                "Status":     data["status"],
                "Ref Range":  data.get("ref_range", "N/A")
            }
            for name, data in blood_values.items()
        ])
        st.dataframe(df, use_container_width=True)

    # ── TAB 2: AI Analysis
    with tab2:
        st.subheader("🧠 AI Analysis")

        with st.spinner("🤖 Asking Gemini AI to analyze blood values..."):
            analysis = analyze_blood_report(blood_values)

        if "error" in analysis:
            st.error(f"AI Error: {analysis['error']}")
            st.stop()

        # Overall status banner
        status = analysis.get("overall_status", "Unknown")
        if status == "Good":
            st.success(f"✅ Overall Status: {status}")
        elif status == "Needs Attention":
            st.warning(f"⚠️ Overall Status: {status}")
        else:
            st.error(f"🚨 Overall Status: {status}")

        st.info(f"📋 **Summary:** {analysis.get('summary', 'N/A')}")

        # Referral alert
        if analysis.get("refer_to_specialist"):
            st.error(f"🏥 **REFER TO SPECIALIST:** {analysis.get('referral_reason')}")

        # Flagged values
        flagged = analysis.get("flagged_values", [])
        if flagged:
            st.subheader(f"🚩 Flagged Values ({len(flagged)} issues)")
            for item in flagged:
                scope_label = "✅ Within HRT Scope" if item.get("within_hrt_scope") else "⛔ Outside Scope"
                with st.expander(f"{item.get('test')} — {item.get('issue')} | {scope_label}"):
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**Value:** {item.get('value')}")
                    col1.markdown(f"**Issue:** {item.get('issue')}")
                    col2.markdown(f"**Scope:** {scope_label}")
                    col2.markdown(f"**Action:** {item.get('action')}")
                    st.markdown(f"**Explanation:** {item.get('explanation')}")
        else:
            st.success("✅ No flagged values — all results are normal!")

        # Store analysis in session so other tabs can use it
        st.session_state["analysis"] = analysis

    # ── TAB 3: Medicine Suggestions
    with tab3:
        st.subheader("💊 Medicine Suggestions")

        if "analysis" not in st.session_state:
            st.info("👆 Please run AI Analysis in Tab 2 first.")
        else:
            medicines   = load_medicines()
            flagged     = st.session_state["analysis"].get("flagged_values", [])
            suggestions = get_medicine_suggestions(flagged, medicines)

            # Store for Tab 4
            st.session_state["suggestions"] = suggestions

            for item in suggestions:
                if item["action"] == "REFER TO SPECIALIST":
                    st.error(f"⛔ **{item['test']}** — {item['note']}")
                elif item["medicines"]:
                    with st.expander(f"✅ {item['test']} ({item['issue']}) — {len(item['medicines'])} medicine(s) found"):
                        for med in item["medicines"]:
                            st.markdown(f"**💊 {med['name']}** ({med['type']})")
                            st.markdown(f"- Dosage: `{med['dosage']}`")
                            st.markdown(f"- Notes: {med['notes']}")
                            st.divider()
                else:
                    st.warning(f"⚠️ **{item['test']}** — {item['note']}")

            st.caption("⚕️ All suggestions are from the internal product database only.")

    # ── TAB 4: Prescription Checker
    with tab4:
        st.subheader("📋 Prescription Match Checker")

        if "suggestions" not in st.session_state:
            st.info("👆 Please complete Tab 2 and Tab 3 first.")
        else:
            st.markdown("Enter the doctor's prescribed medicines below (one per line):")

            prescription_input = st.text_area(
                "Doctor's Prescription",
                placeholder="Anastrozole\nMetformin\nOmega-3 Fish Oil",
                height=150
            )

            if st.button("🔍 Check Prescription Match", type="primary"):
                if not prescription_input.strip():
                    st.warning("Please enter at least one medicine.")
                else:
                    # Parse input into list
                    prescribed = [
                        line.strip()
                        for line in prescription_input.strip().split("\n")
                        if line.strip()
                    ]

                    report = check_prescription(prescribed, st.session_state["suggestions"])

                    # Gauge chart
                    st.plotly_chart(
                        render_match_score_gauge(report["match_score"]),
                        use_container_width=True
                    )

                    col1, col2, col3 = st.columns(3)
                    col1.metric("AI Suggested",      report["total_ai_suggested"])
                    col2.metric("Doctor Prescribed", report["total_prescribed"])
                    col3.metric("Matched",           len(report["matched"]))

                    # Matched
                    if report["matched"]:
                        st.success(f"✅ **Matched ({len(report['matched'])})** — AI agrees with doctor")
                        for m in report["matched"]:
                            st.markdown(f"- **{m['medicine']}** → for {m['test']} ({m['issue']})")

                    # Extra
                    if report["extra_prescriptions"]:
                        st.info(f"➕ **Extra ({len(report['extra_prescriptions'])})** — doctor added, not in AI list")
                        for m in report["extra_prescriptions"]:
                            st.markdown(f"- {m}")

                    # Missed
                    if report["missed_suggestions"]:
                        st.warning(f"⚠️ **Missed ({len(report['missed_suggestions'])})** — AI suggested but not prescribed")
                        for m in report["missed_suggestions"]:
                            st.markdown(f"- **{m['name']}** → for {m['test']} ({m['issue']})")

                    st.caption("⚕️ Doctor has final authority. This tool is advisory only.")

else:
    # Show instructions when no file uploaded
    st.info("👆 Upload a blood report PDF above to get started!")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("### 📄\n**Phase 1**\nPDF Extraction")
    col2.markdown("### 🧠\n**Phase 2**\nAI Analysis")
    col3.markdown("### 💊\n**Phase 3**\nMedicine Match")
    col4.markdown("### 📋\n**Phase 4**\nRx Checker")