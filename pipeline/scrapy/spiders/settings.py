import logging
import warnings
from spiders.extensions import PydanticAdapter
from itemadapter.adapter import ItemAdapter

ItemAdapter.ADAPTER_CLASSES.appendleft(PydanticAdapter)  # pyright: ignore[reportAttributeAccessIssue]

logging.getLogger("httpx").setLevel(logging.WARNING)


warnings.filterwarnings(
    "ignore",
    message='method is a generator and includes a "return" statement with a value different than None',
    category=UserWarning,
    module="scrapy.core.scraper",
)

BOT_NAME = "ira-spiders"

SPIDER_MODULES = ["spiders.spiders.gitabitan"]
NEWSPIDER_MODULE = "spiders.spiders.gitabitan"
ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = 1
HTTPCACHE_ENABLED = True

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"
COOKIES_ENABLED = False
DOWNLOADER_CLIENT_TLS_METHOD = "TLSv1.2"

LOG_FORMATTER = "spiders.extensions.PoliteLogFormatter"
LOG_LEVEL = logging.INFO
LOG_FILE_APPEND = True
DOWNLOAD_WARNSIZE = 0

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
