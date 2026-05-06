import csv

from pipelines.database import Database


class CRICImporter:
    def __init__(self):
        self.db = Database()
        self.db.initialize()

    def import_land_csv(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                query = '''
                INSERT INTO land_transactions (
                    city,
                    parcel_name,
                    transaction_price,
                    winner_company,
                    source_name,
                    source_url
                ) VALUES (?, ?, ?, ?, ?, ?)
                '''

                self.db.execute(query, [
                    row.get('city'),
                    row.get('parcel_name'),
                    row.get('transaction_price'),
                    row.get('winner_company'),
                    'CRIC',
                    'manual_import'
                ])
