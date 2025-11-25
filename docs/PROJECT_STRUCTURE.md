# Leak Detector - Project Structure

## 📁 Directory Organization

```
leak-detector/
├── back/                      # FastAPI backend application
│   ├── database/              # PostgreSQL database layer
│   │   ├── schema.sql         # Database schema (tables, indexes, views)
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── database.py        # Connection management
│   │   ├── README.md          # Database setup guide
│   │   └── __init__.py
│   │
│   ├── ml_service/            # ML inference engine
│   │   ├── ml_service.py      # Real ML service (TensorFlow-based)
│   │   ├── dummy_ml_service.py # Fallback dummy service
│   │   ├── test_ml_service.py  # Test script
│   │   └── __init__.py        # Auto-fallback logic
│   │
│   ├── storage/               # File upload management
│   │   ├── storage.py         # File storage service
│   │   └── __init__.py
│   │
│   ├── process/               # Upload & processing endpoints
│   │   ├── upload.py          # CSV upload endpoint
│   │   ├── process.py         # ML processing endpoint
│   │   └── __init__.py
│   │
│   ├── dashboard/             # Dashboard metrics endpoints
│   │   ├── metric.py          # GET /api/dashboard/metrics
│   │   └── __init__.py
│   │
│   ├── main.py                # FastAPI application entry point
│   └── requirements.txt       # Python dependencies
│
├── ml/                        # ML models and training data
│   ├── optimal_autoencoder_model.keras  # Trained autoencoder
│   ├── supervised_model.joblib          # Trained classifier
│   ├── scaler_std.joblib                # Feature scaler
│   ├── saas_billing_train.csv           # Training dataset (75k rows)
│   └── anamoly.ipynb                    # Training notebook
│
├── data/                      # Runtime data (gitignored)
│   └── uploads/               # Uploaded CSV files (created automatically)
│
├── docs/                      # Documentation
│   └── wireframes/            # UI wireframes and system design
│       ├── README.md          # System architecture & API specs
│       └── *.png              # Wireframe images
│
├── api/                       # API folder (TBD - might be redundant with back/)
├── dashboard/                 # Dashboard folder (TBD - might be for frontend)
│
├── .gitignore                 # Git ignore rules
└── README.md                  # Project overview
```

---

## 🔧 Backend Structure Best Practices

### Current Organization

The backend follows a modular, feature-based structure:

1. **database/** - All database-related code isolated
2. **ml_service/** - ML inference logic separated from API
3. **storage/** - File management utilities  
4. **process/** - Processing-related endpoints
5. **dashboard/** - Dashboard endpoints

### Recommendations

#### ✅ Keep
- Modular structure is good
- Clear separation of concerns
- Database layer is well organized

#### 🚧 To Be Created (Next Phase)
```
back/
├── anomalies/          # Anomaly-related endpoints
│   ├── anomalies.py    # GET /api/anomalies (listing)
│   ├── explain.py      # GET /api/explain/{id} (SHAP)
│   ├── actions.py      # POST /api/anomalies/{id}/action
│   └── __init__.py
```

#### 🤔 To Clarify/Reorganize
- **api/** folder at root - Purpose unclear, might be redundant with `back/`
- **dashboard/** folder at root - If for frontend, rename to `frontend/` or `web/`
- **data/** - Good to have, currently empty but will be used for uploads

---

## 📦 Suggested Cleanup

### Completed ✅
1. ✅ Removed `/notebooks` (empty)
2. ✅ Removed `/infra` (empty)
 3. ✅ Renamed `/back/ml` to `/back/ml_service` (avoid confusion with `/ml`)

### Still To Do
1. **Clarify `/api` folder** - Is this for API documentation or code?
2. **Clarify `/dashboard` folder** - Is this for frontend React/Vue code?
3. **Create `/data/uploads/`** - Will be auto-created by storage service

---

## 🎯 Recommended Final Structure

```
leak-detector/
├── backend/                   # Rename 'back' to 'backend' for clarity
│   ├── src/                   # Application code
│   │   ├── database/
│   │   ├── ml_service/
│   │   ├── storage/
│   │   ├── routers/           # All API endpoints
│   │   │   ├── upload.py
│   │   │   ├── process.py
│   │   │   ├── anomalies.py
│   │   │   ├── dashboard.py
│   │   │   └── __init__.py
│   │   ├── models/            # Pydantic request/response models
│   │   ├── config.py          # Configuration
│   │   └── main.py
│   ├── tests/                 # Unit tests
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                  # Frontend application (if exists)
│   ├── src/
│   ├── public/
│   └── package.json
│
├── ml/                        # ML models and notebooks
│   ├── models/                # Trained model files
│   ├── notebooks/             # Training notebooks  
│   └── data/                  # Training datasets
│
├── docs/                      # Documentation
│   ├── wireframes/
│   ├── api.md                 # API documentation
│   └── setup.md               # Setup guide
│
├── data/                      # Runtime data (gitignored)
│   └── uploads/
│
└── README.md
```

**Note**: This is aspirational. Current structure is functional, just suggesting improvements for long-term maintainability.

---

## 🚀 Current Status

**Working Structure** (as of Nov 25, 2025):
- ✅ Backend is functional with current structure
- ✅ clear separation between `/ml` (models) and `/back/ml_service` (inference code)
- ✅ Database layer is well organized
- ✅ Empty folders cleaned up

**For MVP, current structure is fine. Refactoring can wait until after feature completion.**

---

Last Updated: November 25, 2025
