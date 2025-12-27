"""Simple test to verify core functionality without full server."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from app.db.models import Job, GenerationJob, JobStatus
        print("[OK] Database models imported")
        
        from app.core.config import settings
        print("[OK] Config imported")
        
        from app.core.queue import job_queue
        print("[OK] Job queue imported")
        
        from app.core.generation import ContentGenerator
        print("[OK] Content generator imported")
        
        from app.core.engine import ai_engine
        print("[OK] AI engine imported")
        
        from app.core.virality import ViralityScorer
        print("[OK] Virality scorer imported")
        
        from app.core.captions import CaptionGenerator
        print("[OK] Caption generator imported")
        
        from app.core.clip_detector import ClipDetector
        print("[OK] Clip detector imported")
        
        from app.core.keepalive import start_keepalive, stop_keepalive
        print("[OK] Keep-alive imported")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database():
    """Test database creation."""
    print("\nTesting database...")
    try:
        from app.db.engine import create_db_and_tables
        create_db_and_tables()
        print("[OK] Database created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Database creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Aigis Simple Test")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    
    print("\n" + "=" * 60)
    print("Results:")
    for name, result in results:
        print(f"  {name}: {'[PASSED]' if result else '[FAILED]'}")
    
    all_passed = all(r for _, r in results)
    sys.exit(0 if all_passed else 1)

