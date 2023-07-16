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
        'api.python.langchain.com',
        'docs.scrapy.org',
        'panel.holoviz.org',
        'tenacity.readthedocs.io',
    )
    start_urls = (
        'https://api.python.langchain.com/en/latest/api_reference.html',
        'https://docs.scrapy.org/en/latest',
        'https://panel.holoviz.org/api/index.html',
        'https://tenacity.readthedocs.io/en/latest',
    )
    rules = (
        Rule( LinkExtractor(
            restrict_css = [
                '.body a',
                '.reference.internal',
                '.toctree-l1', '.toctree-l2', '.toctree-l3',
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
            'reference.internal',
            'toctree-wrapper', 'toctree-l1', 'toctree-l2', 'toctree-l3'
        ):
            for toctree_element in soup.select( f'.{toctree_class}' ):
                toctree_element.decompose( )
        content_fragments = soup.body.stripped_strings
        content = '\n'.join( content_fragments )
        item[ 'content' ] = content.strip( ) if content else None
        return item
