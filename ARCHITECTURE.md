# Architecture

```mermaid
flowchart LR
  CSV[Incident platform CSVs] --> EX[Exasol analytical schema]
  PG[PostgreSQL control metadata] --> API[FastAPI]
  EX --> DET[Deterministic detector]
  API --> WF[Workflow]
  WF --> INV[Investigator]
  WF --> ENG[Engineer]
  ENG --> CTRL[Control and SQL policy]
  CTRL --> SIM[Sandbox]
  SIM --> VER[Deterministic verifier]
  VER --> RISK[Risk engine]
  RISK --> DEP[Deploy or approval]
  DEP --> MEM[Qdrant/local memory]
```

Agents propose. The control layer authorizes. The executor executes. The verifier proves.
The current demo uses deterministic Investigator/Engineer behavior and local JSON fallback so it works without an LLM or Qdrant; `ExasolAdapter` and the PostgreSQL schema are production integration boundaries.
