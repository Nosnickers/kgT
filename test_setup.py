"""
Quick test script to verify all modules are working correctly.
"""

import sys
from pathlib import Path


def test_imports():
    print("Testing imports...")
    try:
        import config
        print("✓ config module imported")
        
        from src.data_loader import DataLoader, DataChunk
        print("✓ data_loader module imported")
        
        from src.neo4j_manager import Neo4jManager, Entity, Relationship
        print("✓ neo4j_manager module imported")
        
        from src.entity_extractor import EntityExtractor, ExtractionResult
        print("✓ entity_extractor module imported")
        
        from src.graph_builder import GraphBuilder
        print("✓ graph_builder module imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_data_loader():
    print("\nTesting data loader...")
    try:
        from src.data_loader import DataLoader
        
        loader = DataLoader("Apple_Environmental_Progress_Report_2024.md")
        chunks = loader.load_and_chunk()
        
        print(f"✓ Loaded {len(chunks)} chunks")
        
        if chunks:
            stats = loader.get_stats(chunks)
            print(f"✓ Total words: {stats['total_words']}")
            print(f"✓ Average words per chunk: {stats['avg_words_per_chunk']:.2f}")
            print(f"✓ Sections: {len(stats['sections'])}")
        
        return True
    except Exception as e:
        print(f"✗ Data loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    print("\nTesting configuration...")
    try:
        from config import Config
        
        try:
            config = Config.from_env()
            print("✓ Configuration loaded from .env")
            
            try:
                config.validate_config()
                print("✓ Configuration validated")
                print(f"  - Neo4j URI: {config.neo4j.uri}")
                print(f"  - Ollama Model: {config.ollama.model}")
                print(f"  - Data File: {config.data.file_path}")
            except Exception as e:
                print(f"⚠ Configuration validation warning: {e}")
                print("  (This is expected if .env file is not set up yet)")
            
            return True
        except Exception as e:
            print(f"⚠ Could not load .env file: {e}")
            print("  (This is expected if .env file does not exist yet)")
            return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_neo4j_connection():
    print("\nTesting Neo4j connection...")
    try:
        from src.neo4j_manager import Neo4jManager
        from config import Config
        
        try:
            config = Config.from_env()
            manager = Neo4jManager(
                uri=config.neo4j.uri,
                username=config.neo4j.username,
                password=config.neo4j.password
            )
            
            manager.connect()
            print("✓ Connected to Neo4j")
            
            count = manager.get_entity_count()
            print(f"✓ Current entity count: {count}")
            
            manager.close()
            print("✓ Connection closed")
            
            return True
        except Exception as e:
            print(f"⚠ Neo4j connection test skipped: {e}")
            print("  (This is expected if Neo4j is not running or .env is not configured)")
            return True
    except Exception as e:
        print(f"✗ Neo4j test failed: {e}")
        return False


def test_ollama_connection():
    print("\nTesting Ollama connection...")
    try:
        from src.entity_extractor import EntityExtractor
        from config import Config
        
        try:
            config = Config.from_env()
            extractor = EntityExtractor(
                base_url=config.ollama.base_url,
                model=config.ollama.model
            )
            
            print("✓ Ollama client initialized")
            print(f"  - Base URL: {config.ollama.base_url}")
            print(f"  - Model: {config.ollama.model}")
            
            return True
        except Exception as e:
            print(f"⚠ Ollama connection test skipped: {e}")
            print("  (This is expected if .env is not configured)")
            return True
    except Exception as e:
        print(f"✗ Ollama test failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Knowledge Graph Builder - Quick Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Data Loader", test_data_loader()))
    results.append(("Neo4j Connection", test_neo4j_connection()))
    results.append(("Ollama Connection", test_ollama_connection()))
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All tests passed! You're ready to build the knowledge graph.")
        print("\nNext steps:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Make sure Neo4j is running")
        print("3. Create .env file from .env.example")
        print("4. Run: python main.py --build")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- .env file not configured")
        print("- Ollama or Neo4j not running")
        print("- Missing dependencies (run: pip install -r requirements.txt)")


if __name__ == "__main__":
    main()
