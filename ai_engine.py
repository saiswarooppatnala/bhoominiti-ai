import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CLAUDE_MODEL = "claude-sonnet-4-6"


def build_corpus(research_df):
    corpus = (
        research_df["Title"].fillna("").astype(str) + " "
        + research_df["Type"].fillna("").astype(str) + " "
        + research_df["Theme"].fillna("").astype(str) + " "
        + research_df["Region"].fillna("").astype(str) + " "
        + research_df["Summary"].fillna("").astype(str)
    )
    return corpus.str.replace(r"\s+", " ", regex=True).str.strip()


@st.cache_resource
def build_engine(corpus_tuple):
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vectorizer.fit_transform(list(corpus_tuple))
    return vectorizer, matrix


def search(query, research_df, vectorizer, matrix, top_k=None):
    query = (query or "").strip()
    if not query:
        return pd.DataFrame()

    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, matrix).flatten()

    results = research_df.copy()
    results["Similarity"] = similarities

    query_terms = set(vectorizer.build_analyzer()(query.lower()))

    def boost(text, amount):
        terms = set(vectorizer.build_analyzer()(str(text).lower()))
        return amount if query_terms.intersection(terms) else 0.0

    results["Title_Boost"] = results["Title"].apply(lambda t: boost(t, 0.08))
    results["Theme_Boost"] = results["Theme"].apply(lambda t: boost(t, 0.06))
    results["AI_Relevance"] = (results["Similarity"] + results["Title_Boost"] + results["Theme_Boost"]).clip(0, 1)

    results = results.sort_values(["AI_Relevance", "Year"], ascending=[False, False]).reset_index(drop=True)
    results["Rank"] = results.index + 1
    results["Relevance_Percent"] = (results["AI_Relevance"] * 100).round(1)

    return results.head(top_k) if top_k is not None else results


def rule_based_synthesis(results):
    if results.empty:
        return "No evidence was retrieved for this query."

    themes = results["Theme"].value_counts().index.tolist()
    regions = results["Region"].value_counts().index.tolist()
    years = pd.to_numeric(results["Year"], errors="coerce").dropna()

    parts = [f"The evidence engine retrieved {len(results)} high-ranking research records."]
    if themes:
        parts.append("The strongest evidence concentration is around " + ", ".join(themes[:3]) + ".")
    if regions:
        parts.append("The retrieved evidence covers " + ", ".join(regions[:4]) + ".")
    if not years.empty:
        parts.append(f"The retrieved evidence spans {int(years.min())}\u2013{int(years.max())}.")
    top_titles = results["Title"].head(3).tolist()
    if top_titles:
        parts.append("Priority evidence includes " + "; ".join(top_titles) + ".")

    return " ".join(parts)


def claude_available():
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def _evidence_block(results, max_records=8):
    lines = []
    for _, row in results.head(max_records).iterrows():
        lines.append(
            f"- [{row.get('Region', 'N/A')}, {row.get('Year', 'N/A')}] "
            f"\"{row['Title']}\" ({row.get('Type', 'N/A')}, theme: {row.get('Theme', 'N/A')}): {row['Summary']}"
        )
    return "\n".join(lines)


def claude_synthesis(query, results, api_key):
    if not api_key or results.empty:
        return rule_based_synthesis(results)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        evidence_block = _evidence_block(results)

        system_prompt = (
            "You are a policy research assistant for BhoomiNiti AI, a land governance intelligence "
            "platform. You are given a research question and a list of retrieved evidence records "
            "(title, region, year, theme, summary). Write a concise synthesis (120-180 words) in plain "
            "English that directly answers the question using only the evidence given, notes which "
            "themes and regions the evidence concentrates in, and flags if the evidence is thin or "
            "one-sided. Do not invent facts, statistics, or sources beyond what is listed."
        )
        user_prompt = f"Research question: {query}\n\nRetrieved evidence:\n{evidence_block}"

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = "\n".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
        return text if text else rule_based_synthesis(results)

    except Exception as exc:
        st.caption(f"LLM synthesis unavailable, showing offline summary instead ({exc.__class__.__name__}).")
        return rule_based_synthesis(results)


def claude_answer_followup(question, results, api_key, chat_history=None):
    if not api_key:
        return "Add an Anthropic API key in the sidebar to enable follow-up Q&A over the evidence."
    if results.empty:
        return "No evidence is currently loaded — run a search first."

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        evidence_block = _evidence_block(results, max_records=10)

        system_prompt = (
            "You are a policy research assistant. Answer the user's follow-up question using only "
            "the evidence records provided below. If the evidence doesn't contain the answer, say so "
            "clearly instead of guessing. Keep answers under 150 words unless asked for more detail."
        )

        messages = list(chat_history or [])
        messages.append({"role": "user", "content": f"Evidence records:\n{evidence_block}\n\nQuestion: {question}"})

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=400,
            system=system_prompt,
            messages=messages,
        )

        text = "\n".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
        return text or "Claude returned an empty response."

    except Exception as exc:
        return f"LLM call failed ({exc.__class__.__name__}): {exc}"


def matching_explanation(result):
    parts = []
    if result["Similarity"] > 0:
        parts.append(f"TF-IDF similarity: {result['Similarity'] * 100:.1f}%")
    if result["Title_Boost"] > 0:
        parts.append("title-term match")
    if result["Theme_Boost"] > 0:
        parts.append("theme-term match")
    return " • ".join(parts) if parts else "Low lexical similarity"
