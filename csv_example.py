from decimal import Decimal

import importer


class TestCSVImporter(importer.CSVDictImporter):
    DIVIDERS = {
        'category': '>',
        'images': ',',
    }
    SCHEMA = {
        'stock_online': int,
        'stock_offline': int,
        'warranty': int,
        'weight': Decimal,
    }


with open('products.csv') as f:
    for row in TestCSVImporter(f):
        # save product to database here
        print (row)
