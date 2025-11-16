# Restaurant Menu Summarizer

Small Python/Flask service that takes a **restaurant menu URL + date** and returns a **structured JSON lunch menu** extracted by an LLM, with caching in SQLite. A simple HTML frontend is included for manual testing.

## Web content retrieval – chosen approach

For fetching the restaurant menu pages I use **Variant A: custom scraper**.

- I download the HTML using `requests`.
- I parse and clean the relevant text using **BeautifulSoup**.
- Only the extracted text (not the whole raw HTML) is sent to the LLM.

I deliberately did **not** use any built-in web search / web fetch from the LLM provider, because a custom scraper gives me deterministic control over what exactly goes into the prompt, is easier to debug, and is portable across different LLM APIs.

## LLM API integration and tool calling

I use the OpenAI API with **structured JSON output** that matches a Pydantic schema (e.g. `MenuResponse`, `MenuItem`).  
The model is instructed to always return a valid JSON object with fields like `restaurant_name`, `date`, `menu_items`, etc.

For tool/function calling I implemented:

- **Price parsing and normalisation**  
  A Python tool `normalize_prices` that converts messy price strings such as `"145,-"`, `"149 Kč"`, `"89Kc"` into a clean numeric CZK value (e.g. `145`).  
  The LLM calls this tool for each menu item price, so the final JSON always contains numeric prices instead of raw strings.

This way the LLM focuses on understanding the menu text and mapping items into the schema, while the price formatting rules stay in normal code.

## Caching strategy

For caching I use a **persistent SQLite database** with a single table that stores the full LLM-extracted menu JSON.

- The **cache key** is `(url, date)`, which matches the real-world behaviour that lunch menus change daily.
- The cached value is the entire validated response (including `restaurant_name`, `menu_items`, etc.), so repeated requests for the same `(url, date)` can be served without calling the LLM again.
- On each request I run a simple cleanup that removes entries with `date < today`, which works as a basic TTL and prevents the cache from growing indefinitely.
- Completely **empty menus are not cached** – if the LLM fails to extract anything, I prefer to allow future calls to try again after improving prompts or logic.

I chose **SQLite** because it is:
- easy to set up (no external service required),
- persistent across restarts,
- good enough for a single-node prototype or small deployment.

In a larger production system this could be replaced by PostgreSQL or Redis, and the invalidation logic could be extended (e.g. combining `(url, date)` with a hash of the page content to detect changes during the same day).

## How to run the project (step-by-step)

### 1. Go to project folder
cd Menu
### 2. Install dependencies
py -m pip install -r requirements.txt
### 3. Create .env in the project root
OPENAI_API_KEY=sk-your-real-key-here
API_KEY=supersecret123      # optional, used only for manual API testing (X-API-Key)

API_KEY – optional API key for the X-API-Key header (for Postman / curl).
The frontend does not send this key.

### 4. Run the backend
py main.py
The app starts on:
http://127.0.0.1:5000
### 5. Use the frontend
Open http://127.0.0.1:5000 in a browser.
Paste a restaurant menu URL.
Pick a date (today or in the future).
Click submit.

You’ll see:
restaurant name + date + source URL,
list of menu items,
and the full JSON response (for debugging / integration).

## #How to run tests
From the project root:
py -m pytest

This runs:

### Unit tests:
price normalisation tool (parsing "145,-", "149 Kč", etc. to numeric CZK),
Pydantic schema validation for the menu JSON.

### Integration + caching test:
calls POST /api/menu using Flask’s test client (with mocked LLM),
verifies that:
first call for a given url + date stores the menu in SQLite and returns "cached": false,
second call for the same url + date returns from cache and sets "cached": true without calling the LLM again.

### Thoughts about the solution 
I structured the project around a simple but explicit flow: request → cache → scraper → LLM → validation → response. Each part lives in its own module (cache.py, scraper.py, llm_client.py, models.py, routes.py), which keeps the code readable and makes it easier to test individual pieces. Flask is a good fit here because I only need one main endpoint (POST /api/menu), and on top of that I added a tiny static frontend so it’s comfortable to try out different URLs and dates in a browser.
For data extraction I deliberately combined a classic HTML scraper with an LLM. The scraper (requests + BeautifulSoup) gives me deterministic control over what text is sent to the model and avoids depending on any vendor-specific “web fetch” features. The LLM is used only for the hard part: understanding semi-structured Czech menu text and turning it into a clean JSON that matches a Pydantic schema. On top of that I added a function/tool normalize_prices so the model can convert string prices like 145,- or 149 Kč into numeric CZK values in a consistent way.
Caching is implemented using SQLite with (url, date) as a primary key, which matches the real-world behaviour that lunch menus are daily. I delete entries with date < today as a simple TTL so the cache doesn’t grow forever. One important detail is that I don’t cache completely empty menus – if the LLM finds nothing, I’d rather call it again in the future after improving prompts or logic. Overall, the goal was not to perfectly support every possible menu format on the internet, but to build something that is realistic, debuggable and easy to extend (for example, adding allergen filters, vegetarian detection, or comparing menus across multiple restaurants).

### What I’d like to discuss

1. **HTML parsing vs. LLM**
   - Where would you draw the line between classic HTML parsing (tables, headings, CSS classes) and “let the LLM figure it out” for this kind of menu extraction?

2. **Caching, freshness and reliability**
   - How would you design caching in a real product so that menus stay fresh during the day (e.g. keys, TTL, invalidation on content change)?
   - What would you add to improve reliability of the LLM output (validation, reducing hallucinations, etc.)?

3. **Scaling to many restaurants**
   - If we wanted to monitor tens or hundreds of menus every morning and send notifications, how would you approach scheduling, rate limiting of LLM calls, and handling slow or broken restaurant websites?
     
### Example test URLs used during development
Just for reference, I tested the app on these real pages:

https://jidelna.webflow.io/ – weekly lunch menu

https://www.restauraceandel.cz/denni-nabidka – daily lunch menu

https://www.restaurace-oburka.cz/tydenni-menu-od-11-00-do-14-00hod/ – weekly menu with specific days

