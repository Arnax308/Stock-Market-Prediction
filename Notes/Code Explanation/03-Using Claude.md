---
Title: Using Claude
Created: 12th September 2024 17:52
Last Modified: 12th September 2024 17:52
tags:
  - ML
cssclasses:
---
# Claude

I have used the claude api to extract sectors and companies name from the given headlines/articles. 

## Import Statements

```python
import anthropic
import time
from tenacity import retry, wait_exponential, stop_after_attempt
```

These lines import necessary modules:
- `anthropic`: Likely a library for interacting with the Anthropic API
- `time`: For adding delays between API calls
- `tenacity`: A library for implementing retry logic with exponential backoff

## Client Initialization

```python
client = anthropic.Anthropic(api_key=#Put your key here)
```

This line initializes an Anthropic client object using an API key (which should be replaced with the actual key).

## Retry Decorator

```python
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
def make_api_call(headline):
    ...
```

This decorator applies retry logic to the `make_api_call` function:
- Uses exponential back-off with a multiplier of 1, minimum wait of 4 seconds, and maximum wait of 10 seconds
- Stops after 5 attempts

## API Call Function

```python
def make_api_call(headline):
    return client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system="...",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Identify the company and its sector from this headline: {headline}"
                    }
                ]
            }
        ]
    )
```

This function makes an API call to the Anthropic service:
- Uses a specific model ("claude-3-5-sonnet-20240620")
- Sets parameters like max_tokens and temperature
- Provides a system prompt instructing the model on how to respond
- Sends a user message with the headline to analyze

## Data Structures Initialization

```python
companies = []
sectors = []
```

These lines initialize empty lists to store company names and sectors.

## Main Processing Loop

```python
for headline in headlines:
    ...
```

This loop iterates over a list of headlines (which is not defined in the provided code).

## Error Handling and API Call Execution

```python
try:
    message = make_api_call(headline)
    
    # Extract the text content from the message
    response = message.content[1].text if isinstance(message.content, list) else message.content.text
    
    # Now we can safely use strip() and split()
    response = response.strip()
    company, sector = response.split(',')
    
    # Append to the respective lists
    companies.append(company.strip())
    sectors.append(sector.strip())
    
    # Print the result
    print(f"Headline: {headline}")
    print(f"Company: {company.strip()}")
    print(f"Sector: {sector.strip()}")
    print("-" * 50)
    
    # Add a delay between requests
    time.sleep(1)
except Exception as e:
    print(f"Error processing headline: {headline}")
    print(f"Error: {str(e)}")
```

This try-except block handles each headline:
- Makes an API call using the retry-decorated function
- Extracts and processes the response
- Stores company and sector information
- Prints the results
- Adds a delay before processing the next headline
- Catches and prints any exceptions that occur during processing


