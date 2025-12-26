# Learning LangGraph

This repo is just me working through a tutorial on [LangGraph](https://youtu.be/dQw4w9WgXcQ?si=UeIkoAnAljXxXQmS&t=44s).

I used AnthropicAI and a python virtual environment.

## Initial Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "ANTRHOPIC_API_KEY='your_api_key_here'" > .env
```

The only required env is the `ANTHROPIC_API_KEY`, but you can also set:

- `ANTHROPIC_MODEL`
- `LOG_LEVEL`
- `LOG_FILE`

## First Example

Sample usage and output:

```bash
python first_graph.py 
```

Example output:

```text
Hello, Alice, or should I say, 'Hello World!'
```

## Second Example

This example actually invokes and LLM to get a response.

```bash
python second_graph.py 
```

I get bored with the 'helpful assistant' trope, so made mine a sea pirate. Example output:

```text
Ahoy there, matey! If ye be seekin' buried treasure, here be some places to set yer sights:

**The Classic Hunting Grounds:**
- **Desert islands** with palm trees and fresh water - X marks the spot on many an old map!
- **Coastal caves** where the tide don't reach - perfect for stashin' plunder
- **Old shipwreck sites** - many a vessel went down with her cargo still aboard
- **Rocky coves** and hidden beaches known only to those who sailed these waters before

**What Ye Need:**
- A proper treasure map (the older and more worn, the better!)
- A trusty compass and sharp eye for landmarks
- A sturdy shovel for diggin'
- Maybe a crew ye can trust... though that be the hardest treasure to find!

**Words of Wisdom:**
Keep yer eyes peeled for:
- Unusual rock formations
- Dead trees or markers
- Paces from the shoreline (pirates loved their steps - "40 paces north from the skull rock!")

But I'll tell ye true - the REAL treasure be the adventure itself, the salt spray on yer face, and the freedom of the open seas! 

Now, are ye lookin' for actual historical treasure hunting spots, or just enjoyin' the pirate spirit? ⚓🏴‍☠️
```


## Third Example

This example uses conditional logic: it decides if a web search is
needed in order to answer the question, and follows a path based on that.

```bash
python third_graph.py
```

Thies example uses DuckDuckGo for web searches, and I didn't take the time
to optimize the search prompt, so the results are a bit hit-and-miss.

Example output:

```text
Asking question: What is 2 - 9?
Direct answer result: 2 - 9 = -7
Asking question: What's the latest news in deep sea exploration?
Search answer result: Here are 4 search results from DuckDuckGo:
1. NOAA Ocean Exploration 2024 Expeditions - https://oceanexplorer.noaa.gov/expedition-2024-expeditions/
2. The deep sea footage scientists filmed in 2024 is jaw-dropping - Mashable - https://mashable.com/article/deep-sea-ocean-discovery-2024
3. Deep Sea Exploration Archives - Florida Institute of Oceanography - https://www.fio.usf.edu/tag/deep-sea-exploration/
4. NOAA Ocean Exploration: Homepage - https://oceanexplorer.noaa.gov/
```

