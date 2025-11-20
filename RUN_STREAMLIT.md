# 🚀 Run Streamlit App Locally

## Quick Start

### Step 1: Install Dependencies
```powershell
pip install streamlit plotly
```

Or install all requirements:
```powershell
pip install -r requirements.txt
```

### Step 2: Run the App
```powershell
cd C:\Users\rohit\OneDrive\Desktop\AI_Projects\finanace
streamlit run streamlit_app.py
```

### Step 3: Access the App
The app will automatically open in your browser at:
**http://localhost:8501**

---

## 🎯 What You'll See

1. **Main Interface:**
   - Transaction form on the left
   - Results panel on the right
   - Quick test buttons in sidebar

2. **Test Scenarios:**
   - Click any button in sidebar to test
   - Form auto-fills with test data
   - Click "Analyze Transaction" to see results

3. **Results:**
   - Trust score (0-100)
   - Action (ALLOW/WARN/BLOCK)
   - Risk breakdown charts
   - Detailed explanations

---

## ✅ Verify It Works

1. **Start the app**: `streamlit run streamlit_app.py`
2. **Click "🟢 Safe Transaction"** in sidebar
3. **Click "🔍 Analyze Transaction"**
4. **You should see**: Low risk (green), charts, explanations

---

## 🐛 Troubleshooting

### **Streamlit not found:**
```powershell
pip install streamlit
```

### **Models not loading:**
- Check if models are in `server/models/`
- Verify file paths

### **Import errors:**
- Make sure you're in project root
- Check if `server/agents/` files exist

---

## ☁️ After Testing Locally

Once it works locally:
1. Push to GitHub
2. Deploy on Streamlit Cloud
3. Share the URL!

**Ready to test! Run `streamlit run streamlit_app.py` 🚀**

