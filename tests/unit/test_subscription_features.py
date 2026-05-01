"""Sanity tests for subscription tier feature definitions."""

from __future__ import annotations

from src.models.subscription import TIER_FEATURES, SubscriptionTier


def test_all_tiers_defined() -> None:
    for tier in SubscriptionTier:
        assert tier in TIER_FEATURES, f"{tier} is missing from TIER_FEATURES"


def test_free_tier_has_watermark_and_promo() -> None:
    free = TIER_FEATURES[SubscriptionTier.FREE]
    assert free.has_watermark
    assert free.in_channel_promo_every_n_posts > 0
    assert free.price_stars == 0
    assert not free.can_use_custom_prompt
    assert not free.can_analyze_channel_style


def test_premium_tier_unlimited_no_watermark_no_promo() -> None:
    premium = TIER_FEATURES[SubscriptionTier.PREMIUM]
    assert not premium.has_watermark
    assert premium.in_channel_promo_every_n_posts == 0
    assert premium.monthly_post_limit == -1
    assert premium.can_use_custom_prompt
    assert premium.can_analyze_channel_style


def test_pro_priced_lower_than_premium() -> None:
    pro = TIER_FEATURES[SubscriptionTier.PRO]
    premium = TIER_FEATURES[SubscriptionTier.PREMIUM]
    assert pro.price_stars < premium.price_stars
