"""FinBERT-based sentiment analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple
import logging

from ...core.signals import Signal, SignalProvider
from ..news.alpaca import AlpacaNewsProvider

logger = logging.getLogger(__name__)


class FinBERTSignalProvider:
    """Signal provider using FinBERT for financial sentiment analysis.

    Uses the ProsusAI/finbert transformer model trained on
    financial text for sentiment classification.
    """

    _tokenizer = None
    _model = None
    _device = None
    _labels = ["positive", "negative", "neutral"]

    def __init__(
        self,
        news_provider: Optional[AlpacaNewsProvider] = None,
        contrarian: bool = False,
    ):
        """Initialize FinBERT signal provider.

        Args:
            news_provider: News provider for fetching headlines
            contrarian: If True, invert the sentiment (buy on negative)
        """
        self._news = news_provider or AlpacaNewsProvider()
        self.contrarian = contrarian
        self._ensure_model_loaded()

    @classmethod
    def _ensure_model_loaded(cls):
        """Lazy-load the FinBERT model."""
        if cls._model is None:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            cls._device = "cuda:0" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading FinBERT model on {cls._device}")

            cls._tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            cls._model = AutoModelForSequenceClassification.from_pretrained(
                "ProsusAI/finbert",
                trust_remote_code=True,
            ).to(cls._device)

    @property
    def name(self) -> str:
        return "finbert_contrarian" if self.contrarian else "finbert"

    def estimate_sentiment(self, headlines: list[str]) -> Tuple[float, str]:
        """Analyze sentiment of news headlines.

        Args:
            headlines: List of news headline strings

        Returns:
            Tuple of (probability, sentiment)
            where sentiment is "positive", "negative", or "neutral"
        """
        import torch

        if not headlines:
            return 0.0, "neutral"

        tokens = self._tokenizer(
            headlines,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(self._device)

        with torch.no_grad():
            result = self._model(
                tokens["input_ids"],
                attention_mask=tokens["attention_mask"]
            )["logits"]

        # Sum logits across all headlines and apply softmax
        result = torch.nn.functional.softmax(torch.sum(result, 0), dim=-1)
        probability = float(result[torch.argmax(result)])
        sentiment = self._labels[torch.argmax(result)]

        return probability, sentiment

    def get_signal(self, asset: str, context: dict) -> Signal:
        """Generate trading signal using FinBERT analysis.

        Args:
            asset: Asset symbol (e.g., "BTC/USD")
            context: Must contain "current_date" and "lookback_date"

        Returns:
            Signal with action, confidence, and reasoning
        """
        current_date = context.get("current_date", "")
        lookback_date = context.get("lookback_date", "")

        # Parse dates
        try:
            end_dt = datetime.strptime(current_date, "%Y-%m-%d")
            start_dt = datetime.strptime(lookback_date, "%Y-%m-%d")
        except ValueError as e:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning=f"Invalid date format: {e}",
                metadata={"provider": self.name}
            )

        # Extract symbol (remove quote currency)
        symbol = asset.split("/")[0]

        # Fetch headlines
        try:
            headlines = self._news.get_headlines(symbol, start_dt, end_dt)
        except Exception as e:
            logger.warning(f"Failed to fetch news: {e}")
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning=f"Failed to fetch news: {e}",
                metadata={"provider": self.name, "error": str(e)}
            )

        if not headlines:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="No news headlines found",
                metadata={"provider": self.name}
            )

        # Analyze sentiment
        probability, sentiment = self.estimate_sentiment(headlines)

        # Determine action
        if self.contrarian:
            # Contrarian: buy on negative, sell on positive
            if sentiment == "negative":
                action = "buy"
            elif sentiment == "positive":
                action = "sell"
            else:
                action = "hold"
            reasoning = f"Contrarian FinBERT: {sentiment} sentiment ({probability:.2%})"
        else:
            # Standard: buy on positive, sell on negative
            if sentiment == "positive":
                action = "buy"
            elif sentiment == "negative":
                action = "sell"
            else:
                action = "hold"
            reasoning = f"FinBERT: {sentiment} sentiment ({probability:.2%})"

        return Signal(
            action=action,
            confidence=probability,
            reasoning=reasoning,
            metadata={
                "provider": self.name,
                "sentiment": sentiment,
                "headline_count": len(headlines),
            }
        )


class FinBERTContrarianProvider(FinBERTSignalProvider):
    """FinBERT provider configured for contrarian trading."""

    def __init__(self, **kwargs):
        super().__init__(contrarian=True, **kwargs)
