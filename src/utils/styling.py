import streamlit as st

def apply_custom_css():
    """Applique le CSS personnalisé professionnel."""
    st.markdown("""
    <style>
    /* Global styles */
    .stApp {
        background-color: #0F172A;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }

    [data-testid="stSidebar"] .stRadio > label {
        color: #F1F5F9 !important;
        font-size: 13px;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #E63946, #DC2626);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #DC2626, #B91C1C);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(230, 57, 70, 0.3);
    }

    .stButton > button[kind="secondary"] {
        background: #1E293B;
        border: 1px solid #334155;
        color: #F1F5F9;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #334155;
    }

    /* Sliders */
    .stSlider > div > div > div {
        background-color: #E63946 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: #1E293B;
        color: #F1F5F9;
        border: 1px solid #334155;
        border-radius: 6px;
    }

    /* Dataframes */
    .stDataFrame {
        background-color: #1E293B;
        border-radius: 8px;
        border: 1px solid #334155;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1E293B;
        border-radius: 8px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #94A3B8;
        font-weight: 600;
        font-size: 13px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #E63946 !important;
        color: white !important;
        border-radius: 6px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1E293B;
        color: #F1F5F9;
        border-radius: 6px;
        font-weight: 600;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #E63946 !important;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #F1F5F9;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-size: 11px;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0F172A;
    }

    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }

    /* Alerts */
    .stAlert {
        border-radius: 8px;
        border: none;
    }

    .stAlert [data-testid="stMarkdownContainer"] {
        color: #F1F5F9;
    }

    /* Info box */
    .stInfo {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
    }

    /* Warning */
    .stWarning {
        background-color: #422006;
        border: 1px solid #713F12;
        border-radius: 8px;
    }

    /* Error */
    .stError {
        background-color: #450A0A;
        border: 1px solid #7F1D1D;
        border-radius: 8px;
    }

    /* Success */
    .stSuccess {
        background-color: #052E16;
        border: 1px solid #14532D;
        border-radius: 8px;
    }

    /* Tooltip */
    .stTooltipIcon {
        color: #64748B;
    }

    /* Multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #E63946;
        color: white;
    }

    /* Toggle */
    .stToggle [data-baseweb="toggle"] {
        background-color: #334155;
    }

    .stToggle [data-baseweb="toggle"][aria-checked="true"] {
        background-color: #10B981;
    }

    /* Date input */
    .stDateInput > div > div > input {
        background-color: #1E293B;
        color: #F1F5F9;
        border: 1px solid #334155;
    }

    /* Text area */
    .stTextArea > div > div > textarea {
        background-color: #1E293B;
        color: #F1F5F9;
        border: 1px solid #334155;
    }

    /* Download button */
    .stDownloadButton > button {
        background: #1E293B;
        border: 1px solid #334155;
        color: #3B82F6;
    }

    .stDownloadButton > button:hover {
        background: #334155;
        color: #60A5FA;
    }
    </style>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, color: str = "#F1F5F9", delta: str = None):
    """Rend une carte de métrique personnalisée."""
    delta_html = f"<p style='margin: 4px 0 0 0; font-size: 10px; color: #10B981;'>▲ {delta}</p>" if delta else ""

    st.markdown(f"""
    <div style="background: #0F172A; padding: 12px; border-radius: 8px; 
                border: 1px solid #334155; margin-bottom: 8px;">
        <p style="margin: 0; font-size: 10px; color: #64748B; text-transform: uppercase; letter-spacing: 1px;">
            {label}
        </p>
        <p style="margin: 4px 0 0 0; font-size: 20px; font-weight: 700; color: {color};">
            {value}
        </p>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def render_status_badge(status: str, color: str = "#10B981"):
    """Rend un badge de statut."""
    st.markdown(f"""
    <span style="background: {color}; color: white; font-size: 10px; font-weight: 600; 
                padding: 3px 10px; border-radius: 12px; display: inline-block;">
        {status}
    </span>
    """, unsafe_allow_html=True)
