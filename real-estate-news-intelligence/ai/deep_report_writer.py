class DeepReportWriter:
    def generate_deep_report(self, topic, data_points):
        report = f'''
标题：{topic.get('title')}

导语：
{topic.get('lead')}

第一部分：发生了什么

{data_points.get('event_detail')}

第二部分：为什么发生

{data_points.get('background_analysis')}

第三部分：意味着什么

{data_points.get('future_impact')}
'''

        return report
