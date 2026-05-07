class AnnouncementNewsGenerator:
    def generate(self, parsed_result):
        title = parsed_result.get('title', '')
        companies = '、'.join(parsed_result.get('companies', []))
        risks = parsed_result.get('risks', [])

        risk_text = '；'.join([
            f"{item['risk_type']}({item['keyword']})"
            for item in risks
        ])

        return f'''
{title}

导语：
{companies}发布最新公告。公告内容显示，相关企业涉及{risk_text}等事项，市场关注其后续经营与资金情况。

一、公告核心内容

根据公告内容，企业披露了相关经营与财务情况，并对后续安排进行了说明。

二、市场关注点

市场关注的重点包括债务风险、现金流情况、资产处置以及未来融资能力。

三、行业影响

在房地产行业持续调整背景下，类似公告被认为反映了行业风险出清与企业调整趋势。
'''
