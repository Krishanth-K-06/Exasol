# API

- `GET /health`: process health and Exasol configuration hint.
- `POST /scenarios/SCN-02/inject`: create the schema-change incident.
- `POST /scenarios/SCN-03/inject`: create the null-explosion incident.
- `GET /incidents`: list persisted incidents.
- `GET /incidents/{id}`: inspect state.
- `POST /incidents/{id}/investigate`: run deterministic investigation.
- `POST /incidents/{id}/remediate`: create a controlled fix proposal.
- `POST /incidents/{id}/run`: execute the full safe workflow; pass `?approved=true` for human approval.
- `POST /incidents/{id}/approve`: approve and run a waiting incident.
- `GET /incidents/{id}/timeline`: view workflow stages.

Interactive OpenAPI is available at `/docs`.
