import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from accounts.models import User
from performance.models import Performance

class PerformancePredictor:
    """Predict future employee performance"""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, employee):
        """Extract features for prediction"""
        performances = Performance.objects.filter(
            employee=employee
        ).order_by('-year', '-month')[:12]  # Last 12 months
        
        if len(performances) < 3:
            return None
        
        features = []
        scores = []
        
        # Process performances in chronological order (oldest first)
        for perf in reversed(list(performances)):  # oldest to newest
            # Append score first so it's available for moving average/trend
            scores.append(float(perf.calculated_score))
        
        # Now build features using the scores list
        for i, perf in enumerate(performances):  # most recent first? Actually performances is already newest first
            # We need scores in chronological order for trend calculations
            # Let's use reversed index
            idx = len(scores) - 1 - i  # index in chronological list (oldest first)
            # But for moving average we want past scores relative to current
            # Better to build features in chronological order
            pass
        
        # Simpler: rebuild in chronological order
        perfs_chrono = list(reversed(performances))  # oldest first
        scores_chrono = [float(p.calculated_score) for p in perfs_chrono]
        
        for idx, perf in enumerate(perfs_chrono):
            features.append({
                'month': perf.month,
                'year': perf.year,
                'rating': float(perf.rating),
                'goals': float(perf.goals_completed),
                'attendance': float(perf.attendance_percentage),
                'score': scores_chrono[idx],
                'months_employed': self._months_employed(employee),
                'avg_score_3m': self._moving_average(scores_chrono, idx, 3),
                'trend': self._calculate_trend(scores_chrono, idx)
            })
        
        return pd.DataFrame(features)
    
    def _months_employed(self, employee):
        if not employee.date_of_joining:
            return 0
        delta = datetime.now().date() - employee.date_of_joining
        return delta.days // 30
    
    def _moving_average(self, scores, current_idx, window):
        """Compute moving average of past scores up to current_idx (excluding current if window > 0)"""
        if current_idx < window:
            # Not enough past data, use current score as best estimate
            return scores[current_idx] if scores else 0
        return np.mean(scores[current_idx-window:current_idx])
    
    def _calculate_trend(self, scores, current_idx):
        """Calculate trend based on previous score difference"""
        if current_idx < 1:
            return 0
        return scores[current_idx] - scores[current_idx-1]
    
    def train(self):
        """Train the model on all employees"""
        print("🔄 Training Performance Predictor...")
        
        X_list = []
        y_list = []
        
        employees = User.objects.filter(is_soft_deleted=False)
        
        for emp in employees:
            features_df = self.prepare_features(emp)
            if features_df is not None and len(features_df) > 1:
                # Use all but last for training, last as target
                for i in range(len(features_df)-1):
                    X = features_df.iloc[i].drop('score').values
                    y = features_df.iloc[i+1]['score']
                    X_list.append(X)
                    y_list.append(y)
        
        if len(X_list) < 5:
            print("⚠️ Not enough data for training")
            return False
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        # Scale features
        X = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X, y)
        
        self.is_trained = True
        print(f"✅ Model trained on {len(X)} samples")
        return True
    
    def predict_next_score(self, employee):
        """Predict next month's score"""
        if not self.is_trained:
            return None, 0
        
        features_df = self.prepare_features(employee)
        if features_df is None or len(features_df) == 0:
            return None, 0
        
        # Use most recent feature set for prediction
        latest = features_df.iloc[-1].drop('score').values.reshape(1, -1)
        latest_scaled = self.scaler.transform(latest)
        
        prediction = self.model.predict(latest_scaled)[0]
        
        # Calculate confidence based on historical variance
        scores = [p.calculated_score for p in 
                  Performance.objects.filter(employee=employee)[:6]]
        if len(scores) > 1:
            std = np.std(scores)
            confidence = max(0, min(100, 100 - std * 5))
        else:
            confidence = 50
        
        return float(prediction), float(confidence)