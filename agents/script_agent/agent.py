 
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os
import json

load_dotenv()

llm ="ollama/gemma4:e2b"

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
        Write a YouTube marketing video script for:

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

    crew = Crew(agents=[scriptwriter], tasks=[task], verbose=True)

    print(f"\n🎬 Script Agent: generating YouTube script for {product_name}")

    result = crew.kickoff()
    raw = str(result)
    json_start = raw.find("{")
    json_end = raw.rfind("}") + 1

    try:
        scripts = json.loads(raw[json_start:json_end])
        print("✅ YouTube script generated!")
        return scripts
    except json.JSONDecodeError:
        print("⚠️ JSON parse failed — returning raw")
        return {"raw_output": raw}


# if __name__ == "__main__":
#     result = generate_youtube_script(
#         business_name="Jijo Orchid Nursery",
#         product_name="Fancy Orchid",
#         price="1450",
#         description="Rare imported Orchid form Nagaland, which has an exsecptional beauty and is hard to come by in India.",
#         location="Kollam, Kerala",
#         trending_keywords="Rare Orchid,Orchid in kerala,Foriegn Orchid"
# #     )

#     print("\n" + "="*50)
#     print(json.dumps(result, ensure_ascii=False, indent=2))