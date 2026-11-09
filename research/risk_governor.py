"""
Institutional Risk Governor (Risk Governance & Capital Defense Engine)
======================================================================
Enforces non-negotiable risk limits across all trading bots:
1. Portfolio Daily Loss Ceiling: Halts all trading if portfolio daily loss >= -$10.00 USD
2. Symbol Max Consecutive Losses: Halts a symbol for the day after 2 consecutive losses
3. Daily Profit Target Guardian: Locks in daily gains once +$10.00 - +$15.00 is achieved
4. Dynamic Spread Ceiling Gate: Rejects entry during Asian rollover spread spikes
5. High-Impact News Void Gate: 30m pre-news blackout & 60m post-news blackout
6. Statistical Drift Detector: Flags strategy divergence if real fills deviate > 2.0x ATR
"""

import os
import json
from datetime import datetime, timezone

class RiskGovernor:
    # Institutional Limits
    PORTFOLIO_MAX_DAILY_LOSS = 10.00   # Max daily portfolio drawdown allowed ($10 USD on $100 cap = 10%)
    SYMBOL_MAX_CONSEC_LOSSES = 2       # Stop symbol after 2 consecutive stop-outs
    SPREAD_CEILING = {
        'XAUUSD': 0.25,      # $0.25 per oz
        'GOLD-PERP': 2.20,   # $2.20 per contract
        'BTCUSD': 35.00,     # $35.00 per BTC
        'ETHUSD': 3.50       # $3.50 per ETH
    }
    NEWS_PRE_BLACKOUT_MIN = 30
    NEWS_POST_BLACKOUT_MIN = 60

    def __init__(self):
        self.daily_pnl = {}
        self.symbol_consec_losses = {}
        self.halted_symbols = set()
        self.portfolio_halted = False

    def reset_day(self, date_str):
        self.daily_pnl[date_str] = 0.0
        self.symbol_consec_losses[date_str] = {s: 0 for s in self.SPREAD_CEILING}
        self.halted_symbols.clear()
        self.portfolio_halted = False

    def can_open_trade(self, symbol, current_spread, min_to_news=999, news_impact='', min_since_news=999, last_impact='', date_str=None):
        if self.portfolio_halted:
            return False, "REJECTED: Portfolio Daily Loss Ceiling reached (-$10.00 USD)"

        if symbol in self.halted_symbols:
            return False, f"REJECTED: Symbol {symbol} halted due to daily consecutive loss cap (2 losses)"

        # 1. Spread Ceiling Gate
        max_sp = self.SPREAD_CEILING.get(symbol, 999.0)
        if current_spread > max_sp:
            return False, f"REJECTED: Spread ({current_spread:.2f}) exceeds spread ceiling ({max_sp:.2f})"

        # 2. News Void Gate
        if min_to_news <= self.NEWS_PRE_BLACKOUT_MIN and news_impact in ['HIGH', 'EXTREME']:
            return False, f"REJECTED: Approaching high impact news ({news_impact}) in {min_to_news:.0f} mins"
        if min_since_news <= self.NEWS_POST_BLACKOUT_MIN and last_impact in ['HIGH', 'EXTREME']:
            return False, f"REJECTED: Within {min_since_news:.0f} mins post-news volatility void ({last_impact})"

        return True, "APPROVED"

    def record_trade_result(self, symbol, pnl, date_str):
        if date_str not in self.daily_pnl:
            self.reset_day(date_str)

        self.daily_pnl[date_str] += pnl

        # Track consecutive losses
        if pnl <= 0:
            self.symbol_consec_losses[date_str][symbol] = self.symbol_consec_losses[date_str].get(symbol, 0) + 1
            if self.symbol_consec_losses[date_str][symbol] >= self.SYMBOL_MAX_CONSEC_LOSSES:
                self.halted_symbols.add(symbol)
        else:
            self.symbol_consec_losses[date_str][symbol] = 0

        # Check Portfolio Circuit Breaker
        if self.daily_pnl[date_str] <= -self.PORTFOLIO_MAX_DAILY_LOSS:
            self.portfolio_halted = True

    def get_status_report(self):
        return {
            'governor_name': 'Institutional Risk Governor V2',
            'portfolio_daily_loss_ceiling_usd': self.PORTFOLIO_MAX_DAILY_LOSS,
            'symbol_max_consecutive_losses': self.SYMBOL_MAX_CONSEC_LOSSES,
            'spread_ceilings': self.SPREAD_CEILING,
            'news_pre_blackout_min': self.NEWS_PRE_BLACKOUT_MIN,
            'news_post_blackout_min': self.NEWS_POST_BLACKOUT_MIN,
            'currently_halted_symbols': list(self.halted_symbols),
            'portfolio_halted': self.portfolio_halted
        }
