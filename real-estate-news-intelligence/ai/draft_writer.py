class DraftWriter:
    def generate_news_draft(self, topic, materials):
        draft = f'''
{topic.get('title')}

导语：
{topic.get('summary')}

一、事件经过

根据目前公开信息，{materials.get('background')}。

二、行业背景

从行业角度来看，{materials.get('industry_analysis')}。

三、市场影响

市场人士认为，{materials.get('market_impact')}。
'''

        return draft
