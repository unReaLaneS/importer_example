from decimal import Decimal

import importer


class TextXMLImporter(importer.XMLImporter):
    SCHEMA = {
        'stock_online': int,
        'stock_offline': int,
        'warranty': int,
        'weight': Decimal,
        'price': Decimal,
        'images': {
            'height': int,
            'width': int,
        },
        'properties': {},
    }

    def save_product(self):
        # save product to database here
        print (self.get_product())


with open('products.xml') as f:
    p = TextXMLImporter()
    p.parse(f)


with open('products-tags.xml') as f:
    p = TextXMLImporter()
    p.parse(f)
