# Hiring Agent Project: Agent Overview

This project implements an AI-driven hiring pipeline designed to streamline candidate evaluation while maintaining fairness and providing deep insights.

## Core Agents

### 1. HR Strategy Agent (`src/agents/hr_strategy`)
- **Role**: Requirements Definition & Refinement.
- **Mechanism**: A conversational agent built with **LangGraph**.
- **Function**: Engages in a dialogue with HR to understand the nuances of a role. It uses tools to finalize a structured `HRJobSpec` that includes required skills, bonus items, and culture-fit metrics.

### 2. Data Arrangement Agent (`src/agents/data_arrangement`)
- **Role**: Resume Structuring.
- **Mechanism**: LLM-based semantic parsing (GPT-4o-mini).
- **Function**: Takes raw OCR text from resumes and transforms it into a highly structured `ResumeStructuredProfile`. It includes built-in truncation and sanitization.

### 3. Background Analysis Agent (`src/agents/background_analysis`)
- **Role**: External Validation & Capability Mapping.
- **Mechanism**: Multi-source API orchestration (GitHub, OpenAlex, Semantic Scholar).
- **Function**: Generates a **Capability Overview Graph**. It calculates indices for code activity and academic impact, providing a visual and data-driven summary of a candidate's professional footprint.

### 4. Scoring Agent (`src/agents/scoring`)
- **Role**: Automated Matching & Evaluation.
- **Mechanism**: Structured LLM evaluation.
- **Function**: Performs a "Blind Match" by comparing the `HRJobSpec`, structured resume, and background analysis. It outputs a `Scorecard` with detailed scores and rationales.

### 5. Async Evaluation Pipeline (`src/api/routes_analyze.py`)
- **Role**: Non-blocking candidate experience.
- **Mechanism**: FastAPI BackgroundTasks + permanent file storage.
- **Function**: Immediately accepts candidate submissions and performs full LLM analysis in the background. Recruiter dashboard polls for real-time status updates (`evaluating` vs `ready`). Supports manual re-evaluation by re-processing stored resume files.

### 6. Authentication & Account System (`src/api/`)
- **Role**: Access Control & Multi-role Support.
- **Mechanism**: Token-based authentication with role-based access control (RBAC).
- **Function**: Manages user registration, login, and sessions. Differentiates between `candidate` (can upload resumes) and `recruiter` (can access the full ranking dashboard).

### 7. Jobs Management (`src/api/routes_jobs.py`)
- **Role**: Job lifecycle management.
- **Function**: Allows recruiters to create and edit job postings. Candidates can view available jobs and apply for specific roles, linking their analysis results to the selected job.

### 8. AI Platform Assistant (`src/api/routes_chat.py`)
- **Role**: Context-aware user support and entity navigation.
- **Mechanism**: Dynamic Tool Calling + Multi-segment UI rendering.
- **Function**: Provides real-time assistance to recruiters and candidates. It uses technical IDs (job_id, ranking_id) from the page context to fetch live data and inject interactive entity cards directly into the chat flow.

## Architecture & Security Patterns

### 1. Database & Vector Search (`src/db/`)
- **Infrastructure**: The project uses **FerretDB 2.7.0** with a **PostgreSQL (DocumentDB)** backend. This provides a MongoDB-compatible API backed by a stable relational database.
- **Vector Search**: The database driver (`src/db/mongo.py`) is enhanced with native vector search capabilities using FerretDB's `cosmosSearch`.
  - **create_vector_index**: Supports creating HNSW and IVF indexes with configurable similarity metrics (Cosine, L2, Inner Product).
  - **vector_search**: Implements the `$search` aggregation stage for high-performance approximate nearest neighbor retrieval.
- **Search Logic**: Jobs are indexed by both their full description and AI-generated summary. The `search_jobs` service performs a dual-vector search and merges results to provide high-relevance job matching for recruiters and candidates.
- **Authentication**: Uses `SCRAM-SHA-256` authentication. Credentials and connection parameters are managed via `src/config.py`.

### 2. Service-Layer Decoupling (`src/services/`)
- All core business logic (Jobs, Rankings, Evaluations) is decoupled from the API routes into a dedicated services layer.
- **Hardened Permissions**: Every service function requires a `User` object and performs internal role-based access control (RBAC). This ensures that even if an AI tool attempts an unauthorized call, the service layer will block it.

### 3. Role-Aware Tool Registry
- The AI Assistant's capabilities are dynamically constructed based on the active user's session.
- **Privacy Hardening**: Tools for sensitive operations (e.g., `create_job`) are only bound to the LLM when the user has the `recruiter` role. Candidates never see these capabilities exist.
- **ID Secrecy**: Technical UUIDs are provided to the LLM via the hidden context. The LLM is instructed to use these for data retrieval but never print them in natural language, using human-friendly names instead.

### 4. Interactive Entity Cards
- **Injection Format**: The assistant uses a specialized `[[TYPE:ID]]` marker to inject rich UI components (Cards) into its chat bubbles.
- **Persistence & Navigation**: Cards are interactive. Clicking a Job or Candidate card triggers a global state change, navigating the user to the relevant page while keeping the chat session persistent.

## Frontend Design & UX Strategy

### Design Philosophy (Steady & Professional)
1.  **High Information Density**: Prioritize structured data presentation and efficient use of screen real estate. Use a full-width container (max-width: 1400px) and logical grid grouping over excessive blank space.
2.  **Structural Hierarchy & Sharpness**: Avoid frivolous effects like glassmorphism or overly rounded corners. Use a stable, sharp-cornered design (4px border-radius) with solid borders and clear separation of concerns.
3.  **Integrated Header System**: Maintain a full-width, darkened title bar that anchors the application. Ensure vertical alignment between the header content and the main container.
4.  **Slate-Based Business Palette**: Use a grounded high-contrast theme (Deep Navy background `#0f172a`, darker Header `#111827`, Slate panels `#1e293b`). Vibrancy is reserved for active states: Electric Blue (`#3b82f6`) for actions and Emerald Green (`#10b981`) for success/match scores.
5.  **Unified Data Components**: Re-use visual patterns for similar data across all roles. Chronological data (Education/Experience) must use a **Unified Timeline** with accent dots aligned to the first line of text.
6.  **Responsive Stability**: Ensure components naturally occupy available width while maintaining strict alignment. Avoid "visual breakage" by carefully calculating margins and padding to preserve the established grid.
7.  **Context-Aware Chat Assistant**: A persistent floating assistant that captures structural context (e.g., `job_id`, `candidate_id`) to provide precise, role-specific help and entity navigation.

## Support Modules

### Fairness & Privacy (`src/fairness/`)
- **Blind Screening**: Automatically redacts PII (Names, Emails, Photos, Genders) from profiles before they reach the Scoring Agent to minimize unconscious bias.
- **Injection Sanitization**: Protects the pipeline from prompt injection attacks hidden within resume text.

### Monitoring & Observability (`src/monitoring/`)
- **Agent Registry**: Tracks the execution status (`running`, `completed`, `failed`) and the path taken by candidates through the multi-agent pipeline.
- **SSE Support**: Provides real-time updates to the dashboard via Server-Sent Events.

## Frontend Architecture (`frontend/`)
The frontend is a modular **Vue 3** application built with **Vite**.

- **Structure**:
  - `frontend/src/App.vue`: Main orchestration and layout component.
  - `frontend/src/components/`: Modular UI components:
    - `ResumeUpload.vue`: Professional file upload with validation.
    - `CandidateSnapshot.vue`: Unified timeline for structured resume data.
    - `RecruiterDashboard.vue`: Multi-page dashboard with candidate tracking and evaluation status.
    - `JobManager.vue`: Role-based job management with unified grid layout.
    - `JobList.vue`: Job board for candidates with submission tracking.
    - `ChatBot.vue`: Context-aware AI assistant with card injection and fullscreen support.
- **Serving Logic**: The FastAPI backend (`src/api/main.py`) serves the production build from `frontend/dist/` if present, falling back to `frontend/src/` for development mode.

## Project Structure
- `src/`: Core Python package containing all logic.
  - `agents/`: Individual agent implementations.
  - `services/`: Decoupled core logic with internal RBAC.
  - `api/`: FastAPI-based REST endpoints.
  - `graph/`: Workflow and pipeline definitions.
  - `db/`: Database connection management.
  - `fairness/`: PII redacting and sanitization.
  - `monitoring/`: Runtime tracking.
  - `config.py`: Centralized environment configuration.
  - `version.py`: Version metadata.
- `frontend/`: Vue 3 application source code.
- `uploads/`: Permanent storage for candidate resumes.

## LLM Interaction & Engineering Guidelines

1. **Commit Protocol**: When a major functionality or feature is added, the LLM must prompt the user to commit the changes to version control.
2. **Design Integrity**: Before modifying the frontend, the LLM MUST carefully analyze the current design in the source (`style.css` and existing components). Do NOT break the established visual hierarchy. Calculate paddings, margins, and grid gaps precisely to avoid visual breakage.
3. **Permission Consistency**: New tools added to the AI Assistant must correspond to a service-layer function that performs its own RBAC checks. Always pass the `User` object through to the service.
4. **Tool Documentation**: Every AI tool must have a clear description identifying the specific ID types (e.g., `job_id`, `ranking_id`) it requires to prevent the LLM from attempting to use human names as technical keys.
5. **Standard Language**: All code comments and documentation MUST be written in **English**, even if the user provides prompts in other languages (e.g., Chinese).
6. **Architectural Integrity**: Maintain clean, organized code. Before implementing changes, consider the entire system architecture. Avoid "patch-like" fixes; instead, act as a lead **Architectural Engineer** to ensure changes are seamless, idiomatic, and maintainable.
7. **Documentation Maintenance**: When the file structure is changed or updated, or new functionality is added, the LLM must check and update `AGENTS.md` to ensure it remains the accurate source of truth.
