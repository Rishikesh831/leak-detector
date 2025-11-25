"""
Test script for ML Service
Run this to verify models load correctly
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from ml_service import get_ml_service

def test_model_loading():
    """Test that all models load successfully"""
    print("="*60)
    print("Testing ML Service - Model Loading")
    print("="*60)
    
    try:
        service = get_ml_service()
        print("[OK] ML Service initialized successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to initialize ML service: {e}")
        return False


def test_preprocessing():
    """Test data preprocessing"""
    print("\n" + "="*60)
    print("Testing ML Service - Data Preprocessing")
    print("="*60)
    
    try:
        # Load sample data
        csv_path = Path(__file__).parent.parent.parent / "ml" / "saas_billing_train.csv"
        df = pd.read_csv(csv_path)
        print(f"[OK] Loaded CSV: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Test with first 100 rows
        df_sample = df.head(100)
        
        service = get_ml_service()
        df_clean, df_scaled = service.preprocess_data(df_sample)
        
        print(f"[OK] Preprocessing successful")
        print(f"   - Cleaned data: {df_clean.shape}")
        print(f"   - Scaled features: {df_scaled.shape}")
        print(f"   - Expected features: {service.scaler.n_features_in_}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Preprocessing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anomaly_detection():
    """Test anomaly detection"""
    print("\n" + "="*60)
    print("Testing ML Service - Anomaly Detection")
    print("="*60)
    
    try:
        # Load sample data
        csv_path = Path(__file__).parent.parent.parent / "ml" / "saas_billing_train.csv"
        df = pd.read_csv(csv_path).head(100)
        
        service = get_ml_service()
        df_clean, df_scaled = service.preprocess_data(df)
        
        # Detect anomalies with threshold 0.5
        anomalies = service.detect_anomalies(df_clean, df_scaled, threshold=0.5)
        
        print(f"[OK] Anomaly detection successful")
        print(f"   - Anomalies found: {len(anomalies)}")
        
        if anomalies:
            print(f"\n   Sample anomaly:")
            sample = anomalies[0]
            print(f"   - Row index: {sample['row_index']}")
            print(f"   - Anomaly score: {sample['anomaly_score']:.4f}")
            print(f"   - Severity: {sample['severity']}")
            print(f"   - Prediction: {sample['model_prediction']}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Anomaly detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n[TEST] Starting ML Service Tests\n")
    
    results = []
    
    # Run tests
    results.append(("Model Loading", test_model_loading()))
    results.append(("Preprocessing", test_preprocessing()))
    results.append(("Anomaly Detection", test_anomaly_detection()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] All tests passed! ML service is ready.")
    else:
        print("\n[WARN] Some tests failed. Please check the errors above.")
    
    sys.exit(0 if all_passed else 1)
