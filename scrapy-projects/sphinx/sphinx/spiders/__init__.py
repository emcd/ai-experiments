# Please refer to the documentation for information on how to create and manage
# your spiders.

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from sphinx.items import SphinxItem


class SphinxSpider( CrawlSpider ):

    name = 'sphinx'
    allowed_domains = (
        'docs.scrapy.org',
        #'panel.holoviz.org',
        'python.langchain.com',
    )
    start_urls = (
        'https://docs.scrapy.org/en/latest',
        #'https://panel.holoviz.org/api/index.html',
        'https://python.langchain.com/en/latest/',
    )
    rules = (
        Rule( LinkExtractor(
            restrict_css = [
                '.toctree-l1', '.toctree-l2', '.toctree-l3', '.body a'
            ]), callback = 'parse_item', follow = True ),
    )

    def parse_item( self, response ):
        item = SphinxItem()
        item[ 'url' ] = response.url
        title = response.css( 'h1::text' ).get( )
        item[ 'title' ] = title.strip( ) if title else None
        content = response.css( '.body' ).get( )
        item[ 'content' ] = content.strip( ) if content else None
        content_fragments = response.xpath(
            '//body//text()[normalize-space()]' ).getall( )
        content = '\n'.join(
            fragment.strip( ) for fragment in content_fragments )
        item['content'] = content.strip( ) if content else None
        return item
