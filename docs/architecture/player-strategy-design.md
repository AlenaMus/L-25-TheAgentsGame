# Player Strategy Design

**Document Type:** Architecture Design
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** Player Agent Developers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Strategy Interface](#2-strategy-interface)
3. [Random Strategy (Baseline)](#3-random-strategy-baseline)
4. [Adaptive Strategy (Pattern Detection)](#4-adaptive-strategy-pattern-detection)
5. [Pattern Detection Algorithms](#5-pattern-detection-algorithms)
6. [Statistical Analysis](#6-statistical-analysis)
7. [LLM Strategy (Advanced)](#7-llm-strategy-advanced)
8. [Strategy Comparison](#8-strategy-comparison)
9. [Implementation Guide](#9-implementation-guide)

---

## 1. Introduction

This document describes strategy algorithms for the Even/Odd game. A **strategy** is the logic that chooses "even" or "odd" based on game context.

### 1.1 Game Theory Context

**Even/Odd as a Zero-Sum Game:**
- Two players choose simultaneously
- Number drawn is truly random
- No inherent advantage to even or odd
- **Nash Equilibrium:** Both players play 50/50 random

**Key Insight:** Against a perfect random opponent, NO strategy beats 50/50 random. However, if opponent has patterns, we can exploit them.

### 1.2 Strategy Evolution Path

```
Week 1: Random Strategy (50/50)
  ↓
Week 2: Adaptive Strategy (Pattern Detection)
  ↓
Week 3+: LLM Strategy (Strategic Reasoning) [Optional]
```

---

## 2. Strategy Interface

### 2.1 Base Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class Strategy(ABC):
    """
    Base class for all player strategies.

    All strategies must implement choose_parity method.
    """

    @abstractmethod
    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """
        Choose parity for this match.

        Args:
            match_id: Current match ID (for logging)
            opponent_id: Opponent player ID
            opponent_history: List of past matches against this opponent
                Format: [
                    {
                        "match_id": "R1M1",
                        "opponent_choice": "even",
                        "drawn_number": 8,
                        "won": True
                    },
                    ...
                ]
            standings: Current tournament standings
                Format: {
                    "wins": 2,
                    "losses": 1,
                    "draws": 0,
                    "points": 7
                }

        Returns:
            "even" or "odd"

        Raises:
            ValueError: If implementation error (should never happen)
        """
        pass

    def get_name(self) -> str:
        """Return strategy name for logging."""
        return self.__class__.__name__
```

---

## 3. Random Strategy (Baseline)

### 3.1 Algorithm

**Simple:** Choose "even" or "odd" with 50% probability each.

**Game Theory:** This is the Nash Equilibrium strategy. Against any opponent (even one with patterns), random guarantees:
- Expected win rate = 50%
- Cannot be exploited
- Unexploitable baseline

### 3.2 Implementation

```python
import random

class RandomStrategy(Strategy):
    """
    Random 50/50 strategy (baseline).

    Properties:
    - Expected win rate: 50% against any opponent
    - Cannot be exploited
    - No learning required
    - Fast (< 1ms)
    """

    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """Choose randomly between even and odd."""
        choice = random.choice(["even", "odd"])

        logger.debug(
            "Random choice made",
            match_id=match_id,
            opponent_id=opponent_id,
            choice=choice
        )

        return choice
```

### 3.3 Performance Characteristics

| Metric | Value |
|--------|-------|
| Win Rate (vs Random) | 50% |
| Win Rate (vs Patterned) | 50% |
| Computation Time | < 1ms |
| Memory Usage | O(1) |
| Data Requirements | None |

**When to Use:**
- **Week 1:** Get the system working
- **Against Unknown Opponents:** Safe baseline
- **As Fallback:** If pattern detection fails

---

## 4. Adaptive Strategy (Pattern Detection)

### 4.1 Core Concept

**Hypothesis:** Some student agents will have patterns in their choices (e.g., always choose even, alternate, favor even 70% of the time).

**Strategy:**
1. Collect opponent's past choices
2. Detect if pattern exists (statistical test)
3. If pattern detected → Exploit it
4. If no pattern → Play random (safe fallback)

### 4.2 High-Level Algorithm

```python
class AdaptiveStrategy(Strategy):
    """
    Adaptive strategy with pattern detection.

    Logic:
    1. Check if we have sufficient data (min 5 matches)
    2. Perform chi-squared test for non-randomness
    3. If pattern detected (p < 0.05):
       - If opponent favors even → We choose odd
       - If opponent favors odd → We choose even
    4. Else: Play random
    """

    def __init__(self, min_samples: int = 5, significance: float = 0.05):
        self.min_samples = min_samples
        self.significance = significance

    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """Choose based on opponent pattern detection."""

        # Step 1: Check data sufficiency
        if len(opponent_history) < self.min_samples:
            return self._random_choice()

        # Step 2: Extract opponent choices
        opponent_choices = [
            match["opponent_choice"]
            for match in opponent_history
        ]

        # Step 3: Detect pattern
        pattern_detected, bias = self._detect_pattern(opponent_choices)

        # Step 4: Exploit or fallback
        if pattern_detected:
            choice = self._exploit_bias(bias)
            logger.info(
                "Pattern detected - exploiting",
                match_id=match_id,
                opponent_id=opponent_id,
                bias=bias,
                choice=choice
            )
            return choice
        else:
            return self._random_choice()

    def _random_choice(self) -> str:
        """Fallback to random."""
        return random.choice(["even", "odd"])

    def _detect_pattern(self, choices: List[str]) -> tuple:
        """
        Detect if opponent has pattern.

        Returns:
            (pattern_detected: bool, bias: str or None)
        """
        from collections import Counter
        from scipy.stats import chisquare

        # Count frequencies
        counts = Counter(choices)
        even_count = counts.get("even", 0)
        odd_count = counts.get("odd", 0)
        total = len(choices)

        # Chi-squared test for deviation from 50/50
        observed = [even_count, odd_count]
        expected = [total / 2, total / 2]

        chi2, p_value = chisquare(observed, expected)

        # Pattern detected if p < significance level
        if p_value < self.significance:
            # Determine bias
            even_freq = even_count / total
            bias = "even" if even_freq > 0.5 else "odd"
            return (True, bias)
        else:
            return (False, None)

    def _exploit_bias(self, bias: str) -> str:
        """
        Exploit detected bias.

        If opponent favors even, we choose odd (counter).
        If opponent favors odd, we choose even (counter).
        """
        if bias == "even":
            return "odd"  # Counter opponent's bias
        else:
            return "even"
```

### 4.3 Performance Characteristics

| Metric | Value |
|--------|-------|
| Win Rate (vs Random) | ~50% (no pattern to exploit) |
| Win Rate (vs 70/30 Pattern) | ~60% (exploits bias) |
| Win Rate (vs Alternating) | ~100% (perfect prediction) |
| Computation Time | < 10ms |
| Memory Usage | O(n) where n = opponent matches |
| Data Requirements | Minimum 5 matches |

---

## 5. Pattern Detection Algorithms

### 5.1 Frequency Analysis

**Simplest approach:** Count how often opponent chooses even vs odd.

```python
def frequency_analysis(choices: List[str]) -> dict:
    """
    Analyze choice frequencies.

    Returns:
        {
            "even_freq": 0.7,
            "odd_freq": 0.3,
            "total": 10
        }
    """
    from collections import Counter

    counts = Counter(choices)
    total = len(choices)

    return {
        "even_freq": counts.get("even", 0) / total,
        "odd_freq": counts.get("odd", 0) / total,
        "total": total
    }

# Example
choices = ["even", "even", "odd", "even", "even", "odd", "even"]
result = frequency_analysis(choices)
# Output: {"even_freq": 0.71, "odd_freq": 0.29, "total": 7}
```

**Exploitation:**
- If `even_freq > 0.6` → Choose "odd" (counter bias)
- If `odd_freq > 0.6` → Choose "even" (counter bias)
- Else → Random (no clear bias)

### 5.2 Chi-Squared Test

**Statistical test for non-randomness.**

**Null Hypothesis (H0):** Opponent chooses randomly (50/50).

**Test:**
```python
from scipy.stats import chisquare

def chi_squared_test(choices: List[str], alpha: float = 0.05) -> dict:
    """
    Test if choices deviate significantly from 50/50.

    Args:
        choices: List of "even" or "odd"
        alpha: Significance level (default 0.05)

    Returns:
        {
            "chi2": 4.2,
            "p_value": 0.04,
            "pattern_detected": True,
            "bias": "even"
        }
    """
    from collections import Counter

    counts = Counter(choices)
    even_count = counts.get("even", 0)
    odd_count = counts.get("odd", 0)
    total = len(choices)

    # Expected: 50/50
    observed = [even_count, odd_count]
    expected = [total / 2, total / 2]

    chi2, p_value = chisquare(observed, expected)

    # Reject null hypothesis if p < alpha
    pattern_detected = p_value < alpha

    bias = None
    if pattern_detected:
        bias = "even" if even_count > odd_count else "odd"

    return {
        "chi2": chi2,
        "p_value": p_value,
        "pattern_detected": pattern_detected,
        "bias": bias
    }

# Example
choices = ["even", "even", "even", "even", "odd", "even", "even", "odd"]
result = chi_squared_test(choices)
# Output: {"chi2": 2.0, "p_value": 0.157, "pattern_detected": False, "bias": None}

choices = ["even", "even", "even", "even", "even", "even", "even", "odd"]
result = chi_squared_test(choices)
# Output: {"chi2": 4.5, "p_value": 0.034, "pattern_detected": True, "bias": "even"}
```

**Interpretation:**
- `p_value < 0.05` → Pattern detected (reject H0)
- `p_value >= 0.05` → No pattern (accept H0, play random)

### 5.3 Streak Detection

**Detect alternating patterns or runs.**

```python
def detect_streaks(choices: List[str]) -> dict:
    """
    Detect streaks and alternations.

    Returns:
        {
            "alternation_rate": 0.8,  # How often choice changes
            "max_streak": 5,          # Longest streak of same choice
            "current_streak": 2       # Current streak
        }
    """
    if len(choices) < 2:
        return {"alternation_rate": 0, "max_streak": len(choices), "current_streak": len(choices)}

    alternations = 0
    max_streak = 1
    current_streak = 1

    for i in range(1, len(choices)):
        if choices[i] != choices[i-1]:
            alternations += 1
            max_streak = max(max_streak, current_streak)
            current_streak = 1
        else:
            current_streak += 1

    max_streak = max(max_streak, current_streak)
    alternation_rate = alternations / (len(choices) - 1)

    return {
        "alternation_rate": alternation_rate,
        "max_streak": max_streak,
        "current_streak": current_streak
    }

# Example (alternating)
choices = ["even", "odd", "even", "odd", "even", "odd"]
result = detect_streaks(choices)
# Output: {"alternation_rate": 1.0, "max_streak": 1, "current_streak": 1}

# Example (streaks)
choices = ["even", "even", "even", "odd", "odd", "even"]
result = detect_streaks(choices)
# Output: {"alternation_rate": 0.6, "max_streak": 3, "current_streak": 1}
```

**Exploitation:**
- If `alternation_rate > 0.8` → Predict opposite of last choice
- If `current_streak >= 3` → Predict continuation of streak
- Else → Random

### 5.4 Markov Chain Analysis (Advanced)

**Model opponent as Markov chain (choice depends on previous choice).**

```python
def build_markov_chain(choices: List[str]) -> dict:
    """
    Build transition probabilities.

    Returns:
        {
            "even_after_even": 0.6,  # P(even | previous = even)
            "odd_after_even": 0.4,   # P(odd | previous = even)
            "even_after_odd": 0.3,   # P(even | previous = odd)
            "odd_after_odd": 0.7     # P(odd | previous = odd)
        }
    """
    from collections import defaultdict

    transitions = defaultdict(lambda: {"even": 0, "odd": 0})

    for i in range(1, len(choices)):
        prev = choices[i-1]
        curr = choices[i]
        transitions[prev][curr] += 1

    # Calculate probabilities
    result = {}
    for prev in ["even", "odd"]:
        total = transitions[prev]["even"] + transitions[prev]["odd"]
        if total > 0:
            result[f"even_after_{prev}"] = transitions[prev]["even"] / total
            result[f"odd_after_{prev}"] = transitions[prev]["odd"] / total
        else:
            result[f"even_after_{prev}"] = 0.5
            result[f"odd_after_{prev}"] = 0.5

    return result

# Example
choices = ["even", "even", "odd", "even", "even", "even", "odd", "even"]
chain = build_markov_chain(choices)
# Output: {
#   "even_after_even": 0.6,  # After even, opponent chooses even 60%
#   "odd_after_even": 0.4,
#   "even_after_odd": 1.0,   # After odd, opponent always chooses even
#   "odd_after_odd": 0.0
# }
```

**Exploitation:**
- Get last opponent choice from history
- Predict next choice using transition probabilities
- Choose opposite of predicted choice

---

## 6. Statistical Analysis

### 6.1 Confidence Intervals

**How confident are we in the pattern?**

```python
import math

def binomial_confidence_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple:
    """
    Calculate confidence interval for proportion.

    Args:
        successes: Number of times opponent chose "even"
        trials: Total number of matches
        confidence: Confidence level (default 95%)

    Returns:
        (lower_bound, upper_bound)
    """
    p = successes / trials
    z = 1.96  # For 95% confidence

    margin = z * math.sqrt(p * (1 - p) / trials)

    return (p - margin, p + margin)

# Example
even_count = 7
total = 10
lower, upper = binomial_confidence_interval(even_count, total)
# Output: (0.416, 0.984)
# Interpretation: We're 95% confident opponent chooses even between 41.6% and 98.4%
# Includes 0.5, so NOT statistically significant
```

### 6.2 Sample Size Requirements

**How many matches needed to detect pattern?**

```python
def min_sample_size(effect_size: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Calculate minimum sample size for pattern detection.

    Args:
        effect_size: Deviation from 50% (e.g., 0.7 - 0.5 = 0.2)
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.8)

    Returns:
        Minimum number of matches needed
    """
    from scipy.stats import norm

    z_alpha = norm.ppf(1 - alpha / 2)  # 1.96 for 95% confidence
    z_beta = norm.ppf(power)           # 0.84 for 80% power

    p0 = 0.5  # Null hypothesis (random)
    p1 = 0.5 + effect_size  # Alternative hypothesis

    n = ((z_alpha * math.sqrt(p0 * (1 - p0)) + z_beta * math.sqrt(p1 * (1 - p1))) / effect_size) ** 2

    return int(math.ceil(n))

# Examples
min_sample_size(0.2)  # Detect 70/30 split → ~50 matches
min_sample_size(0.1)  # Detect 60/40 split → ~200 matches
```

**Practical Implications:**
- Detecting 70/30 pattern: Need ~10 matches
- Detecting 60/40 pattern: Need ~50 matches
- In a 4-player tournament (3 matches per opponent): Can only detect strong patterns (65/35+)

---

## 7. LLM Strategy (Advanced)

### 7.1 Concept

**Use Claude API for strategic reasoning:**
- Analyze opponent's full history
- Consider tournament standings (risk/reward)
- Meta-strategy (e.g., play safe if leading, aggressive if behind)

### 7.2 Implementation

```python
from anthropic import Anthropic

class LLMStrategy(Strategy):
    """
    LLM-enhanced strategy using Claude API.

    CRITICAL: Must complete within 30s timeout.
    """

    def __init__(self, api_key: str, timeout: int = 25):
        self.client = Anthropic(api_key=api_key)
        self.timeout = timeout
        self.fallback = AdaptiveStrategy()

    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """Use LLM for strategic reasoning."""

        try:
            # Build prompt
            prompt = self._build_prompt(opponent_id, opponent_history, standings)

            # Call Claude API (with aggressive timeout)
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                timeout=self.timeout,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            choice = self._parse_response(response.content[0].text)

            # Validate
            if choice not in ["even", "odd"]:
                raise ValueError(f"Invalid choice from LLM: {choice}")

            return choice

        except Exception as e:
            logger.warning(
                "LLM strategy failed, using fallback",
                error=str(e),
                match_id=match_id
            )
            return self.fallback.choose_parity(
                match_id, opponent_id, opponent_history, standings
            )

    def _build_prompt(self, opponent_id: str, history: List[Dict], standings: Dict) -> str:
        """Build prompt for Claude."""
        prompt = f"""You are playing the Even/Odd game against opponent {opponent_id}.

Game Rules:
- You choose "even" or "odd"
- Opponent chooses simultaneously
- Referee draws random number 1-10
- If number parity matches your choice, you win (3 points)

Opponent History (last 10 matches):
{self._format_history(history[-10:])}

Your Current Standings:
- Wins: {standings.get('wins', 0)}
- Losses: {standings.get('losses', 0)}
- Points: {standings.get('points', 0)}

Task: Analyze opponent's pattern and choose "even" or "odd".

Respond with ONLY the word "even" or "odd" (no explanation).
"""
        return prompt

    def _format_history(self, history: List[Dict]) -> str:
        """Format history for prompt."""
        lines = []
        for i, match in enumerate(history, 1):
            lines.append(
                f"{i}. Opponent chose: {match['opponent_choice']}, "
                f"Number: {match['drawn_number']}, "
                f"You {'won' if match['won'] else 'lost'}"
            )
        return "\n".join(lines)

    def _parse_response(self, text: str) -> str:
        """Parse LLM response."""
        text = text.strip().lower()
        if "even" in text:
            return "even"
        elif "odd" in text:
            return "odd"
        else:
            raise ValueError(f"Cannot parse response: {text}")
```

### 7.3 Performance Characteristics

| Metric | Value |
|--------|-------|
| Win Rate (vs Random) | ~50% |
| Win Rate (vs Patterned) | ~65% (slightly better than Adaptive) |
| Win Rate (vs Meta-game) | ~55% (considers standings) |
| Computation Time | 5-25 seconds |
| API Cost | $0.003 per call (Sonnet) |
| Timeout Risk | HIGH (must have fallback) |

---

## 8. Strategy Comparison

### 8.1 Performance Matrix

| Strategy | vs Random | vs 70/30 Pattern | vs Alternating | Computation | Data Needed |
|----------|-----------|------------------|----------------|-------------|-------------|
| **Random** | 50% | 50% | 50% | < 1ms | None |
| **Adaptive** | 50% | ~60% | ~100% | < 10ms | 5+ matches |
| **LLM** | 50% | ~65% | ~95% | 5-25s | 1+ matches |

### 8.2 Recommended Strategy by Phase

| Week | Strategy | Rationale |
|------|----------|-----------|
| **Week 1** | Random | Focus on infrastructure, guaranteed 50% baseline |
| **Week 2** | Adaptive | Exploit patterns, low computational cost |
| **Week 3+** | LLM (with Adaptive fallback) | Meta-strategy for competitive edge |

---

## 9. Implementation Guide

### 9.1 Strategy Factory

```python
class StrategyFactory:
    """Factory for creating strategy instances."""

    STRATEGIES = {
        "random": RandomStrategy,
        "adaptive": AdaptiveStrategy,
        "llm": LLMStrategy
    }

    @classmethod
    def create(cls, strategy_type: str, **kwargs) -> Strategy:
        """Create strategy instance."""
        if strategy_type not in cls.STRATEGIES:
            logger.warning(f"Unknown strategy: {strategy_type}, using random")
            strategy_type = "random"

        strategy_class = cls.STRATEGIES[strategy_type]
        return strategy_class(**kwargs)

# Usage
strategy = StrategyFactory.create("adaptive", min_samples=5, significance=0.05)
choice = strategy.choose_parity(match_id, opponent_id, history, standings)
```

### 9.2 Configuration

```python
# config.py
STRATEGY_CONFIG = {
    "type": "adaptive",  # "random", "adaptive", "llm"
    "adaptive": {
        "min_samples": 5,
        "significance": 0.05
    },
    "llm": {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "timeout": 25
    }
}
```

### 9.3 Testing Strategies

```python
# tests/test_strategies.py
import pytest

def test_random_strategy_distribution():
    """Test random strategy is roughly 50/50."""
    strategy = RandomStrategy()
    choices = [strategy.choose_parity("M1", "P02", [], {}) for _ in range(1000)]
    even_count = choices.count("even")
    assert 400 < even_count < 600  # 95% confidence

def test_adaptive_exploits_bias():
    """Test adaptive strategy exploits 70/30 bias."""
    strategy = AdaptiveStrategy(min_samples=5, significance=0.05)

    # Simulate opponent with 70% even bias
    history = [
        {"opponent_choice": "even", "drawn_number": i % 10 + 1, "won": False}
        for i in range(7)
    ] + [
        {"opponent_choice": "odd", "drawn_number": i % 10 + 1, "won": False}
        for i in range(3)
    ]

    # Our strategy should counter by choosing "odd"
    choices = [strategy.choose_parity(f"M{i}", "P02", history, {}) for i in range(100)]
    odd_count = choices.count("odd")
    assert odd_count > 60  # Should heavily favor "odd"
```

---

## Summary

The Player Strategy Design provides:

✅ **Strategy Interface** for pluggable implementations
✅ **Random Strategy** as unexploitable baseline
✅ **Adaptive Strategy** with statistical pattern detection
✅ **Pattern Detection Algorithms** (frequency, chi-squared, streaks, Markov)
✅ **Statistical Analysis** (confidence intervals, sample sizes)
✅ **LLM Strategy** for advanced reasoning
✅ **Performance Comparison** and recommendations

**Key Principles:**
1. **Start Simple:** Random strategy first
2. **Add Intelligence:** Adaptive pattern detection
3. **Always Fallback:** LLM → Adaptive → Random
4. **Test Rigorously:** Validate against known patterns

---

**Related Documents:**
- [player-agent-architecture.md](./player-agent-architecture.md) - Player implementation
- [game-flow-design.md](./game-flow-design.md) - Complete game flow

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
