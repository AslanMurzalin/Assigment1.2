# Development Plan: Link Saver (v1)

The development is divided into 5 sequential iterations based on the project requirements:
1. **Frontend with mockService** (fully interactive responsive UI with no backend dependency)
2. **openapi.yml** (API contract specification)
3. **Backend with In-Memory Storage** (business logic and endpoints running in memory)
4. **Backend with SQLite Storage** (relational persistence layer with M:N tags)
5. **Frontend + Backend Integration** (connecting client and server end-to-end)

Each task is atomic, bite-sized, and includes concrete acceptance criteria.

---

## Iteration 1. Frontend with mockService

> **Goal**: Build a responsive React SPA with complete UI features, running against mock services (in-memory / `localStorage`).

- [x] **Task 1.1: Frontend Project Initialization**
  - Scaffold a new project using Vite + React + TypeScript.
  - Install and configure Tailwind CSS for responsive layouts.
  - Establish base folder structure (`api`, `components`, `pages`, `hooks`, `types`).
  - *Acceptance Criteria*: Project builds successfully (`npm run build`) and runs locally (`npm run dev`).

- [x] **Task 1.2: TypeScript Domain Models & Interfaces**
  - Define interfaces: `User`, `Link` (fields: `id`, `url`, `title`, `description`, `site_type`, `user_notes`, `tags: string[]`, `created_at`), `SiteType` (`youtube` | `generic`), `FilterParams`.
  - Define contract interfaces `IAuthService` and `ILinkService`.
  - *Acceptance Criteria*: Interfaces are exported from `src/types` and ready for service implementations.

- [x] **Task 1.3: Mock Service Implementation (`MockAuthService` & `MockLinkService`)**
  - Create `MockAuthService`: signup, login (stores synthetic token in `localStorage`), get current user.
  - Create `MockLinkService`: methods `getLinks(search?, tag?)`, `createLink(url, notes, tags)`, `updateLink(id, notes, tags)`, `deleteLink(id)`, `download(id)`.
  - Add realistic network latency simulation (`Promise` with `setTimeout` 200–400ms) and initial seed data (YouTube and generic links with tags).
  - For YouTube links, return a simulated download trigger or mock stream progress.
  - *Acceptance Criteria*: Service methods return typed promises and persist changes in `localStorage`.

- [x] **Task 1.4: Authentication Module (Login & Register Pages)**
  - Implement `AuthContext` to manage active user session and auth token.
  - Build responsive Login and Register forms with client-side input validation (email, password).
  - Add form toggle and route protection (redirecting unauthenticated users to `/login`, authenticated users to `/dashboard`).
  - *Acceptance Criteria*: Users can sign up, log in via mock service, and access the dashboard.

- [x] **Task 1.5: UI Shell & Navigation (Layout & Header)**
  - Create a responsive `Navbar`: brand logo, current user indicator, and Logout button.
  - Support mobile viewports (collapsible menu / compact header).
  - *Acceptance Criteria*: Header adapts seamlessly across viewports from 360px to 1920px.

- [x] **Task 1.6: Link Submission Form (AddLinkForm)**
  - Create URL paste input field with validation.
  - Add optional user notes textarea and tag input chips (split by comma or Enter).
  - Add submit button with loading spinner state.
  - In mock service, automatically infer `title` and `site_type` (`youtube` vs `generic`) based on URL domain.
  - *Acceptance Criteria*: New link is added to the list with auto-generated metadata and custom tags.

- [x] **Task 1.7: Link List & Card Display (LinkCard & LinkList)**
  - Create `LinkCard` component: displays title, clickable external URL, source badge (YouTube / Generic), description/notes, tags list, and creation date.
  - Include a delete button with confirmation.
  - *Acceptance Criteria*: Cards render responsively in a list/grid layout.

- [x] **Task 1.8: Notes & Tags Editing**
  - Allow users to edit `user_notes` and `tags` on existing cards (inline or via modal).
  - Save updates through `MockLinkService`.
  - *Acceptance Criteria*: Note and tag changes update instantly in the UI and persist in `localStorage`.

- [x] **Task 1.9: Search & Filtering Bar (SearchBar & TagFilter)**
  - Create search input field for real-time / debounced search over `title`, `user_notes`, and `tags`.
  - Add quick-filter chips for tags.
  - Provide a "Clear filters" action.
  - *Acceptance Criteria*: Typing search terms or clicking tag chips immediately filters the card list.

- [x] **Task 1.10: YouTube Download Action Simulation**
  - Render a "Download (720p)" button **exclusively** on cards where `site_type === 'youtube'`.
  - On click, show loading feedback / download started notification.
  - *Acceptance Criteria*: Download button is visible only for YouTube links and responds to clicks.

---

## Iteration 2. API Contract Specification (`openapi.yml`)

> **Goal**: Define a rigorous OpenAPI 3.0/3.1 contract specifying all endpoints, request/response schemas, error codes, and auth security schemes.

- [x] **Task 2.1: Base Specification & Security Scheme**
  - Create `openapi.yml` at project root.
  - Define API metadata (Title: "Link Saver API", Version: "1.0.0", local server URLs).
  - Define `HTTP Bearer` (JWT) security scheme.
  - *Acceptance Criteria*: File adheres to OpenAPI 3.0+ structure.

- [x] **Task 2.2: Auth Endpoint Contracts (/auth)**
  - Document `POST /api/v1/auth/signup`: request body (`email`, `password`), `201 Created` (`UserRead`).
  - Document `POST /api/v1/auth/login`: request body (`email`, `password`), `200 OK` (`Token`: `access_token`, `token_type`).
  - Document `GET /api/v1/auth/me`: returns authenticated profile (`UserRead`).
  - Define standard error responses (`400 Bad Request`, `401 Unauthorized`, `409 Conflict`).
  - *Acceptance Criteria*: All auth endpoints specify realistic request/response payload examples.

- [x] **Task 2.3: Link Management Contracts (/links)**
  - Define DTO schemas: `LinkCreate` (`url`, `user_notes?`, `tags?: string[]`), `LinkUpdate` (`user_notes?`, `tags?: string[]`), `LinkRead` (includes `tags: string[]`, `site_type`).
  - Document `GET /api/v1/links`: query parameters `q` (search string), `tag` (tag filter).
  - Document `POST /api/v1/links`: creates link with server-side metadata fetching.
  - Document `GET /api/v1/links/{id}`: retrieve single link.
  - Document `PATCH /api/v1/links/{id}`: partial update for notes and tags.
  - Document `DELETE /api/v1/links/{id}`: deletion (`204 No Content`).
  - *Acceptance Criteria*: CRUD operations are strictly typed with validation rules (URL format, string lengths).

- [x] **Task 2.4: Video Streaming Endpoint Contract (/links/{id}/download)**
  - Document `GET /api/v1/links/{id}/download`.
  - Define response as binary video stream (`content: video/mp4` with `format: binary`).
  - Define error responses: `400 Bad Request` (link is not YouTube), `404 Not Found`.
  - *Acceptance Criteria*: Streaming download operation is fully detailed in `openapi.yml`.

- [x] **Task 2.5: OpenAPI Validation**
  - Validate `openapi.yml` using a schema validator or linter.
  - Fix any syntax discrepancies or missing references.
  - *Acceptance Criteria*: File passes validation with 0 errors.

---

## Iteration 3. Backend with In-Memory Storage

> **Goal**: Implement a functional FastAPI backend supporting all endpoints from `openapi.yml` using in-memory data structures.

- [x] **Task 3.1: FastAPI Setup & Project Structure**
  - Scaffold `backend/app/` (`api`, `core`, `schemas`, `repositories`, `services`).
  - Create `requirements.txt` (`fastapi`, `uvicorn`, `pydantic[email]`, `pyjwt`, `passlib[bcrypt]`, `httpx`, `beautifulsoup4`, `yt-dlp`, `pytest`).
  - Create `main.py` configuring CORS for local React development.
  - *Acceptance Criteria*: Application boots via `uvicorn app.main:app --reload` and serves interactive docs at `/docs`.

- [x] **Task 3.2: Pydantic DTO Schemas**
  - Implement `UserCreate`, `UserLogin`, `UserRead`, `Token`.
  - Implement `LinkCreate`, `LinkUpdate`, `LinkRead`, `SiteTypeEnum`.
  - *Acceptance Criteria*: Schemas mirror the structures defined in `openapi.yml`.

- [x] **Task 3.3: Abstract Repository Interfaces**
  - Create `backend/app/repositories/base.py`:
    - `AbstractUserRepository`: `get_by_id`, `get_by_email`, `create`.
    - `AbstractLinkRepository`: `create`, `get_by_id`, `list_by_user(user_id, q?, tag?)`, `update`, `delete`.
  - *Acceptance Criteria*: Interfaces are completely decoupled from database mechanics.

- [x] **Task 3.4: In-Memory Repository Implementation**
  - Create `InMemoryUserRepository` using in-process `dict[str, User]`.
  - Create `InMemoryLinkRepository` using in-process `dict[str, Link]` with case-insensitive search and tag matching.
  - *Acceptance Criteria*: Repositories execute in-memory CRUD operations correctly.

- [x] **Task 3.5: Security & JWT AuthService**
  - Implement `core/security.py`: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`.
  - Implement FastAPI dependency `get_current_user` in `api/dependencies.py`.
  - *Acceptance Criteria*: Unit tests verify password hashing and token generation/decoding.

- [x] **Task 3.6: Auth API Endpoints (/api/v1/auth)**
  - Implement `/signup`, `/login`, `/me` routes.
  - Connect to `AuthService`, ensuring email uniqueness.
  - *Acceptance Criteria*: Able to register a user, obtain a JWT, and read the `/me` profile.

- [x] **Task 3.7: Metadata Extraction Services (YouTube & Generic)**
  - Implement `GenericExtractor`: fetches HTML via `httpx`, parses `<title>` and `<meta name="description">` (or OpenGraph tags).
  - Implement `YouTubeExtractor`: inspects video title via YouTube metadata extractor (without downloading video file).
  - Implement dispatcher `MetadataExtractorService` to route by domain (`youtube.com`/`youtu.be` vs generic).
  - *Acceptance Criteria*: Supplying a URL extracts `title`, `description`, and classifies `site_type`.

- [x] **Task 3.8: Links API Endpoints (/api/v1/links)**
  - Implement routes:
    - `POST /api/v1/links` — creates link with automatic extractor invocation.
    - `GET /api/v1/links` — lists user links with `q` and `tag` filters.
    - `GET /api/v1/links/{id}` — retrieves single link (validating ownership).
    - `PATCH /api/v1/links/{id}` — updates notes and tags.
    - `DELETE /api/v1/links/{id}` — removes link.
  - *Acceptance Criteria*: Full CRUD works in memory with proper user data scoping.

- [x] **Task 3.9: YouTube Streaming Service (/links/{id}/download)**
  - Implement YouTube streaming generator yielding chunks for 720p video.
  - Return `StreamingResponse(chunk_generator, media_type="video/mp4")` with `Content-Disposition`.
  - Verify link ownership and confirm `site_type == 'youtube'`.
  - *Acceptance Criteria*: Endpoint streams video directly to the caller without temporary server files.

- [x] **Task 3.10: In-Memory Backend Tests**
  - Write `pytest` test suite with `TestClient`:
    - Registration & login flow.
    - Link addition and search filters.
    - Data isolation (User A cannot access User B's links).
  - *Acceptance Criteria*: All tests pass (`pytest`).

---

## Iteration 4. Backend with SQLite Storage (M:N Relational Tables)

> **Goal**: Replace in-memory storage with SQLite and SQLAlchemy using normalized relational models (`links`, `tags`, and `link_tags` junction table).

- [ ] **Task 4.1: SQLite Database Connection Setup**
  - Configure database engine `sqlite:///./app.db` and session maker in `backend/app/db/session.py`.
  - Configure `connect_args={"check_same_thread": False}` for multi-threaded SQLite access.
  - Declare `Base` declarative model class.
  - *Acceptance Criteria*: Database connection initializes successfully.

- [ ] **Task 4.2: SQLAlchemy ORM Models (M:N Schema)**
  - Create `UserModel`: `id`, `email` (indexed, unique), `hashed_password`, `created_at`.
  - Create `TagModel`: `id`, `name` (unique).
  - Create `link_tags` association table: `link_id` (FK to links), `tag_id` (FK to tags), composite PK `(link_id, tag_id)`.
  - Create `LinkModel`: `id`, `user_id` (FK to users), `url`, `title`, `description`, `site_type`, `user_notes`, `created_at`, `updated_at`, with `relationship("TagModel", secondary=link_tags)`.
  - Add auto-table creation on application startup (`Base.metadata.create_all`).
  - *Acceptance Criteria*: Tables `users`, `links`, `tags`, and `link_tags` are created in `app.db`.

- [ ] **Task 4.3: SQLite Repository Implementations with M:N Tag Handling**
  - Implement `SQLiteUserRepository(AbstractUserRepository)`.
  - Implement `SQLiteLinkRepository(AbstractLinkRepository)`:
    - Create/find existing tags by name during link creation/update.
    - Manage relationships in `link_tags`.
    - Fetch links with eager-loaded associated tags.
  - *Acceptance Criteria*: Link creation and updates cleanly associate tags via the junction table.

- [ ] **Task 4.4: Relational Search & Tag Filtering in SQLite**
  - Implement case-insensitive search (`ilike`) across `title` and `user_notes`.
  - Implement tag filtering using a SQL join between `links`, `link_tags`, and `tags` where `tags.name == tag`.
  - *Acceptance Criteria*: Search and tag filters return correct matching records via relational queries.

- [ ] **Task 4.5: Dependency Injection Switch to SQLite**
  - In `api/dependencies.py`, configure dependency providers to return SQLite repositories.
  - Add `get_db` session generator.
  - Ensure services and routers require zero modifications.
  - *Acceptance Criteria*: Application writes all data to `app.db`, surviving server restarts.

- [ ] **Task 4.6: SQLite Integration Tests**
  - Configure test suite to run against an in-memory SQLite database (`:memory:`).
  - Execute full test suite against SQLite backend, specifically verifying tag creation, reuse, and filtering.
  - *Acceptance Criteria*: All tests pass under SQLite.

---

## Iteration 5. Connect Frontend + Backend

> **Goal**: Transition the React application from `MockService` to real API communication with the FastAPI backend and verify end-to-end functionality.

- [ ] **Task 5.1: Real Frontend HTTP Client**
  - Configure `src/api/client.ts` with base URL from `import.meta.env.VITE_API_URL`.
  - Add request interceptor injecting `Authorization: Bearer <token>`.
  - Add response interceptor handling `401 Unauthorized` (clearing session and navigating to `/login`).
  - *Acceptance Criteria*: Client transmits tokens and handles network/auth errors gracefully.

- [ ] **Task 5.2: Production HTTP Services**
  - Implement `HttpAuthService` calling `/api/v1/auth/signup`, `/login`, `/me`.
  - Implement `HttpLinkService` calling `/api/v1/links` and `/api/v1/links/{id}/download`.
  - Swap mock implementations for HTTP services in application entry point / providers.
  - *Acceptance Criteria*: Frontend triggers network calls to backend instead of `localStorage`.

- [ ] **Task 5.3: Environment & CORS Configuration**
  - Add `.env.development` with `VITE_API_URL=http://localhost:8000`.
  - Configure FastAPI CORS middleware to accept requests from frontend origin (`http://localhost:5173`).
  - *Acceptance Criteria*: Browser requests execute without CORS violations.

- [ ] **Task 5.4: Authentication End-to-End Verification**
  - Test registration of a new account from the UI.
  - Test login, JWT storage, and automatic profile hydration on refresh.
  - Test logout.
  - *Acceptance Criteria*: Full user auth flow functions seamlessly.

- [ ] **Task 5.5: Link Management End-to-End Verification**
  - Submit YouTube URL (verify auto-extracted title).
  - Submit generic URL (verify standard metadata).
  - Edit notes and tags, confirming persistent updates in SQLite and relational `link_tags`.
  - *Acceptance Criteria*: All submitted links persist in backend SQLite and display correctly in UI.

- [ ] **Task 5.6: Search & Tag Filter Verification**
  - Verify live search by query string and tag filters against the FastAPI backend with database joins.
  - *Acceptance Criteria*: Filtered results return correctly from server to client.

- [ ] **Task 5.7: Video Streaming End-to-End Verification**
  - Click "Download" on a saved YouTube link.
  - Verify that the browser receives the video stream and downloads the file to the user's local disk.
  - *Acceptance Criteria*: Video downloads to device with zero server-side file retention.

- [ ] **Task 5.8: Smoke Testing & Setup Documentation**
  - Perform a complete smoke test run from registration to video streaming.
  - Write a clear `README.md` documenting setup, environment variables, and startup commands for both Frontend and Backend.
  - *Acceptance Criteria*: The complete solution can be started cleanly from documentation instructions.
