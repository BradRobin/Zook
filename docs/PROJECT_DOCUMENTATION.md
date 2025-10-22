# Zook Project - Complete Technical Documentation

**Version:** MVP Phase 1  
**Last Updated:** October 22, 2025  
**Status:** Active Development

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Backend - Authentication Server](#backend---authentication-server)
5. [Frontend - Web UI](#frontend---web-ui)
6. [MediaMTX Integration](#mediamtx-integration)
7. [Database Design](#database-design)
8. [User Flow & Authentication](#user-flow--authentication)
9. [Current Features](#current-features)
10. [Known Limitations](#known-limitations)
11. [Deployment & Setup](#deployment--setup)
12. [Future Roadmap](#future-roadmap)

---

## Project Overview

### Mission
Zook is an AI-powered surveillance platform designed to enhance safety and enforce discipline through real-time threat detection. The project leverages live camera feeds with AI analysis to detect harmful objects (knives, guns, weapons) and alert users.

### Vision: The 4D Watch System
A **4th-dimensional surveillance approach** where AI continuously monitors live feeds 24/7 across multiple environments:
- 🏫 Educational institutions (schools, academies)
- 🛒 Retail & commercial spaces (malls, supermarkets)
- 🚌 Transportation & logistics (matatu fleets, construction sites)
- 🛡️ Security services integration

### Core Philosophy
Transform communities into safer spaces where crime, violence, and abuse fade as people adapt to responsible behavior through transparency and accountability.

### Target Markets
- **Educational Institutions**: Private academies (Brookhouse, Alliance High School)
- **Retail**: Shopping malls (Two Rivers), supermarkets (Naivas)
- **Transportation**: Matatu fleet owners, construction sites
- **Security**: Security firms (G4S Kenya)

### Compliance
- ✅ Kenya Data Protection Act compliant
- ✅ Local processing with minimal data retention
- ✅ Clear consent mechanisms
- ✅ Ethical surveillance (safety enhancement, not overreach)

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         ZOOK PLATFORM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐      ┌──────────────────┐                  │
│  │   Web Browser   │─────▶│  Auth Server     │                  │
│  │  (Frontend UI)  │◀─────│  (Port 8080)     │                  │
│  │                 │      │  Go HTTP Server  │                  │
│  │  - HTML/CSS/JS  │      └──────────────────┘                  │
│  │  - Camera Feed  │               │                            │
│  │  - Detection UI │               │                            │
│  └─────────────────┘               ▼                            │
│          │                  ┌──────────────────┐                │
│          │                  │  In-Memory DB    │                │
│          │                  │  (Production:    │                │
│          │                  │   PostgreSQL)    │                │
│          │                  └──────────────────┘                │
│          │                                                       │
│          │                  ┌──────────────────┐                │
│          └─────────────────▶│  AI Detection    │                │
│                             │  (Port 8000)     │                │
│                             │  YOLOv12/FastAPI │                │
│                             └──────────────────┘                │
│                                                                  │
│                             ┌──────────────────┐                │
│                             │   MediaMTX       │                │
│                             │  WebRTC Server   │                │
│                             │  (Port 8889)     │                │
│                             └──────────────────┘                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Component Communication

1. **Frontend → Auth Server**: User authentication (login/signup)
2. **Frontend → AI Detection**: Camera frame analysis for threat detection
3. **Frontend → MediaMTX**: (Planned) WebRTC streaming
4. **Auth Server → Database**: User credential storage and retrieval
5. **MediaMTX → Auth Server**: (Planned) Stream access authentication

---

## Technology Stack

### Frontend
- **HTML5**: Semantic structure with modern best practices
- **CSS3**: Minimalist "calculator-like" design with monospace fonts
- **Vanilla JavaScript**: Zero dependencies, class-based architecture
- **Browser APIs**:
  - `getUserMedia()` for camera access
  - `Canvas API` for frame capture
  - `Fetch API` for backend communication
  - `localStorage` for client-side auth token storage

### Backend
- **Go 1.25.3**: High-performance HTTP server
- **Standard Library**: `net/http` for routing and server
- **Dependencies**:
  - `golang.org/x/crypto/bcrypt`: Password hashing
  - `github.com/golang-jwt/jwt/v5`: JWT token generation (planned)
  - `github.com/jackc/pgx/v5`: PostgreSQL driver (production)
  - `github.com/redis/go-redis/v9`: Token caching (planned)

### Infrastructure
- **MediaMTX**: WebRTC/RTSP streaming server
- **PostgreSQL**: Production database (schema defined)
- **Redis**: Token caching layer (planned)
- **FastAPI + YOLOv12**: AI detection service (integration pending)

### Development Tools
- **ngrok**: Remote testing tunnels (config in `config.yml`)
- **Go Modules**: Dependency management

---

## Backend - Authentication Server

### Project Structure
```
mediamtx_authserver/
├── main.go                      # Production server with CORS
├── simple_server.go             # Testing stub (always returns success)
├── simple_working_server.go     # Hardcoded test user (Brad/12345678)
├── authserver.exe              # Compiled binary
├── go.mod / go.sum             # Dependencies
│
├── auth_user/
│   ├── simple_auth.go          # Token management logic
│   └── types/
│       ├── actions.go          # Stream action constants
│       ├── error.go            # Custom error definitions
│       ├── login.go            # Login request/response types
│       ├── protocols.go        # Streaming protocol constants
│       ├── redistype.go        # Redis cache data structure
│       ├── request.go          # MediaMTX request validation types
│       └── signup.go           # User registration types
│
└── database/
    ├── memory_db.go            # In-memory user storage (MVP)
    └── postgres.sql            # PostgreSQL schema (production)
```

### Main Server (`main.go`)

**Port**: `8080`  
**Purpose**: Production-ready authentication server with full functionality

#### Endpoints

##### 1. `GET /` - Health Check
```http
GET / HTTP/1.1
Host: localhost:8080

Response:
{
  "status": "ok",
  "message": "Zook Auth Server Running"
}
```

##### 2. `POST /api/auth` - User Registration
```http
POST /api/auth HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepass123",
  "action": ["read", "publish"],
  "protocol": ["webrtc"]
}

Response (Success):
"successfully saved user"

Response (Error):
HTTP 400: "invalid json data"
HTTP 500: "user already exists"
```

**Process Flow**:
1. Decode JSON request body into `types.Signin` struct
2. Validate user doesn't already exist
3. Hash password using bcrypt (cost factor: 10)
4. Store user in database (in-memory or PostgreSQL)
5. Return success message

##### 3. `POST /api/login` - User Authentication
```http
POST /api/login HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepass123",
  "token": ""
}

Response (Success):
"successfully logged in"

Response (Error):
HTTP 401: "invalid credentials"
HTTP 500: "internal server error"
```

**Process Flow**:
1. Decode JSON request body into `types.Logindetails` struct
2. Query database for user by username
3. Compare hashed password using bcrypt
4. Generate and save user token to cache (simplified in MVP)
5. Return success message

#### CORS Configuration
```go
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

### Alternative Servers

#### `simple_server.go` - Testing Stub
- **Purpose**: Frontend development without backend logic
- **Behavior**: Always returns success (no validation)
- **Use Case**: UI/UX testing, frontend development

#### `simple_working_server.go` - Hardcoded Auth
- **Purpose**: Quick testing with known credentials
- **Test User**: `Brad` / `12345678`
- **Behavior**: String-based credential checking (no encryption)

### Database Layer

#### In-Memory Database (`memory_db.go`)

**Current Implementation**: MVP testing database

```go
// Global in-memory store
var users = make(map[string]types.Signin)
var mu sync.RWMutex  // Thread-safe access

// Default user (initialized on startup)
Username: "Brad"
Password: "$2a$10$..." (bcrypt hash of "12345678")
Action: ["read"]
Protocol: ["webrtc"]
```

**Key Functions**:

1. **`Add_user(user types.Signin)`**
   - Checks for duplicate usernames
   - Hashes password with bcrypt (cost: 10)
   - Stores user in memory map
   - Thread-safe with mutex locks

2. **`Get_user(user types.Logindetails)`**
   - Retrieves user by username
   - Validates password using bcrypt comparison
   - Returns full user object on success

#### PostgreSQL Schema (`postgres.sql`)

**Production Database Design**:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE streaming.users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    protocol TEXT[] NOT NULL,
    action TEXT[] NOT NULL
);
```

**Schema Notes**:
- UUID primary keys for distributed systems
- Array types for multi-protocol/multi-action support
- Password field stores bcrypt hashes (never plaintext)

### Type Definitions

#### User Types

**`types.Signin`** - User account structure
```go
type Signin struct {
    Id       string   `json:"id"`
    Username string   `json:"username"`
    Password string   `json:"password"`
    Action   []string `json:"action"`    // ["read", "publish", etc.]
    Protocol []string `json:"protocol"`  // ["webrtc", etc.]
}
```

**`types.Logindetails`** - Login request
```go
type Logindetails struct {
    Username string `json:"username"`
    Password string `json:"password"`
    Token    string `json:"token"`
}
```

#### Action Constants (`types/actions.go`)
```go
const (
    Publishaction  action = "publish"   // Stream publisher
    Readaction     action = "read"      // Stream viewer
    Playbackaction action = "playback"  // Recording playback
    Apiaction      action = "api"       // API access
    Metricsaction  action = "metrics"   // System metrics
    Pprofaction    action = "pprof"     // Profiling
)
```

#### Protocol Constants (`types/protocols.go`)
```go
const (
    webrtc protocol = "webrtc"  // Current: WebRTC only
)
```

#### MediaMTX Integration Types

**`types.UserRequest`** - MediaMTX validation request
```go
type UserRequest struct {
    Username string   `json:"username"`
    Token    string   `json:"token"`
    Id       string   `json:"id"`
    Path     string   `json:"path"`      // Stream path
    Action   []string `json:"action"`
    Protocol string   `json:"protocol"`
}
```

**`types.Redisstoretype`** - Token cache structure
```go
type Redisstoretype struct {
    Username string   `json:"username"`
    Id       string   `json:"userid"`
    Action   []string `json:"action"`
    Protocol []string `json:"protocol"`
    Path     []string `json:"path"`
}
```

### Error Handling

**Custom Errors** (`types/error.go`):
```go
var (
    Decodingusererror         = errors.New("There was an error decoding user values")
    Dbconnectionerror         = errors.New("Error in connecting to the database")
    Hashtooshort              = errors.New("the password is too short")
    Mismatchedhashandpassword = errors.New("incorrect password")
    Hashtoolong               = errors.New("the password is too long")
    Errorgeneratingpass       = errors.New("ther was an in issue in saving your password")
    Savingusererror           = errors.New("There was an error saving user")
    Errorsigningtoken         = errors.New("There was an error generating your token")
    Errorredisstore           = errors.New("there was an issue storing you on the cache")
)
```

### Security Features

1. **Password Hashing**: bcrypt with cost factor 10 (2^10 = 1024 rounds)
2. **Thread Safety**: Mutex locks for concurrent database access
3. **CORS Protection**: Configurable origin restrictions
4. **Input Validation**: JSON schema enforcement
5. **Error Masking**: Generic error messages to prevent information leakage

---

## Frontend - Web UI

### Project Structure
```
ui/src/
├── index.html    # Complete app structure (SPA)
├── style.css     # Minimalist monospace design
├── app.js        # Application logic (zero dependencies)
└── README.md     # Testing guide
```

### Design Philosophy

**Theme**: Ultra-minimalist "calculator-like" interface
- **Typography**: Monospace fonts (`Courier New`, `Roboto Mono`)
- **Colors**: Black (#000), White (#FFF), Gray (#666), Green (#0F0), Red (#F00)
- **Layout**: Maximum white space, clear visual hierarchy
- **Responsiveness**: Mobile-first with breakpoints at 768px and 480px

### Application States

#### 1. Landing Page
```
┌─────────────────────────────────────┐
│                                     │
│             ZOOK                    │
│                                     │
│   Live AI surveillance for safety.  │
│   Grant cam access to start.        │
│                                     │
│          ┌──────────┐              │
│          │   Scan   │              │
│          └──────────┘              │
│                                     │
│  Compliant with Kenya Data          │
│  Protection Act. Local processing.  │
│                                     │
│  Building discipline one scan       │
│  at a time.                         │
└─────────────────────────────────────┘
```

**Elements**:
- Large "Zook" title (4rem)
- Subtext explaining purpose
- Green outlined "Scan" button
- Legal compliance footer
- Philosophy tagline

#### 2. Login Modal
```
┌───────────────────────────────┐
│      Access Required          │
│                               │
│  Username: [____________]     │
│  Password: [____________]     │
│                               │
│  ☐ I consent to local cam     │
│    processing.                │
│                               │
│  [Authenticate] [Cancel]      │
└───────────────────────────────┘
```

**Features**:
- Modal overlay with backdrop blur
- Username/password inputs
- Mandatory consent checkbox
- Form validation
- Error message display
- Close on outside click or Cancel

#### 3. Dashboard View
```
┌─────────────────────────────────────────────────────┐
│  ┌──────────────────────┐  ┌───────────────────┐   │
│  │                      │  │  Detection Log    │   │
│  │   Live Feed Active   │  │                   │   │
│  │                      │  │  • Scanning...    │   │
│  │  [Video Feed Here]   │  │    No threats.    │   │
│  │                      │  │                   │   │
│  │                      │  │  • Camera feed    │   │
│  │                      │  │    active         │   │
│  └──────────────────────┘  └───────────────────┘   │
│                                                     │
│     [Pause Scan]  [Settings]                        │
└─────────────────────────────────────────────────────┘
```

**Layout**: 70% video / 30% status panel (vertical stack on mobile)

**Components**:
- Live camera feed with video element
- Status overlay ("Live Feed Active")
- Detection log with timestamps
- Control buttons (Pause/Settings)

#### 4. Settings Drawer
```
                     ┌───────────────────┐
                     │   Settings        │
                     │                   │
                     │  Alert Email:     │
                     │  [_____________]  │
                     │                   │
                     │  ☑ Detect Knives  │
                     │  ☐ Detect Guns    │
                     │  ☐ Detect Weapons │
                     │                   │
                     │     [Close]       │
                     └───────────────────┘
```

**Slides from right**: Fixed 300px width (full width on mobile)

### JavaScript Architecture

#### Class: `ZookApp`

**Properties**:
```javascript
{
  isScanning: boolean,           // Detection active state
  detectionInterval: timer,      // 5-second detection loop
  videoStream: MediaStream,      // Camera access object
  authToken: string,             // Stored auth token
  apiUrl: string                 // Backend URL (auto-detected)
}
```

**Key Methods**:

##### Initialization
```javascript
constructor()
  ├─ Auto-detect API URL (localhost or ngrok)
  ├─ Bind all event listeners
  └─ Check for stored authentication

init()
  ├─ bindEvents() - Attach UI handlers
  └─ checkStoredAuth() - Restore session
```

##### Authentication Flow
```javascript
handleAuth()
  ├─ Validate form inputs
  ├─ Check consent checkbox
  ├─ POST /api/login with credentials
  ├─ Store token in localStorage
  └─ Transition to dashboard

showLoginModal() / hideLoginModal()
  └─ Toggle modal visibility
```

##### Camera Management
```javascript
startCamera()
  ├─ Request getUserMedia({ video: { ideal: 1280x720 }})
  ├─ Attach stream to <video> element
  └─ Add log entry

destroy()
  ├─ Clear detection interval
  └─ Stop all video tracks
```

##### Detection System
```javascript
startScanning()
  └─ setInterval(simulateDetection, 5000)

simulateDetection()
  ├─ Capture video frame to canvas
  ├─ Convert to JPEG blob
  ├─ POST to http://localhost:8000/detect
  ├─ If API unavailable: simulateRandomDetection()
  └─ Handle threats if detected

handleThreatDetection(threats)
  ├─ Log threat with timestamp & confidence
  ├─ Trigger visual alert (red border pulse)
  └─ Update detection log
```

##### UI Interactions
```javascript
toggleScanning() - Pause/resume detection
toggleSettings() - Show/hide settings drawer
addLogEntry(message, type) - Append to log (max 10)
showError(message) - Display auth errors
```

### API Integration

#### Backend Connection

**Auto-Detection Logic**:
```javascript
if (localhost) {
  apiUrl = 'http://localhost:8080'
} else {
  apiUrl = localStorage or prompt for ngrok URL
}
```

**Authentication Request**:
```javascript
fetch(`${apiUrl}/api/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: username,
    password: password,
    token: ''
  })
})
```

**Error Handling**:
- `Failed to fetch` → "Cannot connect to server"
- `HTTP 401` → "Invalid username or password"
- `HTTP 400` → "Invalid credentials or request format"
- `HTTP 500` → "Server error. Please try again."

#### AI Detection Integration (Planned)

**Frame Capture & Send**:
```javascript
// Capture video frame
const canvas = document.createElement('canvas');
const video = document.getElementById('feed');
canvas.getContext('2d').drawImage(video, 0, 0);

// Convert to blob
const blob = await new Promise(resolve => 
  canvas.toBlob(resolve, 'image/jpeg', 0.8)
);

// Send to AI service
const formData = new FormData();
formData.append('image', blob, 'frame.jpg');

const response = await fetch('http://localhost:8000/detect', {
  method: 'POST',
  body: formData
});
```

**Expected Response Format**:
```json
{
  "threats": [
    {
      "type": "knife",
      "confidence": 92,
      "timestamp": "2025-10-22T15:30:45Z"
    }
  ]
}
```

### Responsive Design

#### Desktop (> 768px)
- 70/30 split layout
- Full-size controls
- Side settings drawer

#### Tablet (768px - 480px)
- Vertical stack layout
- 60/40 video/logs ratio
- Full-width settings drawer
- Touch-friendly buttons

#### Mobile (< 480px)
- Font size reduction (14px base)
- Smaller title (2rem)
- Column layout for all elements
- Maximum touch targets (48px min)

### Browser Compatibility

✅ **Supported**:
- Chrome/Edge 90+ (recommended)
- Firefox 88+
- Safari 14+ (iOS/macOS)

⚠️ **Requirements**:
- Camera permissions
- LocalStorage enabled
- JavaScript enabled
- HTTPS for camera access (except localhost)

---

## MediaMTX Integration

### Configuration (`mediamtx.yml`)

**Purpose**: WebRTC streaming server for multi-client video distribution

#### Core Settings
```yaml
loglevel: info
logDestinations: [file]
logfile: mediamtx.log

readTimeout: 5s
writeTimeout: 5s
writeQueueSize: 512
udpMaxPayloadSize: 1472
```

#### Authentication
```yaml
authMethod: http
authHTTPAddress: http://localhost:8080/api/auth
authHTTPExclude: []
```

**Flow**: MediaMTX calls auth server before allowing stream access

#### WebRTC Configuration
```yaml
webrtc: yes
webrtcAddress: :8889
webrtcEncryption: no  # TODO: Enable for production
webrtcAllowOrigin: 'http://localhost:3500/api/viewstream'
webrtcLocalUDPAddress: :8189
webrtcLocalTCPAddress: ''
```

#### API Server
```yaml
api: yes
apiAddress: :9997
apiEncryption: no  # TODO: Enable for production
```

#### Stream Settings
```yaml
source: publisher
sourceOnDemand: yes
sourceOnDemandStartTimeout: 10s
sourceOnDemandCloseAfter: 10s
maxReaders: 0  # Unlimited viewers
```

### Integration Status

| Feature | Status | Notes |
|---------|--------|-------|
| Config file | ✅ Complete | Ready for use |
| Auth endpoint | ✅ Configured | Points to `:8080/api/auth` |
| WebRTC server | 🔄 Pending | Not started yet |
| Frontend integration | 📋 Planned | Phase 2 feature |

### Future Integration

**Planned Flow**:
1. User authenticates via `/api/login`
2. User receives JWT token
3. Frontend connects to MediaMTX WebRTC endpoint
4. MediaMTX validates token with auth server
5. If valid, stream access granted
6. Multiple viewers can watch same stream

---

## Database Design

### Current: In-Memory Storage

**Implementation**: Thread-safe Go map with mutex locks

**Structure**:
```go
map[string]types.Signin
// Key: username
// Value: user object with hashed password
```

**Pros**:
- Fast for MVP testing
- No external dependencies
- Simple setup

**Cons**:
- Data lost on restart
- Not scalable
- Single-instance only

### Production: PostgreSQL

**Schema** (defined, not yet implemented):
```sql
CREATE TABLE streaming.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,  -- bcrypt hash
    protocol TEXT[] NOT NULL,
    action TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON streaming.users(username);
```

**Migration Path**:
1. Replace `memory_db.go` imports
2. Implement `database/postgres.go` with pgx driver
3. Update `Add_user()` and `Get_user()` to use SQL queries
4. Add connection pooling

### Token Cache: Redis (Planned)

**Purpose**: Store active session tokens with expiration

**Structure**:
```
Key: "<token>"
Value: {
  "username": "john_doe",
  "userid": "uuid",
  "action": ["read", "publish"],
  "protocol": ["webrtc"],
  "path": ["/stream1"]
}
TTL: 24 hours
```

**Benefits**:
- Fast token validation
- Automatic expiration
- Distributed sessions

---

## User Flow & Authentication

### Registration Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. POST /api/auth
       │    { username, password, action, protocol }
       ▼
┌─────────────┐
│ Auth Server │
└──────┬──────┘
       │ 2. Validate input
       │
       │ 3. Check if user exists
       ▼
┌─────────────┐
│  Database   │ ◀─ 4. Store user (if new)
└──────┬──────┘
       │ 5. Hash password (bcrypt)
       │
       ▼
┌─────────────┐
│   Browser   │ ◀─ 6. Return "successfully saved user"
└─────────────┘
```

### Login Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ 1. POST /api/login
       │    { username, password }
       ▼
┌─────────────┐
│ Auth Server │
└──────┬──────┘
       │ 2. Query database
       ▼
┌─────────────┐
│  Database   │
└──────┬──────┘
       │ 3. Return user record
       ▼
┌─────────────┐
│ Auth Server │
└──────┬──────┘
       │ 4. Compare password (bcrypt)
       │
       │ 5. Generate JWT token (planned)
       │
       │ 6. Store in Redis cache (planned)
       │
       ▼
┌─────────────┐
│   Browser   │ ◀─ 7. Return "successfully logged in"
└─────────────┘    8. Store token in localStorage
```

### Streaming Flow (Planned)

```
┌─────────────┐
│   Browser   │ (Authenticated with token)
└──────┬──────┘
       │ 1. Connect to WebRTC endpoint
       │    ws://localhost:8889/mystream
       ▼
┌─────────────┐
│  MediaMTX   │
└──────┬──────┘
       │ 2. Validate token with auth server
       │    POST /api/auth with token
       ▼
┌─────────────┐
│ Auth Server │
└──────┬──────┘
       │ 3. Check token in Redis
       │
       │ 4. Verify action permissions
       │    (read/publish)
       ▼
┌─────────────┐
│  MediaMTX   │
└──────┬──────┘
       │ 5. If valid, establish WebRTC connection
       │
       ▼
┌─────────────┐
│   Browser   │ ◀─ 6. Stream data flows
└─────────────┘
```

---

## Current Features

### ✅ Implemented

#### Backend
- [x] HTTP server on port 8080
- [x] CORS middleware
- [x] User registration endpoint (`/api/auth`)
- [x] User login endpoint (`/api/login`)
- [x] Password hashing with bcrypt
- [x] In-memory database with thread safety
- [x] Custom error handling
- [x] Type-safe request/response structures
- [x] Multiple server variants (production, testing, stub)

#### Frontend
- [x] Ultra-minimalist UI design
- [x] Landing page with branding
- [x] Login modal with form validation
- [x] Dashboard with live camera feed
- [x] Settings drawer
- [x] Detection log display
- [x] Responsive design (mobile/tablet/desktop)
- [x] Camera access via getUserMedia
- [x] Frame capture to canvas
- [x] LocalStorage authentication
- [x] Auto-detect API URL (localhost/ngrok)
- [x] Error handling and user feedback

#### Infrastructure
- [x] MediaMTX configuration file
- [x] PostgreSQL schema definition
- [x] ngrok tunnel configuration
- [x] Go module dependencies
- [x] Project documentation (vision, workflow)

### 🔄 Partially Implemented

- [ ] AI detection endpoint integration (code ready, service not deployed)
- [ ] Token caching (structure defined, Redis not implemented)
- [ ] JWT token generation (dependency added, not used)

---

## Known Limitations

### Security
1. **No JWT tokens**: Current implementation uses plain text success messages
2. **No token expiration**: Sessions persist indefinitely in localStorage
3. **Weak CORS**: Allows all origins (`*`) - needs restriction
4. **No HTTPS**: Running on HTTP (insecure for production)
5. **No rate limiting**: Vulnerable to brute force attacks

### Functionality
1. **No real AI detection**: Simulates 10% random threats
2. **No WebRTC streaming**: MediaMTX configured but not integrated
3. **In-memory database**: Data lost on server restart
4. **No password reset**: Users cannot recover accounts
5. **No session management**: Can't revoke active sessions
6. **No user roles**: All users have same permissions

### Scalability
1. **Single-instance server**: No load balancing
2. **No horizontal scaling**: In-memory DB prevents distribution
3. **No caching layer**: Direct database queries
4. **No CDN**: Static assets served from server

### UX
1. **No registration UI**: Only login modal exists
2. **Basic error messages**: Limited user guidance
3. **No loading states**: Abrupt transitions
4. **No offline support**: Requires constant connection

---

## Deployment & Setup

### Prerequisites
- Go 1.25.3+
- Modern web browser (Chrome/Firefox/Safari)
- Camera-enabled device
- (Optional) PostgreSQL 14+
- (Optional) Redis 7+
- (Optional) MediaMTX server

### Local Development Setup

#### 1. Backend Server
```bash
# Navigate to auth server directory
cd mediamtx_authserver

# Install dependencies
go mod download

# Run the server (choose one)
go run main.go                      # Production server
go run simple_server.go             # Testing stub
go run simple_working_server.go     # Hardcoded test user

# Or use compiled binary
./authserver.exe
```

**Server will start on**: `http://localhost:8080`

#### 2. Frontend UI
```bash
# Navigate to UI directory
cd ui/src

# Open in browser (method 1: direct file)
# Double-click index.html
# Or: File → Open → index.html

# Method 2: HTTP server (recommended for camera access)
# Python 3
python -m http.server 3500

# Node.js
npx http-server -p 3500

# Go
go run -m http.server -p 3500
```

**UI will be available at**: `http://localhost:3500`

#### 3. Test the Application

**Option A: With Backend**
1. Start backend server: `go run main.go`
2. Open frontend: `http://localhost:3500`
3. Click "Scan" button
4. Login with credentials:
   - Username: `Brad`
   - Password: `12345678`
5. Grant camera permissions
6. View live feed and detection logs

**Option B: Frontend Only (Testing)**
1. Start stub server: `go run simple_server.go`
2. Open frontend
3. Any credentials will work (always succeeds)
4. Test UI/UX without auth logic

### Remote Testing (ngrok)

#### Setup ngrok Tunnels
```bash
# Install ngrok (if not already installed)
# Download from https://ngrok.com/

# Start tunnels using config file
ngrok start --config config.yml --all
```

**`config.yml` contents**:
```yaml
version: "2"
tunnels:
  frontend:
    proto: http
    addr: 3500
  backend:
    proto: http
    addr: 8080
```

**Results**:
```
Frontend: https://abc123.ngrok-free.dev → localhost:3500
Backend:  https://xyz789.ngrok-free.dev → localhost:8080
```

#### Update Frontend API URL
Open `ui/src/app.js` and update line 16:
```javascript
this.apiUrl = 'https://xyz789.ngrok-free.dev';
```

Now you can access the app from any device with the ngrok URLs.

### Production Deployment (Planned)

#### Backend
```bash
# Build binary
go build -o zook-authserver

# Set environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/zook"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="your-secret-key"
export PORT=8080

# Run server
./zook-authserver
```

#### Frontend
```bash
# Build optimized assets (if using bundler)
# For now, just serve static files

# Deploy to:
# - Vercel (static hosting)
# - Netlify (static hosting)
# - AWS S3 + CloudFront
# - Your own server (nginx)
```

#### Database Migration
```bash
# Connect to PostgreSQL
psql -U postgres -d zook

# Run schema
\i mediamtx_authserver/database/postgres.sql

# Verify
\dt streaming.*
```

---

## Future Roadmap

### Phase 1: MVP Completion (Current) ✅ 90%
- [x] Basic authentication system
- [x] Camera feed integration
- [x] Minimal UI design
- [ ] AI detection service deployment
- [ ] End-to-end testing

### Phase 2: Core Features 🔄
- [ ] JWT token implementation
- [ ] PostgreSQL database migration
- [ ] Redis token caching
- [ ] Real AI detection (YOLOv12)
- [ ] WebRTC streaming via MediaMTX
- [ ] User registration UI
- [ ] Password reset functionality
- [ ] Multi-object detection (guns, weapons, aggressive behavior)

### Phase 3: Enterprise Features 📋
- [ ] User roles and permissions
- [ ] Advanced analytics dashboard
- [ ] Alert email notifications
- [ ] Mobile app (React Native)
- [ ] Drone camera integration
- [ ] Multi-stream monitoring
- [ ] Recording and playback
- [ ] Audit logs and compliance reports

### Phase 4: Scale & Performance 📋
- [ ] Horizontal scaling (Kubernetes)
- [ ] Load balancing
- [ ] CDN integration
- [ ] Database replication
- [ ] Caching layer (Redis Cluster)
- [ ] Monitoring (Prometheus/Grafana)
- [ ] CI/CD pipeline

### Phase 5: Advanced AI 📋
- [ ] Custom model training for Kenya contexts
- [ ] Behavioral analysis (fighting, running)
- [ ] Face recognition (opt-in)
- [ ] License plate detection
- [ ] Crowd density analysis
- [ ] Incident prediction algorithms

---

## Development Notes

### Testing Credentials
- Username: `Brad`
- Password: `12345678`
- These are hardcoded in `memory_db.go` initialization

### API Endpoints Quick Reference
| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/` | GET | Health check | ✅ Working |
| `/api/auth` | POST | User registration | ✅ Working |
| `/api/login` | POST | User authentication | ✅ Working |
| `/api/verify` | POST | Token validation | 📋 Planned |
| `/api/refresh` | POST | Token refresh | 📋 Planned |

### Port Assignments
- **3500**: Frontend UI
- **8080**: Auth Server (backend)
- **8000**: AI Detection Service (FastAPI)
- **8889**: MediaMTX WebRTC
- **8189**: MediaMTX UDP
- **9997**: MediaMTX API

### Key Files for Development
- `mediamtx_authserver/main.go` - Main server logic
- `mediamtx_authserver/database/memory_db.go` - Database operations
- `ui/src/app.js` - Frontend application logic
- `ui/src/style.css` - UI styling
- `mediamtx.yml` - Streaming server config

### Common Issues & Solutions

**Issue**: Camera access denied
- **Solution**: Ensure HTTPS or localhost, grant browser permissions

**Issue**: Cannot connect to backend
- **Solution**: Check if server is running on port 8080, verify CORS settings

**Issue**: Login fails with valid credentials
- **Solution**: Check console logs, verify database has user, test with Brad/12345678

**Issue**: Detection not working
- **Solution**: AI service not deployed yet - this is expected, using simulation

---

## Compliance & Ethics

### Kenya Data Protection Act Compliance
- ✅ Local processing (no cloud storage of video)
- ✅ Explicit user consent required
- ✅ Clear purpose statement
- 📋 TODO: Data retention policy
- 📋 TODO: User data deletion mechanism
- 📋 TODO: Privacy policy documentation

### Ethical Considerations
- **Transparency**: Users must know they're being monitored
- **Consent**: Explicit opt-in required
- **Purpose Limitation**: Only safety/security use cases
- **Data Minimization**: Process only what's necessary
- **Security**: Encrypt data in transit and at rest

---

## Contributors & Credits

**Team**: GenZ Developers  
**Project Lead**: Brad  
**Started**: October 19, 2025  
**Current Status**: MVP Phase 1 (90% complete)

**Technologies Used**:
- Go standard library
- Vanilla JavaScript (no frameworks)
- MediaMTX (aler9)
- YOLOv12 (Ultralytics) - planned
- PostgreSQL
- Redis

---

## License & Usage

**Status**: Open-source foundation (license TBD)

**Intended Use**: Safety and security enhancement in:
- Educational institutions
- Commercial spaces
- Transportation systems
- Security services

**Prohibited Use**:
- Mass surveillance without consent
- Privacy violations
- Discrimination or profiling
- Law enforcement without proper oversight

---

## Contact & Support

**Documentation**: `docs/`  
**Issues**: GitHub Issues (if repository is public)  
**Updates**: Check `docs/meeting_notes.md` for progress

---

*Last Updated: October 22, 2025*  
*Version: 1.0 (MVP)*  
*Status: Active Development*

