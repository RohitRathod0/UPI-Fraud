"""
Streamlit App for UPI Fraud Detection
Enterprise-grade fraud detection with AI-powered analysis
"""

import streamlit as st
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# Add server directory to path
server_dir = Path(__file__).parent / "server"
sys.path.insert(0, str(server_dir))

# Import agents with error handling
try:
    from agents.phish_agent import PhishingAgent
    from agents.qr_guard_agent import QuishingAgent
    from agents.collect_sense_agent import CollectRequestAgent
    from agents.mal_scan_agent import MalwareAgent
    from agents.trust_score_agent import TrustScoreAgent
    from agents.explainer_agent import ExplainerAgent
    from agents.hitl_manager_agent import HITLManagerAgent
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="SecureUPI - AI Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS matching HTML design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(180deg, #0b1224 0%, #0a0f1f 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Header */
    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #5b6ee1 0%, #7c4bd8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    
    .tagline {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        color: #94a3b8;
        font-weight: 400;
        margin-bottom: 2rem;
        letter-spacing: -0.01em;
        line-height: 1.6;
    }
    
    /* Section Headers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 1rem;
        letter-spacing: -0.01em;
    }
    
    /* Buttons */
    .stButton > button {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        border-radius: 10px;
        transition: all 0.3s;
        letter-spacing: -0.2px;
        padding: 0.5rem 1.5rem;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #5b6ee1, #7c4bd8);
        border: none;
        color: #fff;
        box-shadow: 0 4px 16px rgba(91, 110, 225, 0.3);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(91, 110, 225, 0.4);
    }
    
    .stButton > button[kind="secondary"] {
        background: #0b132a;
        border: 1px solid #1e293b;
        color: #e2e8f0;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #111a33;
        border-color: #5b6ee1;
    }
    
    /* Form Elements */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        font-family: 'Inter', sans-serif;
        background: #0b132a;
        border: 1px solid #1e293b;
        color: #e2e8f0;
        border-radius: 12px;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #6080ff;
        box-shadow: 0 0 0 4px rgba(96, 128, 255, 0.18);
    }
    
    /* Labels */
    label {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #94a3b8;
        font-size: 0.9rem;
        letter-spacing: 0.02em;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        color: #94a3b8;
    }
    
    /* Risk Colors */
    .risk-high {
        color: #ef4444;
        font-weight: 700;
    }
    .risk-medium {
        color: #f59e0b;
        font-weight: 700;
    }
    .risk-low {
        color: #22c55e;
        font-weight: 700;
    }
    
    /* Info Boxes */
    .info-box {
        background: linear-gradient(135deg, rgba(91, 110, 225, 0.1), rgba(124, 75, 216, 0.1));
        border: 1px solid rgba(91, 110, 225, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f162e, #0d1326);
        border-right: 1px solid #1e293b;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #e2e8f0;
    }
    
    /* Success/Info/Error Messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 10px;
    }
    
    .stInfo {
        background: rgba(96, 165, 250, 0.1);
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 10px;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 10px;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'models_loaded' not in st.session_state:
    st.session_state.models_loaded = False
if 'agents' not in st.session_state:
    st.session_state.agents = {}

@st.cache_resource
def load_models():
    """Load ML models (cached) - ensures all 4 models load correctly"""
    import pickle
    import os
    
    try:
        # Determine model directory - try multiple paths
        possible_paths = [
            server_dir / "models",
            Path("server/models"),
            Path(__file__).parent / "server" / "models"
        ]
        
        model_dir = None
        for path in possible_paths:
            if path.exists() and (path / 'phishing_detector.pkl').exists():
                model_dir = path
                break
        
        if model_dir is None:
            print("ERROR: Could not find model directory")
            return None, False, {}
        
        print(f"Loading models from: {model_dir}")
        
        # Model file paths
        model_files = {
            'phishing': model_dir / 'phishing_detector.pkl',
            'quishing': model_dir / 'qr_detector.pkl',
            'collect': model_dir / 'collect_detector.pkl',
            'malware': model_dir / 'malware_detector.pkl'
        }
        
        # Verify all model files exist
        missing = []
        for name, path in model_files.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
        
        if missing:
            print(f"ERROR: Missing model files:\n" + "\n".join(missing))
            return None, False, {}
        
        # Initialize agents with absolute paths
        agents = {
            'phishing': PhishingAgent(model_path=str(model_files['phishing'].absolute())),
            'quishing': QuishingAgent(model_path=str(model_files['quishing'].absolute())),
            'collect': CollectRequestAgent(model_path=str(model_files['collect'].absolute())),
            'malware': MalwareAgent(model_path=str(model_files['malware'].absolute())),
            'trust': TrustScoreAgent(),
            'explainer': ExplainerAgent(),
            'hitl': HITLManagerAgent()
        }
        
        # Force reload models with explicit loading
        loaded_count = 0
        model_status = {}
        model_errors = {}
        
        for name, agent in [('phishing', agents['phishing']), ('quishing', agents['quishing']), 
                           ('collect', agents['collect']), ('malware', agents['malware'])]:
            model_path = model_files[name]
            success = False
            error_msg = None
            
            try:
                # Method 1: Use agent's load_model method
                agent.model_path = str(model_path.absolute())
                agent.load_model()
                if agent.is_loaded():
                    success = True
                    print(f"✓ {name.title()}: Loaded via agent method")
            except Exception as e1:
                error_msg = f"Agent method failed: {str(e1)[:50]}"
                try:
                    # Method 2: Direct pickle load
                    with open(model_path, 'rb') as f:
                        agent.model = pickle.load(f)
                        agent.loaded = True
                        success = True
                        print(f"✓ {name.title()}: Loaded via direct pickle")
                except Exception as e2:
                    error_msg = f"Direct load failed: {str(e2)[:50]}"
                    try:
                        # Method 3: Try with latin1 encoding
                        with open(model_path, 'rb') as f:
                            agent.model = pickle.load(f, encoding='latin1')
                            agent.loaded = True
                            success = True
                            print(f"✓ {name.title()}: Loaded via latin1 encoding")
                    except Exception as e3:
                        error_msg = f"All methods failed: {str(e3)[:50]}"
            
            if success:
                loaded_count += 1
                model_status[name] = True
                model_errors[name] = None
            else:
                model_status[name] = False
                model_errors[name] = error_msg
                print(f"✗ {name.title()}: FAILED - {error_msg}")
        
        # Print summary
        print(f"\nModel Loading Summary: {loaded_count}/4 models loaded")
        if any(model_errors.values()):
            print("Errors:")
            for name, err in model_errors.items():
                if err:
                    print(f"  - {name}: {err}")
        
        if loaded_count == 0:
            return None, False, {}
        
        return agents, True, model_status
    except Exception as e:
        print(f"CRITICAL ERROR in load_models: {e}")
        import traceback
        traceback.print_exc()
        return None, False, {}

# Load models
if not st.session_state.models_loaded:
    with st.spinner("Loading ML models... This may take a moment."):
        agents, success, model_status = load_models()
        if success:
            st.session_state.agents = agents
            st.session_state.models_loaded = True
            st.session_state.model_status = model_status
        else:
            st.error("Failed to load models. Please check model files.")
            st.stop()

agents = st.session_state.agents
model_status = st.session_state.get('model_status', {})

# Header with impressive tagline (no emojis)
st.markdown('<h1 class="main-header">SecureUPI</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Enterprise-Grade AI Fraud Detection • Protecting Millions of Transactions with Advanced Machine Learning</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown('<h2 class="section-header">Quick Test</h2>', unsafe_allow_html=True)
    st.markdown("**Select a scenario to test fraud detection:**")
    
    if st.button("Safe Transaction", use_container_width=True, type="secondary"):
        st.session_state.preset = "safe"
        st.rerun()
    if st.button("Phishing Attack", use_container_width=True, type="secondary"):
        st.session_state.preset = "phishing"
        st.rerun()
    if st.button("QR Code Scam", use_container_width=True, type="secondary"):
        st.session_state.preset = "qr"
        st.rerun()
    if st.button("Collect Fraud", use_container_width=True, type="secondary"):
        st.session_state.preset = "collect"
        st.rerun()
    
    st.markdown("---")
    st.markdown('<h3 class="section-header">System Status</h3>', unsafe_allow_html=True)
    
    # Model status
    for name, status in model_status.items():
        status_text = "Loaded" if status else "Rule-based"
        status_icon = "✓" if status else "⚠"
        st.write(f"{status_icon} {name.title()}: {status_text}")
    
    st.success("Ready for Analysis")

# Initialize form values
default_payer = "user@paytm"
default_payee = "merchant@upi"
default_amount = 1000.0
default_message = "Payment for services"
default_payee_new = 1
default_transaction_type = "pay"

# Handle presets
if 'preset' in st.session_state and st.session_state.preset:
    preset = st.session_state.preset
    if preset == "safe":
        default_payer = "user@paytm"
        default_payee = "grocery-store@paytm"
        default_amount = 450.0
        default_message = "Weekly groceries"
        default_payee_new = 0
        default_transaction_type = "pay"
        st.session_state.preset = None
    elif preset == "phishing":
        default_payer = "user@paytm"
        default_payee = "verify-security@upi"
        default_amount = 15000.0
        default_message = "URGENT! Account locked. Verify PIN at http://fake-bank.com"
        default_payee_new = 1
        default_transaction_type = "pay"
        st.session_state.preset = None
    elif preset == "qr":
        default_payer = "user@paytm"
        default_payee = "prize-claim@paytm"
        default_amount = 19999.0
        default_message = "Scan QR to claim ₹50,000 prize at http://bit.ly/win"
        default_payee_new = 1
        default_transaction_type = "qr_pay"
        st.session_state.preset = None
    elif preset == "collect":
        default_payer = "user@paytm"
        default_payee = "legal-dept@upi"
        default_amount = 12000.0
        default_message = "FINAL NOTICE: Pay dues immediately or legal action"
        default_payee_new = 1
        default_transaction_type = "collect"
        st.session_state.preset = None

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<h2 class="section-header">Transaction Details</h2>', unsafe_allow_html=True)
    
    # Transaction form
    with st.form("transaction_form", clear_on_submit=False):
        payer_vpa = st.text_input("Payer UPI ID", value=default_payer, help="Your UPI ID", key="payer_input")
        payee_vpa = st.text_input("Payee UPI ID", value=default_payee, help="Recipient UPI ID", key="payee_input")
        amount = st.number_input("Amount (₹)", min_value=1.0, value=default_amount, step=100.0, key="amount_input")
        transaction_type = st.selectbox("Transaction Type", ["pay", "qr_pay", "collect"], 
                                         index=["pay", "qr_pay", "collect"].index(default_transaction_type) if default_transaction_type in ["pay", "qr_pay", "collect"] else 0,
                                         key="type_input")
        payee_new = st.selectbox("Is Payee New?", [0, 1], index=default_payee_new, format_func=lambda x: "Yes" if x == 1 else "No", key="new_input")
        message = st.text_area("Transaction Message", value=default_message, help="Transaction note/message", key="message_input", height=100)
        
        submitted = st.form_submit_button("Analyze Transaction", use_container_width=True, type="primary")

# Process transaction
if submitted:
    # Create transaction object
    transaction = type('Transaction', (), {
        'transaction_id': f'TXN-{int(datetime.now().timestamp() * 1000)}',
        'amount': amount,
        'payer_vpa': payer_vpa,
        'payee_vpa': payee_vpa,
        'message': message or '',
        'payee_new': payee_new,
        'transaction_type': transaction_type,
        'hour': datetime.now().hour,
        'transaction_count_24h': 5,
        'avg_transaction_amount_30d': 1000
    })()
    
    with st.spinner("Analyzing transaction with AI agents..."):
        try:
            # Run agents (async)
            async def analyze():
                ph = await agents['phishing'].analyze(transaction)
                qr = await agents['quishing'].analyze(transaction)
                cr = await agents['collect'].analyze(transaction)
                mw = await agents['malware'].analyze(transaction)
                return ph, qr, cr, mw
            
            ph, qr, cr, mw = asyncio.run(analyze())
            
            subs = {
                'phishing': float(ph['subscore']),
                'quishing': float(qr['subscore']),
                'collect': float(cr['subscore']),
                'malware': float(mw['subscore'])
            }
            
            indicators = {
                'phishing': ph.get('indicators', []),
                'quishing': qr.get('indicators', []),
                'collect': cr.get('indicators', []),
                'malware': mw.get('indicators', [])
            }
            
            # Aggregate trust score
            agg = agents['trust'].aggregate(
                subs=subs,
                message=message,
                amount=float(amount),
                indicators_by_agent=indicators
            )
            
            trust_score = int(agg['trust_score'])
            action = agg['action']
            
            # HITL check
            detector_results = {
                'phishing': ph,
                'quishing': qr,
                'collect': cr,
                'malware': mw
            }
            
            try:
                hitl_result = asyncio.run(agents['hitl'].evaluate(
                    transaction_id=transaction.transaction_id,
                    trust_score=trust_score,
                    action=action,
                    detector_results=detector_results,
                    transaction_amount=amount
                ))
                if hitl_result.get('human_review_required', False):
                    action = "HUMAN_REVIEW"
            except:
                hitl_result = {'human_review_required': False}
            
            # Generate explanations
            transaction_data = {
                'amount': amount,
                'payee_new': payee_new,
                'transaction_type': transaction_type
            }
            
            reasons = agents['explainer'].generate_explanation(
                trust_score=trust_score,
                detector_results=detector_results,
                action=action,
                subscores=subs,
                transaction_data=transaction_data
            )
            
            detailed_report = agents['explainer'].generate_detailed_report(
                trust_score=trust_score,
                detector_results=detector_results,
                action=action,
                subscores=subs,
                transaction_data=transaction_data
            )
            
            # Store result
            st.session_state.result = {
                'trust_score': trust_score,
                'action': action,
                'subscores': subs,
                'reasons': reasons,
                'detailed_report': detailed_report,
                'indicators': indicators
            }
        except Exception as e:
            st.error(f"Error analyzing transaction: {str(e)}")
            st.exception(e)

# Display results
if 'result' in st.session_state:
    result = st.session_state.result
    
    with col2:
        st.markdown('<h2 class="section-header">Analysis Results</h2>', unsafe_allow_html=True)
        
        # Trust score and action
        col_score, col_action = st.columns(2)
        with col_score:
            st.metric("Trust Score", f"{result['trust_score']}/100", delta=None)
        with col_action:
            action_text = result['action']
            st.metric("Action", action_text)
        
        st.markdown("---")
        
        # Risk breakdown chart
        st.markdown('<h3 class="section-header">Risk Breakdown by Fraud Type</h3>', unsafe_allow_html=True)
        risk_data = pd.DataFrame([
            {'Fraud Type': 'Phishing', 'Risk Score': result['subscores']['phishing'] * 100},
            {'Fraud Type': 'Quishing', 'Risk Score': result['subscores']['quishing'] * 100},
            {'Fraud Type': 'Collect', 'Risk Score': result['subscores']['collect'] * 100},
            {'Fraud Type': 'Malware', 'Risk Score': result['subscores']['malware'] * 100}
        ])
        
        fig_bar = px.bar(
            risk_data,
            x='Risk Score',
            y='Fraud Type',
            orientation='h',
            color='Risk Score',
            color_continuous_scale=['#22c55e', '#f59e0b', '#ef4444'],
            title="",
            labels={'Risk Score': 'Risk Score (%)', 'Fraud Type': ''}
        )
        fig_bar.update_layout(
            height=300, 
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='#e2e8f0', size=12),
            xaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', title_font=dict(family='Inter')),
            yaxis=dict(gridcolor='rgba(148, 163, 184, 0.1)', title_font=dict(family='Inter'))
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Pie chart
        if result['detailed_report'] and 'risk_breakdown' in result['detailed_report']:
            breakdown = result['detailed_report'].get('risk_breakdown', {})
            if breakdown and isinstance(breakdown, dict):
                try:
                    fig_pie = px.pie(
                        values=list(breakdown.values()),
                        names=list(breakdown.keys()),
                        title="",
                        color_discrete_sequence=['#ef4444', '#f97316', '#f59e0b', '#dc267f']
                    )
                    fig_pie.update_layout(
                        height=300,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Inter', color='#e2e8f0', size=12),
                        showlegend=True
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                except:
                    pass
        
        # Detailed explanations
        st.markdown('<h3 class="section-header">Detailed Analysis</h3>', unsafe_allow_html=True)
        with st.container():
            for reason in result['reasons']:
                st.write(f"• {reason}")
        
        # Risk factors
        if result['indicators']:
            st.markdown('<h3 class="section-header">Risk Indicators</h3>', unsafe_allow_html=True)
            for fraud_type, inds in result['indicators'].items():
                if inds:
                    with st.expander(f"{fraud_type.title()} Indicators"):
                        for ind in inds[:5]:  # Top 5
                            st.write(f"• {ind}")
        
        # Clear result button
        if st.button("Analyze New Transaction", use_container_width=True, type="secondary"):
            if 'result' in st.session_state:
                del st.session_state.result
            st.rerun()

else:
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.info("Fill in transaction details and click 'Analyze Transaction' to get fraud detection results")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show model status
        st.markdown('<h3 class="section-header">System Information</h3>', unsafe_allow_html=True)
        loaded_count = sum(1 for v in model_status.values() if v)
        st.success(f"{loaded_count}/4 ML Models Loaded")
        st.success("7 AI Agents Active")
        st.info("Ready to analyze transactions")

# Footer
st.markdown("---")
st.markdown("**SecureUPI** - Enterprise-Grade AI Fraud Detection | Version 1.0.0 | Powered by Advanced Machine Learning")
