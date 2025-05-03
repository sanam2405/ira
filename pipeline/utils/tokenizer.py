import json
from typing import List, Literal, Optional
from pydantic import BaseModel, RootModel
import tiktoken
from transformers import AutoTokenizer
import structlog


class ItemTokenCount(RootModel[dict[str, int]]):
    pass


class TotalTokenCount(RootModel[dict[str, int]]):
    pass


class TokenCounterResponse(BaseModel):
    per_item_counts: List[ItemTokenCount]
    total_counts: TotalTokenCount
    total_tokens: int


class TokenCounter:
    def __init__(
        self,
        tokenizer: Literal["tiktoken", "transformers"] = "tiktoken",
        encoding: Optional[str] = None,
    ):
        self.tokenizer_type = tokenizer
        self.encoding = encoding
        self.logger = structlog.get_logger(__name__).bind(class_name="TokenCounter")
        match tokenizer:
            case "tiktoken":
                self.encoding = tiktoken.get_encoding(encoding or "cl100k_base")
                self.logger.info(
                    "Initialized tiktoken tokenizer", encoding=self.encoding.name
                )
            case "transformers":
                self.tokenizer = AutoTokenizer.from_pretrained(encoding or "gpt2")
                self.logger.info(
                    "Initialized transformers tokenizer", model=encoding or "gpt2"
                )
            case _:
                self.logger.error("Unknown tokenizer", tokenizer=tokenizer)
                raise ValueError(f"Unknown tokenizer: {tokenizer}")

    def count(self, text: str) -> int:
        match self.tokenizer_type:
            case "tiktoken":
                count = len(self.encoding.encode(text))
                self.logger.info("Counted tokens with tiktoken", text=text, count=count)
                return count
            case "transformers":
                count = len(self.tokenizer.encode(text))
                self.logger.info(
                    "Counted tokens with transformers", text=text, count=count
                )
                return count
            case _:
                self.logger.error(
                    "Unknown tokenizer in count", tokenizer=self.tokenizer_type
                )
                raise ValueError(f"Unknown tokenizer: {self.tokenizer_type}")


def count_tokens_in_jsonl(
    jsonl_path: str, keys: List[str], token_counter: TokenCounter
) -> TokenCounterResponse:
    """
    Count tokens for specified keys in each item and the whole jsonl file.

    Returns:
        TokenCounterResponse: Pydantic model with per-item, per-key, and total token counts.
    """
    per_item_counts = []
    total_counts_dict = {key: 0 for key in keys}
    total_tokens = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            item_counts = {}
            for key in keys:
                value = str(item.get(key, ""))
                count = token_counter.count(value)
                item_counts[key] = count
                total_counts_dict[key] += count
                total_tokens += count
            per_item_counts.append(ItemTokenCount(item_counts))
    return TokenCounterResponse(
        per_item_counts=per_item_counts,
        total_counts=TotalTokenCount(total_counts_dict),
        total_tokens=total_tokens,
    )


if __name__ == "__main__":
    jsonl_path = "scrapy/metacite.jsonl"
    keys_to_count = ["title", "lyrics", "metadata", "citations"]
    # using tiktoken
    # token_counter = TokenCounter(tokenizer="tiktoken", encoding="cl100k_base")
    # using transformers
    token_counter = TokenCounter(tokenizer="transformers", encoding="gpt2")
    result = count_tokens_in_jsonl(jsonl_path, keys_to_count, token_counter)

    logger = structlog.get_logger(__name__).bind(context="main")
    # logger.info(
    #     "PER ITEM TOKEN COUNTS",
    #     per_item_token_counts=[item.model_dump() for item in result.per_item_counts],
    # )
    logger.info(
        "TOTAL TOKENS PER KEY",
        tokenizer_type=token_counter.tokenizer_type,
        encoding=token_counter.encoding,
        total_tokens_per_key=result.total_counts.model_dump(),
    )
    logger.info(
        "TOTAL TOKENS IN FILE",
        tokenizer_type=token_counter.tokenizer_type,
        encoding=token_counter.encoding,
        total_tokens_in_file=result.total_tokens,
    )
