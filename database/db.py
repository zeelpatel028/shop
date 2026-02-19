import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL", "https://jlsksrmegclwvvkxcndc.supabase.co")
key: str = os.environ.get("SUPABASE_KEY", "sb_publishable_OE66YtP6q_b19jE4yrHdbg_nBHWxtGo")
# Note: User provided a long key which seems like an Anon key but starts with sb_publishable.
# The user provided a JWT token as well. I'll use the JWT token as the key if the publishable one fails,
# but usually for python client we need the Anon key (JWT).
# The user provided:
# 1. sb_publishable_... (This looks like a publishable API key, maybe for a different service or custom proxy?)
# 2. eyJhbGciOiJIUz... (This is definitely a JWT Anon Key)

# I will use the JWT token as the key for the Supabase client.
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impsc2tzcm1lZ2Nsd3Z2a3hjbmRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzExNDc0OTYsImV4cCI6MjA4NjcyMzQ5Nn0.q2wJGOBCMZXnoSENKZsNK-93IdXFtmlu8m7IlRJnET8"

supabase: Client = create_client(url, SUPABASE_KEY)

def init_db(app):
    # For Supabase, we don't strictly need to init_app like PyMongo,
    # but we can store the client in app.config if needed.
    app.config["SUPABASE_CLIENT"] = supabase
