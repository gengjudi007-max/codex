RISK_TERMS = {
    'debt_risk': ['债务违约', '无法偿还', '流动性压力'],
    'profit_risk': ['亏损', '盈利下滑', '由盈转亏'],
    'liquidity_risk': ['现金流紧张', '展期', '延期支付'],
    'legal_risk': ['诉讼', '仲裁', '冻结'],
    'liquidation_risk': ['清盘', '清算']
}


class RiskExtractor:
    def extract(self, text):
        risks = []

        for risk_type, keywords in RISK_TERMS.items():
            for keyword in keywords:
                if keyword in text:
                    risks.append({
                        'risk_type': risk_type,
                        'keyword': keyword
                    })

        return risks
