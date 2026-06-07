# Google Credentials Setup — Annai Illam

This guide walks you through creating the Google OAuth client IDs and Maps API key needed for the Annai Illam mobile app.

---

## Before You Start

You will need:
- A Google account with access to [Google Cloud Console](https://console.cloud.google.com)
- The app's **bundle identifiers** (provided below)

---

## App Details

| Field | Value |
|---|---|
| App Name | Annai Illam |
| iOS Bundle ID | `com.annaiillam` |
| Android Package Name | `com.annaiillam` |

---

## Step 1 — Create or Select a Google Cloud Project

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top and select **New Project**
3. Name it `Annai Illam` and click **Create**
4. Make sure this project is selected before continuing

---

## Step 2 — Enable Required APIs

1. In the left sidebar go to **APIs & Services → Library**
2. Search for and enable each of the following:
   - **Google Sign-In** (or "Identity Toolkit API")
   - **Maps SDK for Android**
   - **Maps SDK for iOS**
   - **Geocoding API** *(optional but recommended)*

---

## Step 3 — Configure the OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Select **External** and click **Create**
3. Fill in:
   - **App name**: `Annai Illam`
   - **User support email**: your support email
   - **Developer contact email**: your email
4. Click **Save and Continue** through the remaining steps (scopes and test users can be left as default for now)

---

## Step 4 — Create the OAuth Client IDs

Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**

### 4a — Web Client ID

| Field | Value |
|---|---|
| Application type | **Web application** |
| Name | `Annai Illam Web` |
| Authorised JavaScript origins | Your production domain (e.g. `https://annaiillam.com`) |
| Authorised redirect URIs | Your production domain + `/auth/callback` |

Click **Create** and note the **Client ID** — it looks like:
`XXXXXXXXXX.apps.googleusercontent.com`

---

### 4b — iOS Client ID

| Field | Value |
|---|---|
| Application type | **iOS** |
| Name | `Annai Illam iOS` |
| Bundle ID | `com.annaiillam` |

Click **Create** and note the **Client ID**.

---

### 4c — Android Client ID

Android requires a **SHA-1 fingerprint** — a unique code that identifies the signing key used to build the app. Follow the steps below exactly. You do not need to understand what it means, just copy and paste it.

---

**Step 1 — Create an Expo account (if you don't have one)**

1. Go to [https://expo.dev](https://expo.dev) and click **Sign Up**
2. Create an account with your email

---

**Step 2 — Log in to Expo from the project folder**

Open a terminal inside the `apps/mobile-ui-lab` folder and run:
```
npx eas login
```
Enter your Expo email and password when asked.

---

**Step 3 — Get the SHA-1 fingerprint**

Still in the same terminal, run:
```
npx eas credentials
```

When it asks questions, answer like this:

| Question | Answer |
|---|---|
| Which platform? | **Android** |
| Which build profile? | **development** |
| What do you want to do? | **Set up a new keystore** (if first time) or **Display keystore credentials** |

After it runs, look for a line that says **SHA1 Fingerprint** — it looks like:
```
AB:CD:12:34:EF:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12
```
Copy that entire value including the colons.

> If you see **"Keystore not found"**, choose **"Set up a new keystore"** first, then run `eas credentials` again to view it.

---

**Step 4 — Enter it in Google Cloud Console**

Back in Google Cloud → **APIs & Services → Credentials → Create Credentials → OAuth client ID**:

| Field | Value |
|---|---|
| Application type | **Android** |
| Name | `Annai Illam Android` |
| Package name | `com.annaiillam` |
| SHA-1 certificate fingerprint | *(paste the SHA-1 you copied above)* |

Click **Create** and note the **Client ID**.

> **Note:** You will need to repeat Step 3–4 with **build profile = production** before submitting to the Play Store, as the production signing key is different.



---

## Step 5 — Create the Maps API Key

1. Go to **APIs & Services → Credentials → Create Credentials → API key**
2. A key is generated — click **Edit API key** (pencil icon)
3. **Name** it: `Annai Illam Maps`
4. Under **Application restrictions**, select:
   - **Android apps** for the Android key, or leave unrestricted for a shared key
5. Under **API restrictions**, select **Restrict key** and choose:
   - Maps SDK for Android
   - Maps SDK for iOS
   - Geocoding API *(if enabled)*
6. Click **Save**
7. Note the **API Key** — it looks like: `AIzaSy...`

> **Security tip**: Never commit the API key to source code or share it publicly. It should only be stored in environment config files (`.env`) or your CI/CD secret store.

---

## Step 6 — Share the Credentials

Once all credentials are created, please share the following securely (e.g. via a password manager or encrypted message):

| Credential | Key/ID |
|---|---|
| Web Client ID | `______.apps.googleusercontent.com` |
| iOS Client ID | `______.apps.googleusercontent.com` |
| Android Client ID | `______.apps.googleusercontent.com` |
| Maps API Key | `AIzaSy______` |

---

## Summary of Credentials Needed

| Credential | Used For |
|---|---|
| Web Client ID | Google Sign-In on web / backend token validation |
| iOS Client ID | Google Sign-In on iPhone/iPad |
| Android Client ID | Google Sign-In on Android devices |
| Maps API Key | Displaying maps and geocoding in the app |

---

*If you have any questions or run into issues at any step, please reach out and we can assist.*

---

## Gmail App Password — Invoice Emails

The platform sends payment invoice emails via Gmail SMTP. A **Google App Password** is a 16-character one-time password that lets the backend authenticate with Gmail without storing your main account password.

> **Prerequisite**: The Gmail account must have **2-Step Verification** turned on. App Passwords are not available without it.

### How to Create an App Password

1. Sign in to the Gmail account you want to use (e.g. `test@gmail.com`)
2. Go to your Google Account settings: [https://myaccount.google.com](https://myaccount.google.com)
3. In the left sidebar click **Security**
4. Under "How you sign in to Google", click **2-Step Verification** and make sure it is **On**
5. Scroll to the bottom of the 2-Step Verification page and click **App passwords**
   *(If you don't see "App passwords", search for it in the Google Account search bar)*
6. In the "App name" field type a recognisable name, e.g. `Annai Illam Backend`
7. Click **Create**
8. Google shows a **16-character password** in a yellow box — copy it now (it is shown only once)

### Add It to the Backend `.env`

Open `apps/backend/.env` and set:

```env
GMAIL_USER=your-gmail-address@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

> The password can be entered with or without the spaces Google displays — both work.

### How It Is Used

When a client payment is confirmed (via Razorpay or admin approval), the backend calls `send_payment_invoice()` in `app/services/email_service.py`. If `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set, it connects to `smtp.gmail.com:587` with STARTTLS and sends the styled HTML invoice email.

### Troubleshooting

| Problem | Fix |
|---|---|
| `SMTPAuthenticationError` | App Password is wrong — regenerate one and update `.env` |
| App passwords option not visible | Enable 2-Step Verification first |
| Emails land in spam | Ask the recipient to mark as "Not spam"; consider a custom domain via Resend for production |
| Want to use a different sender name | Change `RESEND_FROM_NAME` in `.env` — this controls the "From" display name |

---

## OTP SMS Setup — Fast2SMS (DLT Route)

The backend sends login OTPs via **Fast2SMS**. For production, TRAI requires all commercial SMS senders in India to be registered on the **DLT (Distributed Ledger Technology)** portal. Without this, telecom operators will silently block your messages.

> **Timeline: Allow 7–14 business days** to complete DLT registration before go-live.

### Step 1 — Register on a DLT Portal

Any TRAI-approved DLT portal works. The most commonly used is Airtel's:

1. Go to [https://www.airtel.in/business/commercial-communication/home](https://www.airtel.in/business/commercial-communication/home)
   *(Alternatives: [Vi DLT](https://vilpower.in), [Jio DLT](https://trueconnect.jio.com), [BSNL DLT](https://www.ucc.dot.gov.in))*
2. Click **Register** and choose entity type:
   - **Enterprise** if registering as a company
   - **Individual** if registering as a sole trader / individual
3. Fill in your business details:
   - Company/entity name
   - PAN number
   - GST number (if applicable)
   - Registered address
   - Authorised signatory details
4. Upload required documents:
   - GST certificate or PAN card
   - Business registration certificate (if company)
   - Address proof
5. Submit — approval typically takes **3–5 business days**
6. Once approved you receive a **Principal Entity ID** — save this

### Step 2 — Register Your Sender ID (Header)

The Sender ID is the name that appears on the recipient's phone instead of a number (e.g. `ANNAIL`).

1. In the DLT portal go to **Sender ID → Register New**
2. Enter a 6-character alphanumeric ID, e.g. `ANNAIL`
3. Select **Transactional** category (OTPs fall under transactional)
4. Submit — approval takes **1–3 business days**

### Step 3 — Register Your OTP Message Template

All SMS templates must be pre-approved. The OTP template used by the backend is:

```
Your Annai Illam verification code is {#var#}. Valid for 10 minutes. Do not share with anyone.
```

1. In the DLT portal go to **Message Template → Register New**
2. Select **Transactional** category
3. Paste the template above (use `{#var#}` exactly where the OTP code goes)
4. Submit — approval takes **1–2 business days**
5. Once approved you receive a **Template ID** — save this

### Step 4 — Get Your Fast2SMS API Key

1. Create an account at [https://www.fast2sms.com](https://www.fast2sms.com)
2. Complete KYC verification (PAN/Aadhaar)
3. In the dashboard go to **Dev API → API Key** and copy it
4. Under **DLT Settings** in your Fast2SMS account, enter your:
   - Principal Entity ID (from Step 1)
   - Sender ID (from Step 2)
   - Template ID (from Step 3)

### Step 5 — Add to Backend `.env`

```env
SMS_PROVIDER=fast2sms
FAST2SMS_API_KEY=your_api_key_here
```

Restart the backend. OTP SMS will now be delivered via your registered DLT sender ID.

### Quick-Route (Dev/Testing Only)

Fast2SMS also has a **Quick SMS** route that skips DLT — useful during development. Just sign up, copy the API key, and set `SMS_PROVIDER=fast2sms`. OTPs will arrive but from a generic shared sender number. **Do not use this in production** — messages may be blocked by carriers.

---

## OTP via WhatsApp Business (Optional)

As an alternative to SMS, OTPs can be delivered over WhatsApp. This requires a **WhatsApp Business API** account through Meta.

> The backend does not yet have a WhatsApp OTP path built in. This section covers how to get the account set up so it can be integrated when needed.

### Step 1 — Create a Meta Business Account

1. Go to [https://business.facebook.com](https://business.facebook.com)
2. Click **Create Account** and fill in your business name, your name, and business email
3. Verify your email address
4. Go to **Business Settings → Business Info** and fill in your full business details
5. Submit for **Meta Business Verification** — upload:
   - Business registration certificate or GST certificate
   - Utility bill or bank statement showing the business address
6. Verification takes **2–7 business days**

### Step 2 — Set Up WhatsApp Business API

1. In Meta Business Settings go to **Accounts → WhatsApp accounts**
2. Click **Add** and follow the prompts to link a **dedicated phone number**
   - This number cannot be used for personal WhatsApp — use a new SIM or VoIP number
   - The number will be verified via a one-time call or SMS from Meta
3. Once the number is added, go to [https://developers.facebook.com](https://developers.facebook.com) and create a new app with **WhatsApp** as the product
4. Under **WhatsApp → API Setup**, note your:
   - **Phone Number ID**
   - **WhatsApp Business Account ID**
   - **Temporary Access Token** (generate a permanent token for production)

### Step 3 — Register an OTP Message Template

WhatsApp requires all templates to be pre-approved by Meta.

1. In Meta Business Manager go to **WhatsApp Manager → Message Templates → Create Template**
2. Category: **Authentication**
3. Template name: e.g. `annai_illam_otp`
4. Language: **English**
5. Body: `Your Annai Illam verification code is {{1}}. Valid for 10 minutes.`
6. Add a **Copy Code** button (Meta's recommended pattern for OTP)
7. Submit — approval usually takes **24–48 hours**
8. Once approved, note the **Template Name** and **Language Code** (`en`)

### Using a BSP Instead (Easier)

If the Meta direct API feels complex, use a **Business Solution Provider (BSP)**. They handle the API integration and give you a simpler dashboard:

| BSP | Free tier | Notes |
|---|---|---|
| [Interakt](https://www.interakt.shop) | 14-day trial | Popular in India, good dashboard |
| [WATI](https://www.wati.io) | No free tier | Enterprise-focused |
| [Gupshup](https://www.gupshup.io) | Pay-per-message | Larger scale |

With a BSP, you still need to complete Steps 1–3 above, but the BSP walks you through it and provides their own API credentials for your backend to call.


