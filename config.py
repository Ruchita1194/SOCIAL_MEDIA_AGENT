"""
config.py
Static default brand brief + scheduling data, used by the CLI (main.py).
The Streamlit app (app.py) doesn't use this - it derives a brief from
free text via brand.py instead.
"""

BRAND_BRIEF = {
    "brand_name": "Verdant & Co.",
    "voice": "warm, encouraging, a little witty — never salesy or shouty",
    "audience": "urban plant beginners, 22-35, apartment dwellers with limited light",
    "themes": [
        "plant care tips",
        "customer plant transformations",
        "myth-busting (overwatering, fake plants, etc.)",
        "behind-the-scenes / team",
        "product spotlight",
        "community Q&A",
    ],
    "platforms": ["Instagram", "TikTok", "LinkedIn"],
    "posts_per_day": 1,
    "banned_words": ["guaranteed", "miracle", "cure"],
}
