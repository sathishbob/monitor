#!/usr/bin/env python3
"""
Test script to verify the monitoring agent installation and dependencies.
"""

import sys
import platform
import importlib

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing module imports...")
    
    required_modules = [
        'elasticsearch',
        'psutil',
        'flask',
        'pandas',
        'numpy',
        'sklearn',
        'statsmodels',
        'argparse',
        'logging',
        'datetime',
        'json',
        'threading',
        'time',
        'subprocess',
        'platform',
        'os',
        're',
        'collections'
    ]
    
    platform_specific_modules = []
    if platform.system() == "Windows":
        platform_specific_modules = ['win32gui', 'win32process', 'win32api', 'win32con', 'win32clipboard']
    elif platform.system() == "Linux":
        platform_specific_modules = ['Xlib', 'pynput', 'pyperclip']
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    print("\nPlatform-specific modules:")
    for module in platform_specific_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e} (optional)")
    
    return len(failed_imports) == 0

def test_basic_functionality():
    """Test basic functionality of the monitoring agent."""
    print("\nTesting basic functionality...")
    
    try:
        # Test if we can import the main module
        from monitor_agent import MonitorAgent, PerformanceMonitor, UserActivityMonitor, CommandMonitor, AIModel, ElasticsearchManager
        
        print("✓ Successfully imported monitoring agent classes")
        
        # Test performance monitor
        pm = PerformanceMonitor()
        metrics = pm.get_system_metrics()
        if metrics:
            print("✓ Performance monitoring working")
        else:
            print("✗ Performance monitoring failed")
        
        # Test user activity monitor
        uam = UserActivityMonitor()
        window = uam.get_active_window()
        print(f"✓ User activity monitoring working (active window: {window['window_title']})")
        
        # Test command monitor
        cm = CommandMonitor()
        print("✓ Command monitoring initialized")
        
        # Test AI model
        ai = AIModel()
        print("✓ AI model initialized")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_elasticsearch_connection():
    """Test Elasticsearch connection."""
    print("\nTesting Elasticsearch connection...")
    
    try:
        from elasticsearch import Elasticsearch
        
        # Try to connect to default Elasticsearch
        es = Elasticsearch(['http://localhost:9200'])
        
        if es.ping():
            print("✓ Elasticsearch connection successful")
            return True
        else:
            print("✗ Elasticsearch connection failed (server may not be running)")
            return False
            
    except Exception as e:
        print(f"✗ Elasticsearch connection test failed: {e}")
        return False

def test_platform_specific():
    """Test platform-specific functionality."""
    print(f"\nTesting platform-specific functionality ({platform.system()})...")
    
    if platform.system() == "Windows":
        try:
            import win32gui
            print("✓ Windows GUI support available")
        except ImportError:
            print("✗ Windows GUI support not available")
        
    elif platform.system() == "Linux":
        try:
            from Xlib import display
            print("✓ Linux X11 support available")
        except ImportError:
            print("✗ Linux X11 support not available")
        
        try:
            import pynput
            print("✓ Linux input monitoring support available")
        except ImportError:
            print("✗ Linux input monitoring support not available")

def main():
    """Main test function."""
    print("Lab Server Monitoring AI Agent - Installation Test")
    print("=" * 50)
    
    # Test Python version
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    # Run tests
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    es_ok = test_elasticsearch_connection()
    test_platform_specific()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Module imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Basic functionality: {'✓ PASS' if functionality_ok else '✗ FAIL'}")
    print(f"Elasticsearch connection: {'✓ PASS' if es_ok else '✗ FAIL (optional)'}")
    
    if imports_ok and functionality_ok:
        print("\n🎉 Installation test PASSED!")
        print("The monitoring agent should be ready to use.")
        if not es_ok:
            print("Note: Elasticsearch is not running. Start Elasticsearch to enable data storage.")
    else:
        print("\n❌ Installation test FAILED!")
        print("Please check the failed components above and install missing dependencies.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
