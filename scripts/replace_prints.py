#!/usr/bin/env python3
"""
Script to replace print() calls with logger calls throughout the codebase
"""

import os
import re
import ast
from pathlib import Path


def get_log_level(message):
    """Determine appropriate log level based on message content"""
    message_lower = message.lower()
    
    # Error indicators
    if any(word in message_lower for word in ['error', 'failed', 'exception', 'traceback']):
        return 'error'
    
    # Warning indicators  
    if any(word in message_lower for word in ['warning', 'warn', 'could not', 'unable to', 'missing']):
        return 'warning'
    
    # Debug indicators
    if any(word in message_lower for word in ['debug', 'trace', 'dump', 'raw', 'request', 'response']):
        return 'debug'
    
    # Info indicators (general information, success messages)
    if any(word in message_lower for word in ['loaded', 'initialized', 'created', 'started', 'completed', 'success']):
        return 'info'
    
    # Default to info for most messages
    return 'info'


def add_logger_import(content, filename):
    """Add logger import to a Python file if not already present"""
    lines = content.split('\n')
    
    # Check if logger import already exists
    has_logger_import = any('from utils.logging_config import get_logger' in line for line in lines)
    has_logger_instance = any('logger = get_logger(__name__)' in line for line in lines)
    
    if has_logger_import and has_logger_instance:
        return content
    
    # Find insertion point after imports
    insert_idx = 0
    in_docstring = False
    docstring_quotes = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Handle docstrings
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = True
                docstring_quotes = stripped[:3]
                if stripped.count(docstring_quotes) >= 2:  # Single line docstring
                    in_docstring = False
                continue
        else:
            if docstring_quotes in stripped:
                in_docstring = False
                continue
            continue
        
        # Skip empty lines and comments after docstring
        if not stripped or stripped.startswith('#'):
            continue
        
        # If it's an import, update insert point
        if stripped.startswith('import ') or stripped.startswith('from '):
            insert_idx = i + 1
        else:
            # Found first non-import line
            break
    
    # Insert logger import and instance
    if not has_logger_import:
        lines.insert(insert_idx, 'from utils.logging_config import get_logger')
        insert_idx += 1
    
    if not has_logger_instance:
        # Add blank line before logger instance if needed
        if insert_idx < len(lines) and lines[insert_idx].strip():
            lines.insert(insert_idx, '')
            insert_idx += 1
        
        lines.insert(insert_idx, f'# Initialize logger for this module')
        lines.insert(insert_idx + 1, f'logger = get_logger(__name__)')
        lines.insert(insert_idx + 2, '')
    
    return '\n'.join(lines)


def replace_print_statements(content):
    """Replace print() statements with appropriate logger calls"""
    # Pattern to match print statements
    print_pattern = r'print\s*\(\s*([^)]+)\s*\)'
    
    def replace_print(match):
        arg = match.group(1).strip()
        
        # Extract the message content for log level determination
        # Handle f-strings, regular strings, and variables
        message_content = arg
        if arg.startswith('f"') or arg.startswith("f'"):
            # F-string
            message_content = arg[2:-1]  # Remove f" and "
        elif arg.startswith('"') or arg.startswith("'"):
            # Regular string
            message_content = arg[1:-1]  # Remove quotes
        
        # Determine log level
        log_level = get_log_level(message_content)
        
        return f'logger.{log_level}({arg})'
    
    # Replace all print statements
    modified_content = re.sub(print_pattern, replace_print, content)
    
    return modified_content


def process_file(file_path):
    """Process a single Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if no print statements
        if 'print(' not in content:
            return False
        
        # Skip test files and scripts that might need print statements
        filename = file_path.name.lower()
        # Only skip actual test files, not our project files
        if 'test_' in filename and 'tests' in str(file_path):
            print(f"Skipping {file_path} (test file)")  # Keep print for script output
            return False
        
        original_content = content
        
        # Add logger import
        content = add_logger_import(content, filename)
        
        # Replace print statements
        content = replace_print_statements(content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Updated: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files"""
    project_root = Path(__file__).parent.parent
    
    # Files to process - include all our project directories
    target_dirs = ['gui', 'api', 'database', 'utils']
    
    # Also process root level files
    root_files = ['main.py', 'config.py']
    
    total_files = 0
    updated_files = 0
    
    # Process root level files
    for filename in root_files:
        file_path = project_root / filename
        if file_path.exists():
            total_files += 1
            if process_file(file_path):
                updated_files += 1
    
    # Process directory files
    for dir_name in target_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue
        
        for py_file in dir_path.rglob('*.py'):
            if py_file.name == '__init__.py':
                continue
                
            # Skip venv directory completely
            if 'venv' in py_file.parts:
                continue
                
            total_files += 1
            if process_file(py_file):
                updated_files += 1
    
    print(f"\nProcessing complete:")
    print(f"  Files processed: {total_files}")
    print(f"  Files updated: {updated_files}")


if __name__ == '__main__':
    main()