"""
Trust Score Aggregator + Policy Gates
Combines subscores and enforces strict safety rules
"""

from typing import Dict, Any, List
import re

# Keyword sets for policy checks
PROMO_WORDS = ['offer', 'prize', 'reward', 'cashback', 'bonus', 'limited', 'deal', 'discount', 'free', 'win', 'won', 'winner', 'grab', 'claim']
URGENCY_WORDS = ['urgent', 'immediately', 'emergency', 'hurry', 'now', 'today', 'asap', 'final', 'last', 'quick', 'limited']
CRED_WORDS = ['otp', 'pin', 'password', 'cvv', 'verify', 'verification', 'account', 'blocked', 'locked', 'suspended']
URL_MARKERS = ['http', 'www', 'bit.ly', 'tinyurl', '.com', '.in']
QR_WORDS = ['qr', 'scan', 'code', 'qrcode']

# NEW: illicit/adult solicitation signals
ADULT_WORDS = ['porn', 'pornhub', 'xnxx', 'xvideos', 'onlyfans', 'escort', 'adult', 'sex', 'xxx']
SOLICIT_WORDS = ['services', 'genuine services', 'dm', 'message me', 'view my story', 'watch highlights', 'proof']


class TrustScoreAgent:
    def __init__(self):
        # Weights can be tuned
        self.weights = {
            'phishing': 0.30,
            'quishing': 0.25,
            'collect':  0.25,
            'malware':  0.20
        }

    def aggregate(self, subs: Dict[str, float], message: str, amount: float,
                  indicators_by_agent: Dict[str, List[str]]) -> Dict[str, Any]:
        # Compute risk and trust
        risk = 0.0
        for k, w in self.weights.items():
            risk += subs.get(k, 0.0) * w
        trust = max(0, min(100, int(round((1.0 - risk) * 100))))

        action = self._base_action(trust)
        reasons: List[str] = []

        # Collect indicators from agents (surface anything flagged)
        for agent_name, indicators in indicators_by_agent.items():
            for ind in indicators:
                if '⚠️' in ind or 'policy gate' in ind.lower() or 'detected' in ind.lower():
                    reasons.append(f"{agent_name.capitalize()}: {ind}")

        # Apply strict policy gates
        result = {
            'trust_score': trust,
            'action': action,
            'reasons': reasons,
            'subscores': subs
        }
        result = self._policy_gates(result, message.lower(), float(amount), indicators_by_agent)

        # Ensure at least one reason exists
        if not result['reasons']:
            if result['trust_score'] >= 90:
                result['reasons'].append('Transaction appears safe based on AI analysis')
            elif result['trust_score'] >= 70:
                result['reasons'].append('Moderate risk detected; review details carefully')
            else:
                result['reasons'].append('High risk detected by AI fraud models')

        return result

    def _base_action(self, trust: int) -> str:
        if trust >= 90: return "ALLOW"
        if trust >= 50: return "WARN"
        if trust >= 35: return "HUMAN_REVIEW"
        return "BLOCK"

    def _policy_gates(self, agg: Dict[str, Any], msg: str, amount: float,
                      ind: Dict[str, List[str]]) -> Dict[str, Any]:
        reasons: List[str] = []
        m = msg.lower()

        # 1) Credential / account text → immediate action by amount
        if any(k in m for k in CRED_WORDS):
            if amount >= 50000:
                agg['action'] = 'BLOCK'
                agg['trust_score'] = min(agg['trust_score'], 30)
                reasons.append('Policy gate: High-value transaction with credential/account text')
            elif amount >= 10000:
                agg['action'] = 'HUMAN_REVIEW'
                agg['trust_score'] = min(agg['trust_score'], 45)
                reasons.append('Policy gate: Medium-value transaction with credential/account text')
            else:
                agg['action'] = 'WARN'
                agg['trust_score'] = min(agg['trust_score'], 55)
                reasons.append('Policy gate: Credential/account verification request detected')

        # 2) URL + urgency on significant amount → BLOCK
        if any(p in m for p in URL_MARKERS) and any(u in m for u in URGENCY_WORDS) and amount >= 5000:
            agg['action'] = 'BLOCK'
            agg['trust_score'] = min(agg['trust_score'], 40)
            reasons.append('Policy gate: URL + urgency language on high amount (phishing)')

        # 3) Promo/offer + (urgency OR number OR URL) → WARN/BLOCK
        has_promo = any(w in m for w in PROMO_WORDS)
        has_urgency = any(w in m for w in URGENCY_WORDS)
        has_url = any(w in m for w in URL_MARKERS)
        has_qr = any(w in m for w in QR_WORDS)
        number_in_text = bool(re.search(r'(rs\.?\s*\d[\d,]*|₹\s*\d[\d,]*|\b\d{4,}\b)', m))

        if has_promo and (has_urgency or number_in_text or has_url):
            if amount >= 10000:
                agg['action'] = 'BLOCK'
                agg['trust_score'] = min(agg['trust_score'], 40)
                reasons.append('Policy gate: Promotional/offer language with urgency/amount (high value)')
            else:
                agg['action'] = 'WARN'
                agg['trust_score'] = min(agg['trust_score'], 60)
                reasons.append('Policy gate: Promotional/offer language with urgency/amount')

        # 4) Urgency + explicit amount mention (even without promo) → WARN for mid amounts
        if has_urgency and number_in_text and agg['action'] == 'ALLOW':
            if amount >= 5000:
                agg['action'] = 'WARN'
                agg['trust_score'] = min(agg['trust_score'], 65)
                reasons.append('Policy gate: Urgency with explicit amount requested')

        # 5) QR/URL + prize/offer scam
        if (has_qr or has_url) and has_promo:
            if amount >= 10000:
                agg['action'] = 'BLOCK'
                agg['trust_score'] = min(agg['trust_score'], 35)
                reasons.append('Policy gate: QR/URL + prize/offer scam (high amount)')
            else:
                agg['action'] = 'WARN'
                agg['trust_score'] = min(agg['trust_score'], 55)
                reasons.append('Policy gate: QR/URL + prize/offer scam')

        # 5b) NEW: Any explicit external link → minimum WARN (prevents ALLOW on spam links)
        if has_url and agg['action'] == 'ALLOW':
            if amount >= 1000:
                agg['action'] = 'WARN'
                agg['trust_score'] = min(agg['trust_score'], 70)
                reasons.append('Policy gate: External link present in payment note')

        # 6) Threatening collect requests
        if 'collect' in m or 'payment request' in m:
            if any(w in m for w in ['legal','court','police','arrest','penalty','fine','lawyer','case']) and any(u in m for u in URGENCY_WORDS + ['final','now','today']):
                if amount >= 5000:
                    agg['action'] = 'BLOCK'
                    agg['trust_score'] = min(agg['trust_score'], 40)
                    reasons.append('Policy gate: Threatening collect request (legal/urgent)')
                else:
                    agg['action'] = 'WARN'
                    agg['trust_score'] = min(agg['trust_score'], 60)
                    reasons.append('Policy gate: Threatening collect request')

        # 7) NEW: Adult/illicit service solicitation + link/solicit words → WARN/BLOCK
        has_adult = any(w in m for w in ADULT_WORDS)
        has_solicit = any(w in m for w in SOLICIT_WORDS)
        if has_adult and (has_url or has_solicit):
            if amount >= 5000:
                agg['action'] = 'BLOCK'
                agg['trust_score'] = min(agg['trust_score'], 35)
                reasons.append('Policy gate: Adult/illicit service solicitation with link (high amount)')
            else:
                agg['action'] = 'WARN'
                agg['trust_score'] = min(agg['trust_score'], 55)
                reasons.append('Policy gate: Adult/illicit service solicitation detected')

        # 8) Global safety cap to prevent ALLOW on suspicious text with high amount
        if any(w in m for w in (CRED_WORDS + URGENCY_WORDS + PROMO_WORDS + ['legal action'])) and amount >= 10000 and agg['action'] == 'ALLOW':
            agg['action'] = 'WARN'
            agg['trust_score'] = min(agg['trust_score'], 60)
            reasons.append('Safety cap: Suspicious text on high amount')

        # Merge
        agg['reasons'].extend(reasons)

        # Fallback reason if low trust and still empty
        if not agg['reasons'] and agg['trust_score'] < 70:
            agg['reasons'].append('Low trust score based on AI agent analysis')

        return agg
