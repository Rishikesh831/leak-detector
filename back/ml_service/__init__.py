"""
ML Service package for Leak Detector backend
Automatically uses dummy ML service if TensorFlow is not available
"""

# Try to import real ML service, fall back to dummy if TensorFlow not available
try:
    from ml_service.ml_service import MLService, get_ml_service, process_upload
    ML_SERVICE_MODE = "REAL"
    print("[OK] Using Real ML Service (TensorFlow available)")
except ImportError as e:
    print(f"[WARN] TensorFlow not available: {e}")
    print("[WARN] Falling back to Dummy ML Service")
    from ml_service.dummy_ml_service import DummyMLService as MLService
    from ml_service.dummy_ml_service import get_dummy_ml_service as get_ml_service
    from ml_service.dummy_ml_service import process_upload_dummy as process_upload
    ML_SERVICE_MODE = "DUMMY"

__all__ = ["MLService", "get_ml_service", "process_upload", "ML_SERVICE_MODE"]
