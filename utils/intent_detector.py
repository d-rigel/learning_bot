import openai
from dotenv import load_dotenv
import os
import numpy as np
import time

from pinecone import Pinecone, ServerlessSpec

load_dotenv()


# configure client
pc = Pinecone(api_key= os.getenv('PINECONE_API_KEY'))
# configure serverless spec
spec = ServerlessSpec(cloud='aws', region='us-east-1')


# check for and delete index if already exists
index_name = 'coding-bot'
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)



# we create a new index
pc.create_index(
        index_name,
        dimension=1536,  # dimensionality of text-embedding-ada-002
        metric='dotproduct',
        spec=spec
    )

# To connect to index
index = pc.Index(index_name)
index.describe_index_stats()



# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def detect_intent(response_text, expected_intent):
    def create_embedding_with_retry(input_text, model="text-embedding-ada-002", max_retries=5):
        retries = 0
        delay = 1

        while retries < max_retries:
            try:
                # Attempt to create embedding
                response = openai.Embedding.create(input=input_text, model=model)
                return response['data'][0]['embedding']
            except openai.error.RateLimitError as e:
                print(f"Rate limit error: {e}")
                print(f"Attempt {retries + 1} of {max_retries}. Retrying in {delay} seconds...")
                time.sleep(delay)
                retries += 1
                delay *= 2

        raise Exception("Rate limit exceeded and all retries failed.")

    # Generate embeddings for both response and expected intent
    response_embedding = create_embedding_with_retry(response_text)
    expected_embedding = create_embedding_with_retry(expected_intent)

    # Calculate cosine similarity
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    similarity_score = cosine_similarity(response_embedding, expected_embedding)

    if similarity_score > 0.8:
        return True, "Great job! You correctly completed the task."
    else:
        hint = generate_hint(expected_intent)
        return False, f"It looks like there's an error. Remember to follow the task instructions. Try again! Here's a hint: {hint}"

def generate_hint(expected_intent):
    # Create embedding for the expected intent
    query_embedding = openai.Embedding.create(input=expected_intent, model="text-embedding-ada-002")['data'][0]['embedding']
    # Upsert the query embedding to Pinecone with a unique identifier

    print(f"query_embedding: {query_embedding}")
 
    index.upsert(vectors=[(query_embedding)])


    
    # Query Pinecone index
    query_results = index.query(
        namespace="ns1",
        vector=query_embedding,
        top_k=2,
        include_values=True,
        include_metadata=True,
    )
    print(query_results)
    
    # Extract relevant information from Pinecone results
    relevant_info = [result['metadata']['text'] for result in query_results.get('matches', []) if 'text' in result.get('metadata', {})]
    
    # Generate hint using OpenAI's GPT-3
    prompt = f"Given the task: '{expected_intent}', and the following relevant information: {relevant_info}, provide a hint to help the user correct their response."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100
    )
    
    return response.choices[0].text.strip()




# import openai
# from dotenv import load_dotenv
# import os
# import numpy as np
# # from pinecone import Pinecone
# # ---------------------------------------------------------
# from pinecone import Pinecone, ServerlessSpec
# import time

# load_dotenv()

# # ------------------------------------------------------------
# # Initialize Pinecone
# # pc = Pinecone(api_key="5fcfb084-8f6d-4b4a-94cc-1fde365764c7")
# # index = pc.Index("code-learning-bot")
# # ------------------------------------------------------------

# # configure client
# pc = Pinecone(api_key='5fcfb084-8f6d-4b4a-94cc-1fde365764c7')
# # configure serverless spec
# spec = ServerlessSpec(cloud='aws', region='us-east-1')


# # check for and delete index if already exists
# index_name = 'coding-bot'
# if index_name in pc.list_indexes().names():
#     pc.delete_index(index_name)



# # we create a new index
# pc.create_index(
#         index_name,
#         dimension=1536,  # dimensionality of text-embedding-ada-002
#         metric='dotproduct',
#         spec=spec
#     )

# # To connect to index
# index = pc.Index(index_name)
# index.describe_index_stats()



# # Set up OpenAI API key
# openai.api_key = os.getenv('OPENAI_API_KEY')

# def detect_intent(response_text, expected_intent):
#     def create_embedding_with_retry(input_text, model="text-embedding-ada-002", max_retries=5):
#         retries = 0
#         delay = 1  # Start with a 1-second delay

#         while retries < max_retries:
#             try:
#                 # Attempt to create the embedding
#                 response = openai.Embedding.create(input=input_text, model=model)
#                 return response['data'][0]['embedding']
#             except openai.error.RateLimitError:
#                 # Handle the rate limit error by waiting and retrying
#                 print(f"Rate limit exceeded. Retrying in {delay} seconds...")
#                 time.sleep(delay)
#                 retries += 1
#                 delay *= 2  # Exponential backoff

#         # If all retries are exhausted, raise an error or handle as needed
#         raise Exception("Rate limit exceeded and all retries failed.")

#     # Generate embeddings for both response and expected intent
#     response_embedding = create_embedding_with_retry(response_text)
#     expected_embedding = create_embedding_with_retry(expected_intent)

#     # Calculate cosine similarity
#     def cosine_similarity(a, b):
#         return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

#     similarity_score = cosine_similarity(response_embedding, expected_embedding)

#     if similarity_score > 0.8:
#         return True, "Great job! You correctly completed the task."
#     else:
#         hint = generate_hint(expected_intent)
#         return False, f"It looks like there's an error. Remember to follow the task instructions. Try again! Here's a hint: {hint}"

