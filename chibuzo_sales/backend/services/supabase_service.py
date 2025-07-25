



from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.supabase_service import supabase_client








from supabase import create_client
supabase_url = 'https://ecsrlqvifparesxakokl.supabase.co' # Your Supabase project URL
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjc3JscXZpZnBhcmVzeGFrb2tsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2NjczMDMsImV4cCI6MjA2MDI0MzMwM30.Zts7p1C3MNFqYYzp-wo3e0z-9MLfRDoY2YJ5cxSexHk'
   
supabase = create_client(supabase_url, supabase_key)
       
