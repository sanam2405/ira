import json
from typing import List, Literal, Optional
from pydantic import BaseModel, RootModel
import tiktoken
from transformers import AutoTokenizer


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
        self.tokenizer = tokenizer
        self.encoding = encoding
        if tokenizer == "tiktoken":
            self.encoding = tiktoken.get_encoding(encoding or "cl100k_base")
        elif tokenizer == "transformers":
            self.tokenizer = AutoTokenizer.from_pretrained(encoding or "gpt2")
        else:
            raise ValueError(f"Unknown tokenizer: {tokenizer}")

    def count(self, text: str) -> int:
        if self.tokenizer == "tiktoken":
            return len(self.encoding.encode(text))
        elif self.tokenizer == "transformers":
            return len(self.tokenizer.encode(text))
        else:
            raise ValueError(f"Unknown tokenizer: {self.tokenizer}")


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
    jsonl_path = "scrapy/gitabitan.jsonl"
    keys_to_count = ["title", "lyrics"]
    # using tiktoken
    token_counter = TokenCounter(tokenizer="tiktoken", encoding="cl100k_base")
    # using transformers
    # token_counter = TokenCounter(tokenizer="transformers", encoding="gpt2")
    result = count_tokens_in_jsonl(jsonl_path, keys_to_count, token_counter)
    print(
        "PER ITEM TOKEN COUNTS:", [item.model_dump() for item in result.per_item_counts]
    )
    print("TOTAL TOKENS PER KEY:", result.total_counts.model_dump())
    print("TOTAL TOKENS IN FILE:", result.total_tokens)
