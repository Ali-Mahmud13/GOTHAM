"""
Test authentication login functionality.

This script tests the login endpoint without needing to start the server.

Run: python scripts/test_auth_login.py
"""

from pathlib import Path
import sys

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session
from app.db import engine
from app.api.auth import LoginRequest, hash_password
from app.models.auth import AuthUser
from sqlmodel import select


def test_login(username: str, password: str):
    """Test login for a given username and password."""
    print(f"\n🔐 Testing login for: {username}")
    
    with Session(engine) as session:
        # Find user
        statement = select(AuthUser).where(AuthUser.username == username)
        auth_user = session.exec(statement).first()
        
        if not auth_user:
            print(f"   ❌ User not found")
            return False
        
        # Verify password
        password_hash = hash_password(password)
        if auth_user.password_hash != password_hash:
            print(f"   ❌ Invalid password")
            return False
        
        print(f"   ✅ Login successful!")
        print(f"   👤 Role: {auth_user.role}")
        
        if auth_user.patient_id:
            print(f"   🏥 Patient ID: {auth_user.patient_id}")
        
        return True


def main():
    print("=" * 60)
    print("🧪 Testing Authentication System")
    print("=" * 60)
    
    # Test doctor login
    print("\n📋 Test 1: Doctor Login")
    test_login("Dr. Ali Mahmud", "123")
    
    # Test patient login
    print("\n📋 Test 2: Patient Login")
    test_login("Ayesha Khan", "123")
    
    # Test invalid credentials
    print("\n📋 Test 3: Invalid Password")
    test_login("Ayesha Khan", "wrong_password")
    
    # Test invalid username
    print("\n📋 Test 4: Invalid Username")
    test_login("Non Existent User", "123")
    
    print("\n" + "=" * 60)
    print("✅ Authentication Tests Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
