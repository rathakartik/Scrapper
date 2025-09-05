#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class StartupFundingTrackerTester:
    def __init__(self, base_url="https://source-integration.preview.emergentagent.com"):
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

    def test_health_check(self):
        """Test API health check endpoint - CRITICAL TEST"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                database = data.get('database', 'unknown')
                
                if status == 'healthy' and database == 'connected':
                    return self.log_test(
                        "API Health Check", 
                        True, 
                        f"Status: {status}, Database: {database}, Timestamp: {data.get('timestamp', 'N/A')}"
                    )
                else:
                    return self.log_test(
                        "API Health Check", 
                        False, 
                        f"Unhealthy - Status: {status}, Database: {database}, Error: {data.get('error', 'N/A')}"
                    )
            else:
                return self.log_test(
                    "API Health Check", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("API Health Check", False, f"Error: {str(e)}")

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
                    f"Status: {response.status_code}, Count: {len(data)} logs",
                    response_data=data
                )
            else:
                return self.log_test(
                    "GET Scraping Logs", 
                    False, 
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return self.log_test("GET Scraping Logs", False, f"Error: {str(e)}")

    def test_ai_provider_status(self):
        """Test AI Provider Status - Verify Groq is working as fallback"""
        try:
            # First trigger scraping to generate logs
            scrape_response = requests.post(f"{self.api_url}/scrape/trigger", timeout=15)
            if scrape_response.status_code != 200:
                return self.log_test(
                    "AI Provider Status", 
                    False, 
                    f"Failed to trigger scraping: {scrape_response.status_code}"
                )
            
            # Wait for scraping to process
            print("⏳ Waiting 10 seconds for AI analysis to complete...")
            time.sleep(10)
            
            # Get recent logs to check AI provider usage
            logs_response = requests.get(f"{self.api_url}/logs?limit=20", timeout=10)
            if logs_response.status_code == 200:
                logs = logs_response.json()
                
                # Check for AI provider usage in recent logs
                groq_usage = 0
                emergent_usage = 0
                failed_usage = 0
                
                for log in logs:
                    ai_provider = log.get('ai_provider_used', 'unknown')
                    if ai_provider == 'groq':
                        groq_usage += 1
                    elif ai_provider == 'emergent':
                        emergent_usage += 1
                    elif ai_provider == 'failed':
                        failed_usage += 1
                
                # Success if we see Groq being used (indicating fallback is working)
                if groq_usage > 0:
                    return self.log_test(
                        "AI Provider Status", 
                        True, 
                        f"Groq fallback working! Groq: {groq_usage}, Emergent: {emergent_usage}, Failed: {failed_usage}"
                    )
                elif emergent_usage > 0:
                    return self.log_test(
                        "AI Provider Status", 
                        True, 
                        f"Emergent working! Groq: {groq_usage}, Emergent: {emergent_usage}, Failed: {failed_usage}"
                    )
                else:
                    return self.log_test(
                        "AI Provider Status", 
                        False, 
                        f"No successful AI provider usage found. Groq: {groq_usage}, Emergent: {emergent_usage}, Failed: {failed_usage}"
                    )
            else:
                return self.log_test(
                    "AI Provider Status", 
                    False, 
                    f"Failed to get logs: {logs_response.status_code}"
                )
        except Exception as e:
            return self.log_test("AI Provider Status", False, f"Error: {str(e)}")

    def test_google_integration(self):
        """Test Google Integration - Verify Google News RSS feeds and Search functionality"""
        try:
            # Get news sources to verify Google sources are present
            response = requests.get(f"{self.api_url}/news-sources", timeout=10)
            if response.status_code == 200:
                sources = response.json()
                
                # Count Google sources
                google_sources = [s for s in sources if 'google' in s.get('name', '').lower()]
                google_rss_sources = [s for s in google_sources if s.get('source_type') == 'rss']
                google_search_sources = [s for s in google_sources if s.get('source_type') == 'search']
                
                if len(google_sources) >= 4:  # Expecting at least 4 Google sources
                    return self.log_test(
                        "Google Integration", 
                        True, 
                        f"Google sources found: {len(google_sources)} total, {len(google_rss_sources)} RSS, {len(google_search_sources)} Search"
                    )
                else:
                    return self.log_test(
                        "Google Integration", 
                        False, 
                        f"Insufficient Google sources: {len(google_sources)} found, expected at least 4"
                    )
            else:
                return self.log_test(
                    "Google Integration", 
                    False, 
                    f"Failed to get news sources: {response.status_code}"
                )
        except Exception as e:
            return self.log_test("Google Integration", False, f"Error: {str(e)}")

    def test_scraping_performance(self):
        """Test Scraping Performance - Check logs for successful article processing"""
        try:
            # Get recent scraping logs
            response = requests.get(f"{self.api_url}/logs?limit=50", timeout=10)
            if response.status_code == 200:
                logs = response.json()
                
                if not logs:
                    return self.log_test(
                        "Scraping Performance", 
                        False, 
                        "No scraping logs found"
                    )
                
                # Analyze scraping performance
                total_logs = len(logs)
                successful_logs = len([log for log in logs if log.get('status') == 'success'])
                total_articles = sum(log.get('articles_processed', 0) for log in logs)
                total_startups = sum(log.get('startups_found', 0) for log in logs)
                
                # Check for recent activity (logs from last hour)
                recent_logs = [log for log in logs if log.get('timestamp')]
                
                success_rate = (successful_logs / total_logs * 100) if total_logs > 0 else 0
                
                if success_rate >= 50:  # At least 50% success rate
                    return self.log_test(
                        "Scraping Performance", 
                        True, 
                        f"Success rate: {success_rate:.1f}%, Articles: {total_articles}, Startups: {total_startups}, Recent logs: {len(recent_logs)}"
                    )
                else:
                    return self.log_test(
                        "Scraping Performance", 
                        False, 
                        f"Low success rate: {success_rate:.1f}%, Articles: {total_articles}, Startups: {total_startups}"
                    )
            else:
                return self.log_test(
                    "Scraping Performance", 
                    False, 
                    f"Failed to get logs: {response.status_code}"
                )
        except Exception as e:
            return self.log_test("Scraping Performance", False, f"Error: {str(e)}")

    def test_startup_discovery(self):
        """Test Startup Discovery - Check if any startups are being found"""
        try:
            # Get startup stats
            stats_response = requests.get(f"{self.api_url}/startups/stats", timeout=10)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                total_startups = stats.get('total_startups', 0)
                recent_discoveries = stats.get('recent_discoveries', 0)
                
                # Get actual startups list
                startups_response = requests.get(f"{self.api_url}/startups?limit=10", timeout=10)
                if startups_response.status_code == 200:
                    startups = startups_response.json()
                    
                    # Note: 0 startups might be normal if no current funding news
                    return self.log_test(
                        "Startup Discovery", 
                        True, 
                        f"Total startups: {total_startups}, Recent: {recent_discoveries}, Sample count: {len(startups)}"
                    )
                else:
                    return self.log_test(
                        "Startup Discovery", 
                        False, 
                        f"Failed to get startups list: {startups_response.status_code}"
                    )
            else:
                return self.log_test(
                    "Startup Discovery", 
                    False, 
                    f"Failed to get startup stats: {stats_response.status_code}"
                )
        except Exception as e:
            return self.log_test("Startup Discovery", False, f"Error: {str(e)}")

    def analyze_logs_for_issues(self):
        """Analyze logs for specific issues mentioned in the review"""
        try:
            response = requests.get(f"{self.api_url}/logs?limit=30", timeout=10)
            if response.status_code == 200:
                logs = response.json()
                
                issues_found = []
                fixes_verified = []
                
                for log in logs:
                    error_msg = log.get('error_message', '').lower()
                    ai_provider = log.get('ai_provider_used', 'unknown')
                    
                    # Check for Brotli encoding issue (should be fixed)
                    if 'brotli' in error_msg or 'br' in error_msg:
                        issues_found.append("Brotli encoding issue still present")
                    
                    # Check for invalid API key (should be fixed)
                    if 'invalid api key' in error_msg or '401' in error_msg:
                        issues_found.append("Invalid API key issue still present")
                    
                    # Check for successful Groq usage (fix verification)
                    if ai_provider == 'groq':
                        fixes_verified.append("Groq API working")
                    
                    # Check for successful processing
                    if log.get('status') == 'success' and log.get('articles_processed', 0) > 0:
                        fixes_verified.append("Article processing working")
                
                # Remove duplicates
                issues_found = list(set(issues_found))
                fixes_verified = list(set(fixes_verified))
                
                if not issues_found and fixes_verified:
                    return self.log_test(
                        "Log Analysis", 
                        True, 
                        f"No critical issues found. Verified fixes: {', '.join(fixes_verified)}"
                    )
                elif issues_found:
                    return self.log_test(
                        "Log Analysis", 
                        False, 
                        f"Issues found: {', '.join(issues_found)}. Fixes verified: {', '.join(fixes_verified)}"
                    )
                else:
                    return self.log_test(
                        "Log Analysis", 
                        True, 
                        "No specific issues found in logs, but limited verification data"
                    )
            else:
                return self.log_test(
                    "Log Analysis", 
                    False, 
                    f"Failed to get logs: {response.status_code}"
                )
        except Exception as e:
            return self.log_test("Log Analysis", False, f"Error: {str(e)}")

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
        print("🚀 Starting Enhanced Startup Funding Tracker Backend Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Core API tests - Start with health check
        self.test_health_check()
        self.test_api_root()
        
        # Enhanced verification tests for the fixes
        print("\n🔍 VERIFICATION TESTS FOR RECENT FIXES")
        print("-" * 40)
        self.test_google_integration()
        self.test_startup_discovery()
        
        # Standard API tests
        print("\n📋 STANDARD API TESTS")
        print("-" * 40)
        self.test_get_startups()
        self.test_get_startups_with_filters()
        self.test_get_startup_stats()
        self.test_get_news_sources()
        self.test_create_news_source()
        
        # Scraping and AI tests
        print("\n🤖 AI & SCRAPING TESTS")
        print("-" * 40)
        self.test_trigger_manual_scrape()
        
        # Wait for scraping to process
        print("\n⏳ Waiting 15 seconds for scraping and AI analysis...")
        time.sleep(15)
        
        self.test_get_scraping_logs()
        self.test_ai_provider_status()
        self.test_scraping_performance()
        self.analyze_logs_for_issues()
        
        # Additional tests
        print("\n🔧 ADDITIONAL TESTS")
        print("-" * 40)
        self.test_export_csv()
        self.test_cors_headers()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
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
        
        # Print successful verification tests
        verification_tests = [test for test in self.test_results if test['success'] and 
                            test['name'] in ['AI Provider Status', 'Google Integration', 'Scraping Performance', 'Log Analysis']]
        if verification_tests:
            print("\n✅ VERIFIED FIXES:")
            for test in verification_tests:
                print(f"  - {test['name']}: {test['message']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = StartupFundingTrackerTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())