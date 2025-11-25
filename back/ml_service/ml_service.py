"""
ML Service for Leak Detection
Handles model loading, preprocessing, anomaly detection, and SHAP explanations
"""
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Try different Keras/TensorFlow import methods
try:
    import tensorflow as tf
    from tensorflow import keras
except ImportError:
    try:
        import keras
        tf = None
    except ImportError:
        raise ImportError(
            "Neither TensorFlow nor standalone Keras found. "
            "Please install: pip install tensorflow or pip install keras"
        )

import shap
from datetime import datetime

# Path to ML models
ML_MODELS_DIR = Path(__file__).parent.parent.parent / "ml"


class MLService:
    """
    Singleton ML service for anomaly detection
    Loads models once and reuses them for all predictions
    """
    
    _instance = None
    _models_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._models_loaded:
            self.load_models()
            self._models_loaded = True
    
    def load_models(self):
        """Load all ML models from disk"""
        try:
            print("[INFO] Loading ML models...")
            
            # Load scaler
            scaler_path = ML_MODELS_DIR / "scaler_std.joblib"
            self.scaler = joblib.load(scaler_path)
            print(f"  [OK] Scaler loaded (expects {self.scaler.n_features_in_} features)")
            
            # Load supervised classifier
            supervised_path = ML_MODELS_DIR / "supervised_model.joblib"
            self.supervised_model = joblib.load(supervised_path)
            print(f"  [OK] Supervised model loaded: {type(self.supervised_model).__name__}")
            
            # Load autoencoder
            autoencoder_path = ML_MODELS_DIR / "optimal_autoencoder_model.keras"
            if tf is not None:
                self.autoencoder = tf.keras.models.load_model(autoencoder_path)
            else:
                self.autoencoder = keras.models.load_model(autoencoder_path)
            print(f"  [OK] Autoencoder loaded: {self.autoencoder.input_shape}")
            
            # Initialize SHAP explainer (lazy loading)
            self.shap_explainer = None
            
            print("[OK] All ML models loaded successfully")
            
        except Exception as e:
            print(f"[ERROR] Error loading ML models: {e}")
            raise e
    
    def preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Preprocess raw CSV data for ML models
        
        Args:
            df: Raw dataframe from CSV upload
            
        Returns:
            Tuple of (original_df, processed_features)
        """
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Parse date columns
        date_columns = ['invoice_date', 'due_date', 'payment_date']
        for col in date_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        
        # Feature engineering
        features_df = self._engineer_features(df_clean)
        
        # Select only numeric features for scaling
        numeric_features = features_df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Scale features
        scaled_features = self.scaler.transform(features_df[numeric_features])
        
        # Create scaled dataframe
        scaled_df = pd.DataFrame(
            scaled_features,
            columns=numeric_features,
            index=features_df.index
        )
        
        return df_clean, scaled_df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering to match training data
        Creates 55 features expected by the scaler
        
        Args:
            df: Cleaned dataframe
            
        Returns:
            DataFrame with engineered features
        """
        features = pd.DataFrame(index=df.index)
        
        # Numeric features from CSV
        numeric_cols = [
            'invoice_amount', 'tax_amount', 'total_amount',
            'discount_applied', 'refund_amount', 'retries',
            'gateway_fee', 'usage_units', 'usage_cost', 'rounding_diff'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                features[col] = df[col].fillna(0)
        
        # Date-based features
        if 'invoice_date' in df.columns and 'payment_date' in df.columns:
            features['payment_delay_days'] = (
                df['payment_date'] - df['invoice_date']
            ).dt.days.fillna(0)
        
        if 'invoice_date' in df.columns and 'due_date' in df.columns:
            features['due_delay_days'] = (
                df['due_date'] - df['invoice_date']
            ).dt.days.fillna(0)
        
        # Categorical encoding (one-hot)
        categorical_cols = [
            'currency', 'payment_status', 'payment_method',
            'subscription_plan', 'billing_cycle', 'country',
            'failed_reason', 'system_version'
        ]
        
        for col in categorical_cols:
            if col in df.columns:
                # One-hot encode with prefix
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                features = pd.concat([features, dummies], axis=1)
        
        # Boolean features
        if 'is_prorated' in df.columns:
            features['is_prorated'] = df['is_prorated'].fillna(0)
        
        # Derived features
        if 'invoice_amount' in features and 'tax_amount' in features:
            features['tax_rate'] = (
                features['tax_amount'] / (features['invoice_amount'] + 1e-6)
            ).fillna(0)
        
        if 'refund_amount' in features and 'total_amount' in features:
            features['refund_rate'] = (
                features['refund_amount'] / (features['total_amount'] + 1e-6)
            ).fillna(0)
        
        # Ensure we have at least 55 features (pad with zeros if needed)
        expected_features = self.scaler.n_features_in_
        current_features = len(features.columns)
        
        if current_features < expected_features:
            for i in range(current_features, expected_features):
                features[f'feature_{i}'] = 0
        elif current_features > expected_features:
            # Take only the first expected_features columns
            features = features.iloc[:, :expected_features]
        
        return features
    
    def detect_anomalies(
        self,
        df_original: pd.DataFrame,
        df_scaled: pd.DataFrame,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies using both autoencoder and supervised model
        
        Args:
            df_original: Original dataframe with raw data
            df_scaled: Scaled features dataframe
            threshold: Anomaly score threshold (0.0 to 1.0)
            
        Returns:
            List of anomaly dictionaries with metadata
        """
        anomalies = []
        
        # 1. Autoencoder reconstruction error
        X = df_scaled.values
        reconstructed = self.autoencoder.predict(X, verbose=0)
        reconstruction_errors = np.mean(np.square(X - reconstructed), axis=1)
        
        # Normalize reconstruction errors to 0-1 range
        max_error = np.max(reconstruction_errors)
        if max_error > 0:
            reconstruction_scores = reconstruction_errors / max_error
        else:
            reconstruction_scores = reconstruction_errors
        
        # 2. Supervised model predictions
        supervised_probs = self.supervised_model.predict_proba(X)
        # Assuming class 1 is "anomaly"
        if supervised_probs.shape[1] > 1:
            supervised_scores = supervised_probs[:, 1]
        else:
            supervised_scores = supervised_probs[:, 0]
        
        # 3. Combine scores (weighted average)
        combined_scores = 0.6 * reconstruction_scores + 0.4 * supervised_scores
        
        # 4. Identify anomalies above threshold
        anomaly_indices = np.where(combined_scores >= threshold)[0]
        
        for idx in anomaly_indices:
            row_data = df_original.iloc[idx]
            
            # Determine severity based on score
            score = float(combined_scores[idx])
            if score >= 0.8:
                severity = "high"
            elif score >= 0.5:
                severity = "medium"
            else:
                severity = "low"
            
            # Get model prediction
            prediction = self.supervised_model.predict(df_scaled.iloc[idx:idx+1])[0]
            
            anomaly = {
                "row_index": int(idx),
                "anomaly_score": score,
                "severity": severity,
                "model_prediction": str(prediction),
                "reconstruction_error": float(reconstruction_errors[idx]),
                "supervised_score": float(supervised_scores[idx]),
                "timestamp": row_data.get('invoice_date', datetime.now()).isoformat() if 'invoice_date' in row_data else datetime.now().isoformat(),
                "feature_values": row_data.to_dict(),
                "shap_values": None  # Will be computed on-demand
            }
            
            anomalies.append(anomaly)
        
        return anomalies
    
    def compute_shap_values(
        self,
        df_scaled: pd.DataFrame,
        row_index: int,
        background_samples: int = 100
    ) -> Dict[str, float]:
        """
        Compute SHAP values for a specific anomaly
        
        Args:
            df_scaled: Scaled features dataframe
            row_index: Index of the row to explain
            background_samples: Number of background samples for SHAP
            
        Returns:
            Dictionary mapping feature names to SHAP values
        """
        try:
            # Initialize SHAP explainer if not already done
            if self.shap_explainer is None:
                # Use a subset of data as background
                background_data = df_scaled.sample(
                    n=min(background_samples, len(df_scaled)),
                    random_state=42
                ).values
                
                self.shap_explainer = shap.KernelExplainer(
                    self.supervised_model.predict_proba,
                    background_data
                )
            
            # Get SHAP values for the specific row
            row_data = df_scaled.iloc[row_index:row_index+1].values
            shap_values = self.shap_explainer.shap_values(row_data)
            
            # If binary classification, take class 1 (anomaly) SHAP values
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            # Map to feature names
            feature_names = df_scaled.columns.tolist()
            shap_dict = {
                feature_names[i]: float(shap_values[0][i])
                for i in range(len(feature_names))
            }
            
            # Sort by absolute value
            shap_dict = dict(sorted(
                shap_dict.items(),
                key=lambda item: abs(item[1]),
                reverse=True
            ))
            
            return shap_dict
            
        except Exception as e:
            print(f"⚠️ SHAP computation failed: {e}")
            return {}
    
    def generate_summary(
        self,
        shap_values: Dict[str, float],
        feature_values: Dict[str, Any],
        top_n: int = 5
    ) -> str:
        """
        Generate human-readable summary of anomaly explanation
        
        Args:
            shap_values: SHAP values for features
            feature_values: Actual feature values
            top_n: Number of top features to include
            
        Returns:
            Text summary
        """
        if not shap_values:
            return "Unable to generate explanation due to SHAP computation error."
        
        # Get top contributing features
        top_features = list(shap_values.items())[:top_n]
        
        summary_parts = ["This transaction was flagged as an anomaly due to:"]
        
        for feature, shap_value in top_features:
            direction = "increasing" if shap_value > 0 else "decreasing"
            actual_value = feature_values.get(feature, "N/A")
            
            summary_parts.append(
                f"- {feature.replace('_', ' ').title()}: {actual_value} "
                f"({direction} anomaly likelihood by {abs(shap_value):.3f})"
            )
        
        summary = "\n".join(summary_parts)
        return summary


# Singleton instance
ml_service = MLService()


# Helper functions for easy access
def get_ml_service() -> MLService:
    """Get the ML service singleton instance"""
    return ml_service


def process_upload(df: pd.DataFrame, threshold: float = 0.5) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Convenience function to process an uploaded CSV
    
    Args:
        df: Raw CSV dataframe
        threshold: Anomaly detection threshold
        
    Returns:
        Tuple of (cleaned_df, anomalies_list)
    """
    service = get_ml_service()
    df_clean, df_scaled = service.preprocess_data(df)
    anomalies = service.detect_anomalies(df_clean, df_scaled, threshold)
    return df_clean, anomalies
