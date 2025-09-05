from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import asyncio
import aiohttp
import csv
import io
from bs4 import BeautifulSoup
import re
import json
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM Chat
llm_chat = LlmChat(
    api_key=os.environ.get('EMERGENT_LLM_KEY'),
    session_id="funding_tracker",
    system_message="""You are an expert at analyzing news articles and identifying startup funding announcements. 
    Your task is to extract structured information about Indian startups that have received funding.
    
    Return only valid JSON with the following structure:
    {
        "is_funding_news": true/false,
        "companies": [
            {
                "name": "Company Name",
                "funding_amount": "Amount raised",
                "funding_stage": "Seed/Series A/Series B/etc",
                "investors": ["Investor 1", "Investor 2"],
                "industry": "Industry sector",
                "location": "City, State"
            }
        ]
    }
    
    Only extract companies that are clearly based in India and have received funding."""
).with_model("gemini", "gemini-2.5-pro")

# Models
class NewsSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    rss_feed: Optional[str] = None
    css_selectors: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NewsSourceCreate(BaseModel):
    name: str
    url: str
    rss_feed: Optional[str] = None
    css_selectors: Dict[str, str] = Field(default_factory=dict)

class Startup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    funding_amount: Optional[str] = None
    funding_stage: Optional[str] = None
    investors: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin_profile: Optional[str] = None
    facebook_profile: Optional[str] = None
    founders: List[Dict[str, Any]] = Field(default_factory=list)
    directors: List[Dict[str, Any]] = Field(default_factory=list)
    source_url: Optional[str] = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verification_status: str = "pending"  # pending, verified, rejected

class ScrapingLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    status: str  # success, error, no_funding_found
    articles_processed: int = 0
    startups_found: int = 0
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Default news sources
DEFAULT_SOURCES = [
    {
        "name": "Economic Times Startups",
        "url": "https://economictimes.indiatimes.com/small-biz/startups",
        "rss_feed": "https://economictimes.indiatimes.com/small-biz/startups/rssfeeds/13352306.cms",
        "css_selectors": {
            "title": "h1",
            "content": ".artText",
            "date": ".publish_on"
        }
    },
    {
        "name": "Inc42",
        "url": "https://inc42.com/buzz/",
        "rss_feed": "https://inc42.com/feed/",
        "css_selectors": {
            "title": "h1",
            "content": ".content-wrapper",
            "date": ".date"
        }
    },
    {
        "name": "YourStory",
        "url": "https://yourstory.com/funding",
        "css_selectors": {
            "title": "h1",
            "content": ".story-content",
            "date": ".date"
        }
    }
]

# Web scraping functions
async def scrape_article_content(session: aiohttp.ClientSession, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    """Scrape content from a single article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                article_data = {
                    'url': url,
                    'title': '',
                    'content': '',
                    'date': ''
                }
                
                # Extract title
                if 'title' in selectors:
                    title_elem = soup.select_one(selectors['title'])
                    if title_elem:
                        article_data['title'] = title_elem.get_text(strip=True)
                
                # Extract content
                if 'content' in selectors:
                    content_elem = soup.select_one(selectors['content'])
                    if content_elem:
                        article_data['content'] = content_elem.get_text(strip=True)
                
                # Extract date
                if 'date' in selectors:
                    date_elem = soup.select_one(selectors['date'])
                    if date_elem:
                        article_data['date'] = date_elem.get_text(strip=True)
                
                return article_data
                
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return None

async def analyze_with_ai(content: str, title: str) -> Dict[str, Any]:
    """Analyze article content with AI to extract funding information"""
    try:
        prompt = f"""
        Analyze this Indian news article for startup funding announcements:
        
        Title: {title}
        Content: {content[:3000]}  # Limit content to avoid token limits
        
        Extract information about Indian startups that received funding. Return only valid JSON.
        """
        
        user_message = UserMessage(text=prompt)
        response = await llm_chat.send_message(user_message)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from response if it's wrapped in text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"is_funding_news": False, "companies": []}
            
    except Exception as e:
        logger.error(f"Error in AI analysis: {str(e)}")
        return {"is_funding_news": False, "companies": []}

async def enrich_startup_data(company_name: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Enrich startup data by searching for website and social profiles"""
    enriched_data = {
        "website": None,
        "linkedin_profile": None,
        "facebook_profile": None,
        "founders": [],
        "directors": []
    }
    
    try:
        # Simple Google search simulation for company website
        search_query = f"{company_name} startup India website"
        # This would normally use a search API, for now we'll return placeholder
        # In production, you'd integrate with Google Custom Search API or similar
        
        # Placeholder for website detection logic
        # You would implement actual web search and domain extraction here
        
    except Exception as e:
        logger.error(f"Error enriching data for {company_name}: {str(e)}")
    
    return enriched_data

async def scrape_news_source(source: NewsSource) -> ScrapingLog:
    """Scrape a single news source for funding announcements"""
    log = ScrapingLog(source_id=source.id, status="running")
    
    try:
        async with aiohttp.ClientSession() as session:
            # If RSS feed is available, use it
            if source.rss_feed:
                await scrape_rss_feed(session, source, log)
            else:
                await scrape_website_directly(session, source, log)
                
        log.status = "success"
        
    except Exception as e:
        log.status = "error"
        log.error_message = str(e)
        logger.error(f"Error scraping {source.name}: {str(e)}")
    
    # Save log to database
    await db.scraping_logs.insert_one(log.dict())
    return log

async def scrape_rss_feed(session: aiohttp.ClientSession, source: NewsSource, log: ScrapingLog):
    """Scrape RSS feed for articles"""
    try:
        async with session.get(source.rss_feed) as response:
            if response.status == 200:
                rss_content = await response.text()
                soup = BeautifulSoup(rss_content, 'xml')
                
                items = soup.find_all('item')[:10]  # Limit to recent 10 articles
                log.articles_processed = len(items)
                
                for item in items:
                    title = item.find('title').text if item.find('title') else ""
                    link = item.find('link').text if item.find('link') else ""
                    description = item.find('description').text if item.find('description') else ""
                    
                    if link:
                        # Scrape full article content
                        article_data = await scrape_article_content(session, link, source.css_selectors)
                        if article_data:
                            # Analyze with AI
                            analysis = await analyze_with_ai(article_data['content'], article_data['title'])
                            
                            if analysis.get('is_funding_news') and analysis.get('companies'):
                                await process_found_companies(analysis['companies'], link)
                                log.startups_found += len(analysis['companies'])
                                
    except Exception as e:
        raise Exception(f"RSS scraping error: {str(e)}")

async def scrape_website_directly(session: aiohttp.ClientSession, source: NewsSource, log: ScrapingLog):
    """Scrape website directly for articles"""
    try:
        async with session.get(source.url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find article links (this would need to be customized per site)
                article_links = soup.find_all('a', href=True)[:20]  # Limit to 20 links
                
                processed = 0
                for link in article_links:
                    href = link.get('href')
                    if href and ('startup' in href.lower() or 'funding' in href.lower()):
                        if not href.startswith('http'):
                            href = source.url.rstrip('/') + '/' + href.lstrip('/')
                        
                        article_data = await scrape_article_content(session, href, source.css_selectors)
                        if article_data and article_data['content']:
                            analysis = await analyze_with_ai(article_data['content'], article_data['title'])
                            
                            if analysis.get('is_funding_news') and analysis.get('companies'):
                                await process_found_companies(analysis['companies'], href)
                                log.startups_found += len(analysis['companies'])
                        
                        processed += 1
                        if processed >= 10:  # Limit processing
                            break
                
                log.articles_processed = processed
                
    except Exception as e:
        raise Exception(f"Website scraping error: {str(e)}")

async def process_found_companies(companies: List[Dict], source_url: str):
    """Process and save found companies to database"""
    for company_data in companies:
        # Check if company already exists
        existing = await db.startups.find_one({"name": company_data.get('name')})
        
        if not existing:
            # Enrich company data
            async with aiohttp.ClientSession() as session:
                enriched = await enrich_startup_data(company_data.get('name', ''), session)
            
            startup = Startup(
                name=company_data.get('name', ''),
                funding_amount=company_data.get('funding_amount'),
                funding_stage=company_data.get('funding_stage'),
                investors=company_data.get('investors', []),
                industry=company_data.get('industry'),
                location=company_data.get('location'),
                website=enriched.get('website'),
                linkedin_profile=enriched.get('linkedin_profile'),
                facebook_profile=enriched.get('facebook_profile'),
                founders=enriched.get('founders', []),
                directors=enriched.get('directors', []),
                source_url=source_url
            )
            
            await db.startups.insert_one(startup.dict())

# Background task for periodic scraping
async def periodic_scraping():
    """Run periodic scraping every 5 minutes"""
    while True:
        try:
            logger.info("Starting periodic scraping...")
            
            # Get all active news sources
            sources_cursor = db.news_sources.find({"is_active": True})
            sources = await sources_cursor.to_list(length=None)
            
            for source_data in sources:
                source = NewsSource(**source_data)
                await scrape_news_source(source)
                
            logger.info("Periodic scraping completed")
            
        except Exception as e:
            logger.error(f"Error in periodic scraping: {str(e)}")
        
        # Wait 5 minutes
        await asyncio.sleep(300)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Startup Funding Tracker API"}

# News Sources Management
@api_router.post("/news-sources", response_model=NewsSource)
async def create_news_source(source: NewsSourceCreate):
    news_source = NewsSource(**source.dict())
    await db.news_sources.insert_one(news_source.dict())
    return news_source

@api_router.get("/news-sources", response_model=List[NewsSource])
async def get_news_sources():
    sources = await db.news_sources.find().to_list(length=None)
    return [NewsSource(**source) for source in sources]

@api_router.put("/news-sources/{source_id}")
async def update_news_source(source_id: str, source_data: NewsSourceCreate):
    update_data = source_data.dict()
    update_data["last_updated"] = datetime.now(timezone.utc)
    
    result = await db.news_sources.update_one(
        {"id": source_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="News source not found")
    
    return {"message": "News source updated successfully"}

@api_router.delete("/news-sources/{source_id}")
async def delete_news_source(source_id: str):
    result = await db.news_sources.delete_one({"id": source_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News source not found")
    
    return {"message": "News source deleted successfully"}

# Startups Management
@api_router.get("/startups", response_model=List[Startup])
async def get_startups(
    skip: int = 0, 
    limit: int = 100,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    funding_stage: Optional[str] = None
):
    filter_query = {}
    
    if industry:
        filter_query["industry"] = {"$regex": industry, "$options": "i"}
    if location:
        filter_query["location"] = {"$regex": location, "$options": "i"}
    if funding_stage:
        filter_query["funding_stage"] = {"$regex": funding_stage, "$options": "i"}
    
    startups = await db.startups.find(filter_query).skip(skip).limit(limit).sort("discovered_at", -1).to_list(length=None)
    return [Startup(**startup) for startup in startups]

@api_router.get("/startups/stats")
async def get_startup_stats():
    total_startups = await db.startups.count_documents({})
    
    # Get funding stages distribution
    stages_pipeline = [
        {"$group": {"_id": "$funding_stage", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    stages = await db.startups.aggregate(stages_pipeline).to_list(length=None)
    
    # Get industries distribution
    industries_pipeline = [
        {"$group": {"_id": "$industry", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    industries = await db.startups.aggregate(industries_pipeline).to_list(length=None)
    
    # Get recent discoveries (last 24 hours)
    from datetime import timedelta
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent_count = await db.startups.count_documents({"discovered_at": {"$gte": yesterday}})
    
    return {
        "total_startups": total_startups,
        "recent_discoveries": recent_count,
        "funding_stages": stages,
        "top_industries": industries
    }

# Manual scraping trigger
@api_router.post("/scrape/trigger")
async def trigger_manual_scrape(background_tasks: BackgroundTasks):
    """Manually trigger scraping of all sources"""
    async def run_scraping():
        sources_cursor = db.news_sources.find({"is_active": True})
        sources = await sources_cursor.to_list(length=None)
        
        for source_data in sources:
            source = NewsSource(**source_data)
            await scrape_news_source(source)
    
    background_tasks.add_task(run_scraping)
    return {"message": "Manual scraping triggered"}

# CSV Export
@api_router.get("/export/csv")
async def export_startups_csv():
    """Export all startups to CSV"""
    startups = await db.startups.find().sort("discovered_at", -1).to_list(length=None)
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Name', 'Funding Amount', 'Funding Stage', 'Investors', 'Industry', 
        'Location', 'Website', 'LinkedIn', 'Facebook', 'Founders', 'Directors',
        'Source URL', 'Discovered At'
    ])
    
    # Write data
    for startup in startups:
        startup_obj = Startup(**startup)
        writer.writerow([
            startup_obj.name,
            startup_obj.funding_amount or '',
            startup_obj.funding_stage or '',
            ', '.join(startup_obj.investors),
            startup_obj.industry or '',
            startup_obj.location or '',
            startup_obj.website or '',
            startup_obj.linkedin_profile or '',
            startup_obj.facebook_profile or '',
            json.dumps(startup_obj.founders),
            json.dumps(startup_obj.directors),
            startup_obj.source_url or '',
            startup_obj.discovered_at.isoformat()
        ])
    
    # Save to file
    csv_path = "/tmp/startups_export.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        f.write(output.getvalue())
    
    return FileResponse(csv_path, filename="startups_funding_data.csv", media_type="text/csv")

# Scraping logs
@api_router.get("/logs", response_model=List[ScrapingLog])
async def get_scraping_logs(limit: int = 50):
    logs = await db.scraping_logs.find().sort("timestamp", -1).limit(limit).to_list(length=None)
    return [ScrapingLog(**log) for log in logs]

# Initialize default sources on startup
@app.on_event("startup")
async def startup_event():
    # Initialize default news sources
    for source_data in DEFAULT_SOURCES:
        existing = await db.news_sources.find_one({"name": source_data["name"]})
        if not existing:
            source = NewsSource(**source_data)
            await db.news_sources.insert_one(source.dict())
    
    # Start periodic scraping in background
    asyncio.create_task(periodic_scraping())
    logger.info("Startup funding tracker initialized")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()