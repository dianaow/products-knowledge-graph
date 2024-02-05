# Implementing Retrieval-Augmented Generation (RAG) with a Knowledge Graph (KG)

### Constructing a KG with skincare products found on an e-commerce website
### Product similarity search with vector embeddings
Tools: Python, OpenAI (free tier), LangChain, Neo4j

### Set up
1. Create a Python virtual environment where the dependencies for this project will be installed.
```
cd server
python3 -m venv venv
```

2. Activate the environment and install all the packages available in the requirement.txt file.
```
source venv/bin/activate
pip install -r ./requirements.txt
```

3. If a  `.env` file is not present in the server folder, create one to store the private OpenAI API key, which is required to use the LLMs. 
```
OPENAI_API_KEY=XXXXXX
NEO4J_PW=XXX
```

4. Run the Python script to web scrape product information found online.
```
python3 web_scrape.py
```

5. The `llm_kg.ipynb` file explains:
- How to use LLM to extract new relations from product descriptions and construct Knowledge Graph
- Methods to query the graph database (based on embeddings, LLM-generated entities in prompt, Cypher)


![Image of Knowledge Graph](https://github.com/dianaow/products-knowledge-graph/blob/main/graph_overview.png)