from datetime import datetime


class TopicCardGenerator:
    def generate(self, topic_data):
        return {
            'topic_title': topic_data.get('topic_title'),
            'trigger_event': topic_data.get('trigger_event'),
            'source': topic_data.get('source'),
            'importance': topic_data.get('importance'),
            'core_fact': topic_data.get('core_fact'),
            'abnormal_point': topic_data.get('abnormal_point'),
            'news_angle': topic_data.get('news_angle'),
            'interview_targets': topic_data.get('interview_targets', []),
            'created_at': datetime.now().isoformat()
        }


if __name__ == '__main__':
    generator = TopicCardGenerator()

    card = generator.generate({
        'topic_title': '城投拿地占比持续上升',
        'trigger_event': '重点城市土地市场变化',
        'source': '中国土地市场网',
        'importance': 'high',
        'core_fact': '多地城投成为土地市场主要买方',
        'abnormal_point': '民企拿地明显减少',
        'news_angle': '地方财政与土地市场变化',
        'interview_targets': [
            '自然资源部门人士',
            '券商地产分析师',
            '城投平台人士'
        ]
    })

    print(card)
