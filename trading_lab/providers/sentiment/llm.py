"""LLM-based sentiment analysis using Ollama."""

import json
from typing import Optional

from langchain_ollama import OllamaLLM

from ...core.signals import Signal, SignalProvider
from ...core.config import get_settings
from ..news.serper import SerperNewsProvider


class LLMSignalProvider:
    """Signal provider using local LLM for sentiment analysis.

    Uses Ollama to run local LLMs for analyzing news sentiment
    and generating trading signals.
    """

    def __init__(
        self,
        model: str = "qwen2.5:14b",
        news_provider: Optional[SerperNewsProvider] = None,
        mode: str = "sentiment",  # "sentiment" or "recommendation"
    ):
        """Initialize LLM signal provider.

        Args:
            model: Ollama model name
            news_provider: News provider for fetching articles
            mode: "sentiment" for positive/negative analysis,
                  "recommendation" for buy/sell/hold signals
        """
        settings = get_settings()
        self.model = model
        self.mode = mode
        self._llm = OllamaLLM(model=model, format="json")
        self._news = news_provider or SerperNewsProvider()

    @property
    def name(self) -> str:
        return f"llm_{self.mode}"

    def _sentiment_prompt(self, news: str) -> str:
        """Create sentiment analysis prompt."""
        return f"""You are a helpful financial assistant, provide helpful, harmless and honest answers.
Using the news below, respond as to whether the sentiment in the news is either ['positive', 'negative'] and give a score of
how strong the sentiment is between 0 to 1. Respond using the keys sentiment, score.

example result
'sentiment':'positive',
'score':0.2

Do not reply with neutral sentiment or mixed.

News
{news}"""

    def _recommendation_prompt(self, news: str) -> str:
        """Create trading recommendation prompt."""
        return f"""You are a helpful financial assistant, provide helpful, harmless and honest answers.
Using the news below, respond as to whether an investor should buy, sell or hold and how strong the signal is between 0 to 1.
The output should be in the format of recommendation and score.

Example Result
'recommendation':'hold',
'score':0.2

News
{news}"""

    def _parse_sentiment_response(self, response: str) -> Signal:
        """Parse LLM sentiment response into Signal."""
        try:
            data = json.loads(response)
            sentiment = data.get("sentiment", "").lower()
            score = float(data.get("score", 0.5))

            if sentiment == "positive":
                action = "buy"
            elif sentiment == "negative":
                action = "sell"
            else:
                action = "hold"

            return Signal(
                action=action,
                confidence=min(max(score, 0.0), 1.0),
                reasoning=f"LLM sentiment: {sentiment}",
                metadata={"raw_response": data, "provider": self.name}
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning=f"Failed to parse LLM response: {e}",
                metadata={"error": str(e), "provider": self.name}
            )

    def _parse_recommendation_response(self, response: str) -> Signal:
        """Parse LLM recommendation response into Signal."""
        try:
            data = json.loads(response)
            recommendation = data.get("recommendation", "").lower()
            score = float(data.get("score", 0.5))

            if recommendation in ("buy", "sell", "hold"):
                action = recommendation
            else:
                action = "hold"

            return Signal(
                action=action,
                confidence=min(max(score, 0.0), 1.0),
                reasoning=f"LLM recommendation: {recommendation}",
                metadata={"raw_response": data, "provider": self.name}
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning=f"Failed to parse LLM response: {e}",
                metadata={"error": str(e), "provider": self.name}
            )

    def get_signal(self, asset: str, context: dict) -> Signal:
        """Generate trading signal using LLM analysis.

        Args:
            asset: Asset symbol (e.g., "BTC/USD")
            context: Must contain "current_date" and "lookback_date"

        Returns:
            Signal with action, confidence, and reasoning
        """
        current_date = context.get("current_date", "")
        lookback_date = context.get("lookback_date", "")

        # Extract asset name for search
        asset_name = asset.split("/")[0].lower()
        if asset_name == "btc":
            asset_name = "bitcoin"
        elif asset_name == "eth":
            asset_name = "ethereum"
        elif asset_name == "sol":
            asset_name = "solana"

        # Fetch news
        news = self._news.search(asset_name, lookback_date, current_date)

        if not news:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="No news found",
                metadata={"provider": self.name}
            )

        # Generate prompt and get LLM response
        if self.mode == "sentiment":
            prompt = self._sentiment_prompt(news)
            response = self._llm.invoke(prompt)
            return self._parse_sentiment_response(response)
        else:
            prompt = self._recommendation_prompt(news)
            response = self._llm.invoke(prompt)
            return self._parse_recommendation_response(response)


class LLMSentimentProvider(LLMSignalProvider):
    """LLM provider configured for sentiment analysis."""

    def __init__(self, model: str = "qwen2.5:14b", **kwargs):
        super().__init__(model=model, mode="sentiment", **kwargs)


class LLMRecommendationProvider(LLMSignalProvider):
    """LLM provider configured for direct recommendations."""

    def __init__(self, model: str = "openhermes", **kwargs):
        super().__init__(model=model, mode="recommendation", **kwargs)
