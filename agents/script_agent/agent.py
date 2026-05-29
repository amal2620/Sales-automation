 
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm ="ollama/gemma4:e2b"

PLATFORM_RULES = {
    "youtube": "2 min script, hook+body+CTA, SEO title under 60 chars, keyword-rich description"
}

scriptwriter = Agent(
    role = "YouTube Marketing Copywriter",
    goal = "Write compelling YouTube scripts for micro-businesses that drive real sales",
    backstory="""You are an expert YouTube scriptwriter specialising in 
    Indian small businesses. You understand Kerala culture, local products, 
    and what makes Indian customers buy. You write punchy hooks, clear 
    product benefits, and strong calls to action.""",
    llm=llm,
    llm_config={"temperature": 0.7}
)

critic = Agent(
    role="Marketing Quality Reviewer",
    goal="Ensure every script meets quality standards before reaching the human",
    backstory="""Harsh but fair marketing director with 15 years experience.
    You reject scripts with weak hooks, unclear pricing, or generic content.
    You give specific actionable feedback — not just 'make it better'.
    You approve only when the script would genuinely make a Kerala customer stop and buy.""",
    llm=llm,
    llm_config={"temperature": 0.7}
)

def generate_youtube_script(
    business_name: str,
    product_name: str,
    price: str,
    description: str,
    location: str,
    trending_keywords: str
) -> dict:

    task = Task(
        description=f"""
        Write a YouTube marketing video script using these platform rules:
        PLATFORM RULES: {PLATFORM_RULES['youtube']}

        Business: {business_name}
        Product: {product_name}
        Price: ₹{price}
        Description: {description}
        Location: {location}
        Trending Keywords: {trending_keywords}

        Return valid JSON only:
        {{
            "title": "SEO optimised YouTube title under 60 chars",
            "hook": "first 15 seconds — grab attention immediately",
            "body": "main content 60-90 seconds — benefits, story, why buy",
            "cta": "final 15 seconds — price + where to buy + urgency",
            "description": "YouTube description 150 words with keywords",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
            "key_selling_points": ["point1", "point2", "point3"]
        }}

        RULES:
        - English only
        - Hook must stop scrolling in first 3 seconds
        - Mention price clearly
        - Location keywords important for local SEO
        - Return ONLY the JSON, nothing else
        """,
        expected_output="Valid JSON with YouTube script",
        agent=scriptwriter
    )

    critic_task = Task(
        description=f"""
        Review the YouTube script written for {product_name} priced at ₹{price}.

        Score it on these criteria (1-10 each):
        1. Hook strength — does it stop scrolling in 3 seconds?
        2. Price clarity — is ₹{price} mentioned clearly?
        3. Local relevance — does it feel authentic to {location}?
        4. CTA strength — does it create urgency to buy?
        5. Overall quality — would a Kerala customer actually buy?

        If average score >= 7: approve it.
        If average score < 7: reject with specific rewrite instructions.

        Return valid JSON only:
        {{
            "approved": true or false,
            "scores": {{
                "hook": 0,
                "price_clarity": 0,
                "local_relevance": 0,
                "cta_strength": 0,
                "overall": 0
            }},
            "average_score": 0.0,
            "feedback": "specific feedback if rejected, empty string if approved"
        }}
        """,
        expected_output="Valid JSON with approval decision and scores",
        agent=critic,
        context=[task]  # ← critic reads script output first
    )

    crew = Crew(
        agents=[scriptwriter, critic],
        tasks=[task, critic_task],
        verbose=True,
        max_iter=3  # ← max 3 refinement loops
    )

    print(f"\n🎬 Script Agent: generating YouTube script for {product_name}")

    crew.kickoff()
    # Get script output from task 1 directly
    # WHY: crew.kickoff() returns last task — we want first task
    script_raw = str(task.output.raw)
    critic_raw = str(critic_task.output.raw)

    # Parse critic decision
    try:
        c_start = critic_raw.find("{")
        c_end = critic_raw.rfind("}") + 1
        critic_result = json.loads(critic_raw[c_start:c_end])
        print(f"📊 Critic Score: {critic_result['average_score']}/10")
        print(f"✅ Approved: {critic_result['approved']}")
    except:
        critic_result = {}

    # Parse script
    try:
        s_start = script_raw.find("{")
        s_end = script_raw.rfind("}") + 1
        script_result = json.loads(script_raw[s_start:s_end])
        print("✅ Script extracted!")
        return {
            "script": script_result,
            "critic": critic_result
        }
    except json.JSONDecodeError:
        print("⚠️ JSON parse failed — returning raw")
        return {"raw_output": script_raw}
    
if __name__ == "__main__":
    result = generate_youtube_script(
        business_name="Jijo Orchid Nursery",
        product_name="Fancy Orchid",
        price="1450",
        description="Rare imported Orchid from Nagaland, exceptional beauty, hard to find in India.",
        location="Kollam, Kerala",
        trending_keywords="rare orchid kerala, exotic plants kollam, foreign orchid india"
    )

    print("\n" + "="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))