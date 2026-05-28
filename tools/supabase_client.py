from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def test_connection():
    result = supabase.table("businesses").select("*").execute()
    print("    Supabase connected!")
    print(f"   Businesses in DB: {len(result.data)}")
    return supabase

if __name__ == "__main__":
    test_connection() 
