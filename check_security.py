#!/usr/bin/env python3
"""
Security Check Script for Classora LMS
Verifies no sensitive information is committed to version control
"""

import os
import re
import sys
from pathlib import Path

# Patterns that should not be in committed files (excluding documentation)
SENSITIVE_PATTERNS = [
    r'GEMINI_API_KEY\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']',  # Real API keys (longer)
    r'SECRET_KEY\s*=\s*["\'][A-Za-z0-9!@#$%^&*()_-]{30,}["\']',  # Real Django secrets (longer)
    r'password\s*=\s*["\'][^"\']{8,}["\']',  # Real passwords (not test ones)
    r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
    r'-----BEGIN [A-Z]+ KEY-----',  # Private keys
]

# Ignore these patterns in documentation and example files
IGNORE_IN_FILES = [
    'your_api_key_here',
    'your-secret-key-here',
    'django-insecure-',
    'adminpass123',  # Test password
    'placeholder',
    'example',
]

# Files that should never be committed
FORBIDDEN_FILES = [
    '.env',
    '.env.local',
    '.env.development',
    '.env.test',
    '.env.production',
    'secrets.json',
    'credentials.json',
    'api_keys.txt',
    'local_settings.py',
    'db.sqlite3',
    '*.pem',
    '*.key',
    '*.p12',
    '*.pfx',
]

def check_file_for_secrets(filepath):
    """Check a single file for potential secrets"""
    # Skip documentation, test, and example files
    skip_patterns = [
        '.md', 'README', 'GUIDE', 'test_', '_test.', 
        'example', 'setup', 'package-lock.json'
    ]
    
    if any(pattern in filepath for pattern in skip_patterns):
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Skip if content contains ignore patterns
        if any(ignore in content for ignore in IGNORE_IN_FILES):
            return False
            
        for pattern in SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Skip if it's a placeholder or example
                matched_text = match.group()
                if any(ignore in matched_text for ignore in IGNORE_IN_FILES):
                    continue
                    
                line_num = content[:match.start()].count('\n') + 1
                print(f"⚠️  Potential secret found in {filepath}:{line_num}")
                print(f"   Pattern: {matched_text[:50]}...")
                return True
    except Exception as e:
        print(f"Could not read {filepath}: {e}")
    
    return False

def check_git_tracked_files():
    """Check all git-tracked files for secrets"""
    print("🔍 Checking git-tracked files for sensitive information...")
    
    # Get list of tracked files
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True,
            text=True,
            check=True
        )
        tracked_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        print("❌ Not a git repository or git not available")
        return False
    
    secrets_found = False
    
    for filepath in tracked_files:
        # Skip binary files and certain directories
        if any(skip in filepath for skip in ['.git/', 'node_modules/', 'venv/', '__pycache__/']):
            continue
            
        # Check if it's a forbidden file
        for forbidden in FORBIDDEN_FILES:
            if forbidden.endswith('*'):
                if filepath.startswith(forbidden[:-1]):
                    print(f"❌ Forbidden file tracked: {filepath}")
                    secrets_found = True
            elif filepath == forbidden:
                print(f"❌ Forbidden file tracked: {filepath}")
                secrets_found = True
        
        # Check file content for secrets
        if filepath.endswith(('.py', '.js', '.jsx', '.json', '.yml', '.yaml', '.md', '.txt')):
            if check_file_for_secrets(filepath):
                secrets_found = True
    
    return not secrets_found

def check_gitignore():
    """Check if .gitignore exists and contains essential patterns"""
    print("\n📋 Checking .gitignore configuration...")
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        print("❌ .gitignore file not found!")
        return False
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    essential_patterns = [
        '.env',
        '*.key',
        '*.pem',
        'secrets.json',
        'credentials.json',
        'local_settings.py',
        'db.sqlite3',
    ]
    
    missing_patterns = []
    for pattern in essential_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"⚠️  Missing patterns in .gitignore: {', '.join(missing_patterns)}")
        return False
    
    print("✅ .gitignore contains essential patterns")
    return True

def check_environment_variables():
    """Check if environment variables are properly set"""
    print("\n🔧 Checking environment configuration...")
    
    # Check if .env file exists
    env_path = Path('.env')
    if env_path.exists():
        print("⚠️  .env file exists - make sure it's not committed!")
        
        # Check if it contains placeholder values
        with open(env_path, 'r') as f:
            env_content = f.read()
            
        placeholders = ['your-', 'placeholder', 'change-me', 'xxx']
        for placeholder in placeholders:
            if placeholder in env_content.lower():
                print(f"⚠️  Found placeholder values in .env file")
    
    # Check if example file exists
    example_path = Path('env.example')
    if example_path.exists():
        print("✅ Environment example file exists")
    else:
        print("⚠️  Consider creating env.example file for reference")
    
    return True

def main():
    print("🔐 Classora LMS Security Check")
    print("=" * 40)
    
    all_checks_passed = True
    
    # Run all security checks
    if not check_gitignore():
        all_checks_passed = False
    
    if not check_git_tracked_files():
        all_checks_passed = False
    
    if not check_environment_variables():
        all_checks_passed = False
    
    print("\n" + "=" * 40)
    if all_checks_passed:
        print("✅ All security checks passed!")
        print("🎉 Your repository appears to be secure.")
        sys.exit(0)
    else:
        print("❌ Security issues found!")
        print("🚨 Please address the issues above before committing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
