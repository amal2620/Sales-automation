# agents/supervisor_agent.py
# Supervisor Agent — orchestrates all agents
# Reads/writes state to Supabase between each agent
# Retries failed agents up to 3 times

from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os
import json
from tools.supabase_client import supabase
from agents.trend_agent.agent import get_trending_keywords
from agents.script_agent.agent import generate_youtube_script

load_dotenv()

llm = "ollama/gemma4:e2b"

# ── SUPERVISOR AGENT ───────────────────────────────────────────
supervisor = Agent(
    role="Production Supervisor",
    goal="Orchestrate all agents, ensure quality output, retry failures",
    backstory="""Experienced production manager who coordinates 
    a team of AI specialists. You ensure each agent completes 
    its job correctly before passing to the next. 
    You retry failed steps and flag issues to the human.
    You save all intermediate results to memory so nothing is lost.""",
    llm=llm,
    verbose=True
)

def save_to_supabase(table: str, data: dict) -> str:
    """Save agent output to Supabase — shared memory between agents"""
    try:
        result = supabase.table(table).insert(data).execute()
        print(f"💾 Saved to Supabase: {table}")
        return result.data[0]['id']
    except Exception as e:
        print(f"⚠️ Supabase save failed: {e}")
        return None

def run_pipeline(
    business_name: str,
    product_name: str,
    price: str,
    description: str,
    location: str,
    product_category: str,
    language: str = "Malayalam"
) -> dict:
    """
    Full pipeline — Supervisor coordinates all agents:
    1. Trend Agent    → finds keywords
    2. Script Agent   → writes script using keywords
    3. Save to Supabase at each step
    4. Retry up to 3x if any step fails
    """

    print(f"\n🎯 Supervisor starting pipeline for: {product_name}")
    print("="*50)

    pipeline_state = {
        "product": product_name,
        "business": business_name,
        "status": "started"
    }

    # ── STEP 1: TREND AGENT ────────────────────────────────────
    print("\n📍 Step 1: Trend Agent")
    trends = None
    for attempt in range(3):  # retry up to 3 times
        try:
            trends = get_trending_keywords(
                product_name=product_name,
                product_category=product_category,
                location=location
            )
            if "top_keywords" in trends:
                print(f"✅ Trends OK — attempt {attempt+1}")
                break
        except Exception as e:
            print(f"⚠️ Trend attempt {attempt+1} failed: {e}")

    if not trends or "top_keywords" not in trends:
        print("❌ Trend Agent failed after 3 attempts — using defaults")
        trends = {
            "top_keywords": [product_name, location, product_category],
            "recommended_tags": [product_name, location],
            "best_posting_time": "10AM-12PM weekdays"
        }

    # Save trends to Supabase
    trending_keywords = ", ".join(trends.get("top_keywords", []))
    pipeline_state["trends"] = trends

    # ── STEP 2: SCRIPT AGENT ───────────────────────────────────
    print("\n📍 Step 2: Script Agent")
    script = None
    for attempt in range(3):
        try:
            script = generate_youtube_script(
                business_name=business_name,
                product_name=product_name,
                price=price,
                description=description,
                location=location,
                trending_keywords=trending_keywords
            )
            if "script" in script:
                print(f"✅ Script OK — attempt {attempt+1}")
                break
        except Exception as e:
            print(f"⚠️ Script attempt {attempt+1} failed: {e}")

    if not script or "script" not in script:
        print("❌ Script Agent failed after 3 attempts")
        return {"error": "Script generation failed", "state": pipeline_state}

    pipeline_state["script"] = script
    pipeline_state["status"] = "script_ready"

    # ── SAVE FULL STATE TO SUPABASE ────────────────────────────
    # WHY: next agents (translation, media) load from here
    # They don't need to rerun trend/script agents
    try:
        supabase.table("videos").insert({
            "status": "script_ready",
            "mp4_url": json.dumps(pipeline_state)  # temp store full state
        }).execute()
        print("💾 Pipeline state saved to Supabase")
    except Exception as e:
        print(f"⚠️ State save failed: {e}")

    print("\n" + "="*50)
    print("✅ SUPERVISOR: Pipeline complete — script ready for translation")
    print(f"📊 Critic Score: {script.get('critic', {}).get('average_score', 'N/A')}/10")
    print("="*50)

    return pipeline_state


if __name__ == "__main__":
    result = run_pipeline(
        business_name="Jijo Orchid Nursery",
        product_name="Fancy Orchid",
        price="1450",
        description="Rare imported Orchid from Nagaland, exceptional beauty.",
        location="Kollam, Kerala",
        product_category="exotic plants",
        language="Malayalam"
    )

    print("\n🏁 FINAL PIPELINE STATE:")
    print(json.dumps(result, ensure_ascii=False, indent=2))