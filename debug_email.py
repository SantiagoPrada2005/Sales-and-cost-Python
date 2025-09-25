#!/usr/bin/env python3
"""
Script de depuración para validación de email
"""

from email_validator import validate_email, EmailNotValidError

def test_email_validation():
    """Probar diferentes emails para entender el problema"""
    test_emails = [
        'test@example.com',
        'user@gmail.com',
        'admin@localhost',
        'test@test.local',
        'valid@domain.org'
    ]
    
    for email in test_emails:
        try:
            result = validate_email(email)
            print(f"✅ {email} -> VÁLIDO: {result.email}")
        except EmailNotValidError as e:
            print(f"❌ {email} -> INVÁLIDO: {e}")

if __name__ == "__main__":
    print("🔍 Probando validación de emails...")
    test_email_validation()