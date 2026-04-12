#!/usr/bin/env python3
"""
Test script for Invest Together API
Run this to verify the backend is working correctly
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = 'http://127.0.0.1:5001'
TEST_USERNAME = 'testuser'
TEST_EMAIL = 'testuser@example.com'
TEST_PASSWORD = 'testpassword123'

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_backend_connection():
    print_section("1. Testing Backend Connection")
    try:
        response = requests.get(f'{BACKEND_URL}/api/v1/valid_user', 
                              json={'username': 'dummy'}, 
                              timeout=5)
        print(f"✅ Backend is running on {BACKEND_URL}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}")
        print(f"   Make sure backend is running: python3 main.py")
        return False

def test_signup():
    print_section("2. Testing User Registration")
    
    # First check if user exists
    response = requests.post(f'{BACKEND_URL}/api/v1/valid_user',
                           json={'username': TEST_USERNAME})
    
    if response.status_code == 200:
        print(f"✅ Username '{TEST_USERNAME}' is available")
    
    # Try to signup
    signup_data = {
        'username': TEST_USERNAME,
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    }
    
    response = requests.post(f'{BACKEND_URL}/api/v1/signup',
                           json=signup_data)
    
    if response.status_code == 201:
        print(f"✅ User registered successfully")
        return True
    elif response.status_code == 400 and 'already' in response.text.lower():
        print(f"ℹ️  User already exists (this is ok)")
        return True
    else:
        print(f"❌ Signup failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_login():
    print_section("3. Testing User Login")
    
    login_data = {
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD
    }
    
    response = requests.post(f'{BACKEND_URL}/api/v1/login',
                           json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        if token:
            print(f"✅ Login successful")
            print(f"   Token: {token[:30]}...")
            return token
        else:
            print(f"❌ No token in response")
            return None
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_create_club(token):
    print_section("4. Testing Create Club")
    
    if not token:
        print("❌ Skipped (no token)")
        return None
    
    headers = {'Authentication-Token': token}
    club_data = {'club_name': 'Test Club'}
    
    response = requests.post(f'{BACKEND_URL}/api/club/create',
                           json=club_data,
                           headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            club_id = data.get('club_id')
            join_code = data.get('join_code')
            print(f"✅ Club created successfully")
            print(f"   Club ID: {club_id}")
            print(f"   Join Code: {join_code}")
            return club_id, join_code
        else:
            print(f"❌ Club creation failed: {data.get('error')}")
            return None
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_get_clubs(token):
    print_section("5. Testing Get My Clubs")
    
    if not token:
        print("❌ Skipped (no token)")
        return
    
    headers = {'Authentication-Token': token}
    
    response = requests.get(f'{BACKEND_URL}/api/club/my-clubs',
                          headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            clubs = data.get('clubs', [])
            print(f"✅ Retrieved {len(clubs)} club(s)")
            for club in clubs:
                print(f"   - {club['club_name']} (ID: {club['club_id']}, Code: {club['join_code']})")
        else:
            print(f"❌ Failed to get clubs: {data.get('error')}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")

def main():
    print("\n" + "="*60)
    print("  Invest Together - Backend API Test")
    print("="*60)
    
    # Test 1: Connection
    if not test_backend_connection():
        sys.exit(1)
    
    # Test 2: Signup
    if not test_signup():
        sys.exit(1)
    
    # Test 3: Login
    token = test_login()
    if not token:
        sys.exit(1)
    
    # Test 4: Create Club
    club_info = test_create_club(token)
    
    # Test 5: Get Clubs
    test_get_clubs(token)
    
    print_section("✅ All Tests Completed!")
    print("Backend is working correctly!\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
