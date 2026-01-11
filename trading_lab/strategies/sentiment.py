"""Sentiment-based trading strategies."""

from typing import Literal

from ..core.strategy import BaseStrategy
from ..core.signals import SignalProvider
from ..providers.sentiment.llm import LLMSentimentProvider, LLMRecommendationProvider
from ..providers.sentiment.finbert import FinBERTSignalProvider
from .registry import register


@register(
    name="llm_sentiment",
    description="LLM-based sentiment analysis trading",
    default_provider="llm_sentiment",
)
class LLMSentimentStrategy(BaseStrategy):
    """Trading strategy using local LLM for sentiment analysis.

    Analyzes news sentiment using Ollama and trades based on
    positive/negative sentiment scores.
    """

    def initialize(
        self,
        model: str = "qwen2.5:14b",
        threshold: float = 0.7,
        **kwargs
    ):
        """Initialize LLM sentiment strategy.

        Args:
            model: Ollama model name
            threshold: Minimum confidence to trade
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = LLMSentimentProvider(model=model)

        super().initialize(
            signal_provider=signal_provider,
            threshold=threshold,
            **kwargs
        )


@register(
    name="llm_recommendation",
    description="LLM direct buy/sell/hold recommendations",
    default_provider="llm_recommendation",
)
class LLMRecommendationStrategy(BaseStrategy):
    """Trading strategy using LLM for direct recommendations.

    The LLM directly recommends buy/sell/hold actions
    rather than just sentiment classification.
    """

    def initialize(
        self,
        model: str = "openhermes",
        threshold: float = 0.7,
        **kwargs
    ):
        """Initialize LLM recommendation strategy.

        Args:
            model: Ollama model name
            threshold: Minimum confidence to trade
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = LLMRecommendationProvider(model=model)

        super().initialize(
            signal_provider=signal_provider,
            threshold=threshold,
            **kwargs
        )


@register(
    name="finbert",
    description="FinBERT transformer sentiment analysis",
    default_provider="finbert",
)
class FinBERTStrategy(BaseStrategy):
    """Trading strategy using FinBERT for sentiment analysis.

    Uses the ProsusAI/finbert model trained on financial text
    to classify news sentiment and generate trading signals.
    """

    def initialize(
        self,
        threshold: float = 0.999,  # FinBERT typically needs high threshold
        **kwargs
    ):
        """Initialize FinBERT strategy.

        Args:
            threshold: Minimum probability to trade (default 0.999)
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = FinBERTSignalProvider()

        super().initialize(
            signal_provider=signal_provider,
            threshold=threshold,
            **kwargs
        )


@register(
    name="sentiment",
    description="Configurable sentiment strategy (LLM or FinBERT)",
    default_provider="finbert",
)
class SentimentStrategy(BaseStrategy):
    """Unified sentiment strategy with configurable provider.

    Can use either LLM-based or FinBERT-based sentiment analysis
    depending on configuration.
    """

    def initialize(
        self,
        provider_type: Literal["llm", "finbert"] = "finbert",
        model: str | None = None,
        threshold: float | None = None,
        **kwargs
    ):
        """Initialize sentiment strategy.

        Args:
            provider_type: "llm" for Ollama-based, "finbert" for transformer
            model: Model name (only for LLM provider)
            threshold: Minimum confidence (defaults based on provider)
            **kwargs: Passed to BaseStrategy.initialize()
        """
        if provider_type == "llm":
            signal_provider = LLMSentimentProvider(model=model or "qwen2.5:14b")
            default_threshold = 0.7
        else:
            signal_provider = FinBERTSignalProvider()
            default_threshold = 0.999

        super().initialize(
            signal_provider=signal_provider,
            threshold=threshold if threshold is not None else default_threshold,
            **kwargs
        )
