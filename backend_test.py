#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class StartupFundingTrackerTester:
    def __init__(self, base_url="https://hungry-rhodes-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, message="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "name": name,
            "success": success,
            "message": message,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status} - {name}: {message}")
        return success

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "API Root", 
                    True, 
                    f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
                )
            else:
                return self.log_test(
                    "API Root", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("API Root", False, f"Error: {str(e)}")

    def test_get_startups(self):
        """Test GET /api/startups endpoint"""
        try:
            response = requests.get(f"{self.api_url}/startups", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "GET Startups", 
                    True, 
                    f"Status: {response.status_code}, Count: {len(data)} startups"
                )
            else:
                return self.log_test(
                    "GET Startups", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("GET Startups", False, f"Error: {str(e)}")

    def test_get_startups_with_filters(self):
        """Test GET /api/startups with filters"""
        try:
            params = {
                'industry': 'fintech',
                'location': 'bangalore',
                'funding_stage': 'seed'
            }
            response = requests.get(f"{self.api_url}/startups", params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "GET Startups with Filters", 
                    True, 
                    f"Status: {response.status_code}, Filtered count: {len(data)}"
                )
            else:
                return self.log_test(
                    "GET Startups with Filters", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("GET Startups with Filters", False, f"Error: {str(e)}")

    def test_get_startup_stats(self):
        """Test GET /api/startups/stats endpoint"""
        try:
            response = requests.get(f"{self.api_url}/startups/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                required_keys = ['total_startups', 'recent_discoveries', 'funding_stages', 'top_industries']
                missing_keys = [key for key in required_keys if key not in data]
                
                if not missing_keys:
                    return self.log_test(
                        "GET Startup Stats", 
                        True, 
                        f"Status: {response.status_code}, Total: {data.get('total_startups', 0)}, Recent: {data.get('recent_discoveries', 0)}"
                    )
                else:
                    return self.log_test(
                        "GET Startup Stats", 
                        False, 
                        f"Missing keys: {missing_keys}"
                    )
            else:
                return self.log_test(
                    "GET Startup Stats", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("GET Startup Stats", False, f"Error: {str(e)}")

    def test_get_news_sources(self):
        """Test GET /api/news-sources endpoint"""
        try:
            response = requests.get(f"{self.api_url}/news-sources", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "GET News Sources", 
                    True, 
                    f"Status: {response.status_code}, Count: {len(data)} sources"
                )
            else:
                return self.log_test(
                    "GET News Sources", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("GET News Sources", False, f"Error: {str(e)}")

    def test_create_news_source(self):
        """Test POST /api/news-sources endpoint"""
        try:
            test_source = {
                "name": f"Test Source {datetime.now().strftime('%H%M%S')}",
                "url": "https://example.com/test",
                "rss_feed": "https://example.com/test/feed.xml",
                "css_selectors": {
                    "title": "h1",
                    "content": ".content"
                }
            }
            
            response = requests.post(
                f"{self.api_url}/news-sources", 
                json=test_source, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Store the created source ID for potential cleanup
                self.test_source_id = data.get('id')
                return self.log_test(
                    "POST News Source", 
                    True, 
                    f"Status: {response.status_code}, Created source: {data.get('name')}"
                )
            else:
                return self.log_test(
                    "POST News Source", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("POST News Source", False, f"Error: {str(e)}")

    def test_trigger_manual_scrape(self):
        """Test POST /api/scrape/trigger endpoint"""
        try:
            response = requests.post(f"{self.api_url}/scrape/trigger", timeout=15)
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "POST Trigger Scrape", 
                    True, 
                    f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
                )
            else:
                return self.log_test(
                    "POST Trigger Scrape", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("POST Trigger Scrape", False, f"Error: {str(e)}")

    def test_get_scraping_logs(self):
        """Test GET /api/logs endpoint"""
        try:
            response = requests.get(f"{self.api_url}/logs", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "GET Scraping Logs", 
                    True, 
                    f"Status: {response.status_code}, Count: {len(data)} logs"
                )
            else:
                return self.log_test(
                    "GET Scraping Logs", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("GET Scraping Logs", False, f"Error: {str(e)}")

    def test_export_csv(self):
        """Test GET /api/export/csv endpoint"""
        try:
            response = requests.get(f"{self.api_url}/export/csv", timeout=15)
            if response.status_code == 200:
                # Check if response is CSV format
                content_type = response.headers.get('content-type', '')
                if 'csv' in content_type.lower() or len(response.content) > 0:
                    return self.log_test(
                        "GET Export CSV", 
                        True, 
                        f"Status: {response.status_code}, Content-Type: {content_type}, Size: {len(response.content)} bytes"
                    )
                else:
                    return self.log_test(
                        "GET Export CSV", 
                        False, 
                        f"Invalid CSV response, Content-Type: {content_type}"
                    )
            else:
                return self.log_test(
                    "GET Export CSV", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("GET Export CSV", False, f"Error: {str(e)}")

    def test_cors_headers(self):
        """Test CORS configuration"""
        try:
            response = requests.options(f"{self.api_url}/startups", timeout=10)
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if any(cors_headers.values()):
                return self.log_test(
                    "CORS Configuration", 
                    True, 
                    f"CORS headers present: {cors_headers}"
                )
            else:
                return self.log_test(
                    "CORS Configuration", 
                    False, 
                    "No CORS headers found"
                )
        except Exception as e:
            return self.log_test("CORS Configuration", False, f"Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data if created"""
        if hasattr(self, 'test_source_id') and self.test_source_id:
            try:
                response = requests.delete(f"{self.api_url}/news-sources/{self.test_source_id}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ Cleaned up test source: {self.test_source_id}")
                else:
                    print(f"⚠️  Failed to cleanup test source: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Error during cleanup: {str(e)}")

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Startup Funding Tracker Backend API Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Core API tests
        self.test_api_root()
        self.test_get_startups()
        self.test_get_startups_with_filters()
        self.test_get_startup_stats()
        self.test_get_news_sources()
        self.test_create_news_source()
        self.test_trigger_manual_scrape()
        
        # Wait a bit for scraping to potentially start
        print("\n⏳ Waiting 5 seconds for scraping to process...")
        time.sleep(5)
        
        self.test_get_scraping_logs()
        self.test_export_csv()
        self.test_cors_headers()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['message']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = StartupFundingTrackerTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())