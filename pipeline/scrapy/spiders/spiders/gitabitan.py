import re
from typing import override

import ftfy
import structlog
from lxml import etree, html
from pydantic import BaseModel, computed_field

import scrapy
from scrapy import Request
from scrapy.http import TextResponse

from .schema import SpiderDomain


class GitabitanItem(BaseModel):
    domain: SpiderDomain = "gitabitan"
    title: str
    url: str
    lyrics: str
    metadata: dict
    citations: list[str]

    @computed_field
    @property
    @override
    def identifier(self) -> str:
        return str(self.url)

    """
    TODO:
    - Extract metadata of the song
    - Extract metadata of author and song timeline
    - Analyze and create a unique identifier or genre for classification
    """


class GitabitanSpider(scrapy.Spider):
    name = "gitabitan"
    base_url = "http://gitabitan.net"
    song_id_range = range(1, 2307 + 1)
    logger = structlog.get_logger(__name__).bind(class_name="GitabitanSpider")

    MAP_KEYS = {
        "রচনাকাল": "composition_date",
        "রচনাস্থান": "composition_location",
        "কবির বয়স": "poet_age",
        "প্রকাশ": "publication_date",
        "গীতবিতান(পর্যায়;#/পৃ)": "gitabitan_index",
        "রাগ / তাল": "raag_taal",
        "স্বরলিপি": "notation",
        "স্বরলিপিকার": "notator",
        "raag": "raag",
        "taal": "taal",
        "context": "context",
    }

    def convert_metadata_keys(self, metadata):
        return {self.MAP_KEYS.get(k, k): v for k, v in metadata.items()}

    def clean_text(self, text):
        # Convert to string if not already
        if not isinstance(text, str):
            text = str(text)
        # Fix broken Unicode characters
        text = ftfy.fix_text(text)
        # Replace non-breaking spaces, tabs, carriage returns, and form feeds with a space
        text = re.sub(r"[\xa0\t\r\f]", " ", text)
        # Replace multiple spaces (including those created by above) with a single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines (with optional spaces/tabs in between) with a single newline
        text = re.sub(r" *\n+", "\n", text)
        # Remove leading/trailing whitespace and newlines
        text = text.strip()
        return text

    def start_requests(self):
        for song_id in self.song_id_range:
            yield Request(
                url=f"{self.base_url}/top.asp?songid={song_id}", callback=self.parse
            )

    def parse(self, response):
        # Get the td with id=" ccelltd1" (note the space in the id)
        lyrics_element = response.css('td[id=" ccelltd1"]')
        metadata_element = response.css('div[id="remainder"]')
        citations_element = response.css('div[id="divrbar"]')
        self.logger.info("lyrics_element", lyrics_element=lyrics_element)
        self.logger.info("metadata_element", metadata_element=metadata_element)
        self.logger.info("citations_element", citations_element=citations_element)
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
                text = self.clean_text(text)
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
            title = first_line
            if len(lyrics_lines) > 1:
                title = f"{first_line} {lyrics_lines[1]}"

        lyrics = "\n".join(lyrics_lines)
        if metadata_element:
            metadata = self.parse_metadata(metadata_element)
            metadata = self.convert_metadata_keys(metadata)
        else:
            metadata = {}

        if citations_element:
            citations = self.parse_citations(citations_element.get())
        else:
            citations = []

        item = GitabitanItem(
            title=title,
            url=response.url,
            lyrics=lyrics,
            metadata=metadata,
            citations=citations,
        )
        self.logger.info("item", item=item)
        yield item

    def parse_metadata(self, metadata_element):
        metadata = {}
        spans = metadata_element.xpath('.//span[contains(@class, "uy11")]')
        for span in spans:
            key = (
                "".join(span.xpath(".//text()").getall())
                .strip()
                .rstrip(":")
                .replace("\xa0", " ")
            )
            # Skip keys that start with "লিঙ্ক"
            if key.startswith("লিঙ্ক"):
                continue
            value_parts = []
            for sib in span.xpath("./following-sibling::node()"):
                if isinstance(sib.root, etree._Element):
                    if sib.root.tag == "span" and "uy11" in sib.root.attrib.get(
                        "class", ""
                    ):
                        break
                    if sib.root.tag == "br":
                        break
                text = (
                    sib.xpath(".//text()").getall()
                    if isinstance(sib.root, etree._Element)
                    else [sib.get()]
                )
                if text:
                    value_parts.extend(text)
            value = "".join(value_parts).strip().replace("\xa0", " ")
            if value:
                metadata[key] = self.clean_text(value)

        raag = metadata_element.xpath('.//span[@id="raag"]/text()').get()
        if raag:
            metadata["raag"] = raag.strip()
        taal = metadata_element.xpath('.//span[@id="taal"]/text()').get()
        if taal:
            metadata["taal"] = taal.strip()

        alochona_span = metadata_element.xpath('.//span[contains(text(), "আলোচনা")]')
        if alochona_span:
            alochona_p = alochona_span.xpath("./ancestor::p[1]")
            if alochona_p:
                alochona_parts = []
                for sib in alochona_p[0].xpath("./following-sibling::node()"):
                    if isinstance(sib.root, etree._Element) and sib.root.tag == "hr":
                        break
                    text = (
                        sib.xpath(".//text()").getall()
                        if isinstance(sib.root, etree._Element)
                        else [sib.get()]
                    )
                    if text:
                        if isinstance(text, list):
                            text = "".join(text)
                        text = self.clean_text(text)
                        alochona_parts.extend(text)
                alochona_text = "".join(alochona_parts).strip().replace("\xa0", " ")
                if alochona_text:
                    metadata["context"] = alochona_text

        return metadata

    def parse_citations(self, divrbar_html):
        tree = html.fromstring(divrbar_html)
        citations = []
        current = []
        for elem in tree.iterchildren():
            if elem.tag == "hr":
                if current:
                    citation_html = "".join(
                        [html.tostring(e, encoding="unicode") for e in current]
                    )
                    citation_text = html.fromstring(
                        f"<div>{citation_html}</div>"
                    ).text_content()
                    citations.append(citation_text)
                    current = []
            else:
                current.append(elem)
        if current:
            citation_html = "".join(
                [html.tostring(e, encoding="unicode") for e in current]
            )
            citation_text = html.fromstring(
                f"<div>{citation_html}</div>"
            ).text_content()
            citations.append(citation_text)
        cleaned_citations = [self.clean_text(c) for c in citations if c.strip()]
        return cleaned_citations
