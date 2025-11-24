           ┌─────────────────────────────┐
           │         Frontend            │
           │   (Next.js / Streamlit)     │
           └──────────────┬──────────────┘
                          │   (HTTPS)
                          ▼
                ┌──────────────────────┐
                │     FastAPI API      │
                │  (Backend Services)  │
                └───────┬──────────────┘
                        │
        ┌───────────────┼──────────────────────┐
        ▼               ▼                      ▼
┌─────────────┐  ┌────────────┐       ┌────────────────┐
│ ML Engine   │  │ Postgres   │       │ Redis Queue     │
│ model.pkl   │  │ invoices   │       │ background jobs │
│ shap expl.  │  │ anomalies  │       │ processing      │
└─────────────┘  └────────────┘       └────────────────┘
