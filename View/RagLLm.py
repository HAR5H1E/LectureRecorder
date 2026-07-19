import os
from pathlib import Path
ParentDir = Path(__file__).resolve().parent
scriptDir = ParentDir.parent
print(scriptDir)
os.environ["FASTEMBED_CACHE_PATH"] = str(scriptDir / "FastEmbedCache")
print("FASTEMBED_CACHE_PATH set to:", os.environ["FASTEMBED_CACHE_PATH"])
import hashlib
from semantic_text_splitter import MarkdownSplitter
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct, Document
from textblob import TextBlob
import ollama as LLM
import uuid
import traceback



DB_PATH = str(scriptDir / "DBStorage")
model = "sentence-transformers/all-minilm-l6-v2"
bm25Model = "qdrant/bm25"

def Build():
    """Independent schema builder. Opens and closes its own client safely."""
    client = QdrantClient(path=DB_PATH)
    try:
        if not client.collection_exists(collection_name="TextRAG"):
            client.create_collection(
                collection_name="TextRAG",
                vectors_config={
                    "dense_vector": models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "bm25_sparse_vectors": models.SparseVectorParams(
                        modifier=models.Modifier.IDF
                    )
                }
            )
        else:
            print("Collection Exists!!!")
    finally:
        client.close() 

    
def EncodeContextText(textDocument, maxCharacters, chunkSize, overlap, GetValue, Filename):
    Build() 
    print(Filename)
    global model, bm25Model
    client = QdrantClient(path=DB_PATH)
    try:
        MarkSplitter = MarkdownSplitter.from_tiktoken_model("gpt-3.5-turbo", capacity=maxCharacters)
        ParentChunks = MarkSplitter.chunks(textDocument)
        childSpliter = MarkdownSplitter.from_tiktoken_model("gpt-3.5-turbo", capacity=chunkSize, overlap=overlap)
        
        for ParentVal in ParentChunks:    
            childChunks = childSpliter.chunks(ParentVal)
            Points = []
            for child in childChunks:
                if not child.strip():
                    continue

                print("oooh encoding...")
                point = PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, child)),
                    payload={
                        "TextChunk": child,
                        "ParentChunk": ParentVal,
                        "FileName": Filename     
                    },
                    vector={
                        "dense_vector": Document(text=child, model=model),
                        "bm25_sparse_vectors": Document(text=child, model=bm25Model)
                    }
                )
                print(point.payload.get('FileName'))
                Points.append(point)
            
            print("oooh uploading...")
            client.upload_points(
                collection_name="TextRAG",
                points=Points,
                batch_size=64
            )
                
        print("Encoded")
        GetValue.put(True)  
    except Exception as e:
        print(f"Error in context encoding: {e}")
    finally:
        client.close() 
    


def encodeQuery(Query, fileName, resVal):
    Build() 
    global model, bm25Model

    print(DB_PATH)
    client = QdrantClient(path=DB_PATH)
    print(Query)
    try:
        
        print(fileName)
        results = client.query_points(
            collection_name="TextRAG",
            prefetch=[
                
                models.Prefetch(
                    query=models.Document(text=Query, model=model),
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="FileName",
                                match=models.MatchValue(value=fileName)
                            )
                        ]
                    ),
                    using="dense_vector",
                    limit=5
                ),
                models.Prefetch(
                    query=models.Document(text=Query, model=bm25Model),
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="FileName",
                                match=models.MatchValue(value=fileName)
                            )
                        ]
                    ),
                    using="bm25_sparse_vectors",
                    limit=5
                )
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=5,
            with_payload=True
        )

        ContextText = ""
        for result in results.points:

            print(result)
            if result.score > 0.5:
                ContextText += result.payload.get("ParentChunk", "") + "\n\n"

        print(ContextText)
       
        resVal.put(prompt(ContextText, Query))
        
        resVal.put(True)
    except Exception as e:
        print(f"Error in query thread: {e}")
        traceback.print_exc()
        resVal.put(False)
    finally:
        client.close()
        
def deleteQuery(fileName):
    client = QdrantClient(path=DB_PATH)
    print(fileName)
    response = client.delete(
        collection_name="TextRAG",
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="FileName",
                        match=models.MatchValue(value=fileName)
                    )
                ]
            )
        ),
        wait=True
    )

    client.close()
    return

def prompt(contextText, Query):
    prompt_str = f"""Context:
{contextText}

Question: {Query}

Task: Answer the question using only the context above. Be extremely brief (1-2 sentences). Do not explain your reasoning.
If the the question dosent seem to align with the context respond with "I don't have that Information"

Answer:"""

    print("okat")
    response = LLM.generate(
        model="llama3.2:latest",
        prompt=prompt_str,
        options={
            "temperature": 0.2,
            "num_predict": 150  
        },
    )
    return response['response']