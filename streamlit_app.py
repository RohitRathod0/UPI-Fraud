"""
Streamlit App for UPI Fraud Detection
Uses trained models for prediction only
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

# Add server directory to path
server_dir = Path(__file__).parent / "server"
sys.path.insert(0, str(server_dir))

# Import agents
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
    page_title="SecureUPI - Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #5b6ee1, #7c4bd8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
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
    .metric-card {
        background: #0f172a;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #1e293b;
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
    """Load ML models (cached)"""
    try:
        # Determine model directory
        model_dir = server_dir / "models"
        if not model_dir.exists():
            model_dir = Path("server/models")
        
        st.info(f"Loading models from: {model_dir}")
        
        # Initialize agents
        agents = {
            'phishing': PhishingAgent(model_path=str(model_dir / 'phishing_detector.pkl')),
            'quishing': QuishingAgent(model_path=str(model_dir / 'qr_detector.pkl')),
            'collect': CollectRequestAgent(model_path=str(model_dir / 'collect_detector.pkl')),
            'malware': MalwareAgent(model_path=str(model_dir / 'malware_detector.pkl')),
            'trust': TrustScoreAgent(),
            'explainer': ExplainerAgent(),
            'hitl': HITLManagerAgent()
        }
        
        # Load models
        agents['phishing'].load_model()
        agents['quishing'].load_model()
        agents['collect'].load_model()
        agents['malware'].load_model()
        
        return agents, True
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")
        return None, False

# Load models
if not st.session_state.models_loaded:
    with st.spinner("Loading ML models... This may take a moment."):
        agents, success = load_models()
        if success:
            st.session_state.agents = agents
            st.session_state.models_loaded = True
            st.success("✅ All models loaded successfully!")
        else:
            st.error("❌ Failed to load models. Please check model files.")
            st.stop()

agents = st.session_state.agents

# Header
st.markdown('<h1 class="main-header">🛡️ SecureUPI</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered UPI Fraud Detection System")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("### Quick Test Scenarios")
    
    if st.button("🟢 Safe Transaction", use_container_width=True):
        st.session_state.preset = "safe"
    if st.button("🔴 Phishing Attack", use_container_width=True):
        st.session_state.preset = "phishing"
    if st.button("🟡 QR Scam", use_container_width=True):
        st.session_state.preset = "qr"
    if st.button("🟠 Collect Fraud", use_container_width=True):
        st.session_state.preset = "collect"
    
    st.markdown("---")
    st.markdown("### System Status")
    st.success("✅ All Models Loaded")
    st.info("🔄 Ready for Analysis")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Transaction Details")
    
    # Transaction form
    with st.form("transaction_form"):
        payer_vpa_input = st.text_input("Payer UPI ID", value=payer_vpa, help="Your UPI ID", key="payer_input")
        payee_vpa_input = st.text_input("Payee UPI ID", value=payee_vpa, help="Recipient UPI ID", key="payee_input")
        amount_input = st.number_input("Amount (₹)", min_value=1.0, value=amount, step=100.0, key="amount_input")
        transaction_type_input = st.selectbox("Transaction Type", ["pay", "qr_pay", "collect"], 
                                             index=["pay", "qr_pay", "collect"].index(transaction_type) if transaction_type in ["pay", "qr_pay", "collect"] else 0,
                                             key="type_input")
        payee_new_input = st.selectbox("Is Payee New?", [0, 1], index=payee_new, format_func=lambda x: "Yes" if x == 1 else "No", key="new_input")
        message_input = st.text_area("Transaction Message", value=message, help="Transaction note/message", key="message_input")
        
        submitted = st.form_submit_button("🔍 Analyze Transaction", use_container_width=True, type="primary")
        
        # Use form values
        payer_vpa = payer_vpa_input
        payee_vpa = payee_vpa_input
        amount = amount_input
        transaction_type = transaction_type_input
        payee_new = payee_new_input
        message = message_input

# Handle presets - set default values
if 'preset' in st.session_state and st.session_state.preset:
    preset = st.session_state.preset
    if preset == "safe":
        payer_vpa = "user@paytm"
        payee_vpa = "grocery-store@paytm"
        amount = 450.0
        message = "Weekly groceries"
        payee_new = 0
        transaction_type = "pay"
        st.session_state.preset = None
    elif preset == "phishing":
        payer_vpa = "user@paytm"
        payee_vpa = "verify-security@upi"
        amount = 15000.0
        message = "URGENT! Account locked. Verify PIN at http://fake-bank.com"
        payee_new = 1
        transaction_type = "pay"
        st.session_state.preset = None
    elif preset == "qr":
        payer_vpa = "user@paytm"
        payee_vpa = "prize-claim@paytm"
        amount = 19999.0
        message = "Scan QR to claim ₹50,000 prize at http://bit.ly/win"
        payee_new = 1
        transaction_type = "qr_pay"
        st.session_state.preset = None
    elif preset == "collect":
        payer_vpa = "user@paytm"
        payee_vpa = "legal-dept@upi"
        amount = 12000.0
        message = "FINAL NOTICE: Pay dues immediately or legal action"
        payee_new = 1
        transaction_type = "collect"
        st.session_state.preset = None
    else:
        # Default values if no preset
        payer_vpa = st.session_state.get('payer_vpa', 'user@paytm')
        payee_vpa = st.session_state.get('payee_vpa', 'merchant@upi')
        amount = st.session_state.get('amount', 1000.0)
        message = st.session_state.get('message', 'Payment for services')
        payee_new = st.session_state.get('payee_new', 1)
        transaction_type = st.session_state.get('transaction_type', 'pay')
else:
    # Default values
    payer_vpa = st.session_state.get('payer_vpa', 'user@paytm')
    payee_vpa = st.session_state.get('payee_vpa', 'merchant@upi')
    amount = st.session_state.get('amount', 1000.0)
    message = st.session_state.get('message', 'Payment for services')
    payee_new = st.session_state.get('payee_new', 1)
    transaction_type = st.session_state.get('transaction_type', 'pay')

# Process transaction
if submitted or 'result' in st.session_state:
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
        
        with st.spinner("🔍 Analyzing transaction with AI agents..."):
            # Run agents (async)
            try:
                async def analyze():
                    ph = await agents['phishing'].analyze(transaction)
                    qr = await agents['quishing'].analyze(transaction)
                    cr = await agents['collect'].analyze(transaction)
                    mw = await agents['malware'].analyze(transaction)
                    return ph, qr, cr, mw
                
                ph, qr, cr, mw = asyncio.run(analyze())
            except Exception as e:
                st.error(f"Error analyzing transaction: {str(e)}")
                st.stop()
            
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
            except Exception as e:
                # If HITL fails, continue without it
                hitl_result = {'human_review_required': False}
                st.warning(f"HITL check failed: {str(e)}")
            
            if hitl_result['human_review_required']:
                action = "HUMAN_REVIEW"
            
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
    
    # Display results
    if 'result' in st.session_state:
        result = st.session_state.result
        
        with col2:
            st.header("📊 Analysis Results")
            
            # Trust score and action
            col_score, col_action = st.columns(2)
            with col_score:
                risk_class = "risk-low" if result['trust_score'] >= 65 else "risk-medium" if result['trust_score'] >= 45 else "risk-high"
                st.metric("Trust Score", f"{result['trust_score']}/100", delta=None)
            with col_action:
                action_colors = {
                    "ALLOW": "🟢",
                    "WARN": "🟡",
                    "BLOCK": "🔴",
                    "HUMAN_REVIEW": "🟠"
                }
                st.metric("Action", f"{action_colors.get(result['action'], '⚪')} {result['action']}")
            
            st.markdown("---")
            
            # Risk breakdown chart
            st.subheader("Risk Breakdown by Fraud Type")
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
                title="Risk Score by Fraud Type (%)"
            )
            fig_bar.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Pie chart
            if result['detailed_report'] and 'risk_breakdown' in result['detailed_report']:
                breakdown = result['detailed_report']['risk_breakdown']
                if breakdown:
                    fig_pie = px.pie(
                        values=list(breakdown.values()),
                        names=list(breakdown.keys()),
                        title="Risk Distribution"
                    )
                    fig_pie.update_layout(height=300)
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            # Detailed explanations
            st.subheader("📋 Detailed Analysis")
            for reason in result['reasons']:
                st.write(f"• {reason}")
            
            # Risk factors
            if result['indicators']:
                st.subheader("🚨 Risk Indicators")
                for fraud_type, inds in result['indicators'].items():
                    if inds:
                        with st.expander(f"{fraud_type.title()} Indicators"):
                            for ind in inds[:5]:  # Top 5
                                st.write(f"• {ind}")
        
        # Clear result button
        if st.button("🔄 Analyze New Transaction", use_container_width=True):
            if 'result' in st.session_state:
                del st.session_state.result
            st.rerun()

else:
    with col2:
        st.info("👈 Fill in transaction details and click 'Analyze Transaction' to get fraud detection results")
        
        # Show model status
        st.markdown("### System Information")
        st.success("✅ 4 ML Models Loaded")
        st.success("✅ 7 AI Agents Active")
        st.info("🔄 Ready to analyze transactions")

# Footer
st.markdown("---")
st.markdown("**SecureUPI** - AI-Powered Fraud Detection | Version 1.0.0")

