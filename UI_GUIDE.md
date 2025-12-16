# Fieldmap UI Guide

## Expected User Experience

### 1. About Page (Not Signed In)

**Layout**: Two-column layout, no header

**Left Column**:
```
[Logo Image - logo.png, 250px width]

Hello!

Welcome to Fieldmap.

A non-profit app to assist biomedical engineers with lab efficiency and documentation.

• 📸 Capture and annotate photos directly in your browser
• 📁 Organize images into sessions (albums)
• ☁️ Auto-sync to your Google Drive
• ✏️ Edits create new copies, originals stay untouched
• 🔐 Secure, private storage in your own Drive

[Sign in with Google]  <-- Big primary button
```

**Right Column**:
```
[biomedical.jpg image - full width, rounded corners, shadow]
```

**Sidebar**:
```
[Logo - logo.png]

Fieldmap
Documentation support for the cadaver lab.

Sections
ℹ️ Please sign in on the About page to access Fieldmap and Gallery.

○ About  <-- Selected
```

### 2. About Page (Signed In)

**Left Column**:
```
[Logo Image - logo.png, 250px width]

Hello!

Welcome to Fieldmap.

A non-profit app to assist biomedical engineers with lab efficiency and documentation.

• 📸 Capture and annotate photos directly in your browser
• 📁 Organize images into sessions (albums)
• ☁️ Auto-sync to your Google Drive
• ✏️ Edits create new copies, originals stay untouched
• 🔐 Secure, private storage in your own Drive

✅ Signed in as user@example.com

ℹ️ Use the sidebar to access Fieldmap and Gallery

[Sign Out]  <-- Secondary button
```

**Right Column**: Same biomedical.jpg image

**Sidebar**:
```
[Logo - logo.png]

Fieldmap
Documentation support for the cadaver lab.

Sections

● Fieldmap
○ Gallery
○ About  <-- All three options now available
```

### 3. OAuth Flow

**Step 1**: User clicks "Sign in with Google"
- Browser redirects to Google OAuth page
- User sees: "Fieldmap wants to access your Google Account"
- Permissions shown:
  - View your email address
  - Create files in Google Drive

**Step 2**: User clicks "Allow"
- Google redirects to `https://fieldmap.streamlit.app/oauth2callback?code=...&state=...`

**Step 3**: OAuth Callback Page
```
🔐 Completing sign in...

✅ Sign in successful!

ℹ️ Redirecting to Fieldmap...

[Click here to continue if not redirected automatically]
```

**Step 4**: Redirect back to main app (About page, now signed in)

### 4. Fieldmap Page

**Header**: Logo centered

**Session Section**:
```
Session

[Default ▼]  [New]  <-- Dropdown and button

----

Camera

[Camera input widget]
📷 Take a photo

✅ Photo saved! (ID: 1)

----

Last Photo

Notes/Comments:
[Text area for comments]

Edit Photo
ℹ️ Use the annotation tools below. Click Save to apply changes or Cancel to discard.

[MarkerJS 3 Editor Component]
```

**MarkerJS Tools**:
- ✏️ Freehand
- ➡️ Arrow
- ━ Line
- 🔤 Text
- ⭕ Circle (outline)
- ▭ Rectangle (outline)
- 💾 Save
- ✕ Cancel

### 5. Gallery Page

**Header**: Photo Gallery

**If Drive not initialized**:
```
⚠️ Gallery Unavailable

ℹ️ Google Drive storage is not initialized. This may happen if you just signed in. Please refresh the page.

[Refresh Page]  <-- Primary button
```

**Normal Gallery View**:
```
Photo Gallery

View Session: [All Sessions ▼]

ℹ️ 📱 Drag photos between sessions to organize them. Click a tile to view details.

📁 Default (2 photos)
[Draggable tiles in grid]
┌─────┐ ┌─────┐
│     │ │     │
│ IMG │ │ IMG │
│ #1  │ │ #2  │
└─────┘ └─────┘

📁 Session 2 (1 photo)
┌─────┐
│     │
│ IMG │
│ 📝#3│  <-- Annotated badge
└─────┘

✓ Photos reorganized! Drive folders updated.

----

Click a photo to view details:

📁 Default
[📷 #1] [📷 #2]

📁 Session 2
[📝 #3]

----

📸 Photo Details

Photo #3

[✕ Close Details]

Session: Session 2      Type: 📝 Edited
Time: 2024-12-16 15:30  Derived from: Photo #1

---

[Image preview]

[Download Photo (annotated)]

---

Notes/Comments:
[Text area with comment]

[Update Comment]

---

Add Annotations

[Edit Photo] [button would be here if original]

---

Move Photo

Move to session: [Select session ▼]

---

[🗑️ Delete Photo]
```

### 6. OAuth Callback Error States

**If state mismatch**:
```
❌ Invalid OAuth state - possible CSRF attack

ℹ️ Please close this page and try signing in again.
```

**If code missing**:
```
❌ No authorization code received

ℹ️ Please close this page and try signing in again.
```

**If exchange fails**:
```
❌ Failed to complete authentication

ℹ️ Please close this page and try signing in again.
```

## Color Scheme

- Primary Green: `#4CAF50`
- Background: `#f5f5f5`
- Cards: `#ffffff`
- Borders: `#e0e0e0`
- Text: `#1f1f1f`
- Secondary Text: `#666`

## Typography

- Hero Title: 3rem, bold
- Hero Greeting: 2rem, regular
- Body: 1.1rem
- Small: 0.85em

## Responsive Behavior

- Mobile: Single column layout on About page
- Desktop: Two-column layout on About page
- Gallery: Tiles wrap to fit screen width
- Max tiles per row: 8

## Key UX Principles

1. **No header on About page** - Clean, minimal design
2. **Direct OAuth** - No intermediate pages or manual auth buttons
3. **Only draggable tiles in Gallery** - No separate photo grid
4. **Clear feedback** - Success messages for all actions
5. **Gated access** - Must sign in to access Fieldmap and Gallery
