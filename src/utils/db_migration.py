import argparse
import os
import subprocess
import sys

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"

def create_migration(message):
    """Create a new migration with the given message"""
    cmd = f"alembic revision --autogenerate -m \"{message}\""
    success, output = run_command(cmd)
    if success:
        print(f"✅ Migration created successfully: {output}")
    else:
        print(f"❌ Failed to create migration: {output}")

def apply_migrations():
    """Apply all pending migrations"""
    cmd = "alembic upgrade head"
    success, output = run_command(cmd)
    if success:
        print(f"✅ Migrations applied successfully")
    else:
        print(f"❌ Failed to apply migrations: {output}")

def show_migrations():
    """Show migration history"""
    cmd = "alembic history"
    success, output = run_command(cmd)
    if success:
        print(f"📋 Migration history:\n{output}")
    else:
        print(f"❌ Failed to show migration history: {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Database migration helper')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create migration command
    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('message', help='Migration message')
    
    # Apply migrations command
    apply_parser = subparsers.add_parser('apply', help='Apply pending migrations')
    
    # Show migrations command
    history_parser = subparsers.add_parser('history', help='Show migration history')
    
    args = parser.parse_args()
    
    if args.command == 'create' and args.message:
        create_migration(args.message)
    elif args.command == 'apply':
        apply_migrations()
    elif args.command == 'history':
        show_migrations()
    else:
        parser.print_help()