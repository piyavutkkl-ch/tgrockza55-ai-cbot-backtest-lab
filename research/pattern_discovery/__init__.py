"""
Scalping & Intraday Pattern Discovery and Statistical Validation Engine (V5)
============================================================================
Discovers and validates zero-lookahead Single Conditions, Price-Anchored Multi-Step
Sequences, and Causal Dual-HTF Multi-Timeframe Relationships across XAUUSD, BTCUSD,
and ETHUSD by fusing Tier 1 Live L2 DOM / Order Flow / Real Spread with Tier 2 cTrader
Real Multi-Timeframe OHLCV.
"""

__all__ = [
    "data_loader",
    "level_memory",
    "event_tokenizer",
    "statistical_validator",
    "sequence_mtf_miner",
    "library_builder",
]
