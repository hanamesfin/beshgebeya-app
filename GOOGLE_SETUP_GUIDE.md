# 🥬 Google Login Setup Guide

To enable **real Google accounts** for your BeshGebeya app, follow these 4 simple steps to get your API keys.

---

### Step 1: Create a Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click **Select a project** (top left) > **New Project**.
3. Name it `BeshGebeya` and click **Create**.

### Step 2: Configure Consent Screen
1. Go to **APIs & Services** > [**OAuth consent screen**](https://console.cloud.google.com/apis/credentials/consent).
2. Select **External** > **Create**.
3. Fill in:
   - **App name**: `BeshGebeya`
   - **User support email**: [Your Email]
   - **Developer contact info**: [Your Email]
4. Click **Save and Continue** until you reach the Dashboard.

### Step 3: Create Credentials
1. Go to **APIs & Services** > [**Credentials**](https://console.cloud.google.com/apis/credentials).
2. Click **+ Create Credentials** > **OAuth client ID**.
3. **Application type**: `Web application`.
4. **Authorized redirect URIs**: 
   - Click **+ Add URI** and paste exactly: `http://127.0.0.1:5000/auth/google/callback`
   - Click **+ Add URI** again and paste: `https://beshgebeya-app.onrender.com/auth/google/callback`
5. **Authorized JavaScript origins**:
   - Click **+ Add URI** and paste: `http://127.0.0.1:5000`
   - Click **+ Add URI** again and paste: `https://beshgebeya-app.onrender.com`
6. Click **Create**. A popup will show your **Client ID** and **Client Secret**.

### Step 4: Add to BeshGebeya
1. Open your [**.env**](file:///Users/janus/Downloads/beshgebeya-app-main-4/.env) file.
2. Paste your keys:
   ```env
   GOOGLE_CLIENT_ID=your_id_here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_secret_here
   ```
3. Restart your app: `python app.py`

---

> [!TIP]
> **Why do I need these keys?**
> Google uses these keys to verify that it is *your* specific app asking for login permission. It keeps your user data secure.
