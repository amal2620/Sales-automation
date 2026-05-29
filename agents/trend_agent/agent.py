# agents/trend_agent/agent.py
# Trend Agent — finds real Google Trends keywords
# Tool: PyTrends (free, no API key needed)
# Output: top keywords → passed to Script Agent

from crewai import Agent, Task, Crew
from crewai.tools import tool
from pytrends.request import TrendReq
from dotenv import load_dotenv
import json

load_dotenv()

llm = "ollama/gemma4:e2b"

# ── PYTRENDS TOOL ──────────────────────────────────────────────
# WHY @tool decorator: tells CrewAI this function is a tool
# agents can call it automatically during their task
@tool("Google Trends Fetcher")
def fetch_google_trends(keywords: str) -> str:
    """
    Fetch real Google Trends data for given keywords.
    Input: comma separated keywords e.g. 'orchid kerala, exotic plants'
    Output: trend scores and related queries as JSON string
    """
    try:
        pytrends = TrendReq(hl='en-IN', tz=330)  # India timezone
        kw_list = [k.strip() for k in keywords.split(",")][:5]  # max 5 keywords

        # Build payload — last 90 days, India
        pytrends.build_payload(
            kw_list,
            timeframe='today 3-m',
            geo='IN-KL'  # Kerala specifically
        )

        # Get interest over time
        interest_df = pytrends.interest_over_time()

        if interest_df.empty:
            return json.dumps({"error": "No trend data found", "keywords": kw_list})

        # Get average score per keyword
        scores = {}
        for kw in kw_list:
            if kw in interest_df.columns:
                scores[kw] = round(float(interest_df[kw].mean()), 2)

        # Get related queries for top keyword
        related = pytrends.related_queries()
        top_related = []
        for kw in kw_list:
            if kw in related and related[kw]['top'] is not None:
                top_queries = related[kw]['top'].head(3)['query'].tolist()
                top_related.extend(top_queries)

        return json.dumps({
            "keyword_scores": scores,
            "related_queries": top_related[:5],
            "geo": "Kerala, India",
            "timeframe": "last 90 days"
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


# ── TREND RESEARCHER AGENT ─────────────────────────────────────
trend_researcher = Agent(
    role="SEO & Trend Researcher",
    goal="Find the best trending keywords for Kerala products to maximise YouTube reach",
    backstory="""Expert SEO researcher specialising in Kerala markets.
    You analyse Google Trends data and identify which keywords drive 
    the most traffic for small businesses in Kerala.
    You understand seasonal trends — Onam, Vishu, wedding season.
    You always back recommendations with real data, not guesses.""",
    llm=llm,
    tools=[fetch_google_trends],  # ← give agent the PyTrends tool
    verbose=True
)

def get_trending_keywords(
    product_name: str,
    product_category: str,
    location: str = "Kerala"
) -> dict:

    task = Task(
        description=f"""
        Find the best trending keywords for this product:

        Product: {product_name}
        Category: {product_category}
        Location: {location}

        Steps:
        1. Use the Google Trends Fetcher tool with relevant keywords
        2. Analyse which keywords have highest scores
        3. Suggest best keywords to use in YouTube title and description

        Search these keywords:
        "{product_name} {location}, {product_category} {location}, 
        buy {product_name} online, {product_name} price india"

        Return valid JSON only:
        {{
            "top_keywords": ["keyword1", "keyword2", "keyword3"],
            "trending_score": {{"keyword1": 0, "keyword2": 0, "keyword3": 0}},
            "recommended_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
            "best_posting_time": "recommendation based on trends",
            "seasonal_notes": "any relevant seasonal trends"
        }}

        Return ONLY the JSON, nothing else.
        """,
        expected_output="Valid JSON with trending keywords and scores",
        agent=trend_researcher
    )

    crew = Crew(
        agents=[trend_researcher],
        tasks=[task],
        verbose=True
    )

    print(f"\n🔍 Trend Agent: searching keywords for {product_name}")
    result = crew.kickoff()

    raw = str(result)
    json_start = raw.find("{")
    json_end = raw.rfind("}") + 1

    try:
        output = json.loads(raw[json_start:json_end])
        print("✅ Trends fetched!")
        return output
    except json.JSONDecodeError:
        print("⚠️ JSON parse failed — returning raw")
        return {"raw_output": raw}


if __name__ == "__main__":
    result = get_trending_keywords(
        product_name="Fancy Orchid",
        product_category="exotic plants",
        location="Kerala"
    )

    print("\n" + "="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))