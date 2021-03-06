# -*- coding: utf-8 -*-
import arrow    # datetime parsing
from urlparse import urljoin
from scrapy.spider import Spider
from scrapy.http import Request
from ride_scraper.items import RideItem


class KasVaziuojaSpider(Spider):
    name = 'kas_vaziuoja'
    start_urls = ['http://www.kasvaziuoja.lt/']
    # Required - see SetSourcePipeline
    ad_id_pattern = 'kelione-(?P<id>\d+)'

    def is_expired(self, db_item, scraped_items):
        """
        Ad is expired if its ride date is already in the past
        """
        now = arrow.utcnow()
        if db_item.ride_date < now:
            return True
        else:
            return False

    def parse(self, response):
        """
        Crawler entry point
        """
        rides = response.xpath("//div[@class='entry black']")
        for ride in rides:

            # Actual ad link
            ride_url = ride.xpath(
                "div[@class='photoBox']/a/@href").extract()[0]
            ride_url = urljoin(response.url, ride_url)

            # Begin populating the item now
            ride_item = RideItem()

            # Check if ride is being offered or looked for
            is_looking_for = ride.xpath(
                "div[@class='message']/div/strong/span/text()").extract()[0]
            if is_looking_for == u'Ieškau':
                ride_item['is_looking_for'] = True
            elif is_looking_for == u'Siūlau':
                ride_item['is_looking_for'] = False

            # Open the ad and scrape the rest of its content
            yield Request(
                url=ride_url,
                meta={'ride_item': ride_item},
                callback=self.parse_ride)

    def parse_ride(self, response):
        ride_item = response.meta['ride_item']

        # Parse main fields
        fields = response.xpath(
            "//div[@class='fl info']/strong/following-sibling::text()").extract()
        last = len(fields) - 1
        ride_item['phone'] = fields[last - 2].strip()
        ride_item['ride_date'] = arrow.get(fields[last - 1].strip())
        ride_item['content'] = fields[last].strip()
        ride_item['ad_url'] = response.url

        # Parse cities
        route_raw = response.xpath(
            # 'ė' left out intentionally to avoid encoding problems
            "//h1[contains(text(), 'Kelion')]/a/text()").extract()[0]
        cities = route_raw.split("-")
        ride_item['routes'] = [{
            'origin': cities[0].strip(),
            'destination': cities[1].strip()
        }]

        # Parse facebook url.
        # Instead of trying to click javascript link in the ad content,
        # use <script> tag containing that FB url.
        fb_link_js = response.xpath(
            "//script[contains(text(), 'facebook.com')]/text()").extract()[0]
        fb_idx = fb_link_js.index('facebook.com')
        # Extract what's between apostrophes - full url
        fb_url_start = fb_link_js.rfind("'", 0, fb_idx) + 1
        fb_url_end = fb_link_js.find("'", fb_idx)
        fb_url = fb_link_js[fb_url_start:fb_url_end]
        ride_item['fb_url'] = fb_url

        yield ride_item
