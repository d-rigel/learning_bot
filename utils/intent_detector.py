import openai
from dotenv import load_dotenv
import os

from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("jitappvector")


load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def detect_intent(response_text, expected_intent):
    # Step 1: Generate embedding for the user's response text using OpenAI
    response_embedding = openai.Embedding.create(input=response_text, model="text-embedding-ada-002")['data'][0]['embedding']
    
    # Step 2: Upsert (insert or update) the response embedding into Pinecone
    Pinecone.upsert([("response", response_embedding)])
    
    # Step 3: Generate embedding for the expected intent using OpenAI
    expected_embedding = openai.Embedding.create(input=expected_intent, model="text-embedding-ada-002")['data'][0]['embedding']
    
    # Step 4: Calculate the similarity score between the response embedding and the expected intent embedding using Pinecone
    similarity_score = Pinecone.similarity("response", expected_embedding)
    
    # Step 5: Determine if the similarity score is above a certain threshold (0.8 in this case)
    return similarity_score > 0.8