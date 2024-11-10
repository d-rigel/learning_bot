import openai
from dotenv import load_dotenv
import os
import numpy as np
import time
from pinecone import Pinecone, ServerlessSpec
import json

load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')
# # configure client
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


# --------------------------------------------------

# Set up Pinecone API key and environment
# pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENVIRONMENT'))

# Configure Pinecone index
# index_name = 'coding-bot'
# if index_name not in pinecone.list_indexes():
    # pinecone.create_index(index_name, dimension=1536, metric='cosine')
# index = pinecone.Index(index_name)

# Define the functions that the model can call
functions = [
    {
        "name": "detect_intent",
        "description": "Detects the intent of the user's response and provides feedback.",
        "parameters": {
            "type": "object",
            "properties": {
                "response_text": {
                    "type": "string",
                    "description": "The text of the user's response."
                },
                "expected_intent": {
                    "type": "string",
                    "description": "The expected intent based on the current session."
                }
            },
            "required": ["response_text", "expected_intent"]
        }
    },
    {
        "name": "generate_hint",
        "description": "Generates a hint based on the expected intent.",
        "parameters": {
            "type": "object",
            "properties": {
                "expected_intent": {
                    "type": "string",
                    "description": "The expected intent based on the current session."
                }
            },
            "required": ["expected_intent"]
        }
    }
]

def create_embedding_with_retry(text, max_retries=5, initial_delay=1, max_delay=60):
    retries = 0
    delay = initial_delay

    while retries < max_retries:
        try:
            embedding = openai.Embedding.create(input=text, model="text-embedding-ada-002")['data'][0]['embedding']
            return embedding
        except openai.error.RateLimitError:
            print(f"Rate limit exceeded. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            retries += 1
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            retries += 1

    raise Exception("Rate limit exceeded and all retries failed.")

def detect_intent(response_text, expected_intent):
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
    query_embedding = create_embedding_with_retry(expected_intent)
    
    # Query Pinecone index
    query_results = index.query(
        vector=query_embedding,
        top_k=2,
        include_values=True,
        include_metadata=True
    )
    
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

def handle_function_call(function_name, arguments):
    if function_name == "detect_intent":
        response_text = arguments.get("response_text")
        expected_intent = arguments.get("expected_intent")
        return detect_intent(response_text, expected_intent)
    elif function_name == "generate_hint":
        expected_intent = arguments.get("expected_intent")
        return generate_hint(expected_intent)
    else:
        return "Function not found."

def process_openai_response(response):
    if response.get("function_call"):
        function_name = response["function_call"]["name"]
        arguments = json.loads(response["function_call"]["arguments"])
        return handle_function_call(function_name, arguments)
    else:
        return response["choices"][0]["message"]["content"]

def generate_response(user_input):
    # Query Pinecone to get the top 5 record messages
    user_embedding = create_embedding_with_retry(user_input)
    pinecone_results = index.query(
        vector=user_embedding,
        top_k=5,
        include_values=True,
        include_metadata=True
    )
    
    # Extract relevant information and functions from Pinecone results
    relevant_info = [result['metadata']['text'] for result in pinecone_results.get('matches', []) if 'text' in result.get('metadata', {})]
    available_functions = [result['metadata']['function'] for result in pinecone_results.get('matches', []) if 'function' in result.get('metadata', {})]
    
    # Generate response using OpenAI's ChatCompletion API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {"role": "user", "content": user_input},
            {"role": "system", "content": f"Relevant information: {relevant_info}"}
        ],
        functions=functions,
        function_call="auto"
    )
    
    return process_openai_response(response)








# import openai
# from dotenv import load_dotenv
# import os
# import numpy as np
# import time

# from pinecone import Pinecone, ServerlessSpec

# load_dotenv()


# # configure client
# pc = Pinecone(api_key= os.getenv('PINECONE_API_KEY'))
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
#         delay = 1

#         while retries < max_retries:
#             try:
#                 # Attempt to create embedding
#                 response = openai.Embedding.create(input=input_text, model=model)
#                 print(f"response: {response}")
#                 return response['data'][0]['embedding']
#             except openai.error.RateLimitError as e:
#                 print(f"Rate limit error: {e}")
#                 print(f"Attempt {retries + 1} of {max_retries}. Retrying in {delay} seconds...")
#                 time.sleep(delay)
#                 retries += 1
#                 delay *= 2

#         raise Exception("Rate limit exceeded and all retries failed.")

#     # Generate embeddings for both response and expected intent
#     response_embedding = create_embedding_with_retry(response_text)
#     expected_embedding = create_embedding_with_retry(expected_intent)

#     print(f"expected_embedding: {expected_embedding}")
#     print(f"response_embedding: {response_embedding}")

#     # Calculate cosine similarity
#     def cosine_similarity(a, b):
#         return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

#     similarity_score = cosine_similarity(response_embedding, expected_embedding)

#     if similarity_score > 0.8:
#         return True, "Great job! You correctly completed the task."
#     else:
#         hint = generate_hint(expected_intent)
#         return False, f"It looks like there's an error. Remember to follow the task instructions. Try again! Here's a hint: {hint}"

# def generate_hint(expected_intent):
#     # Create embedding for the expected intent
#     query_embedding = openai.Embedding.create(input=expected_intent, model="text-embedding-ada-002")['data'][0]['embedding']
#     # Upsert the query embedding to Pinecone with a unique identifier

    
 
#     index.upsert(vectors=[(query_embedding)])


    
#     # Query Pinecone index
#     query_results = index.query(
#         namespace="ns1",
#         vector=query_embedding,
#         top_k=2,
#         include_values=True,
#         include_metadata=True,
#     )
#     print(query_results)
    
#     # Extract relevant information from Pinecone results
#     relevant_info = [result['metadata']['text'] for result in query_results.get('matches', []) if 'text' in result.get('metadata', {})]
    
#     # Generate hint using OpenAI's GPT-3
#     prompt = f"Given the task: '{expected_intent}', and the following relevant information: {relevant_info}, provide a hint to help the user correct their response."
#     response = openai.Completion.create(
#         engine="text-davinci-003",
#         prompt=prompt,
#         max_tokens=100
#     )
    
#     return response.choices[0].text.strip()


