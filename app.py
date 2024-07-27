import os
import google.generativeai as genai
from pinecone import Pinecone
import logging
from prompts import *
from openai import OpenAI
from pdf_conversion import convert_to_pdf
import json
from datetime import datetime
from business_interviewer import BusinessInterviewer
import sys
import asyncio
import websockets
from aiohttp import web
import aiohttp_cors

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up API keys
GOOGLE_API_KEY = ""
PINECONE_API_KEY = ""
OPENAI_API_KEY = ""

# Initialize clients
genai.configure(api_key=GOOGLE_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Set up Pinecone index
INDEX_NAME = "corpus-anything-llm-2"
NAMESPACE = "pinecone"
index = pc.Index(INDEX_NAME)

# Hardcoded query option (set to None if you want to use user input)
HARDCODED_QUERY = None

# Set up logging files
downloads_folder = os.path.expanduser("~/Downloads")
log_file = os.path.join(downloads_folder, f"Business_Chatbot_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
transcript_file = os.path.join(downloads_folder, f"Conversation_Transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Global variable to store the terminal output
terminal_output = []
websocket_connections = set()

async def capture_output(message):
    global terminal_output
    terminal_output.append(message)
    print(message)  # Still print to actual terminal for debugging
    if websocket_connections:
        await asyncio.gather(*[ws.send(json.dumps({'type': 'terminal', 'content': message})) for ws in websocket_connections])

def log_to_file(message, category="INFO", print_to_console=True):
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - {category}: {message}\n\n")
    if print_to_console:
        logging.info(f"{category}: {message}")

def log_transcript(role, message):
    with open(transcript_file, 'a') as f:
        f.write(f"{role}: {message}\n\n")

def generate_embedding(text):
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    except Exception as e:
        log_to_file(f"Error generating embedding: {str(e)}", "ERROR")
        return None

def check_index_empty():
    try:
        stats = index.describe_index_stats()
        return stats['total_vector_count'] == 0
    except Exception as e:
        log_to_file(f"Error checking index stats: {str(e)}", "ERROR")
        return None

def query_pinecone(prompt, summary=""):
    try:
        combined_query = f"{prompt}\n\nContext: {summary}".strip()
        log_to_file(f"Generating embedding for combined query: {combined_query[:100]}...")
        embedding = generate_embedding(combined_query)
        if embedding is None:
            return "Error generating embedding for query"

        if check_index_empty():
            log_to_file("Pinecone index is empty", "WARNING")
            return "Pinecone index is empty"

        log_to_file("Querying Pinecone")
        results = index.query(
            namespace=NAMESPACE,
            vector=embedding,
            top_k=12,
            include_values=True,
            include_metadata=True
        )
        log_to_file("Pinecone query completed", print_to_console=False)

        if not results['matches']:
            log_to_file("No matches found in Pinecone query", "WARNING")
            return "No relevant information found in vector database"

        relevant_info = ""
        for match in results['matches']:
            relevant_info += f"Score: {match['score']}, Text: {match['metadata'].get('text', 'No text available')}\n\n"
        
        return relevant_info
    except Exception as e:
        log_to_file(f"Error querying Pinecone: {str(e)}", "ERROR")
        return f"Error retrieving relevant information: {str(e)}"

def initialize_chat_session():
    model = genai.GenerativeModel('gemini-1.5-pro')
    return model.start_chat(history=[])

async def send_message_to_gemini(chat, prompt):
    try:
        await capture_output("Sending prompt to Gemini")
        response = chat.send_message(prompt, stream=True)
        full_response = ""
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
                # Send each chunk as a separate message
                for websocket in websocket_connections:
                    await websocket.send(json.dumps({'type': 'stream', 'content': chunk.text}))
                await asyncio.sleep(0.05)  # Increased delay for smoother updates
        await capture_output("Received response from Gemini")
        return full_response
    except Exception as e:
        await capture_output(f"Error in send_message_to_gemini: {str(e)}")
        return "Error generating response from Gemini"

def summarize_conversation(conversation_history):
    prompt = f"""
Write a detailed, comprehensive summary of the following business consultation conversation, focusing on the highly specific key concepts regarding the business problem, highly specific business information/metrics, and highly specific questions based on the problem. Do not mention the logic technique strategies like Q* or Monte Carlo as they are irrelevant.  Give more weight to the most recent exchanges. Capture the evolving context of the discussion while highlighting the specific complex business issues. At the end, provide a long list of relevant questions, keywords, and phrases optimized for vector search in my corpus of business textbooks.

Conversation transcript:
{conversation_history}

Summary:
"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        if response.parts:
            summary = response.text
        else:
            summary = "Error: Empty response from Gemini API"

        log_to_file(f"Generated conversation summary: {summary}", print_to_console=False)
        return summary
    except Exception as e:
        error_msg = f"Error in summarize_conversation: {str(e)}"
        log_to_file(error_msg, "ERROR")
        return error_msg

def save_final_report(report, filename):
    file_path = os.path.join(downloads_folder, filename)
    with open(file_path, 'w') as f:
        f.write(report)
    log_to_file(f"Saved report to {file_path}")

async def process_gemini_prompt(chat, prompt, continuation_prompt, vector_info):
    formatted_prompt = f"""
{prompt}
Please utilize the following lessons and concepts from our business textbook database to assist in your answer:
<database>
{vector_info}
</database>
"""
    log_to_file(f"Formatted prompt sent to Gemini: {formatted_prompt}", "PROMPT", print_to_console=False)
    
    response = await send_message_to_gemini(chat, formatted_prompt)
    full_response = response
    
    while True:
        claude_check = summarize_conversation(full_response)
        log_to_file(f"Claude completeness check: {claude_check}", print_to_console=False)
        
        if isinstance(claude_check, str):
            if "NOT DONE" not in claude_check.upper():
                break
        else:
            log_to_file(f"Unexpected type for claude_check: {type(claude_check)}", "WARNING")
            break
        
        continuation = await send_message_to_gemini(chat, continuation_prompt)
        full_response += continuation
    
    return full_response

async def async_main_logic(user_input=None):
    log_to_file("Starting CEO-PRO")
    await capture_output("Welcome to CEO-PRO!")
    
    conversation_history = ""
    summary = ""
    
    if user_input is None:
        if HARDCODED_QUERY:
            user_input = HARDCODED_QUERY
            log_to_file(f"Using hardcoded query: {user_input}")
            await capture_output(f"Using hardcoded query: {user_input}")
        else:
            interviewer = BusinessInterviewer(GOOGLE_API_KEY)
            user_input = interviewer.conduct_interview()
            log_to_file(f"User input from interview: {user_input[:200]}...")  # Log first 200 characters

    full_response = ""
    while user_input.lower() != 'exit':
        log_transcript("User", user_input)
        conversation_history += f"User: {user_input}\n\n"

        vector_info = query_pinecone(user_input, summary)
        log_to_file(f"Vector database information retrieved", print_to_console=False)

        chat = initialize_chat_session()

        for prompt_num, prompt in enumerate([PROMPT_1, PROMPT_2, PROMPT_3, PROMPT_4, PROMPT_5], start=1):
            gemini_prompt = prompt.format(user_query=user_input) if prompt_num == 1 else prompt
            response = await process_gemini_prompt(chat, gemini_prompt, "continue with your response", vector_info)
            log_to_file(f"Gemini response for PROMPT_{prompt_num} received", print_to_console=False)
            log_transcript("Assistant", response)
            conversation_history += f"Assistant: {response}\n\n"
            summary = summarize_conversation(conversation_history)
            vector_info = query_pinecone(prompt, summary)
            full_response += response

        for critique_prompt in [CRITIQUE_PROMPT, CONTINUE_CRITIQUE_PROMPT]:
            vector_info = query_pinecone(critique_prompt, summary)
            critique_response = await process_gemini_prompt(chat, critique_prompt, "continue with your response", vector_info)
            log_to_file(f"Gemini response for {critique_prompt.split()[0]} received", print_to_console=False)
            log_transcript("Assistant", critique_response)
            conversation_history += f"Assistant: {critique_response}\n\n"
            summary = summarize_conversation(conversation_history)
            full_response += critique_response

        final_report = await process_gemini_prompt(chat, REWRITE_PROMPT, "continue with your response", query_pinecone(REWRITE_PROMPT, summary))
        log_to_file(f"Gemini response for REWRITE_PROMPT received", print_to_console=False)
        log_transcript("Assistant", final_report)
        conversation_history += f"Assistant: {final_report}\n\n"
        save_final_report(final_report, "Final_Business_Report.md")
        full_response += final_report

        implementation_plan = await process_gemini_prompt(chat, IMPLEMENTATION_PROMPT, "continue with your response", query_pinecone(IMPLEMENTATION_PROMPT, summary))
        log_to_file(f"Gemini response for IMPLEMENTATION_PROMPT received", print_to_console=False)
        log_transcript("Assistant", implementation_plan)
        conversation_history += f"Assistant: {implementation_plan}\n\n"
        save_final_report(implementation_plan, "Final_Implementation_Plan.md")
        full_response += implementation_plan

        await capture_output("Assistant: Analysis complete. Final reports have been saved to your Downloads folder.")
        log_to_file("Analysis complete. Final reports saved.")

        convert_to_pdf(os.path.join(downloads_folder, "Final_Business_Report.md"))
        convert_to_pdf(os.path.join(downloads_folder, "Final_Implementation_Plan.md"))
        
        with open(transcript_file, 'r') as f:
            transcript_content = f.read()
        
        cleaned_transcript = '\n'.join([line for line in transcript_content.split('\n') if not line.startswith('[')])
        
        cleaned_transcript_file = os.path.join(downloads_folder, "Cleaned_Conversation_Transcript.md")
        with open(cleaned_transcript_file, 'w') as f:
            f.write(cleaned_transcript)
        
        convert_to_pdf(cleaned_transcript_file)
        
        await capture_output("PDFs have been generated for the final reports and conversation transcript.")
        log_to_file("PDFs generated for final reports and conversation transcript.")

        if HARDCODED_QUERY:
            break
        else:
            user_input = input("User: ")
            log_to_file(f"User input: {user_input}")

    log_to_file("CEO-Pro session ended")
    await capture_output("Thank you for using CEO-Pro!")
    return full_response

async def websocket_handler(websocket, path):
    try:
        websocket_connections.add(websocket)
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'message':
                await async_main_logic(data['content'])
                await websocket.send(json.dumps({'type': 'complete'}))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        websocket_connections.remove(websocket)

async def index(request):
    with open('index.html', 'r') as f:
        return web.Response(text=f.read(), content_type='text/html')

async def main():
    app = web.Application()
    app.router.add_get('/', index)
    
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)

    await site.start()

    ws_server = await websockets.serve(websocket_handler, '0.0.0.0', 8765)

    await capture_output("Server started. Open http://localhost:8080 in your browser.")
    await capture_output("For CLI mode, press Ctrl+C and run 'python app.py cli'")
    
    try:
        await asyncio.gather(
            ws_server.wait_closed(),
            asyncio.Future()  # This future never completes, keeping the server running
        )
    finally:
        await runner.cleanup()

interviewer = BusinessInterviewer(GOOGLE_API_KEY)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        asyncio.run(async_main_logic())
    else:
        asyncio.run(main())