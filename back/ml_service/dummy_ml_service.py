"""
Dummy ML Service - Fallback when TensorFlow is not available
Generates synthetic anomalies for testing purposes
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime

class DummyMLService:
    """
    Dummy ML service that generates synthetic anomalies
    Used when actual ML models cannot be loaded
    """
    
    def __init__(self):
        self.models_loaded = False
        print("⚠️ Using Dummy ML Service (TensorFlow not available)")
    
    def load_models(self):
        """Dummy model loading"""
        self.models_loaded = True
        print("✅ Dummy models loaded (synthetic data will be generated)")
    
    def preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Minimal preprocessing for dummy service
        
        Args:
            df: Raw dataframe
            
        Returns:
            Tuple of (original_df, dummy_scaled_df)
        """
        # Just return original and a copy as "scaled"
        df_clean = df.copy()
        
        # Create dummy scaled features (just normalize numeric columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df_scaled = df[numeric_cols].copy()
        
        # Simple min-max scaling
        for col in df_scaled.columns:
            min_val = df_scaled[col].min()
            max_val = df_scaled[col].max()
            if max_val > min_val:
                df_scaled[col] = (df_scaled[col] - min_val) / (max_val - min_val)
        
        return df_clean, df_scaled
    
    def detect_anomalies(
        self,
        df_original: pd.DataFrame,
        df_scaled: pd.DataFrame,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic anomalies based on simple rules
        
        Args:
            df_original: Original dataframe
            df_scaled: Scaled features
            threshold: Anomaly threshold
            
        Returns:
            List of anomaly dictionaries
        """
        anomalies = []
        
        # Generate random anomalies (5-10% of data)
        num_anomalies = int(len(df_original) * np.random.uniform(0.05, 0.10))
        anomaly_indices = np.random.choice(len(df_original), num_anomalies, replace=False)
        
        for idx in anomaly_indices:
            row_data = df_original.iloc[idx]
            
            # Generate random anomaly score
            score = np.random.uniform(threshold, 1.0)
            
            # Determine severity
            if score >= 0.8:
                severity = "high"
            elif score >= 0.5:
                severity = "medium"
            else:
                severity = "low"
            
            anomaly = {
                "row_index": int(idx),
                "anomaly_score": float(score),
                "severity": severity,
                "model_prediction": "anomaly" if score > 0.7 else "suspicious",
                "reconstruction_error": float(score * 0.6),
                "supervised_score": float(score * 0.4),
                "timestamp": row_data.get('invoice_date', datetime.now()).isoformat() if 'invoice_date' in row_data else datetime.now().isoformat(),
                "feature_values": row_data.to_dict(),
                "shap_values": None
            }
            
            anomalies.append(anomaly)
        
        # Sort by score descending
        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
        
        print(f"✅ Dummy ML generated {len(anomalies)} synthetic anomalies")
        return anomalies
    
    def compute_shap_values(
        self,
        df_scaled: pd.DataFrame,
        row_index: int,
        background_samples: int = 100
    ) -> Dict[str, float]:
        """
        Generate dummy SHAP values
        
        Args:
            df_scaled: Scaled features
            row_index: Row index
            background_samples: Not used in dummy
            
        Returns:
            Dictionary of dummy SHAP values
        """
        # Generate random SHAP values for available columns
        shap_dict = {}
        
        for col in df_scaled.columns[:10]:  # Top 10 features
            shap_dict[col] = float(np.random.uniform(-0.5, 0.5))
        
        # Sort by absolute value
        shap_dict = dict(sorted(
            shap_dict.items(),
            key=lambda item: abs(item[1]),
            reverse=True
        ))
        
        return shap_dict
    
    def generate_summary(
        self,
        shap_values: Dict[str, float],
        feature_values: Dict[str, Any],
        top_n: int = 5
    ) -> str:
        """
        Generate dummy summary
        
        Args:
            shap_values: SHAP values
            feature_values: Feature values
            top_n: Number of top features
            
        Returns:
            Text summary
        """
        if not shap_values:
            return "⚠️ Dummy ML: Anomaly detected based on synthetic rules."
        
        summary = "⚠️ DUMMY ML EXPLANATION (for testing only):\n\n"
        summary += "This transaction was flagged as anomalous due to:\n"
        
        for i, (feature, value) in enumerate(list(shap_values.items())[:top_n], 1):
            direction = "increasing" if value > 0 else "decreasing"
            summary += f"{i}. {feature}: {direction} anomaly likelihood\n"
        
        summary += "\n⚠️ Note: This is synthetic data. Install TensorFlow for real ML predictions."
        
        return summary


# Export dummy service
dummy_ml_service = DummyMLService()


def get_dummy_ml_service() -> DummyMLService:
    """Get dummy ML service instance"""
    return dummy_ml_service


# Convenience function
def process_upload_dummy(df: pd.DataFrame, threshold: float = 0.5) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Process upload using dummy ML service
    
    Args:
        df: Raw CSV dataframe
        threshold: Anomaly threshold
        
    Returns:
        Tuple of (cleaned_df, anomalies_list)
    """
    service = get_dummy_ml_service()
    df_clean, df_scaled = service.preprocess_data(df)
    anomalies = service.detect_anomalies(df_clean, df_scaled, threshold)
    return df_clean, anomalies
