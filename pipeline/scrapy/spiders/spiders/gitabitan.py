import scrapy
from scrapy import Request
from scrapy.http import TextResponse
from typing import override
from pydantic import BaseModel, computed_field
from .schema import SpiderDomain


class GitabitanItem(BaseModel):
    domain: SpiderDomain = "gitabitan"
    title: str
    url: str
    lyrics: str

    @computed_field
    @property
    @override
    def identifier(self) -> str:
        return str(self.url)


class GitabitanSpider(scrapy.Spider):
    name = "gitabitan"
    base_url = "http://gitabitan.net"
    song_id_range = range(1, 111 + 1)

    def start_requests(self):
        for song_id in self.song_id_range:
            yield Request(
                url=f"{self.base_url}/top.asp?songid={song_id}", callback=self.parse
            )

    def parse(self, response):
        # Get the td with id=" ccelltd1" (note the space in the id)
        lyrics_element = response.css('td[id=" ccelltd1"]')
        print("lyrics_element", lyrics_element)
        if not lyrics_element:
            return

        # Extract all text nodes and <br> tags
        lyrics_parts = lyrics_element.xpath(".//text()|.//br").getall()

        # Process the lyrics: filter out empty lines and the numbered heading
        lyrics_lines = []
        for part in lyrics_parts:
            if part == "<br>":
                continue
            # Replace multiple non-breaking spaces with a single regular space
            text = part.strip().replace("\xa0", " ")
            # Remove multiple spaces
            text = " ".join(text.split())
            if (
                text
                and not text.isdigit()
                and not text.startswith("(")
                and not text.endswith(")")
            ):
                lyrics_lines.append(text)

        if not lyrics_lines:
            return

        # First meaningful line becomes the title
        title = lyrics_lines[0]
        # Join all lines with newlines
        lyrics = "\n".join(lyrics_lines)

        item = GitabitanItem(
            title=title,
            url=response.url,
            lyrics=lyrics,
        )
        print(item)
        yield item
