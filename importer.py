import csv
import logging
import xml.sax
from decimal import Decimal, InvalidOperation

logger = logging.getLogger('parser')


class Base:
    def convert_values(self, schema, data):
        for key, fn in schema.items():
            if isinstance(fn, dict):
                # skip nested schemas
                continue

            if key in data:
                try:
                    data[key] = fn(data[key])
                except ValueError:
                    logger.warning(
                        'Key {} cant be converted to {}. Value: {}'.format(key, fn.__name__, data[key])
                    )
                except InvalidOperation:
                    logger.warning(
                        'Key {} cant be converted to decimal. Value: {}'.format(key, data[key])
                    )

        return data


class CSVDictImporter(Base, csv.DictReader):
    PROPERTY_DIVIDER = ','
    KEY_VALUE_DIVIDER = ':'

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

    def __next__(self):
        data = super().__next__()

        # divide complex fields
        for field, divider in self.DIVIDERS.items():
            if field in data:
                data[field] = data[field].split(divider)

        data = self.convert_values(self.SCHEMA, data)

        if 'properties' in data:
            data['properties'] = self.process_properties(data['properties'])

        return data

    def process_properties(self, data):
        props = {}
        for prop in data.split(self.PROPERTY_DIVIDER):
            try:
                key, value = prop.split(self.KEY_VALUE_DIVIDER)
                props[key] = value
            except ValueError:
                pass

        return props


class XMLImporter(Base, xml.sax.ContentHandler):
    content = ''
    product = None
    in_product = False
    in_properties = False
    in_packaging = False

    tags = {
        'id', 'ean', 'upc', 'name', 'brand', 'model', 'price', 'old_price',
        'sale_price', 'stock_online', 'stock_offline', 'warranty', 'url',
        'small_description', 'description',
    }

    SCHEMA = {
        'stock_online': int,
        'stock_offline': int,
        'warranty': int,
        'weight': Decimal,
        'images': {
            'height': int,
            'width': int,
        },
        'properties': {},
    }

    def startElement(self, name, attrs):  # noqa
        name = name.lower()

        if name == 'product':
            self.in_product = True
            self.product = dict(images=list(), properties=list(), categories=list(), packaging=list())
            self.product.update(attrs)

        if name == 'image' and self.in_product:
            if attrs.get('url'):
                self.product['images'].append(self.convert_values(self.SCHEMA['images'], dict(attrs)))

        if name == 'packaging':
            self.in_packaging = True

        if name == 'property':
            if self.in_properties:
                self.product['properties'].append(self.convert_values(self.SCHEMA['properties'], dict(attrs)))

            if self.in_packaging:
                self.product['packaging'].append(self.convert_values(self.SCHEMA['properties'], dict(attrs)))

        if name == 'properties':
            self.in_properties = True

    def endElement(self, name):
        name = name.lower()

        if name == 'product':
            self.in_product = False
            self.save_product()

        if name == 'category':
            # add category
            self.product['categories'].append(self.content.strip())

        if name == 'packaging':
            self.in_packaging = False

        if name == 'properties':
            self.in_properties = False

        if name in self.tags:
            self.product[name] = self.content.strip()

        self.content = ''

    def characters(self, content):
        self.content += content

    def get_product(self):
        return self.convert_values(self.SCHEMA, self.product)

    def save_product(self):
        raise NotImplementedError

    def parse(self, file):
        try:
            xml.sax.parse(file, self)
        except Exception as exc:
            logger.error('XML parsing error: {}'.format(exc))
