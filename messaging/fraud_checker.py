"""
Fraud Checker: Calls the FastAPI backend with extracted data
"""

import requests
import json
import time
from typing import Dict, Any


class FraudChecker:
    def __init__(self, config_path: str = "../messaging_fraud_config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.api = self.config['api_integration']
        self.endpoint = self.api['endpoint']
    
    def check(self, extracted_data: Dict, payer_vpa: str = "user@paytm") -> Dict[str, Any]:
        """Send extracted data to fraud detection API"""
        payload = {
            "transaction_id": f"MSG-{int(time.time() * 1000)}",
            "payer_vpa": payer_vpa,
            "payee_vpa": extracted_data.get('payee_vpa'),
            "mobile_number": extracted_data.get('mobile_number'),
            "amount": extracted_data.get('amount'),
            "message": extracted_data.get('message'),
            "transaction_type": extracted_data.get('transaction_type', 'pay'),
            "payee_new": 1
        }
        
        try:
            response = requests.post(
                self.endpoint,
                headers=self.api['headers'],
                json=payload,
                timeout=3
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "error": str(e),
                "trust_score": 0,
                "action": "ERROR",
                "reasons": ["Could not connect to fraud detection service"]
            }


# Example usage
if __name__ == "__main__":
    from parser import PaymentMessageParser
    
    parser = PaymentMessageParser()
    checker = FraudChecker()
    
    test_message = "Hi! Please pay ₹15000 to verify-security@upi. URGENT account verification required."
    
    print("=" * 60)
    print("Testing Message Fraud Detection")
    print("=" * 60)
    print(f"\nMessage: {test_message}\n")
    
    extracted = parser.extract(test_message)
    print("Extracted Data:")
    print(json.dumps(extracted, indent=2, ensure_ascii=False))
    
    if parser.validate(extracted):
        print("\n" + "=" * 60)
        print("Calling Fraud Detection API...")
        print("=" * 60)
        
        result = checker.check(extracted, payer_vpa="vikas@paytm")
        
        print("\nFraud Check Result:")
        print(f"  Trust Score: {result.get('trust_score', 'N/A')}")
        print(f"  Action: {result.get('action', 'N/A')}")
        print(f"  Reasons:")
        for reason in result.get('reasons', []):
            print(f"    • {reason}")
        
        if 'subscores' in result:
            print(f"\n  Subscores:")
            for agent, score in result['subscores'].items():
                print(f"    {agent.capitalize()}: {score:.2f}")
    else:
        print("\n Invalid data extracted - missing required fields")
