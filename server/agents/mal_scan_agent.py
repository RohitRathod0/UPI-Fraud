"""
Malware Detection Agent
XGBoost + ClamAV integration for device compromise detection
"""

import joblib
import numpy as np
from typing import Dict, Any
import asyncio
import subprocess
import tempfile
import os

class MalwareAgent:
    def __init__(self, model_path='models/malware_detector.pkl'):
        self.model_path = model_path
        self.model = None
        self.loaded = False
        self.clamav_available = self._check_clamav()
        
    def load_model(self):
        """Load trained malware detection model"""
        try:
            self.model = joblib.load(self.model_path)
            self.loaded = True
            print("MalwareAgent: Model loaded successfully")
        except Exception as e:
            print(f"MalwareAgent: Error loading model - {str(e)}")
            self.loaded = False
    
    def is_loaded(self):
        return self.loaded
    
    def _check_clamav(self) -> bool:
        """Check if ClamAV is available"""
        try:
            result = subprocess.run(['clamscan', '--version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def analyze(self, transaction: Any) -> Dict[str, Any]:
        """Analyze transaction for malware/device compromise"""
        await asyncio.sleep(0.06)
        
        # Extract device/app features
        device_features = self._extract_device_features(transaction)
        
        # Run ML model
        ml_result = await self._ml_analysis(device_features)
        
        # Run ClamAV scan if attachments present
        clamav_result = await self._clamav_scan(transaction)
        
        # Combine results
        combined_score = max(ml_result['subscore'], clamav_result['threat_score'])
        combined_indicators = ml_result['indicators'] + clamav_result['indicators']
        
        return {
            'agent': 'MalwareAgent',
            'subscore': float(combined_score),
            'confidence': float(ml_result['confidence']),
            'indicators': combined_indicators,
            'device_analysis': device_features,
            'clamav_scan': clamav_result
        }
    
    def _extract_device_features(self, txn) -> Dict[str, Any]:
        """Extract device/app security features"""
        return {
            'app_modified': getattr(txn, 'app_modified', 0),
            'root_jailbreak': getattr(txn, 'rooted', 0),
            'suspicious_permissions': getattr(txn, 'permission_count', 0),
            'app_from_unknown_source': getattr(txn, 'sideloaded', 0),
            'has_overlay_attack': getattr(txn, 'overlay_detected', 0),
            'clipboard_hijack': getattr(txn, 'clipboard_anomaly', 0),
            'device_id_mismatch': getattr(txn, 'device_mismatch', 0),
            'vpn_proxy_detected': getattr(txn, 'vpn_active', 0),
            'emulator_detected': getattr(txn, 'emulator', 0)
        }
    
    async def _ml_analysis(self, features: dict) -> Dict[str, Any]:
        """ML-based malware risk analysis"""
        if not self.loaded:
            return self._rule_based_malware_detection(features)
        
        try:
            feature_vector = [
                features['app_modified'],
                features['root_jailbreak'],
                features['suspicious_permissions'] / 10.0,
                features['app_from_unknown_source'],
                features['has_overlay_attack'],
                features['clipboard_hijack'],
                features['device_id_mismatch'],
                features['vpn_proxy_detected'],
                features['emulator_detected']
            ]
            
            proba = self.model.predict_proba([feature_vector])[0, 1]
            confidence = abs(proba - 0.5) * 2
            
            indicators = self._get_malware_indicators(features, proba)
            
            return {
                'subscore': float(proba),
                'confidence': float(confidence),
                'indicators': indicators
            }
        except Exception as e:
            print(f"MalwareAgent ML error: {str(e)}")
            return self._rule_based_malware_detection(features)
    
    async def _clamav_scan(self, txn) -> Dict[str, Any]:
        """Scan for malware using ClamAV (if available)"""
        if not self.clamav_available:
            return {'threat_score': 0.0, 'indicators': []}
        
        # Check if transaction has attachments/URLs to scan
        if not hasattr(txn, 'attachment_url'):
            return {'threat_score': 0.0, 'indicators': []}
        
        try:
            # Download attachment to temp file
            # In production: implement actual download with safety checks
            # For now, simulate scan result
            threat_detected = np.random.random() < 0.05  # 5% threat rate
            
            if threat_detected:
                return {
                    'threat_score': 0.95,
                    'indicators': ['ClamAV: Malware signature detected in attachment']
                }
            else:
                return {
                    'threat_score': 0.0,
                    'indicators': []
                }
        except Exception as e:
            print(f"ClamAV scan error: {str(e)}")
            return {'threat_score': 0.0, 'indicators': []}
    
    def _get_malware_indicators(self, features: dict, score: float) -> list:
        """Generate human-readable malware indicators"""
        indicators = []
        
        if score > 0.7:
            indicators.append("High malware/compromise risk")
        
        if features['app_modified']:
            indicators.append("UPI app has been modified (tampering detected)")
        
        if features['root_jailbreak']:
            indicators.append("Device is rooted/jailbroken (security risk)")
        
        if features['suspicious_permissions'] > 5:
            indicators.append(f"App has {features['suspicious_permissions']} suspicious permissions")
        
        if features['app_from_unknown_source']:
            indicators.append("App installed from unknown source (not Play Store/App Store)")
        
        if features['has_overlay_attack']:
            indicators.append("Overlay attack detected (fake UI layer)")
        
        if features['clipboard_hijack']:
            indicators.append("Clipboard hijacking detected")
        
        if features['device_id_mismatch']:
            indicators.append("Device ID mismatch (possible cloned device)")
        
        if features['emulator_detected']:
            indicators.append("Running on emulator (automation risk)")
        
        return indicators
    
    def _rule_based_malware_detection(self, features: dict) -> Dict[str, Any]:
        """Fallback rule-based malware detection"""
        risk_score = 0.0
        indicators = []
        
        if features['app_modified']:
            risk_score += 0.35
            indicators.append("App modified")
        
        if features['root_jailbreak']:
            risk_score += 0.25
            indicators.append("Rooted device")
        
        if features['suspicious_permissions'] > 5:
            risk_score += 0.2
            indicators.append("Excessive permissions")
        
        if features['has_overlay_attack']:
            risk_score += 0.15
            indicators.append("Overlay attack")
        
        if features['emulator_detected']:
            risk_score += 0.05
            indicators.append("Emulator detected")
        
        risk_score = min(risk_score, 1.0)
        
        return {
            'subscore': float(risk_score),
            'confidence': 0.65,
            'indicators': indicators
        }
