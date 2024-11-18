import scrapy
import random
import json
from urllib.parse import urljoin

class MainSpider(scrapy.Spider):
    name = "main"
    allowed_domains = ["pandaexpress.com"]
    start_urls = ["https://www.pandaexpress.com/locations"]
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; rv:54.0) Gecko/20100101 Firefox/54.0',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36 Edge/17.17134',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; ASLJ; ASLJ) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
    ]
    custom_settings = {
        'USER_AGENT': random.choice(user_agents),
        'COOKIES_ENABLED': True,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.pandaexpress.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    }

    def parse(self, response):
        main_url = response.url
        states = response.xpath('//div[contains(@class, "locations_filter__content")]//div[contains(@class, "wrapper")]//a/@href').getall()
        for state in states:
#            test = state.xpath('.//a/@href').get()

            full_url = urljoin(main_url, state)
            yield response.follow(full_url, callback=self.new_city)


    def new_city(self, response):
        c_cities = response.xpath('//div[contains(@class, "locations_filter__content")]//div[contains(@class, "wrapper")]//a/@href').getall()
        for city in c_cities:
            full_url = urljoin(response.url, city)
            yield response.follow(full_url, callback=self.new_stores)
    
    def new_stores(self, response):
        new_store = response.xpath('//div[contains(@class, "locations_filter__content")]//div[contains(@class, "wrapper")]//a/@href').getall()
        for store in new_store:
            full_url = urljoin(response.url, store)
            yield response.follow(full_url, callback=self.extract_store)

    def extract_store(self, response):
        get_name = response.xpath('//div[contains(@class, "name")]/h1/text()').get()
        phone_number = response.xpath('//div[contains(@class, "phone")]/a/text()').get()
        address = response.xpath('string(//div[contains(@class, "address")])').get()
        json_data = response.xpath('(//script[@type="application/ld+json"])/text()').get()
        id = response.xpath('//div[contains(@class, "location_link")]/a/@href').get()
        if id:
            new_id = id.split('/')[-1]

        loc_dict = {}
        hours_dict = {}
        days = response.xpath('//div[contains(@class, "hours_list")]//div[contains(@class, "day")]')
        if days:
            for day in days:
                day_s = day.xpath('.//div[contains(@class, "day_name")]/text()').get()
                hour_s = day.xpath('.//div[contains(@class, "day_hours")]/text()').get()
                if day_s and hour_s:

                    hours_dict[day_s.strip().lower()] = {
                        'open_time' : hour_s[:8].strip(),
                        'close_time' : hour_s[11:].strip()
                    }

        if json_data:
            new_json = json.loads(json_data)
            loc_dict = {
                "type" : "Point",
                "coordinates" : [
                    new_json['geo']['latitude'],
                    new_json['geo']['longitude']
                ]
            }

        if not get_name or not phone_number or not address:
            return
        yield{
            'name' : get_name,
            'phone_number' : phone_number,
            'address' : address,
            'url' : response.url,
            'location' : loc_dict,
            'hours' : hours_dict,
            'id' : new_id
        }

    