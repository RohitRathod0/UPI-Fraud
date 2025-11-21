# Streamlit Cloud packages.txt Fix

## Problem
Streamlit Cloud is trying to install comment text as packages, causing deployment to fail.

## Solution
The `packages.txt` file must contain **ONLY package names**, one per line, with **NO comments**.

### Current Issue
If your `packages.txt` on GitHub has comments like:
```
# System packages for Streamlit Cloud
# This is optional but can help with certain dependencies
libgl1-mesa-glx
libglib2.0-0
```

Streamlit Cloud's apt-get will try to install "#", "System", "packages", etc. as packages, causing errors.

### Fixed Version
Your `packages.txt` should look like this (NO comments):

```
libgl1-mesa-glx
libglib2.0-0
```

## Steps to Fix

1. **Ensure your local `packages.txt` has no comments:**
   ```bash
   # Check the file
   cat packages.txt
   ```

2. **If it has comments, remove them:**
   - Open `packages.txt`
   - Remove all lines starting with `#`
   - Keep only package names, one per line

3. **Commit and push:**
   ```bash
   git add packages.txt
   git commit -m "Fix packages.txt - remove comments"
   git push origin main
   ```

4. **Redeploy on Streamlit Cloud**
   - Streamlit Cloud will automatically redeploy
   - Check logs to confirm it works

## Verification
After pushing, check Streamlit Cloud logs. You should see:
```
✅ Apt dependencies were installed successfully
```

Instead of:
```
❌ E: Unable to locate package #
```

## Optional Packages
If you need additional system packages later, add them one per line:
```
libgl1-mesa-glx
libglib2.0-0
libsm6
libxext6
```

**Remember: NO comments, NO blank lines with text, ONLY package names!**

