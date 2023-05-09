import string

import nltk
import scrapy
from nltk import word_tokenize
from nltk.corpus import stopwords
from scrapy.http import Response


nltk.download("stopwords")
STOP_WORDS = set(stopwords.words("english"))


class VacanciesSpider(scrapy.Spider):
    name = "vacancies"
    allowed_domains = ["djinni.co"]
    start_urls = ["https://djinni.co/jobs/?primary_keyword=Python"]

    def parse(self, response: Response, **kwargs):
        for vacancy in response.css(".list-jobs__item"):
            vacancy_url = vacancy.css("a.profile::attr(href)").get()
            yield response.follow(
                vacancy_url, callback=self.parse_vacancy_page
            )

        next_page = response.css(
            ".pagination li:last-child a::attr(href)"
        ).get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_vacancy_page(self, response: Response):
        yield {
            "vacancy": response.css("h1::text").get().strip(),
            "company": response.css(".job-details--title::text").get().strip(),
            "experience": int(
                response.css(
                    ".job-additional-info--body li:last-child div::text"
                )
                .get()
                .split()[0]
                .replace("Без", "0")
            ),
            "views": int(
                response.css("p.text-muted").re_first(r"(\d+) перегляд")
            ),
            "applications": int(
                response.css("p.text-muted").re_first(r"(\d+) відгук")
            ),
            "salary": response.css(".public-salary-item::text").get(),
            "technologies": self.parse_technologies(response),
        }

    def parse_technologies(self, response: Response):
        vacancy_description = (
            " ".join(response.css("div.profile-page-section::text").getall())
            .strip()
            .lower()
        )
        tokens = word_tokenize(vacancy_description)

        return list(
            set(
                word
                for word in tokens
                if word not in STOP_WORDS and word not in string.punctuation
            )
        )
