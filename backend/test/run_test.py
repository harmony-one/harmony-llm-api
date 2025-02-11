import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from api_tester import APITester
from deep_seek_tester import DeepSeekTester

def main():
    # tester = APITester()
    # tester.run_api_tests()
    
    deep_seek_tester = DeepSeekTester()
    deep_seek_tester.test_deepseek_api()
if __name__ == "__main__":
    main()