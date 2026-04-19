import os
import json
import chromadb
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()

# We need a custom embedded function to interface with Chromadb because google-genai is used natively
class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        response = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=input
        )
        return [e.values for e in response.embeddings]


# 1. Formulation logic
def load_and_structure_schema() -> List[Dict[str, Any]]:
    if not os.path.exists('schema.json'):
        return []
        
    with open('schema.json', 'r') as f:
        schema_data = json.load(f)
        
    tables_map = {}
    
    # First pass: Aggregate columns and foreign keys per table
    for row in schema_data:
        tname = row['table_name']
        if tname not in tables_map:
            tables_map[tname] = {
                "name": tname,
                "description": "Auto-generated table schema",
                "domain": "general",
                "joins_to": set(),
                "columns": [],
                "has_dates": False,
                "has_amounts": False,
                "has_geography": False
            }
            
        t = tables_map[tname]
        cname = row['column_name']
        dtype = str(row['data_type']).lower()
        
        # Format column string
        col_str = f"- {cname} ({dtype})"
        if row['is_primary_key']:
            col_str += " [PK]"
        if row['foreign_table_name']:
            ftable = row['foreign_table_name']
            col_str += f" [FK -> {ftable}({row['foreign_column_name']})]"
            t["joins_to"].add(ftable)
            
        if row.get('column_description'):
            col_str += f" // {row['column_description']}"
            
        t["columns"].append(col_str)
        
        # Meta inferences
        if any(x in dtype for x in ['date', 'time']):
            t["has_dates"] = True
        if any(x in dtype for x in ['numeric', 'decimal', 'money', 'real', 'double']):
            t["has_amounts"] = True
        
        # Geography checks on column name
        cname_lower = cname.lower()
        if any(x in cname_lower for x in ['city', 'country', 'region', 'lat', 'long', 'zip', 'address', 'state']):
            t["has_geography"] = True

    # Build the final documents
    structured_data = []
    for tname, t in tables_map.items():
        joins = list(t["joins_to"])
        relationship_line = f"\nRelationships: joins to {', '.join(joins)}" if joins else ""
        
        document_text = (
            f"Table: {t['name']}\n"
            f"Description: {t['description']}\n"
            f"Domain: {t['domain']}\n"
            f"\nColumns:\n"
            + "\n".join(t["columns"])
            + relationship_line
        )
        
        metadata = {
            "table": t["name"],
            "domain": t["domain"],
            "has_dates": t["has_dates"],
            "has_amounts": t["has_amounts"],
            "has_geography": t["has_geography"],
            "joins_to": ",".join(joins)
        }
        
        structured_data.append({
            "id": t["name"],
            "document": document_text,
            "metadata": metadata
        })
        
    return structured_data

# Global DB Instance
def get_chroma_db():
    chroma_client = chromadb.PersistentClient()
    db = chroma_client.get_or_create_collection(
        name="vectorDb_tables_advanced", 
        embedding_function=GeminiEmbeddingFunction()
    )
    return db

def initialize_database():
    print("Building Document chunks...", flush=True)
    db = get_chroma_db()
    data = load_and_structure_schema()
    if data:
        # We can just upsert all tables blindly
        db.upsert(
            ids=[d["id"] for d in data],
            documents=[d["document"] for d in data],
            metadatas=[d["metadata"] for d in data]
        )
        print(f"Upserted {len(data)} table documents into ChromaDB.", flush=True)

# Pre-filtering Heuristics
def build_where_filter(query: str) -> dict:
    query_lower = query.lower()
    conditions = []
    
    if any(word in query_lower for word in ['when', 'date', 'month', 'year', 'day', 'time', 'recent', 'oldest']):
        conditions.append({"has_dates": True})
        
    if any(word in query_lower for word in ['total', 'sum', 'average', 'cost', 'price', 'revenue', 'dollar', 'amount']):
        conditions.append({"has_amounts": True})
        
    if any(word in query_lower for word in ['where', 'city', 'country', 'location', 'region', 'address']):
        conditions.append({"has_geography": True})
        
    if len(conditions) == 1:
        return conditions[0]
    elif len(conditions) > 1:
        return {"$and": conditions}
    else:
        return None # No pre-filter

def generate_sql(query: str):
    import sys
    print(f"\n--- Advanced RAG SQL Pipeline ---", flush=True)
    sys.stdout.flush()
    
    # 1. Initialize if needed
    initialize_database()
    
    # 2. Get DB
    db = get_chroma_db()
    
    # 3. Pre-filter
    where_filter = build_where_filter(query)
    filter_log = f"Pre-filtering applied: {json.dumps(where_filter) if where_filter else 'None (Full search)'}"
    print(filter_log, flush=True)
    
    # 4. Search
    results = db.query(
        query_texts=[query],
        n_results=3,
        where=where_filter
    )
    
    docs = results.get('documents', [[]])[0]
    passage = "\n\n".join(docs)
    
    print("Fetched schema chunks successfully.", flush=True)
    
    # 5. Generate SQL
    prompt = f"""You are an expert PostgreSQL developer. Write a highly accurate SQL query based on the following database schema constraints.
    
Schema Context:
{passage}

User Query: {query}

Instructions:
- Return ONLY the raw PostgreSQL statement.
- Do not include markdown code block syntax (like ```sql).
- Do not include conversational text.
"""
    
    print("Calling LLM...", flush=True)
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        sql_query = response.text.strip()
    except Exception as e:
        print(f"LLM API Error: {e}", flush=True)
        return {
            "sql": f"-- Error: The AI service is currently unavailable or experiencing high demand.\n-- Details: {str(e)}\n-- Please try again later.",
            "context": f"[Error] LLM service failed to process the retrieved context.\n\n[Chunks Retrieved] {len(docs)} tables fetched.\n\n--- Retrieved Payload ---\n{passage}"
        }
    
    if sql_query.startswith("```"):
        lines = sql_query.split("\n")
        if lines[-1].strip() == "```":
            sql_query = "\n".join(lines[1:-1])
        else:
            sql_query = "\n".join(lines[1:])
            
    if sql_query.startswith("sql\n"):
        sql_query = sql_query[4:]
        
    # Formatting context output for the UI
    context_out = f"[User Query] {query}\n"
    context_out += f"[{filter_log}]\n"
    context_out += f"[Chunks Retrieved] {len(docs)} tables fetched.\n\n"
    context_out += "--- Retrieved Payload ---\n" + passage
        
    return {
        "sql": sql_query.strip(),
        "context": context_out
    }