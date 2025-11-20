# SecureUPI - Streamlit Deployment

## 🚀 Quick Start

This project is ready for deployment on Streamlit Cloud.

### **Deploy Now:**

1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `UPI-Fraud`
5. Main file: `streamlit_app.py`
6. Click "Deploy"

---

## 📋 What This App Does

**SecureUPI** is an enterprise-grade AI fraud detection system that:

- ✅ Detects phishing attempts in UPI transactions
- ✅ Identifies QR code scams (quishing)
- ✅ Prevents collect request fraud
- ✅ Detects malware-related transactions
- ✅ Provides real-time trust scores
- ✅ Visualizes risk breakdown with charts

---

## 🏗️ Architecture

- **4 ML Models**: XGBoost, Random Forest, Logistic Regression
- **7 AI Agents**: Specialized fraud detection agents
- **Real-time Analysis**: <200ms response time
- **Visual Dashboard**: Interactive charts and risk visualization

---

## 📁 Project Structure

```
├── streamlit_app.py          # Main Streamlit app
├── requirements.txt          # Dependencies
├── .streamlit/
│   └── config.toml          # Streamlit config
└── server/
    ├── models/              # ML models (.pkl files)
    └── agents/             # Agent modules
```

---

## 🔧 Local Development

### **Run Locally:**

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

App will open at: http://localhost:8501

---

## 📊 Features

- **Transaction Form** - Input transaction details
- **Quick Test Scenarios** - Pre-filled examples
- **Real-time Analysis** - Instant fraud detection
- **Visual Charts** - Risk breakdown visualization
- **Detailed Explanations** - Why transactions are risky/safe
- **Professional UI** - Clean, modern design

---

## 🎨 UI Design

- **Fonts**: Space Grotesk (headings), Inter (body)
- **Theme**: Dark mode with gradient accents
- **Colors**: Professional blue/purple gradient
- **Responsive**: Works on all screen sizes

---

## 📦 Dependencies

All dependencies are listed in `requirements.txt`:
- Streamlit
- Plotly
- Scikit-learn
- XGBoost
- LightGBM
- And more...

---

## ✅ Deployment Status

**Ready for Streamlit Cloud!**

All files are prepared and tested. Just deploy using the steps above.

---

## 📝 License

This project is for demonstration purposes.

---

## 🙏 Credits

Built with:
- Streamlit
- FastAPI (backend)
- XGBoost, Random Forest, Logistic Regression
- Advanced Machine Learning techniques

**Deploy now and protect millions of transactions! 🛡️**

