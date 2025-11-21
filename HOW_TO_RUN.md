# 🚀 How to Run the App - Step by Step

## Method 1: Using the Run Script (Easiest)

### For Windows (PowerShell):
1. Open Cursor IDE terminal
2. Navigate to project folder:
   ```powershell
   cd C:\Users\rohit\OneDrive\Desktop\AI_Projects\finanace
   ```
3. Run the script:
   ```powershell
   .\run_app.ps1
   ```

### For Windows (Command Prompt):
1. Double-click `run_app.bat` file
2. Or run in terminal:
   ```cmd
   run_app.bat
   ```

---

## Method 2: Manual Run (If script doesn't work)

### Step 1: Open Terminal in Cursor IDE
- Press `` Ctrl + ` `` (backtick) to open terminal
- Or go to: Terminal → New Terminal

### Step 2: Navigate to Server Directory
```powershell
cd C:\Users\rohit\OneDrive\Desktop\AI_Projects\finanace\server
```

### Step 3: Run the App
```powershell
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**OR if python doesn't work, try:**
```powershell
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**OR if you have uvicorn installed globally:**
```powershell
uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## Step 4: Access the App

Once you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Open your browser and go to:**
- http://localhost:8000
- OR http://127.0.0.1:8000

---

## Common Errors & Solutions

### Error 1: "python is not recognized"
**Solution:**
```powershell
# Try python3 instead
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000

# Or use full path to Python
# Find Python path first:
where python
```

### Error 2: "No module named 'uvicorn'"
**Solution:**
```powershell
# Install uvicorn
pip install uvicorn

# Or install all requirements
pip install -r requirements.txt
```

### Error 3: "No module named 'fastapi'"
**Solution:**
```powershell
# Install all requirements
pip install -r requirements.txt
```

### Error 4: "ModuleNotFoundError: No module named 'server'"
**Solution:**
- Make sure you're in the `server` directory
- Or run from project root:
  ```powershell
  cd C:\Users\rohit\OneDrive\Desktop\AI_Projects\finanace
  python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
  ```

### Error 5: "Port 8000 already in use"
**Solution:**
- Use a different port:
  ```powershell
  uvicorn app:app --host 0.0.0.0 --port 8001
  ```
- Or close the app using port 8000

---

## Quick Test Commands

### Test if app is running:
```powershell
# In browser: http://localhost:8000
# Or in terminal:
curl http://localhost:8000
```

### Test health endpoint:
```powershell
curl http://localhost:8000/health
```

---

## Complete Step-by-Step (Copy & Paste)

```powershell
# 1. Navigate to project
cd C:\Users\rohit\OneDrive\Desktop\AI_Projects\finanace

# 2. Go to server directory
cd server

# 3. Install dependencies (if not installed)
pip install -r ..\requirements.txt

# 4. Run the app
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## What You Should See

When it works, you'll see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
Loading ML models...
PhishingAgent: Model loaded successfully
QuishingAgent: Model loaded successfully
CollectRequestAgent: Model loaded successfully
MalwareAgent: Model loaded successfully
All models loaded successfully!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Then open: **http://localhost:8000** in your browser!

---

## Still Not Working?

1. **Check Python is installed:**
   ```powershell
   python --version
   ```

2. **Check if you're in the right directory:**
   ```powershell
   pwd
   # Should show: ...\finanace\server
   ```

3. **Check if app.py exists:**
   ```powershell
   dir app.py
   ```

4. **Install all requirements:**
   ```powershell
   cd ..
   pip install -r requirements.txt
   cd server
   ```

5. **Try running Python directly:**
   ```powershell
   python app.py
   ```

---

## Need More Help?

Share the exact error message you're seeing, and I'll help you fix it!


