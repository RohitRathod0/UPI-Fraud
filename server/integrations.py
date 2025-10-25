"""
External API Integrations
Google Safe Browsing, PhishTank, VirusTotal, ClamAV
"""

import requests
import asyncio
import aiohttp
from typing import Dict, Any, Optional
import hashlib
import json
from functools import lru_cache
import redis
from datetime import timedelta

from config import config

# Redis cache for API results
redis_client = redis.from_url(config.REDIS_URL) if config.REDIS_URL else None

class SafeBrowsingAPI:
    """Google Safe Browsing API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.GOOGLE_SAFE_BROWSING_API_KEY
        self.base_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        self.enabled = bool(self.api_key) and config.ENABLE_EXTERNAL_API_CALLS
    
    async def check_url(self, url: str) -> Dict[str, Any]:
        """
        Check if URL is malicious using Google Safe Browsing
        
        Returns:
            {
                'is_threat': bool,
                'threat_types': list,
                'platforms': list
            }
        """
        if not self.enabled:
            return {'is_threat': False, 'threat_types': [], 'source': 'disabled'}
        
        # Check cache first
        cache_key = f"safebrowsing:{hashlib.md5(url.encode()).hexdigest()}"
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        payload = {
            "client": {
                "clientId": "upi-fraud-detection",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        result = {
                            'is_threat': 'matches' in data,
                            'threat_types': [m['threatType'] for m in data.get('matches', [])],
                            'platforms': [m['platformType'] for m in data.get('matches', [])],
                            'source': 'google_safe_browsing'
                        }
                        
                        # Cache result for 1 hour
                        if redis_client:
                            redis_client.setex(cache_key, timedelta(hours=1), json.dumps(result))
                        
                        return result
                    else:
                        return {'is_threat': False, 'threat_types': [], 'source': 'api_error'}
        
        except Exception as e:
            print(f"Safe Browsing API error: {str(e)}")
            return {'is_threat': False, 'threat_types': [], 'source': 'exception'}


class PhishTankAPI:
    """PhishTank API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.PHISHTANK_API_KEY
        self.base_url = "https://checkurl.phishtank.com/checkurl/"
        self.enabled = config.ENABLE_EXTERNAL_API_CALLS
    
    async def check_url(self, url: str) -> Dict[str, Any]:
        """
        Check if URL is in PhishTank database
        
        Returns:
            {
                'is_phishing': bool,
                'verified': bool,
                'phish_id': int or None
            }
        """
        if not self.enabled:
            return {'is_phishing': False, 'verified': False, 'source': 'disabled'}
        
        # Check cache
        cache_key = f"phishtank:{hashlib.md5(url.encode()).hexdigest()}"
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        payload = {
            'url': url,
            'format': 'json'
        }
        
        if self.api_key:
            payload['app_key'] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    data=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        result = {
                            'is_phishing': data['results']['in_database'],
                            'verified': data['results'].get('verified', False),
                            'phish_id': data['results'].get('phish_id'),
                            'source': 'phishtank'
                        }
                        
                        # Cache for 6 hours
                        if redis_client:
                            redis_client.setex(cache_key, timedelta(hours=6), json.dumps(result))
                        
                        return result
                    else:
                        return {'is_phishing': False, 'verified': False, 'source': 'api_error'}
        
        except Exception as e:
            print(f"PhishTank API error: {str(e)}")
            return {'is_phishing': False, 'verified': False, 'source': 'exception'}


class VirusTotalAPI:
    """VirusTotal API integration (optional, free tier 4 req/min)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('VIRUSTOTAL_API_KEY')
        self.base_url = "https://www.virustotal.com/api/v3"
        self.enabled = bool(self.api_key) and config.ENABLE_EXTERNAL_API_CALLS
    
    async def scan_url(self, url: str) -> Dict[str, Any]:
        """
        Scan URL with VirusTotal
        
        Returns:
            {
                'malicious_count': int,
                'suspicious_count': int,
                'clean_count': int,
                'total_engines': int
            }
        """
        if not self.enabled:
            return {'malicious_count': 0, 'total_engines': 0, 'source': 'disabled'}
        
        # Check cache
        cache_key = f"virustotal:{hashlib.md5(url.encode()).hexdigest()}"
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        headers = {
            'x-apikey': self.api_key
        }
        
        try:
            # URL encode
            url_id = hashlib.sha256(url.encode()).hexdigest()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/urls/{url_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        stats = data['data']['attributes']['last_analysis_stats']
                        
                        result = {
                            'malicious_count': stats.get('malicious', 0),
                            'suspicious_count': stats.get('suspicious', 0),
                            'clean_count': stats.get('harmless', 0),
                            'total_engines': sum(stats.values()),
                            'source': 'virustotal'
                        }
                        
                        # Cache for 12 hours
                        if redis_client:
                            redis_client.setex(cache_key, timedelta(hours=12), json.dumps(result))
                        
                        return result
                    else:
                        return {'malicious_count': 0, 'total_engines': 0, 'source': 'api_error'}
        
        except Exception as e:
            print(f"VirusTotal API error: {str(e)}")
            return {'malicious_count': 0, 'total_engines': 0, 'source': 'exception'}


class IntegrationService:
    """Unified service for all external integrations"""
    
    def __init__(self):
        self.safe_browsing = SafeBrowsingAPI()
        self.phishtank = PhishTankAPI()
        self.virustotal = VirusTotalAPI()
    
    async def check_url_reputation(self, url: str) -> Dict[str, Any]:
        """
        Check URL against multiple threat intelligence sources
        
        Returns aggregated threat assessment
        """
        if not url or not url.startswith('http'):
            return {
                'is_malicious': False,
                'threat_score': 0.0,
                'sources_checked': []
            }
        
        # Run all checks in parallel
        results = await asyncio.gather(
            self.safe_browsing.check_url(url),
            self.phishtank.check_url(url),
            self.virustotal.scan_url(url),
            return_exceptions=True
        )
        
        safe_browsing_result, phishtank_result, virustotal_result = results
        
        # Aggregate results
        threat_score = 0.0
        sources = []
        
        if isinstance(safe_browsing_result, dict) and safe_browsing_result.get('is_threat'):
            threat_score += 0.4
            sources.append('Google Safe Browsing')
        
        if isinstance(phishtank_result, dict) and phishtank_result.get('is_phishing'):
            threat_score += 0.3
            sources.append('PhishTank')
        
        if isinstance(virustotal_result, dict):
            malicious_ratio = virustotal_result.get('malicious_count', 0) / max(virustotal_result.get('total_engines', 1), 1)
            if malicious_ratio > 0.1:  # >10% engines flag as malicious
                threat_score += 0.3 * malicious_ratio
                sources.append('VirusTotal')
        
        return {
            'is_malicious': threat_score > 0.3,
            'threat_score': min(threat_score, 1.0),
            'sources_flagged': sources,
            'details': {
                'safe_browsing': safe_browsing_result if isinstance(safe_browsing_result, dict) else {},
                'phishtank': phishtank_result if isinstance(phishtank_result, dict) else {},
                'virustotal': virustotal_result if isinstance(virustotal_result, dict) else {}
            }
        }


# Global instance
integration_service = IntegrationService()
