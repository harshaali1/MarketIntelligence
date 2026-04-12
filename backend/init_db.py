#!/usr/bin/env python3
"""
Initialize database tables for Invest Together feature
Run this once to create the investment_club, club_member, club_sharing tables
"""

import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from applications.database import db
from applications.config import Config
from main import app
from applications.models import InvestmentClub, ClubMember, ClubSharing

if __name__ == '__main__':
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)
    
    # Enter app context
    with app.app_context():
        print("\n1. Checking database configuration...")
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
        print(f"   Database URI: {db_uri}")
        
        print("\n2. Creating all tables...")
        try:
            db.create_all()
            print("   ✅ All tables created successfully!")
        except Exception as e:
            print(f"   ❌ Error creating tables: {e}")
            sys.exit(1)
        
        print("\n3. Verifying new tables exist...")
        try:
            # Try to query each table
            investment_clubs_count = InvestmentClub.query.count()
            club_members_count = ClubMember.query.count()
            club_sharing_count = ClubSharing.query.count()
            
            print(f"   ✅ investment_club table: {investment_clubs_count} records")
            print(f"   ✅ club_member table: {club_members_count} records")
            print(f"   ✅ club_sharing table: {club_sharing_count} records")
        except Exception as e:
            print(f"   ❌ Error verifying tables: {e}")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("Database initialization complete! ✅")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Start the backend: python3 main.py")
        print("2. Create investment clubs from the frontend")
        print("3. Join and manage clubs with team members")
