# web_scraper.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import requests
from bs4 import BeautifulSoup
import re

class WebScraperInput(BaseModel):
    """Input schema for WebScraper tool."""
    url: str = Field(..., description="The URL of the webpage to scrape.")

class WebScraperTool(BaseTool):
    name: str = "Web Scraper"
    description: str = "Scrapes the content from a given URL to extract relevant information."
    args_schema: Type[BaseModel] = WebScraperInput
    
    def _run(self, url: str) -> str:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
                
            # Get text
            text = soup.get_text(separator='\n')
            
            # Remove excessive whitespace
            text = re.sub(r'\n+', '\n', text)
            text = re.sub(r' +', ' ', text)
            
            # Truncate if too long (to avoid token limits)
            if len(text) > 15000:
                text = text[:15000] + "...[content truncated due to length]"
                
            return text
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"