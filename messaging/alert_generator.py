"""
Alert Generator: Builds UI alerts based on fraud detection results
"""

import json
from typing import Dict, Any


class AlertGenerator:
    def __init__(self, config_path: str = "../messaging_fraud_config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.templates = self.config['ui_alerts']['alert_templates']
    
    def generate(self, fraud_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alert UI configuration based on action"""
        action = fraud_result.get('action', 'WARN')
        template = self.templates.get(action, self.templates['WARN'])
        
        alert = {
            "color": template['color'],
            "icon": template['icon'],
            "title": template['title'],
            "message": template['message'],
            "trust_score": fraud_result.get('trust_score', 0),
            "reasons": fraud_result.get('reasons', []) if template['show_reasons'] else [],
            "actions": template['actions']
        }
        
        return alert
    
    def render_html(self, alert: Dict[str, Any]) -> str:
        """Render alert as HTML snippet"""
        reasons_html = ""
        if alert['reasons']:
            reasons_list = "\n".join([f"        <li>{r}</li>" for r in alert['reasons']])
            reasons_html = f"""
    <div class="alert-reasons">
        <ul>
{reasons_list}
        </ul>
    </div>"""
        
        actions_html = "\n".join([
            f'        <button class="alert-btn">{action}</button>'
            for action in alert['actions']
        ])
        
        return f"""
<div class="fraud-alert" style="border-left: 4px solid {alert['color']};">
    <div class="alert-icon">{alert['icon']}</div>
    <div class="alert-content">
        <div class="alert-title">{alert['title']}</div>
        <div class="alert-score">Trust Score: {alert['trust_score']}</div>
        <div class="alert-message">{alert['message']}</div>{reasons_html}
    </div>
    <div class="alert-actions">
{actions_html}
    </div>
</div>
"""


# Example usage
if __name__ == "__main__":
    generator = AlertGenerator()
    
    sample_result = {
        "trust_score": 40,
        "action": "BLOCK",
        "reasons": [
            "Policy gate: Credential/account verification request detected",
            "Phishing: Urgent/threatening language",
            "Policy gate: URL + urgency language on high amount (phishing)"
        ]
    }
    
    print("=" * 60)
    print("Testing Alert Generator")
    print("=" * 60)
    
    alert = generator.generate(sample_result)
    print("\nAlert Config:")
    print(json.dumps(alert, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)
    print("HTML Output:")
    print("=" * 60)
    print(generator.render_html(alert))
