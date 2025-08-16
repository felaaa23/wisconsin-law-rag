Steps to make it work:

Run: git clone <your-repo-url>
Then: cd <your-repo-folder>
Then: "python -m venv venv" to make a virtual environment
On Mac: "source venv/bin/activate" or on Windows: venv\Scripts\activate
Type "pip install -r requirements.txt" to get installation of what is needed
Before that, you're gonna need to create a OPENAPI key and put it within .env
After put this here after line 2 of .env:
"DATA_DIR=./data
CHROMA_DIR=./chroma
COLLECTION=wi-law
EMBED_MODEL=text-embedding-3-small"

Next after setting the first line as OPENAI_API_KEY="sk-etc-etc" paste this below "CHROMA_OPENAI_API_KEY=${OPENAI_API_KEY}"
Run the webscraper.py to mass download every pdf given by https://docs.legis.wisconsin.gov/statutes/prefaces/toc
Then run fill_db.py in order to send to chromadb
After creating and setting the key, youre gonna need to run "export OPENAI_API_KEY="sk-..." on the terminal in order for the RAG to work
Then run ask.py to ask any police related questions needed within the terminal


When I first started off with this I originally began with some guy's 10 minute Youtube tutorial and worked my way up from there (https://tomstechacademy.com/retrieval-augmented-generation-rag/)
Originally, what had been a simple parser for vegetables to answer questions about gardening had been instead been used to hundreds of pdf files of Wisconsin policy and law
I first wanted the raw data so I had used BeautifulSoup to scour any bluetext link that had a .pdf ending within and automatically download it
Then, using the data, I had built fill_db using Chromadb (I was not gonna use MongoDB or any other vector database I felt chroma was most versatile for this specific task)
I broke everything down into specific types of metadata and doctypes in order for OPENAPI to breakdown and use based on what was assigned
Then I upserted everything to the ChromaDB folder that would be created
With ask.py, I had to tokenize everything and break it down into smaller little sections in order for GPT to actually be able to process everything
Then I had a bunch of different helper functions that would add or subtract points such as if it was by the department or how recent it was and grade the confidence level of the RAG based on it. 
In short I just saw if certain parameters were met and would send back to the user if it was more trustworthy based on it
Then I had to break down all the weird little symbols and then send it back to the user and has edge cases if it encounters any errors


