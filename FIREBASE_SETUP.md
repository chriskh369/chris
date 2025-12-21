# Firebase Push Notifications Setup for StudyHub

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"** (or "Add project")
3. Enter project name: `StudyHub-Push`
4. Disable Google Analytics (not needed)
5. Click **Create Project**

## Step 2: Add Web App

1. In your new project, click the **Web icon** (</>)
2. Register app with nickname: `StudyHub Web`
3. **Copy the firebaseConfig** - you'll need these values:
   ```javascript
   const firebaseConfig = {
     apiKey: "your-api-key",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-project.appspot.com",
     messagingSenderId: "your-sender-id",
     appId: "your-app-id"
   };
   ```

## Step 3: Enable Cloud Messaging

1. Go to **Project Settings** (gear icon)
2. Click **Cloud Messaging** tab
3. Under "Web Push certificates", click **Generate key pair**
4. Copy the **Key pair** (this is the VAPID key)

## Step 4: Give me the config

Send me:
1. The `firebaseConfig` object
2. The VAPID key (Web Push certificate key pair)

I will update the code with your real Firebase credentials!

---

## What Firebase Gives You (FREE):

- ✅ Push notifications even when app is closed
- ✅ Works on Android Chrome
- ✅ Works on Windows/Mac browsers
- ❌ iOS Safari still doesn't support web push (Apple limitation)

## Pricing

Firebase Cloud Messaging is **completely FREE** with no limits on notifications!
