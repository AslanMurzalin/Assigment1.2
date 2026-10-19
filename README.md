# Link Saver (v1)

A responsive, high-performance web application for saving, organizing, and exploring links with automated metadata extraction and specialized on-demand video streaming.

Built with a modern **Orange & White** visual identity, clean layered architecture, and relational database modeling.

---

## Architecture & Technology Stack

| Component | Technology | Description |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons | Responsive UI (360px–1920px), dependency-injected services (`HttpAuthService`, `HttpLinkService`), visual progress tracking |
| **Backend** | FastAPI, Python 3.10+, Pydantic v2, Uvicorn | Clean architecture: Routers &rarr; Domain Services &rarr; Repositories |
| **Database & ORM** | SQLite (`app.db`), SQLAlchemy | Normalized $M:N$ relational model: `users`, `links`, `tags`, and `link_tags` junction table |
| **Video Streaming** | `yt-dlp`, `imageio-ffmpeg` | On-demand accelerated 720p stream with zero permanent server retention; accurate duration seeking and fast muxing |
| **Metadata Extraction** | `httpx` + `BeautifulSoup4` | Automatic parsing of HTML `<title>` and `<meta name="description">` / OpenGraph |
| **Security** | `pyjwt`, `passlib[bcrypt]` | JWT Bearer token authentication, salted bcrypt password hashing, strict user data isolation |
| **API Contract** | OpenAPI 3.0.3 (`openapi.yml`) | Single source of truth specifying all endpoints, DTO schemas, and security schemes |

---

## Features

1. **User Authentication & Session Management**:
   - Secure registration, login, and profile retrieval via JWT Bearer tokens.
   - User-scoped data isolation (users cannot access, update, or delete other users' links).
2. **Automated Metadata Extraction**:
   - Save links with instant server-side metadata fetching.
   - Domain-based dispatching for YouTube videos vs. generic websites.
3. **Normalized Relational Tags ($M:N$)**:
   - Tags are stored uniquely in `tags` and linked via `link_tags` junction table.
   - Automatic tag deduplication and reuse across links.
4. **Relational Search & Filtering**:
   - SQL `ilike` substring search across link titles and personal notes.
   - Relational SQL joins for tag-based filtering.
5. **High-Performance 720p YouTube Video Streaming**:
   - On-demand streaming download with concurrent audio/video download and proper metadata muxing.
   - Seekable timeline with preserved duration (no "live stream" display artifacts).
   - Temporary file-based on-demand muxing with automatic cleanup in a `finally` block (**zero permanent files stored on the server**).
   - Real-time animated **filling scale progress bar** with loaded bytes, speed, percentage, and ETA metrics.
   - Protection against accidental page unload/refresh during active downloads.
6. **Orange & White Design System**:
   - Clean, accessible visual hierarchy adhering to `docs/design.md`.

---

## Project Structure

```text
.
├── openapi.yml                # API contract specification (OpenAPI 3.0)
├── AGENTS.md                  # Agent operating guide and project memory
├── docs/                      # Technical documentation
│   ├── architecture.md        # Architectural diagrams and schema specifications
│   ├── tasks.md               # 5-iteration checklist of all atomic tasks
│   ├── scope.md               # Original v1 product requirements
│   ├── engineer.md            # Issue resolution handbook and testing guide
│   ├── design.md              # Orange-White visual identity guide
│   └── QA.md                  # QA role specification & issue reopening protocol
│
├── frontend/                  # React 19 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── api/               # Axios client, HTTP services, and Mock services
│   │   ├── components/        # Modals, link cards, search bar, navigation
│   │   ├── context/           # AuthContext provider
│   │   ├── hooks/             # Custom React hooks (useAuth, useLinks)
│   │   ├── pages/             # AuthPage, DashboardPage
│   │   └── types/             # Domain TypeScript interfaces
│   ├── .env.development       # Development environment config (VITE_API_URL)
│   ├── package.json
│   └── vite.config.ts
│
└── backend/                   # FastAPI application
    ├── app/
    │   ├── api/               # Auth, links, and streaming routes
    │   ├── core/              # Config, security, exceptions
    │   ├── db/                # SQLite connection and session management
    │   ├── models/            # SQLAlchemy models (User, Link, Tag, link_tags)
    │   ├── repositories/      # Abstract, InMemory, and SQLite implementations
    │   ├── schemas/           # Pydantic v2 DTOs
    │   ├── services/          # Metadata extractors and streaming generators
    │   └── main.py            # Application factory and CORS middleware
    ├── tests/                 # Automated pytest test suites
    └── requirements.txt       # Python dependencies
```

---

## Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher
- **Git**

---

### Backend Setup

1. **Navigate to the backend directory and activate your virtual environment**:
   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI development server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **Verify the API**:
   - Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```

4. **Open in browser**:
   - Development server runs at [http://localhost:5173](http://localhost:5173).

---

### Running Automated Tests

Run the full pytest suite (In-Memory, SQLite M:N, and End-to-End integration):

```bash
pytest backend/tests/ -v
```

All 9 tests pass:
- `test_health_check`
- `test_auth_flow`
- `test_links_crud_and_search`
- `test_user_data_isolation`
- `test_download_validation`
- `test_sqlite_auth_flow`
- `test_sqlite_mn_tags_and_deduplication`
- `test_e2e_full_lifecycle`
- `test_youtube_streaming_generator`

---

## License

This project was developed for Assignment 1.2 under the MIT License.
