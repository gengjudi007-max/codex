from pipelines.database import Database


class IngestPipeline:
    def __init__(self):
        self.db = Database()
        self.db.initialize()

    def save_raw_document(self, document):
        query = '''
        INSERT OR IGNORE INTO raw_documents (
            source_name,
            source_type,
            source_url,
            title,
            publish_time,
            raw_text,
            raw_html
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''

        self.db.execute(query, [
            document.get('source_name'),
            document.get('source_type'),
            document.get('source_url'),
            document.get('title'),
            document.get('publish_time'),
            document.get('raw_text'),
            document.get('raw_html')
        ])


if __name__ == '__main__':
    pipeline = IngestPipeline()

    sample_document = {
        'source_name': '住房和城乡建设部',
        'source_type': 'policy',
        'source_url': 'https://example.com/policy',
        'title': '房地产市场稳定政策',
        'publish_time': '2026-05-06',
        'raw_text': '政策正文',
        'raw_html': '<html></html>'
    }

    pipeline.save_raw_document(sample_document)
    print('Document saved.')
