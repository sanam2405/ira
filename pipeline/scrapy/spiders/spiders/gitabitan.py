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
    song_id_range = range(2120, 2133 + 1)

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

        # Check if first line has more than one word
        first_line = lyrics_lines[0]
        words_in_first_line = first_line.split()

        if len(words_in_first_line) > 1:
            title = first_line
        else:
            # If there's only one word, use first two lines
            # Make sure there's a second line before trying to use it
            title = first_line
            if len(lyrics_lines) > 1:
                title = f"{first_line} {lyrics_lines[1]}"

        lyrics = "\n".join(lyrics_lines)

        item = GitabitanItem(
            title=title,
            url=response.url,
            lyrics=lyrics,
        )
        print(item)
        yield item
