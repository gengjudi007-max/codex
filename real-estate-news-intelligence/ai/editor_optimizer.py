REPLACE_RULES = {
    '公司表示': '相关人士表示',
    '持续深耕': '继续布局',
    '赋能': '支持',
    '高质量发展': '业务发展'
}


class EditorOptimizer:
    def optimize(self, text):
        optimized = text

        for old, new in REPLACE_RULES.items():
            optimized = optimized.replace(old, new)

        return optimized


if __name__ == '__main__':
    optimizer = EditorOptimizer()

    sample = '公司表示，将持续深耕房地产行业，赋能城市高质量发展。'

    print(optimizer.optimize(sample))
