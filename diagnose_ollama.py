#!/usr/bin/env python3
"""
Ollama Diagnostic Script for Devika AI
This script helps diagnose and fix common Ollama issues
"""

import sys
import os
import requests
import subprocess
import time
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config import Config
    from src.logger import Logger
    from src.llm.ollama_client import Ollama
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the Devika project root directory")
    sys.exit(1)

class OllamaDiagnostic:
    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        self.endpoint = self.config.get_ollama_api_endpoint()
        
    def check_ollama_installation(self) -> bool:
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"[OK] Ollama installed: {result.stdout.strip()}")
                return True
            else:
                print("[ERROR] Ollama command failed")
                return False
        except FileNotFoundError:
            print("[ERROR] Ollama not found in PATH")
            print("   Install Ollama from: https://ollama.ai/download")
            return False
        except subprocess.TimeoutExpired:
            print("[ERROR] Ollama command timeout")
            return False
        except Exception as e:
            print(f"[ERROR] Error checking Ollama installation: {e}")
            return False
    
    def check_ollama_server(self) -> bool:
        """Check if Ollama server is running"""
        try:
            print(f"[INFO] Testing connection to: {self.endpoint}")
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            
            if response.status_code == 200:
                print("[OK] Ollama server is running and accessible")
                return True
            else:
                print(f"[ERROR] Ollama server returned status: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Cannot connect to Ollama server at {self.endpoint}")
            print("   Start server with: ollama serve")
            return False
        except requests.exceptions.Timeout:
            print("[ERROR] Connection timeout to Ollama server")
            return False
        except Exception as e:
            print(f"[ERROR] Error connecting to Ollama server: {e}")
            return False
    
    def list_available_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [model.get('name', 'unknown') for model in models]
                
                if model_names:
                    print(f"[OK] Available models ({len(model_names)}):")
                    for i, model in enumerate(model_names, 1):
                        print(f"   {i}. {model}")
                else:
                    print("[WARNING] No models found")
                    print("   Pull a model with: ollama pull llama2")
                
                return model_names
            else:
                print(f"[ERROR] Failed to list models: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] Error listing models: {e}")
            return []
    
    def test_model_inference(self, model_name: str = None) -> bool:
        """Test inference with a specific model"""
        try:
            models = self.list_available_models()
            
            if not models:
                print("[ERROR] No models available for testing")
                return False
            
            # Use provided model or first available
            test_model = model_name if model_name and model_name in models else models[0]
            
            print(f"[TEST] Testing inference with model: {test_model}")
            
            # Create Ollama client and test
            ollama_client = Ollama()
            
            if not ollama_client.is_available:
                print("[ERROR] Ollama client not available")
                return False
            
            test_prompt = "Hello, please respond with 'Hello from Ollama!'"
            
            print("   Sending test prompt...")
            start_time = time.time()
            
            response = ollama_client.inference(test_model, test_prompt)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response and response.strip():
                print(f"[OK] Inference successful! ({duration:.2f}s)")
                print(f"   Response: {response[:100]}...")
                return True
            else:
                print("[ERROR] Empty response from model")
                return False
                
        except Exception as e:
            print(f"[ERROR] Inference test failed: {e}")
            return False
    
    def suggest_fixes(self):
        """Suggest fixes for common issues"""
        print("\n[FIXES] Common fixes:")
        print("1. Install Ollama: https://ollama.ai/download")
        print("2. Start server: ollama serve")
        print("3. Pull a model: ollama pull llama2")
        print("4. Check firewall/antivirus blocking port 11434")
        print("5. Verify endpoint in config.toml: OLLAMA = \"http://127.0.0.1:11434\"")
        print("6. Try different model: ollama pull mistral")
    
    def run_full_diagnostic(self):
        """Run complete diagnostic"""
        print("[DIAGNOSTIC] Ollama Diagnostic for Devika AI")
        print("=" * 50)
        
        # Check installation
        print("\n1. Checking Ollama installation...")
        installation_ok = self.check_ollama_installation()
        
        if not installation_ok:
            print("\n[ERROR] Ollama not properly installed")
            self.suggest_fixes()
            return False
        
        # Check server
        print("\n2. Checking Ollama server...")
        server_ok = self.check_ollama_server()
        
        if not server_ok:
            print("\n[ERROR] Ollama server not running")
            self.suggest_fixes()
            return False
        
        # List models
        print("\n3. Checking available models...")
        models = self.list_available_models()
        
        if not models:
            print("\n[WARNING] No models available")
            print("   Download a model with: ollama pull llama2")
            return False
        
        # Test inference
        print("\n4. Testing model inference...")
        inference_ok = self.test_model_inference()
        
        if inference_ok:
            print("\n[SUCCESS] All checks passed! Ollama is working correctly.")
            return True
        else:
            print("\n[ERROR] Inference test failed")
            self.suggest_fixes()
            return False

def main():
    """Main diagnostic function"""
    diagnostic = OllamaDiagnostic()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            model_name = sys.argv[2] if len(sys.argv) > 2 else None
            diagnostic.test_model_inference(model_name)
        elif command == "models":
            diagnostic.list_available_models()
        elif command == "server":
            diagnostic.check_ollama_server()
        elif command == "install":
            diagnostic.check_ollama_installation()
        else:
            print("Usage: python diagnose_ollama.py [test|models|server|install]")
    else:
        # Run full diagnostic
        diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main()
