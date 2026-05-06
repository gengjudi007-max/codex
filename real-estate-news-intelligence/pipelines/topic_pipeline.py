from analyzers.topic_scoring_engine import TopicScoringEngine
from analyzers.topic_card_generator import TopicCardGenerator


class TopicPipeline:
    def __init__(self):
        self.scoring_engine = TopicScoringEngine()
        self.card_generator = TopicCardGenerator()

    def build_topic(self, raw_topic):
        score = self.scoring_engine.calculate_score({
            'importance': raw_topic.get('importance', 50),
            'timeliness': raw_topic.get('timeliness', 50),
            'abnormality': raw_topic.get('abnormality', 50),
            'exclusivity': raw_topic.get('exclusivity', 50),
            'data_support': raw_topic.get('data_support', 50),
            'interview_feasibility': raw_topic.get('interview_feasibility', 50)
        })

        raw_topic['total_score'] = score

        return self.card_generator.generate(raw_topic)
