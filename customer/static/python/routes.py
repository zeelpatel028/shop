from flask import render_template
from ... import customer_bp
from database.db import supabase

# Dashboard Logic
from . import dashboard

# Customer Management & CRUD
from . import customers

# Billing, Pending/Approved Bills & APIs
from . import billing
