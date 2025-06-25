import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional, List
import datetime
import pytz
import json
from datetime import timedelta
import random
import re
import io
import base64
from babel.numbers import format_currency
import qrcode
from PIL import Image
import feedparser
import pyjokes
import yfinance as yf
from bs4 import BeautifulSoup
import pycountry
import openai
import glob
import fnmatch

@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str) -> str:
    """
    Get the current weather for a given city.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str) -> str:
    """
    Search the web using DuckDuckGo.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."    

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email through Gmail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"

# Tools for everyday life tasks

@function_tool()
async def get_time(
    context: RunContext,  # type: ignore
    timezone: str = "UTC"
) -> str:
    """
    Get the current time in a specific timezone.
    
    Args:
        timezone: Timezone name (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")
    """
    try:
        if timezone not in pytz.all_timezones:
            closest = [tz for tz in pytz.all_timezones if timezone.lower() in tz.lower()]
            if closest:
                timezone = closest[0]
                note = f"Using closest match: {timezone}"
            else:
                timezone = "UTC"
                note = "Invalid timezone. Using UTC instead."
        else:
            note = ""
            
        tz = pytz.timezone(timezone)
        current_time = datetime.datetime.now(tz)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        result = f"Current time in {timezone}: {formatted_time}"
        if note:
            result += f" (Note: {note})"
            
        logging.info(result)
        return result
    except Exception as e:
        logging.error(f"Error getting time for timezone '{timezone}': {e}")
        return f"An error occurred while getting time: {str(e)}"

@function_tool()
async def set_reminder(
    context: RunContext,  # type: ignore
    task: str,
    time_minutes: int = 5
) -> str:
    """
    Create a simple reminder for a task.
    
    Args:
        task: The task to be reminded about
        time_minutes: Minutes from now to set the reminder (default: 5)
    """
    try:
        current_time = datetime.datetime.now()
        reminder_time = current_time + timedelta(minutes=time_minutes)
        formatted_time = reminder_time.strftime("%H:%M:%S")
        
        # This is a simplified version - in a real implementation, you'd set up
        # a proper notification system or integration with a reminder service
        reminder_info = {
            "task": task,
            "time": formatted_time,
            "created_at": current_time.strftime("%H:%M:%S")
        }
        
        # Log the reminder (in a real app, you'd save this to a database)
        logging.info(f"Reminder set: {json.dumps(reminder_info)}")
        
        return f"Reminder set for '{task}' at {formatted_time} ({time_minutes} minutes from now)"
    except Exception as e:
        logging.error(f"Error setting reminder: {e}")
        return f"An error occurred while setting the reminder: {str(e)}"

@function_tool()
async def currency_converter(
    context: RunContext,  # type: ignore
    amount: float,
    from_currency: str,
    to_currency: str
) -> str:
    """
    Convert currency using the latest exchange rates.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., USD, EUR, JPY)
        to_currency: Target currency code (e.g., USD, EUR, JPY)
    """
    try:
        # Standardize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Use a free currency API
        api_url = f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}&amount={amount}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") is False:
                return f"Currency conversion failed: {data.get('error', 'Unknown error')}"
                
            result = data.get("result")
            rate = data.get("info", {}).get("rate")
            
            if result is not None and rate is not None:
                formatted_result = format_currency(result, to_currency)
                logging.info(f"Converted {amount} {from_currency} to {result} {to_currency}")
                return f"{amount} {from_currency} = {formatted_result} (Rate: {rate:.4f})"
            else:
                return "Currency conversion failed: Invalid response data"
        else:
            logging.error(f"API request failed with status code {response.status_code}")
            return f"Currency conversion failed: API error (status code {response.status_code})"
    except Exception as e:
        logging.error(f"Error converting currency: {e}")
        return f"An error occurred during currency conversion: {str(e)}"

@function_tool()
async def generate_password(
    context: RunContext,  # type: ignore
    length: int = 16,
    include_special_chars: bool = True
) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Password length (default: 16)
        include_special_chars: Whether to include special characters (default: True)
    """
    try:
        if length < 8:
            return "Password length must be at least 8 characters for security"
        
        if length > 128:
            return "Password length must not exceed 128 characters"
            
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
        
        # Ensure all character types are included
        chars = lowercase + uppercase + digits
        if include_special_chars:
            chars += special
            
        # Generate password
        password = []
        # Ensure at least one character from each required set
        password.append(random.choice(lowercase))
        password.append(random.choice(uppercase))
        password.append(random.choice(digits))
        if include_special_chars:
            password.append(random.choice(special))
            
        # Fill the rest randomly
        for _ in range(length - len(password)):
            password.append(random.choice(chars))
            
        # Shuffle the password to avoid predictable positions
        random.shuffle(password)
        password = ''.join(password)
        
        logging.info(f"Generated password of length {length} with special chars: {include_special_chars}")
        return f"Generated password: {password}"
    except Exception as e:
        logging.error(f"Error generating password: {e}")
        return f"An error occurred while generating password: {str(e)}"

@function_tool()
async def get_joke(
    context: RunContext,  # type: ignore
    category: str = "neutral"
) -> str:
    """
    Get a random joke.
    
    Args:
        category: Joke category - 'neutral', 'chuck', 'all', 'twister', or 'programming' (default: neutral)
    """
    try:
        # Map user-friendly categories to pyjokes categories
        category_map = {
            "neutral": "neutral",
            "chuck": "chuck",
            "all": "all",
            "twister": "twister",
            "programming": "neutral"  # pyjokes is programming-focused by default
        }
        
        # Default to neutral if category not recognized
        joke_category = category_map.get(category.lower(), "neutral")
        
        # Get joke from pyjokes
        joke = pyjokes.get_joke(category=joke_category)
        
        logging.info(f"Retrieved joke from category '{category}'")
        return joke
    except Exception as e:
        logging.error(f"Error retrieving joke: {e}")
        return f"An error occurred while retrieving a joke: {str(e)}"

@function_tool()
async def generate_qr_code(
    context: RunContext,  # type: ignore
    data: str,
    size: int = 10
) -> str:
    """
    Generate a QR code for the given data.
    
    Args:
        data: Text or URL to encode in the QR code
        size: Size of the QR code image (default: 10)
    """
    try:
        if not data:
            return "QR code generation failed: No data provided"
        
        if size < 1 or size > 40:
            return "QR code generation failed: Size must be between 1 and 40"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for easy display
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        logging.info(f"Generated QR code for data: {data[:30]}{'...' if len(data) > 30 else ''}")
        
        # Return in a format that can be displayed in HTML or markdown
        return f"QR Code generated for: {data}\nBase64 encoded image: {img_str}"
    except Exception as e:
        logging.error(f"Error generating QR code: {e}")
        return f"An error occurred while generating QR code: {str(e)}"

# Tools for developers

@function_tool()
async def search_stackoverflow(
    context: RunContext,  # type: ignore
    query: str
) -> str:
    """
    Search Stack Overflow for programming questions and answers.
    
    Args:
        query: Search query for programming questions
    """
    try:
        # Encode query for URL
        encoded_query = requests.utils.quote(query)
        
        # Build Stack Overflow search URL with Google
        search_query = f"site:stackoverflow.com {query}"
        
        # Use the existing search_web function
        results = await search_web(context, search_query)
        
        logging.info(f"Searched Stack Overflow for '{query}'")
        return f"Stack Overflow results for '{query}':\n\n{results}"
    except Exception as e:
        logging.error(f"Error searching Stack Overflow: {e}")
        return f"An error occurred while searching Stack Overflow: {str(e)}"

@function_tool()
async def parse_git_repo_url(
    context: RunContext,  # type: ignore
    repo_url: str
) -> str:
    """
    Parse and validate a Git repository URL.
    
    Args:
        repo_url: Git repository URL to parse
    """
    try:
        # Common patterns for git URLs
        github_pattern = r"(https?://)?(www\.)?github\.com/([^/]+)/([^/]+)(\.git)?(/)?$"
        gitlab_pattern = r"(https?://)?(www\.)?gitlab\.com/([^/]+)/([^/]+)(\.git)?(/)?$"
        bitbucket_pattern = r"(https?://)?(www\.)?bitbucket\.org/([^/]+)/([^/]+)(\.git)?(/)?$"
        
        # Check GitHub
        github_match = re.match(github_pattern, repo_url)
        if github_match:
            owner = github_match.group(3)
            repo = github_match.group(4)
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            # Normalize URL
            https_url = f"https://github.com/{owner}/{repo}.git"
            ssh_url = f"git@github.com:{owner}/{repo}.git"
            clone_command = f"git clone {https_url}"
            
            return f"""
Repository information:
- Type: GitHub
- Owner: {owner}
- Repository: {repo}
- HTTPS URL: {https_url}
- SSH URL: {ssh_url}
- Clone command: {clone_command}
"""
        
        # Check GitLab
        gitlab_match = re.match(gitlab_pattern, repo_url)
        if gitlab_match:
            owner = gitlab_match.group(3)
            repo = gitlab_match.group(4)
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            # Normalize URL
            https_url = f"https://gitlab.com/{owner}/{repo}.git"
            ssh_url = f"git@gitlab.com:{owner}/{repo}.git"
            clone_command = f"git clone {https_url}"
            
            return f"""
Repository information:
- Type: GitLab
- Owner: {owner}
- Repository: {repo}
- HTTPS URL: {https_url}
- SSH URL: {ssh_url}
- Clone command: {clone_command}
"""
        
        # Check Bitbucket
        bitbucket_match = re.match(bitbucket_pattern, repo_url)
        if bitbucket_match:
            owner = bitbucket_match.group(3)
            repo = bitbucket_match.group(4)
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            # Normalize URL
            https_url = f"https://bitbucket.org/{owner}/{repo}.git"
            ssh_url = f"git@bitbucket.org:{owner}/{repo}.git"
            clone_command = f"git clone {https_url}"
            
            return f"""
Repository information:
- Type: Bitbucket
- Owner: {owner}
- Repository: {repo}
- HTTPS URL: {https_url}
- SSH URL: {ssh_url}
- Clone command: {clone_command}
"""
        
        # If no match found
        return "Invalid or unsupported Git repository URL format."
    except Exception as e:
        logging.error(f"Error parsing Git repository URL: {e}")
        return f"An error occurred while parsing the Git URL: {str(e)}"

@function_tool()
async def generate_code_snippet(
    context: RunContext,  # type: ignore
    language: str,
    task_description: str
) -> str:
    """
    Generate a code snippet example for common programming tasks.
    
    Args:
        language: Programming language (e.g., python, javascript, java, etc.)
        task_description: Description of the task to generate code for
    """
    try:
        language = language.lower()
        
        # Dictionary of common code snippets by language
        snippets = {
            "python": {
                "read file": 
"""# Read a file in Python
with open('filename.txt', 'r') as file:
    content = file.read()
    print(content)
""",
                "http request": 
"""# Make an HTTP request in Python
import requests

response = requests.get('https://api.example.com/data')
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")
""",
                "connect to database": 
"""# Connect to a database in Python
import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# Create a table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
)
''')

# Insert a record
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", 
              ("John Doe", "john@example.com"))

# Commit changes and close
conn.commit()
conn.close()
"""
            },
            "javascript": {
                "read file": 
"""// Read a file in JavaScript (Node.js)
const fs = require('fs');

fs.readFile('filename.txt', 'utf8', (err, data) => {
  if (err) {
    console.error('Error reading file:', err);
    return;
  }
  console.log(data);
});

// Or using promises
async function readFile() {
  try {
    const data = await fs.promises.readFile('filename.txt', 'utf8');
    console.log(data);
  } catch (err) {
    console.error('Error reading file:', err);
  }
}
""",
                "http request": 
"""// Make an HTTP request in JavaScript
// Using fetch (browser or Node.js with node-fetch)
fetch('https://api.example.com/data')
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => console.log(data))
  .catch(error => console.error('Fetch error:', error));

// Using async/await
async function fetchData() {
  try {
    const response = await fetch('https://api.example.com/data');
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Fetch error:', error);
  }
}
"""
            },
            "java": {
                "read file": 
"""// Read a file in Java
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class ReadFile {
    public static void main(String[] args) {
        try (BufferedReader reader = new BufferedReader(new FileReader("filename.txt"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
        } catch (IOException e) {
            System.err.println("Error reading file: " + e.getMessage());
        }
    }
}
""",
                "http request": 
"""// Make an HTTP request in Java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;

public class HttpRequestExample {
    public static void main(String[] args) {
        try {
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("https://api.example.com/data"))
                    .GET()
                    .build();
            
            HttpResponse<String> response = client.send(request, BodyHandlers.ofString());
            
            System.out.println("Status code: " + response.statusCode());
            System.out.println("Response body: " + response.body());
        } catch (Exception e) {
            System.err.println("Error making HTTP request: " + e.getMessage());
        }
    }
}
"""
            }
        }
        
        # Look for matching snippet
        if language in snippets:
            for key, snippet in snippets[language].items():
                if key.lower() in task_description.lower():
                    logging.info(f"Generated code snippet for {language} - {key}")
                    return f"```{language}\n{snippet}\n```"
        
        # If no specific snippet found, return a general message
        return f"No pre-defined code snippet available for '{task_description}' in {language}. Try searching Stack Overflow for specific examples."
    except Exception as e:
        logging.error(f"Error generating code snippet: {e}")
        return f"An error occurred while generating the code snippet: {str(e)}"

# Tools for business professionals

@function_tool()
async def get_stock_price(
    context: RunContext,  # type: ignore
    symbol: str
) -> str:
    """
    Get the current stock price and recent performance for a given ticker symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
    """
    try:
        # Standardize symbol
        symbol = symbol.upper().strip()
        
        # Get stock information using yfinance
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Get current price data
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
        previous_close = info.get('previousClose', 'N/A')
        
        # Calculate price change and percentage
        if current_price != 'N/A' and previous_close != 'N/A':
            price_change = current_price - previous_close
            price_change_percent = (price_change / previous_close) * 100
            change_symbol = "+" if price_change >= 0 else ""
        else:
            price_change = price_change_percent = 'N/A'
            change_symbol = ""
        
        # Get additional information
        company_name = info.get('shortName', symbol)
        market_cap = info.get('marketCap', 'N/A')
        if market_cap != 'N/A':
            # Format market cap to show billions/millions
            if market_cap >= 1_000_000_000:
                market_cap_formatted = f"${market_cap / 1_000_000_000:.2f}B"
            else:
                market_cap_formatted = f"${market_cap / 1_000_000:.2f}M"
        else:
            market_cap_formatted = 'N/A'
        
        # Format the result
        result = f"""
Stock Information for {company_name} ({symbol}):
Current Price: ${current_price:.2f} ({change_symbol}{price_change:.2f}, {change_symbol}{price_change_percent:.2f}%)
Previous Close: ${previous_close:.2f}
Market Cap: {market_cap_formatted}
"""
        
        logging.info(f"Retrieved stock price for {symbol}")
        return result.strip()
    except Exception as e:
        logging.error(f"Error retrieving stock price for {symbol}: {e}")
        return f"An error occurred while retrieving stock information for {symbol}: {str(e)}"

@function_tool()
async def get_news(
    context: RunContext,  # type: ignore
    topic: str = "technology",
    count: int = 5
) -> str:
    """
    Get latest news on a specific topic.
    
    Args:
        topic: News topic (e.g., technology, business, sports)
        count: Number of news items to return (default: 5)
    """
    try:
        # Map of topics to RSS feed URLs
        feeds = {
            "technology": "https://feeds.feedburner.com/TechCrunch",
            "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
            "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "science": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
            "health": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
            "sports": "https://sports.yahoo.com/rss/",
            "us": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"
        }
        
        # Get the appropriate feed URL, or default to technology
        feed_url = feeds.get(topic.lower(), feeds["technology"])
        
        # Parse the RSS feed
        feed = feedparser.parse(feed_url)
        
        # Extract news items
        news_items = []
        for i, entry in enumerate(feed.entries[:count]):
            title = entry.title
            link = entry.link
            published = entry.get('published', 'N/A')
            
            # Try to get a summary, falling back to content if necessary
            if 'summary' in entry:
                summary = BeautifulSoup(entry.summary, 'html.parser').get_text()
            elif 'content' in entry and entry.content:
                summary = BeautifulSoup(entry.content[0].value, 'html.parser').get_text()
            else:
                summary = "No summary available."
            
            # Limit summary length
            summary = summary[:200] + "..." if len(summary) > 200 else summary
            
            # Format news item
            news_item = f"""
{i+1}. {title}
Published: {published}
{summary}
Link: {link}
"""
            news_items.append(news_item)
        
        # Format the result
        source_name = feed.feed.title if hasattr(feed, 'feed') and hasattr(feed.feed, 'title') else "Unknown Source"
        result = f"Latest {topic.capitalize()} News from {source_name}:\n\n" + "\n".join(news_items)
        
        logging.info(f"Retrieved {count} news items about {topic}")
        return result
    except Exception as e:
        logging.error(f"Error retrieving news for {topic}: {e}")
        return f"An error occurred while retrieving news for {topic}: {str(e)}"

@function_tool()
async def create_agenda(
    context: RunContext,  # type: ignore
    meeting_title: str,
    duration_minutes: int = 60,
    topics: Optional[str] = None
) -> str:
    """
    Create a professional meeting agenda with time allocations.
    
    Args:
        meeting_title: Title of the meeting
        duration_minutes: Total duration of the meeting in minutes (default: 60)
        topics: Comma-separated list of topics to discuss
    """
    try:
        if not meeting_title:
            return "Please provide a meeting title."
        
        # Default topics if none provided
        if not topics:
            topics = "Introduction, Updates, Discussion, Action Items, Next Steps"
        
        # Parse topics into a list
        topic_list = [topic.strip() for topic in topics.split(',')]
        
        # Time allocation logic
        num_topics = len(topic_list)
        
        # Reserve time for opening and closing
        opening_time = 5  # minutes
        closing_time = 5  # minutes
        
        # Available time for topics
        available_time = duration_minutes - (opening_time + closing_time)
        
        # Time per topic (ensure at least 1 minute per topic)
        time_per_topic = max(1, available_time // num_topics)
        
        # Adjust closing time if needed
        remaining_time = available_time - (time_per_topic * num_topics)
        closing_time += remaining_time
        
        # Generate agenda
        agenda = f"""
# Meeting Agenda: {meeting_title}
Duration: {duration_minutes} minutes

## Opening (5 minutes)
- Welcome and introduction
- Review of agenda and meeting objectives

"""
        
        # Add topics with time allocations
        current_time = opening_time
        for i, topic in enumerate(topic_list):
            agenda += f"## {topic} ({time_per_topic} minutes)\n"
            if i == 0:  # For the first topic
                agenda += "- Presentation of key points\n- Initial feedback\n\n"
            elif i == num_topics - 1:  # For the last topic
                agenda += "- Discussion of final items\n- Summary of decisions\n\n"
            else:  # For middle topics
                agenda += "- Update and status report\n- Discussion and decisions\n\n"
            current_time += time_per_topic
        
        # Add closing
        agenda += f"""## Closing ({closing_time} minutes)
- Review of action items and responsibilities
- Next meeting scheduling
- Adjournment
"""
        
        logging.info(f"Created agenda for meeting: {meeting_title}")
        return agenda
    except Exception as e:
        logging.error(f"Error creating meeting agenda: {e}")
        return f"An error occurred while creating the meeting agenda: {str(e)}"

@function_tool()
async def calculate_roi(
    context: RunContext,  # type: ignore
    initial_investment: float,
    final_value: float,
    time_period_years: float = 1.0
) -> str:
    """
    Calculate Return on Investment (ROI) with annualized returns.
    
    Args:
        initial_investment: Initial investment amount
        final_value: Final value of the investment
        time_period_years: Time period in years (default: 1.0)
    """
    try:
        if initial_investment <= 0:
            return "Initial investment must be greater than zero."
        
        if time_period_years <= 0:
            return "Time period must be greater than zero."
        
        # Calculate ROI
        net_return = final_value - initial_investment
        roi = (net_return / initial_investment) * 100
        
        # Calculate annualized ROI if time period is not 1 year
        if time_period_years != 1.0:
            annualized_roi = ((final_value / initial_investment) ** (1 / time_period_years) - 1) * 100
        else:
            annualized_roi = roi
        
        # Format the results
        result = f"""
ROI Analysis:
Initial Investment: ${initial_investment:,.2f}
Final Value: ${final_value:,.2f}
Net Return: ${net_return:,.2f}
Time Period: {time_period_years:.2f} years

ROI: {roi:.2f}%
"""

        if time_period_years != 1.0:
            result += f"Annualized ROI: {annualized_roi:.2f}%"
        
        logging.info(f"Calculated ROI: {roi:.2f}%, Annualized: {annualized_roi:.2f}%")
        return result.strip()
    except Exception as e:
        logging.error(f"Error calculating ROI: {e}")
        return f"An error occurred while calculating ROI: {str(e)}"

@function_tool()
async def ask_openai_coding(
    context: RunContext,  # type: ignore
    question: str,
    language: Optional[str] = None
) -> str:
    """
    Get coding or technical answers directly from OpenAI's API instead of Stack Overflow.
    
    Args:
        question: Coding or technical question to ask
        language: Optional programming language for context (e.g., python, javascript, java)
    """
    try:
        # Get OpenAI API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            logging.error("OpenAI API key not found in environment variables")
            return "Unable to use OpenAI: API key not configured in environment variables (OPENAI_API_KEY)"
            
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Prepare the prompt with language context if provided
        if language:
            prompt = f"As an expert {language} developer, please answer this technical question: {question}"
        else:
            prompt = f"As a programming expert, please answer this technical question: {question}"
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # You can also use gpt-4 if available
            messages=[
                {"role": "system", "content": "You are a helpful programming assistant. Provide clear, accurate, and concise answers to technical and coding questions. Include code examples where appropriate."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.2  # Lower temperature for more focused, deterministic answers
        )
        
        # Extract and return the answer
        answer = response.choices[0].message.content
        
        logging.info(f"Retrieved OpenAI response for coding question")
        return f"OpenAI Answer:\n\n{answer}"
        
    except Exception as e:
        logging.error(f"Error getting OpenAI answer: {e}")
        return f"An error occurred while getting an answer from OpenAI: {str(e)}"
    
@function_tool()
async def search_files(
    context: RunContext,  # type: ignore
    search_term: str,
    file_types: Optional[str] = None,
    start_path: Optional[str] = None,
    max_results: int = 20
) -> str:
    """
    Search for files on your local system by name or extension, useful for finding files to attach to emails.
    
    Args:
        search_term: The term to search for in file names
        file_types: Optional comma-separated list of file extensions to filter by (e.g., "pdf,docx,txt")
        start_path: Optional starting directory path for the search (default: user's home directory)
        max_results: Maximum number of results to return (default: 20)
    """
    try:
        # Set default search path if not provided
        if not start_path:
            start_path = os.path.expanduser("~")
        
        # Check if path exists
        if not os.path.exists(start_path):
            return f"Error: The specified path '{start_path}' does not exist."
        
        # Process file types if provided
        file_type_list = []
        if file_types:
            file_type_list = [f".{ext.lower().strip('.')}" for ext in file_types.split(',')]
        
        # Initialize results
        found_files = []
        
        # Walk through directory structure
        logging.info(f"Searching for files matching '{search_term}' starting at '{start_path}'")
        
        for root, dirs, files in os.walk(start_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                
                # Check if file matches search criteria
                file_matches = search_term.lower() in file.lower()
                
                # Check extension if file types are specified
                ext_matches = True
                if file_type_list:
                    ext_matches = any(file.lower().endswith(ext) for ext in file_type_list)
                
                if file_matches and ext_matches:
                    full_path = os.path.join(root, file)
                    file_size = os.path.getsize(full_path)
                    file_mtime = os.path.getmtime(full_path)
                    file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Format file size
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.2f} KB"
                    else:
                        size_str = f"{file_size / (1024 * 1024):.2f} MB"
                    
                    found_files.append({
                        "path": full_path,
                        "name": file,
                        "size": size_str,
                        "modified": file_mtime_str
                    })
                    
                    # Limit results
                    if len(found_files) >= max_results:
                        break
            
            # Stop searching if we've reached the maximum
            if len(found_files) >= max_results:
                break
        
        # Format results
        if found_files:
            result = f"Found {len(found_files)} file(s) matching '{search_term}':\n\n"
            for i, file in enumerate(found_files):
                result += f"{i+1}. {file['name']}\n"
                result += f"   Path: {file['path']}\n"
                result += f"   Size: {file['size']}\n"
                result += f"   Modified: {file['modified']}\n\n"
            
            if len(found_files) == max_results:
                result += f"Note: Results limited to {max_results} files. Refine your search to see more specific results."
        else:
            result = f"No files found matching '{search_term}'"
            if file_type_list:
                result += f" with extension(s): {', '.join(file_type_list)}"
            result += f" in '{start_path}'."
        
        logging.info(f"Found {len(found_files)} files matching '{search_term}'")
        return result
    except Exception as e:
        logging.error(f"Error searching for files: {e}")
        return f"An error occurred while searching for files: {str(e)}"

@function_tool()
async def send_email_with_attachment(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    attachment_path: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email with an attachment through Gmail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        attachment_path: Full path to the file to attach
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Verify attachment exists
        if not os.path.exists(attachment_path):
            logging.error(f"Attachment file not found: {attachment_path}")
            return f"Email sending failed: Attachment file not found at {attachment_path}"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Determine MIME type based on file extension
        import mimetypes
        ctype, encoding = mimetypes.guess_type(attachment_path)
        
        if ctype is None or encoding is not None:
            # If type could not be guessed, use a generic type
            ctype = 'application/octet-stream'
        
        maintype, subtype = ctype.split('/', 1)
        
        # Read and attach the file
        with open(attachment_path, 'rb') as file:
            attachment = MIMEBase(maintype, subtype)
            attachment.set_payload(file.read())
            
        # Encode the attachment in base64
        import email.encoders
        email.encoders.encode_base64(attachment)
        
        # Add header with filename
        filename = os.path.basename(attachment_path)
        attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(attachment)
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        file_size = os.path.getsize(attachment_path)
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
        
        logging.info(f"Email with attachment sent successfully to {to_email}")
        return f"Email with attachment '{filename}' ({size_str}) sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email with attachment: {e}")
        return f"An error occurred while sending email with attachment: {str(e)}"