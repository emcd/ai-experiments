# Please refer to the documentation for information on how to create and manage
# your spiders.

from bs4 import BeautifulSoup
from scrapy.linkextractors import LinkExtractor
#from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider, Rule

from sphinx.items import SphinxItem


class SphinxSpider( CrawlSpider ):

    name = 'sphinx'
    allowed_domains = (
        'docs.scrapy.org',
        'panel.holoviz.org',
        'python.langchain.com',
    )
    start_urls = (
        'https://docs.scrapy.org/en/latest',
        'https://panel.holoviz.org/api/index.html',
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
        soup = BeautifulSoup( response.body, 'html.parser' )
        for unwanted_tag in soup( ( 'canvas', 'nav', 'script', ) ):
            unwanted_tag.decompose( )
        for toctree_class in (
            'toctree-wrapper', 'toctree-l1', 'toctree-l2', 'toctree-l3'
        ):
            for toctree_element in soup.select( f'.{toctree_class}' ):
                toctree_element.decompose( )
        content_fragments = soup.body.stripped_strings
        content = '\n'.join( content_fragments )
        item[ 'content' ] = content.strip( ) if content else None
        return item
