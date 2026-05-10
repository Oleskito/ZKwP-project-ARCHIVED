PRICE_IDS: dict[tuple[str, str], str] = {
    ("Start", "monthly"): "price_1TVV2RDkxHlGZirdq3U1eYle",
    ("Start", "yearly"): "price_1TVV3TDkxHlGZirdKl85mcw9",
    ("Pro", "monthly"): "price_1TVV4bDkxHlGZirdYAC5qNZo",
    ("Pro", "yearly"): "price_1TVV55DkxHlGZirduUCYUoNF",
    ("VIP", "monthly"): "price_1TVV5vDkxHlGZirdfznDuiBb",
    ("VIP", "yearly"): "price_1TVV6ADkxHlGZirdg3lBLHcr",
}

VALID_PRICE_IDS: frozenset[str] = frozenset(PRICE_IDS.values())

# Reverse mapping: price_id → (plan_name, interval)
PRICE_ID_TO_PLAN: dict[str, tuple[str, str]] = {v: k for k, v in PRICE_IDS.items()}
