# 📜 Catullus Translation Lab

Welcome to the snarkiest Latin poetry project on GitHub.

This app lets you:
- Explore Catullus' Latin poems 🏛️
- Compare English translations side-by-side 🔍
- Generate sarcastic rewrites with the power of AI 🤖💬

Choose your translation pair, set your sarcasm level, and let LLaMA 3 roast your favorite neoteric verses.

---

## 🌟 Features

- ✨ Side-by-side line comparison across translators
- 🧠 Style comparison table: Tone, Diction, Fluency, Devices, Neoteric Spirit
- 🧂 Snark slider: Mild → Medium → High
- 🎭 AI-powered sarcastic rewrite in the style of a second translator
- 🚀 Powered by Groq’s ultra-fast LLaMA 3 API

---

## 🛠️ Installation

```bash
git clone https://github.com/JacDo/Catullus-poems.git
cd Catullus-poems
pip install -r requirements.txt
```

---

## 🔐 API Key Setup

To use the Groq API (for sarcasm & comparison), you'll need an API key.

1. Create a file called `.env` in the root of the repo.
2. Paste your key into it like this:

```
GROQ_API_KEY=your_really_long_groq_key_here
```

> ⚠️ Make sure the `.env` file is **NOT committed to GitHub**. It's already excluded via `.gitignore`.

---

## 🚀 Run the App

```bash
streamlit run app/catullus_app.py
```

---

## 📁 Project Structure

```
Catullus-poems/
├── app/
│   └── catullus_app.py            # Streamlit app
├── data/
│   ├── catullus_all_poems.json
│   ├── catullus_combined_translations.json
│   └── translations/
│       ├── catullus_english_perseus.json
│       ├── catullus_english_negenborn.json
│       ├── catullus_english_poetryintranslation.json
│       └── catullus_wikisource_english_all.json
├── scripts/
│   └── webscrape.py               # Collects and formats translation data
├── .env                           # Your API key (excluded from Git)
├── .gitignore
├── requirements.txt
└── README.md                      # You’re reading this
```

---

## 🧠 How It Works

- Translations are loaded from JSON files
- The app uses LLaMA 3 (via Groq’s API) to compare translations and generate sarcastic rewrites
- Prompts are crafted for literary precision and aesthetic judgment — with just the right
