"""EdgeMed Agent — Local Offline UI (Streamlit).

Inspired by the web demo design: patient management, workspace, copilot chat,
records browser, queue & sync status — all offline-first.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LOCAL_API = "http://localhost:8000"

SAMPLE_NOTES = {
    "ER Visit — Chest Pain (EN)": (
        "Patient: Maria Gonzalez, 54F\n"
        "Chief Complaint: \"I've been having chest pain for the past 3 days\"\n"
        "HPI: 54-year-old female presents with substernal chest pain, described as "
        "pressure-like, radiating to the left arm. Pain is worse with exertion and "
        "relieved by rest. No associated shortness of breath, nausea, or diaphoresis.\n"
        "PMH: Hypertension (10 years), Type 2 DM (5 years), Hyperlipidemia\n"
        "Medications: Metformin 1000mg BID, Lisinopril 20mg daily, Atorvastatin 40mg daily\n"
        "Allergies: Penicillin (rash)\n"
        "Assessment/Plan:\n"
        "1. Chest pain - rule out ACS. Order troponin, EKG, CXR. Start aspirin 325mg.\n"
        "2. Hypertension - poorly controlled. Increase lisinopril to 40mg daily.\n"
        "3. Diabetes - continue metformin. Check HbA1c.\n"
        "Follow-up in 1 week or sooner if symptoms worsen."
    ),
    "Chronic Disease Follow-up (EN)": (
        "CC: Diabetes follow-up\n"
        "HPI: 62yo female here for routine diabetes management. A1C last month was "
        "7.8%, up from 7.2%. Reports occasional hypoglycemia in the mornings.\n"
        "Medications: Metformin 1000mg BID, Glipizide 5mg daily, Lisinopril 20mg daily, "
        "Atorvastatin 40mg daily\n"
        "Allergies: NKDA\n"
        "Assessment: 1. Type 2 DM, suboptimal control. 2. Hypertension, stable.\n"
        "Plan: Increase Metformin to 1000mg BID if tolerating, add Jardiance 10mg daily, "
        "recheck A1C in 3 months, diabetic eye exam referral.\n"
        "Follow-up: Return in 3 months."
    ),
    "Consulta ER — Dolor torácico (ES)": (
        "Paciente: María González, 54F\n"
        "Motivo de consulta: \"He tenido dolor en el pecho durante los últimos 3 días\"\n"
        "Historia: Mujer de 54 años presenta dolor torácico subesternal, descrito como "
        "presión, irradiado al brazo izquierdo.\n"
        "Antecedentes: Hipertensión (10 años), DM tipo 2 (5 años), Hiperlipidemia\n"
        "Medicamentos: Metformina 1000mg BID, Lisinopril 20mg diario, Atorvastatina 40mg\n"
        "Alergias: Penicilina (erupción)\n"
        "Plan: Descartar SCA. Troponina, EKG, RX tórax. Aspirina 325mg."
    ),
}

st.set_page_config(
    page_title="EdgeMed Agent — Local",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _api_get(path: str, timeout: int = 10):
    """GET helper with error handling."""
    return httpx.get(f"{LOCAL_API}{path}", timeout=timeout)


def _api_post(path: str, payload: dict, timeout: int = 60):
    """POST helper with error handling."""
    return httpx.post(f"{LOCAL_API}{path}", json=payload, timeout=timeout)


# ──────────────────────────── Sidebar ────────────────────────────

def render_sidebar():
    st.sidebar.markdown(
        """
        <div style="text-align:center;padding:0.5rem 0 1rem 0">
            <h2 style="margin:0;letter-spacing:-0.5px">EdgeMed Agent</h2>
            <p style="margin:0;font-size:0.75rem;opacity:0.6">Offline Clinical Documentation</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # API status
    try:
        r = _api_get("/local/queue", timeout=3)
        st.sidebar.success("Local API: Connected", icon="🟢")
    except Exception:
        st.sidebar.error("Local API: Disconnected", icon="🔴")

    st.sidebar.divider()

    # Patient management
    st.sidebar.subheader("Patient")
    if "patients" not in st.session_state:
        st.session_state.patients = [
            {"id": "p-001", "name": "Maria Gonzalez", "age": 54, "sex": "F"},
            {"id": "p-002", "name": "James Rivera", "age": 67, "sex": "M"},
            {"id": "p-003", "name": "Ana López", "age": 32, "sex": "F"},
        ]
    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = None

    patient_names = ["None"] + [f"{p['name']} ({p['age']}{p['sex']})" for p in st.session_state.patients]
    sel_idx = st.sidebar.selectbox(
        "Select patient",
        range(len(patient_names)),
        format_func=lambda i: patient_names[i],
        key="patient_select",
    )
    if sel_idx == 0:
        st.session_state.selected_patient = None
    else:
        st.session_state.selected_patient = st.session_state.patients[sel_idx - 1]

    with st.sidebar.expander("Add Patient"):
        name = st.text_input("Name", key="new_p_name")
        c1, c2 = st.columns(2)
        age = c1.number_input("Age", min_value=0, max_value=150, value=30, key="new_p_age")
        sex = c2.selectbox("Sex", ["F", "M", "O"], key="new_p_sex")
        if st.button("Add", key="add_patient"):
            if name.strip():
                new_p = {"id": f"p-{int(time.time())}", "name": name.strip(), "age": int(age), "sex": sex}
                st.session_state.patients.append(new_p)
                st.rerun()

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigate",
        ["Workspace", "Copilot Chat", "Records", "Queue Status", "Sync Status"],
        key="nav_radio",
    )
    return page


# ──────────────────────────── Workspace ────────────────────────────

def page_workspace():
    st.markdown(
        """<div style="background:rgba(37,99,235,0.06);border:1px solid rgba(37,99,235,0.2);
        border-radius:12px;padding:1rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:1rem">
        <div style="font-size:1.5rem">🩺</div>
        <div>
            <div style="font-weight:600;font-size:0.9rem">Welcome, Doctor</div>
            <div style="font-size:0.75rem;opacity:0.6">
                Paste or dictate your clinical note below. EdgeMed will extract structured EHR-ready data with safety checks.
            </div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("Clinical Note Input")

        tab_paste, tab_sample = st.tabs(["Paste Note", "Use Sample Note"])

        with tab_sample:
            sample_choice = st.selectbox("Choose sample", list(SAMPLE_NOTES.keys()), key="sample_choice")
            if st.button("Load Sample", key="load_sample"):
                st.session_state["note_text"] = SAMPLE_NOTES[sample_choice]
                st.rerun()

        with tab_paste:
            note_text = st.text_area(
                "Enter clinical note:",
                value=st.session_state.get("note_text", ""),
                height=300,
                key="note_input",
                placeholder="Paste a clinical note here...",
            )

        c_lang, c_btn = st.columns([1, 3])
        locale = c_lang.selectbox("Language", ["en", "es"], key="locale_sel")

        extract_clicked = c_btn.button(
            "Extract Structured Record",
            type="primary",
            disabled=len(st.session_state.get("note_text", note_text).strip()) < 10,
            use_container_width=True,
        )

        if extract_clicked:
            with st.spinner("Processing with MedGemma..."):
                start = time.time()
                try:
                    r = _api_post(
                        "/local/extract",
                        {"note_text": note_text, "locale": locale},
                    )
                    r.raise_for_status()
                    result = r.json()
                    st.session_state["last_result"] = result
                    st.session_state["last_note_text"] = note_text
                    elapsed = time.time() - start
                    st.success(f"Extraction complete in {elapsed:.1f}s")
                except httpx.ConnectError:
                    st.error("Cannot connect to local API. Make sure the local server is running on port 8000.")
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

    with col_result:
        if "last_result" not in st.session_state:
            st.markdown(
                """<div style="display:flex;align-items:center;justify-content:center;
                min-height:400px;border:1px dashed rgba(128,128,128,0.3);border-radius:12px">
                <p style="color:rgba(128,128,128,0.6);font-size:0.9rem">
                Results will appear here after extraction</p></div>""",
                unsafe_allow_html=True,
            )
        else:
            _render_result(st.session_state["last_result"])


def _render_result(result: dict):
    record = result.get("record", {})
    flags = result.get("flags", {})
    score = flags.get("completeness_score", 0)
    if isinstance(score, (int, float)) and score <= 1:
        score_pct = int(score * 100)
    else:
        score_pct = int(score)

    st.subheader("Structured Record")
    st.progress(score_pct / 100, text=f"{score_pct}% complete")

    tab_read, tab_json = st.tabs(["Readable", "Raw JSON"])

    with tab_read:
        if record.get("chief_complaint"):
            st.markdown(f"**Chief Complaint:** {record['chief_complaint']}")
        if record.get("hpi"):
            st.markdown(f"**HPI:** {record['hpi']}")

        if record.get("assessment"):
            st.markdown("**Assessment / Diagnoses:**")
            for p in record["assessment"]:
                if isinstance(p, dict):
                    desc = p.get("description", str(p))
                    icd = p.get("icd10", "")
                    conf = p.get("confidence", "")
                    badge = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "")
                    line = f"- {desc}"
                    if icd:
                        line += f" `{icd}`"
                    if badge:
                        line += f" {badge} {conf}"
                    st.markdown(line)
                else:
                    st.markdown(f"- {p}")

        if record.get("medications"):
            st.markdown("**Medications:**")
            for m in record["medications"]:
                if isinstance(m, dict):
                    parts = [m.get("name", "")]
                    if m.get("dose"):
                        parts.append(m["dose"])
                    if m.get("frequency"):
                        parts.append(m["frequency"])
                    status = m.get("status", "")
                    line = " ".join(parts)
                    if status:
                        line += f" — *{status}*"
                    st.markdown(f"- {line}")
                else:
                    st.markdown(f"- {m}")

        if record.get("allergies"):
            st.markdown("**Allergies:**")
            for a in record["allergies"]:
                if isinstance(a, dict):
                    line = a.get("substance", "")
                    if a.get("reaction"):
                        line += f" ({a['reaction']})"
                    st.markdown(f"- {line}")
                else:
                    st.markdown(f"- {a}")

        if record.get("plan"):
            st.markdown(f"**Plan:**\n{record['plan']}")

        if record.get("red_flags"):
            st.warning("**Red Flags:** " + " | ".join(record["red_flags"]))

        if record.get("follow_up"):
            st.markdown(f"**Follow-up:** {record['follow_up']}")

        if record.get("patient_summary_plain_language"):
            st.info(f"**Patient Summary:** {record['patient_summary_plain_language']}")

    with tab_json:
        st.code(json.dumps(record, indent=2, ensure_ascii=False), language="json")

    # Flags
    st.divider()
    st.subheader("Safety & Quality Flags")

    if flags.get("missing_fields"):
        missing = flags["missing_fields"]
        st.warning("**Missing Fields:** " + ", ".join(missing if isinstance(missing[0], str) else [f["field"] for f in missing]))

    if flags.get("contradictions"):
        for c in flags["contradictions"]:
            st.error(f"Contradiction: {c}")
    else:
        st.success("No contradictions detected")

    if flags.get("confidence_by_field"):
        st.markdown("**Field Confidence:**")
        cols = st.columns(4)
        for i, (field, conf) in enumerate(flags["confidence_by_field"].items()):
            icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "⚪")
            cols[i % 4].markdown(f"{icon} **{field}**: {conf}")

    # Actions
    st.divider()
    c1, c2, c3 = st.columns(3)
    if c1.button("Approve & Save to Queue", type="primary", use_container_width=True):
        _save_to_queue(st.session_state["last_result"])
    if c2.button("Edit", use_container_width=True):
        st.info("Edit mode — modify the note above and re-extract.")
    if c3.button("Re-run Repair", use_container_width=True):
        st.info("Re-run triggered — use workspace extract button.")


def _save_to_queue(result: dict):
    try:
        r = _api_post(
            "/local/save",
            {
                "note_id": result.get("note_id", f"local-{int(time.time())}"),
                "record": result["record"],
                "flags": result["flags"],
                "note_text": st.session_state.get("last_note_text"),
            },
            timeout=10,
        )
        r.raise_for_status()
        st.success("Saved to encrypted queue!")
    except Exception as e:
        st.error(f"Save failed: {e}")


# ──────────────────────────── Copilot Chat ────────────────────────────

def page_copilot():
    st.markdown(
        """<div style="background:rgba(234,179,8,0.08);border:1px solid rgba(234,179,8,0.3);
        border-radius:8px;padding:0.75rem;margin-bottom:1rem;display:flex;gap:0.5rem;align-items:start">
        <span>⚠️</span>
        <span style="font-size:0.8rem;color:rgba(234,179,8,0.9)">
        This assistant is for documentation support only. Not for diagnosis or clinical decision-making.</span>
        </div>""",
        unsafe_allow_html=True,
    )

    st.subheader("Clinician Copilot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    starters = [
        "What's missing before I finalize?",
        "Rewrite the plan in clean clinical format",
        "Generate SBAR referral summary",
        "Generate patient instructions (simple Spanish)",
    ]

    if not st.session_state.chat_history:
        st.markdown("*Ask me about the extracted record. I can help you finalize documentation.*")
        cols = st.columns(2)
        for i, s in enumerate(starters):
            if cols[i % 2].button(s, key=f"starter_{i}", use_container_width=True):
                _send_chat(s)
                st.rerun()

    for msg in st.session_state.chat_history:
        role = msg["role"]
        with st.chat_message("assistant" if role == "assistant" else "user"):
            st.markdown(msg["content"])
            if msg.get("grounded"):
                st.caption(f"Grounded on: {msg['grounded']}")

    prompt = st.chat_input("Ask about the record...")
    if prompt:
        _send_chat(prompt)
        st.rerun()


def _send_chat(text: str):
    st.session_state.chat_history.append({"role": "user", "content": text})

    record = {}
    if "last_result" in st.session_state:
        record = st.session_state["last_result"].get("record", {})
    note_text = st.session_state.get("last_note_text")

    try:
        r = _api_post(
            "/local/chat",
            {
                "note_id": f"chat-{int(time.time())}",
                "question": text,
                "record": record,
                "note_text": note_text,
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": data.get("answer", "No answer received."),
            "grounded": ", ".join(data.get("grounded_on", ["Record"])),
        })
    except Exception:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": (
                "I can help with that. Based on the current record, some information is "
                "**not documented / unknown**. Could you provide more details?\n\n"
                "*(Local chat API unavailable — this is a fallback response)*"
            ),
            "grounded": "Record (demo fallback)",
        })


# ──────────────────────────── Records ────────────────────────────

def page_records():
    st.subheader("Extracted Records")

    search = st.text_input("Search by note ID...", key="rec_search", placeholder="Type to filter...")

    try:
        r = _api_get("/local/records")
        r.raise_for_status()
        records = r.json().get("records", [])
    except httpx.ConnectError:
        st.error("Cannot connect to local API.")
        records = []
    except Exception as e:
        st.error(f"Failed to load records: {e}")
        records = []

    if not records:
        st.info("No records saved yet. Extract a note and save it to the queue first.")
        return

    if search:
        records = [r for r in records if search.lower() in r.get("note_id", "").lower()]

    for rec in records:
        note_id = rec.get("note_id", "unknown")[:20]
        status = rec.get("status", "")
        flags = rec.get("flags", {})
        score = flags.get("completeness_score", 0)
        if isinstance(score, (int, float)) and score <= 1:
            score = int(score * 100)

        status_icon = {"queued": "🔵", "syncing": "🟡", "synced": "🟢", "failed": "🔴"}.get(status, "⚪")

        with st.expander(f"{status_icon} {note_id}... — {score}% complete — {status}"):
            record_data = rec.get("record", rec.get("payload", {}))
            if isinstance(record_data, dict):
                if record_data.get("chief_complaint"):
                    st.markdown(f"**CC:** {record_data['chief_complaint']}")
                if record_data.get("hpi"):
                    st.markdown(f"**HPI:** {record_data['hpi'][:200]}...")

                tab_detail, tab_raw = st.tabs(["Details", "Raw JSON"])
                with tab_detail:
                    if record_data.get("medications"):
                        st.markdown("**Medications:**")
                        for m in record_data["medications"]:
                            if isinstance(m, dict):
                                st.markdown(f"- {m.get('name', '')} {m.get('dose', '')} {m.get('frequency', '')}")
                    if record_data.get("allergies"):
                        st.markdown("**Allergies:**")
                        for a in record_data["allergies"]:
                            if isinstance(a, dict):
                                st.markdown(f"- {a.get('substance', '')} ({a.get('reaction', '')})")
                with tab_raw:
                    st.code(json.dumps(rec, indent=2, ensure_ascii=False, default=str), language="json")

                col_ex, col_del = st.columns(2)
                if col_ex.button("Export JSON", key=f"exp_{note_id}"):
                    st.code(json.dumps(record_data, indent=2, ensure_ascii=False), language="json")
            else:
                st.json(rec)


# ──────────────────────────── Queue Status ────────────────────────────

def page_queue_status():
    st.subheader("Encrypted Queue Status")

    try:
        r = _api_get("/local/queue")
        r.raise_for_status()
        data = r.json()
    except httpx.ConnectError:
        st.error("Cannot connect to local API.")
        return
    except Exception as e:
        st.error(f"Failed to load queue: {e}")
        return

    counts = data.get("counts", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Queued", counts.get("queued", 0))
    c2.metric("Syncing", counts.get("syncing", 0))
    c3.metric("Synced", counts.get("synced", 0))
    c4.metric("Failed", counts.get("failed", 0))

    items = data.get("items", [])
    if items:
        st.divider()
        for item in items:
            status = item.get("status", "")
            icon = {"queued": "🔵", "syncing": "🟡", "synced": "🟢", "failed": "🔴"}.get(status, "⚪")
            nid = item.get("note_id", "?")[:16]
            retries = item.get("retry_count", 0)
            created = item.get("created_at", "")

            st.markdown(
                f"{icon} **{nid}...** — Status: `{status}` — "
                f"Retries: {retries} — Created: {created}"
            )
            if item.get("fail_reason"):
                st.caption(f"Failure: {item['fail_reason']}")
    else:
        st.info("Queue is empty.")


# ──────────────────────────── Sync Status ────────────────────────────

def page_sync_status():
    st.subheader("Sync Status")

    st.markdown(
        """<div style="background:rgba(37,99,235,0.06);border:1px solid rgba(37,99,235,0.2);
        border-radius:12px;padding:1rem;margin-bottom:1rem">
        <p style="font-weight:600;font-size:0.9rem;margin:0">Offline-First Architecture</p>
        <p style="font-size:0.8rem;opacity:0.6;margin:0.25rem 0 0 0">
        In the local app, records are processed on-device first. When internet returns,
        they sync automatically. Clinical workflows are never interrupted by network issues.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    col_status, col_action = st.columns([2, 1])

    with col_status:
        st.markdown("**Connectivity:**")
        try:
            r = _api_get("/local/queue", timeout=3)
            st.success("Local API: Connected")
            counts = r.json().get("counts", {})
            pending = counts.get("queued", 0)
            st.info(f"**{pending}** items pending sync")
        except Exception:
            st.error("Local API: Disconnected")

    with col_action:
        st.markdown("**Manual Sync:**")
        if st.button("Trigger Sync Now", type="primary", use_container_width=True):
            with st.spinner("Syncing..."):
                try:
                    r = _api_post("/local/sync/trigger", {}, timeout=60)
                    r.raise_for_status()
                    result = r.json()
                    st.success(
                        f"Sync complete: {result.get('synced_count', 0)} synced, "
                        f"{result.get('failed_count', 0)} failed"
                    )
                except httpx.ConnectError:
                    st.error("Cannot connect to local API.")
                except Exception as e:
                    st.error(f"Sync failed: {e}")

    st.divider()
    st.subheader("How Sync Works")
    steps = [
        ("1. Local Processing", "MedGemma runs on your device. Notes are extracted into structured JSON without any network calls."),
        ("2. Queue", "Extracted records enter a local encrypted queue. Each record is assigned a status: queued → syncing → synced / failed."),
        ("3. Auto-Sync", "When connectivity is detected, the agent syncs records to the cloud. Failed syncs retry with exponential backoff."),
        ("4. Conflict Resolution", "Server-side timestamps and idempotency keys ensure no data is overwritten. Conflicts are flagged for clinician review."),
    ]
    for title, desc in steps:
        st.markdown(f"**{title}:** {desc}")


# ──────────────────────────── Main ────────────────────────────

def main():
    page = render_sidebar()

    if page == "Workspace":
        page_workspace()
    elif page == "Copilot Chat":
        page_copilot()
    elif page == "Records":
        page_records()
    elif page == "Queue Status":
        page_queue_status()
    elif page == "Sync Status":
        page_sync_status()


if __name__ == "__main__":
    main()
