class TopicScoringEngine:
    def __init__(self):
        self.weights = {
            'importance': 30,
            'timeliness': 20,
            'abnormality': 20,
            'exclusivity': 15,
            'data_support': 10,
            'interview_feasibility': 5
        }

    def calculate_score(self, metrics):
        total = 0

        for key, weight in self.weights.items():
            total += metrics.get(key, 0) * weight

        return round(total / 100, 2)


if __name__ == '__main__':
    engine = TopicScoringEngine()

    score = engine.calculate_score({
        'importance': 90,
        'timeliness': 85,
        'abnormality': 80,
        'exclusivity': 75,
        'data_support': 95,
        'interview_feasibility': 60
    })

    print('Topic Score:', score)
