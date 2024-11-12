import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import asyncio

class MLService:
    def __init__(self):
        # Detector de anomalías
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            n_estimators=200,
            max_samples='auto',
            random_state=42
        )
        
        # Clasificador para patrones conocidos de fraude
        self.fraud_classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
        
        # Escalador para normalizar características
        self.scaler = StandardScaler()
        
        # Lista negra de direcciones conocidas
        self.blacklisted_addresses = set()  # Aquí podrías cargar addresses conocidas maliciosas
        
        # Patrones de comportamiento sospechoso
        self.suspicious_patterns = {
            'high_frequency_small_tx': {
                'threshold': 20,  # transacciones por hora
                'weight': 0.3
            },
            'large_value_tx': {
                'threshold': 100,  # ETH
                'weight': 0.4
            },
            'interaction_with_blacklist': {
                'weight': 0.5
            }
        }

    async def analyze_wallet(self, wallet_data: Dict) -> Dict:
        """Análisis avanzado de wallet usando múltiples métodos"""
        try:
            # Extraer características avanzadas
            features, temporal_patterns = self._extract_advanced_features(wallet_data)
            
            # Detectar anomalías
            anomaly_score = self._detect_anomalies(features)
            
            # Analizar patrones temporales
            pattern_score, patterns = self._analyze_temporal_patterns(temporal_patterns)
            
            # Verificar interacciones con blacklist
            blacklist_score = self._check_blacklist_interactions(wallet_data)
            
            # Calcular score final ponderado
            risk_score = self._calculate_final_score(
                anomaly_score=anomaly_score,
                pattern_score=pattern_score,
                blacklist_score=blacklist_score
            )
            
            # Identificar factores específicos de riesgo
            risk_factors = self._identify_specific_risks(
                wallet_data,
                patterns,
                anomaly_score,
                blacklist_score
            )
            
            return {
                "risk_score": round(risk_score, 2),
                "risk_level": self._get_risk_level(risk_score),
                "risk_factors": risk_factors,
                "analysis_details": {
                    "anomaly_score": round(anomaly_score, 2),
                    "pattern_score": round(pattern_score, 2),
                    "blacklist_score": round(blacklist_score, 2),
                    "temporal_patterns": patterns,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            raise Exception(f"Advanced ML analysis failed: {str(e)}")

    def _extract_advanced_features(self, wallet_data: Dict) -> Tuple[np.ndarray, Dict]:
        """Extrae características avanzadas para análisis"""
        transactions = wallet_data.get('transactions', [])
        if not transactions:
            return np.zeros((1, 8)), {}

        df = pd.DataFrame(transactions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Características temporales
        time_diffs = df['timestamp'].diff().dt.total_seconds().fillna(0)
        value_changes = df['value'].pct_change().fillna(0)
        
        # Calcular características avanzadas
        features = np.array([[
            len(transactions),                    # Número total de transacciones
            df['value'].mean(),                  # Valor promedio
            df['value'].std(),                   # Volatilidad
            len(df['to'].unique()),              # Addresses únicas
            time_diffs.mean(),                   # Tiempo promedio entre txs
            time_diffs.std(),                    # Variabilidad temporal
            value_changes.mean(),                # Cambio promedio en valores
            len(wallet_data.get('token_holdings', [])) # Diversidad de tokens
        ]])
        
        # Patrones temporales
        temporal_patterns = {
            'hourly_tx_counts': self._get_hourly_transaction_counts(df),
            'value_distribution': self._analyze_value_distribution(df),
            'address_patterns': self._analyze_address_patterns(df)
        }
        
        return features, temporal_patterns

    def _detect_anomalies(self, features: np.ndarray) -> float:
        """Detección mejorada de anomalías"""
        if features.shape[1] == 0:
            return 50.0
            
        # Normalizar características
        features_scaled = self.scaler.fit_transform(features)
        
        # Detectar anomalías
        self.isolation_forest.fit(features_scaled)
        anomaly_scores = self.isolation_forest.score_samples(features_scaled)
        
        # Convertir a score de riesgo (0-100)
        risk_score = (1 - (anomaly_scores + 1) / 2) * 100
        return float(risk_score[0])

    def _analyze_temporal_patterns(self, patterns: Dict) -> Tuple[float, Dict]:
        """Analiza patrones temporales para detectar comportamientos sospechosos"""
        risk_score = 0
        detected_patterns = {}
        
        # Analizar frecuencia de transacciones
        hourly_tx = patterns['hourly_tx_counts']
        if max(hourly_tx.values()) > self.suspicious_patterns['high_frequency_small_tx']['threshold']:
            risk_score += 30
            detected_patterns['high_frequency'] = True
        
        # Analizar distribución de valores
        value_dist = patterns['value_distribution']
        if value_dist['large_tx_ratio'] > 0.2:  # Más del 20% son transacciones grandes
            risk_score += 40
            detected_patterns['large_values'] = True
            
        # Analizar patrones de direcciones
        addr_patterns = patterns['address_patterns']
        if addr_patterns['reuse_ratio'] > 0.7:  # Alto reuso de direcciones
            risk_score += 20
            detected_patterns['address_reuse'] = True
            
        return min(risk_score, 100), detected_patterns

    def _check_blacklist_interactions(self, wallet_data: Dict) -> float:
        """Verifica interacciones con direcciones en lista negra"""
        if not wallet_data.get('transactions'):
            return 0
            
        interactions = 0
        total_tx = len(wallet_data['transactions'])
        
        for tx in wallet_data['transactions']:
            if tx['to'] in self.blacklisted_addresses or tx['from'] in self.blacklisted_addresses:
                interactions += 1
                
        return (interactions / total_tx) * 100 if total_tx > 0 else 0

    def _calculate_final_score(self, **scores) -> float:
        """Calcula score final ponderado"""
        weights = {
            'anomaly_score': 0.3,
            'pattern_score': 0.4,
            'blacklist_score': 0.3
        }
        
        final_score = sum(score * weights[name] for name, score in scores.items())
        return min(max(final_score, 0), 100)

    def _identify_specific_risks(self, wallet_data: Dict, patterns: Dict, 
                               anomaly_score: float, blacklist_score: float) -> List[Dict]:
        """Identifica factores específicos de riesgo"""
        risk_factors = []
        
        if anomaly_score > 70:
            risk_factors.append({
                "name": "Anomalous Behavior",
                "description": "Unusual transaction patterns detected",
                "severity": "HIGH",
                "score_contribution": round(anomaly_score * 0.3, 2)
            })
            
        if patterns.get('high_frequency'):
            risk_factors.append({
                "name": "High Frequency Trading",
                "description": "Unusual high frequency of transactions",
                "severity": "MEDIUM",
                "score_contribution": 30.0
            })
            
        if patterns.get('large_values'):
            risk_factors.append({
                "name": "Large Transactions",
                "description": "Significant number of high-value transactions",
                "severity": "HIGH",
                "score_contribution": 40.0
            })
            
        if blacklist_score > 0:
            risk_factors.append({
                "name": "Blacklist Interaction",
                "description": "Interactions with known suspicious addresses",
                "severity": "HIGH",
                "score_contribution": round(blacklist_score * 0.3, 2)
            })
            
        return risk_factors

    def _get_hourly_transaction_counts(self, df: pd.DataFrame) -> Dict:
        """Analiza la distribución horaria de transacciones"""
        return df.groupby(df['timestamp'].dt.hour).size().to_dict()

    def _analyze_value_distribution(self, df: pd.DataFrame) -> Dict:
        """Analiza la distribución de valores de transacciones"""
        mean_value = df['value'].mean()
        return {
            'large_tx_ratio': len(df[df['value'] > mean_value * 2]) / len(df),
            'small_tx_ratio': len(df[df['value'] < mean_value * 0.5]) / len(df)
        }

    def _analyze_address_patterns(self, df: pd.DataFrame) -> Dict:
        """Analiza patrones en el uso de direcciones"""
        unique_addresses = set(df['to'].unique()) | set(df['from'].unique())
        return {
            'unique_count': len(unique_addresses),
            'reuse_ratio': 1 - (len(unique_addresses) / (len(df) * 2))
        }

    def _get_risk_level(self, risk_score: float) -> str:
        """Determina el nivel de riesgo basado en el score"""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        return "LOW"
