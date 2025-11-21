"""
Message Parser: Extracts payment request data from text messages
"""

import re
import json
from typing import Dict, Optional


class PaymentMessageParser:
    def __init__(self, config_path: str = "../messaging_fraud_config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.rules = self.config['data_extraction']['rules']
    
    def extract(self, message_text: str) -> Dict[str, Optional[str]]:
        """Extract structured payment data from a message"""
        result = {}
        
        for rule in self.rules:
            field = rule['field']
            patterns = rule['patterns']
            
            if field == 'message':
                result[field] = message_text
                continue
            
            # Try each pattern until one matches
            for pattern in patterns:
                match = re.search(pattern, message_text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    
                    # Apply transforms
                    if field == 'amount':
                        value = float(value.replace(',', ''))
                    
                    result[field] = value
                    break
            
            # Set default if not found
            if field not in result:
                if field == 'transaction_type':
                    result[field] = 'pay'
                else:
                    result[field] = None
        
        return result
    
    def validate(self, extracted: Dict) -> bool:
        """Check if required fields are present"""
        required = [r['field'] for r in self.rules if r.get('required')]
        return all(extracted.get(f) is not None for f in required)


# Example usage
if __name__ == "__main__":
    parser = PaymentMessageParser()
    
    test_message = "URGENT! Pay ₹8000 to verify-security@upi for account verification. Contact: 9876543210"
    data = parser.extract(test_message)
    print("Extracted:", json.dumps(data, indent=2, ensure_ascii=False))
    print("Valid:", parser.validate(data))
