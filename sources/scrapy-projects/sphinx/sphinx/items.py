# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class SphinxItem( Item ):
    title = Field( )
    url = Field( )
    content = Field( )
