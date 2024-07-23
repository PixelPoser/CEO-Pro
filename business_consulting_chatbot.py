import os
import google.generativeai as genai
from pinecone import Pinecone
import logging
from prompts import *
from openai import OpenAI
from pdf_conversion import convert_to_pdf
import json
from datetime import datetime
from business_interviewer import BusinessInterviewer  # New import

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

def send_message_to_gemini(chat, prompt):
    try:
        log_to_file(f"Sending prompt to Gemini", print_to_console=False)
        response = chat.send_message(prompt, stream=True)
        full_response = ""
        for chunk in response:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_response += chunk.text
        print()  # New line after streaming is complete
        log_to_file(f"Received response from Gemini", print_to_console=False)
        return full_response
    except Exception as e:
        log_to_file(f"Error in send_message_to_gemini: {str(e)}", "ERROR")
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

        # Modified logging statement
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

def process_gemini_prompt(chat, prompt, continuation_prompt, vector_info):
    formatted_prompt = f"""
{prompt}
Please utilize the following lessons and concepts from our business textbook database to assist in your answer:
<database>
{vector_info}
</database>
"""
    log_to_file(f"Formatted prompt sent to Gemini: {formatted_prompt}", "PROMPT", print_to_console=False)
    
    response = send_message_to_gemini(chat, formatted_prompt)
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
        
        continuation = send_message_to_gemini(chat, continuation_prompt)
        full_response += continuation
    
    return full_response

def main():
    log_to_file("Starting CEO-PRO")
    print("Welcome to CEO-PRO!")
    
    conversation_history = ""
    summary = ""
    
    # Check if there's a hardcoded query
    if HARDCODED_QUERY:
        user_input = HARDCODED_QUERY
        log_to_file(f"Using hardcoded query: {user_input}")
        print(f"Using hardcoded query: {user_input}")
    else:
        # Initialize BusinessInterviewer
        interviewer = BusinessInterviewer(GOOGLE_API_KEY)
        user_input = interviewer.conduct_interview()
        log_to_file(f"User input from interview: {user_input[:200]}...")  # Log first 200 characters

    while user_input.lower() != 'exit':
        log_transcript("User", user_input)
        conversation_history += f"User: {user_input}\n\n"

        # Query Pinecone for relevant information
        vector_info = query_pinecone(user_input, summary)
        log_to_file(f"Vector database information retrieved", print_to_console=False)

        # Initialize chat session
        chat = initialize_chat_session()

        # Process with Gemini using PROMPT_1
        gemini_prompt_1 = PROMPT_1.format(user_query=user_input)
        response_1 = process_gemini_prompt(chat, gemini_prompt_1, "continue with your response", vector_info)
        log_to_file(f"Gemini response for PROMPT_1 received", print_to_console=False)
        log_transcript("Assistant", response_1)
        conversation_history += f"Assistant: {response_1}\n\n"

        # Update summary after first exchange
        summary = summarize_conversation(conversation_history)

        # Process with Gemini using PROMPT_2
        vector_info = query_pinecone(PROMPT_2, summary)
        response_2 = process_gemini_prompt(chat, PROMPT_2, "continue with your response", vector_info)
        log_to_file(f"Gemini response for PROMPT_2 received", print_to_console=False)
        log_transcript("Assistant", response_2)
        conversation_history += f"Assistant: {response_2}\n\n"

        # Update summary after PROMPT_2
        summary = summarize_conversation(conversation_history)

        # Process with Gemini using PROMPT_3
        vector_info = query_pinecone(PROMPT_3, summary)
        response_3 = process_gemini_prompt(chat, PROMPT_3, "Continue with evaluations", vector_info)
        log_to_file(f"Gemini response for PROMPT_3 received", print_to_console=False)
        log_transcript("Assistant", response_3)
        conversation_history += f"Assistant: {response_3}\n\n"

        # Update summary after PROMPT_3
        summary = summarize_conversation(conversation_history)

        # Process with Gemini using PROMPT_4
        vector_info = query_pinecone(PROMPT_4, summary)
        response_4 = process_gemini_prompt(chat, PROMPT_4, "continue with your response", vector_info)
        log_to_file(f"Gemini response for PROMPT_4 received", print_to_console=False)
        log_transcript("Assistant", response_4)
        conversation_history += f"Assistant: {response_4}\n\n"

        # Update summary after PROMPT_4
        summary = summarize_conversation(conversation_history)

        # Process with Gemini using PROMPT_5
        vector_info = query_pinecone(PROMPT_5, summary)
        response_5 = process_gemini_prompt(chat, PROMPT_5, "continue with your response", vector_info)
        log_to_file(f"Gemini response for PROMPT_5 received", print_to_console=False)
        log_transcript("Assistant", response_5)
        conversation_history += f"Assistant: {response_5}\n\n"

        # Update summary after PROMPT_5
        summary = summarize_conversation(conversation_history)

        # First round of critique
        vector_info = query_pinecone(CRITIQUE_PROMPT, summary)
        critique_response = process_gemini_prompt(chat, CRITIQUE_PROMPT, "continue with your response", vector_info)
        log_to_file(f"Gemini response for CRITIQUE_PROMPT received", print_to_console=False)
        log_transcript("Assistant", critique_response)
        conversation_history += f"Assistant: {critique_response}\n\n"

        # Update summary after first critique
        summary = summarize_conversation(conversation_history)

        # Second round of critique
        vector_info = query_pinecone(CONTINUE_CRITIQUE_PROMPT, summary)
        second_critique_response = process_gemini_prompt(chat, CONTINUE_CRITIQUE_PROMPT, "continue with your response", vector_info)
        log_to_file(f"Gemini response for CONTINUE_CRITIQUE_PROMPT received", print_to_console=False)
        log_transcript("Assistant", second_critique_response)
        conversation_history += f"Assistant: {second_critique_response}\n\n"

        # Update summary after second critique
        summary = summarize_conversation(conversation_history)

        # Final report generation
        final_report = process_gemini_prompt(chat, REWRITE_PROMPT, "continue with your response", query_pinecone(REWRITE_PROMPT, summary))
        log_to_file(f"Gemini response for REWRITE_PROMPT received", print_to_console=False)
        log_transcript("Assistant", final_report)
        conversation_history += f"Assistant: {final_report}\n\n"
        save_final_report(final_report, "Final_Business_Report.md")

        # Generate implementation plan
        implementation_plan = process_gemini_prompt(chat, IMPLEMENTATION_PROMPT, "continue with your response", query_pinecone(IMPLEMENTATION_PROMPT, summary))
        log_to_file(f"Gemini response for IMPLEMENTATION_PROMPT received", print_to_console=False)
        log_transcript("Assistant", implementation_plan)
        conversation_history += f"Assistant: {implementation_plan}\n\n"
        save_final_report(implementation_plan, "Final_Implementation_Plan.md")

        print("Assistant: Analysis complete. Final reports have been saved to your Downloads folder.")
        log_to_file("Analysis complete. Final reports saved.")

        # Convert final reports and transcript to PDF
        convert_to_pdf(os.path.join(downloads_folder, "Final_Business_Report.md"))
        convert_to_pdf(os.path.join(downloads_folder, "Final_Implementation_Plan.md"))
        
        # Convert conversation transcript to PDF
        with open(transcript_file, 'r') as f:
            transcript_content = f.read()
        
        # Remove metadata from transcript
        cleaned_transcript = '\n'.join([line for line in transcript_content.split('\n') if not line.startswith('[')])
        
        cleaned_transcript_file = os.path.join(downloads_folder, "Cleaned_Conversation_Transcript.md")
        with open(cleaned_transcript_file, 'w') as f:
            f.write(cleaned_transcript)
        
        convert_to_pdf(cleaned_transcript_file)
        
        print("PDFs have been generated for the final reports and conversation transcript.")
        log_to_file("PDFs generated for final reports and conversation transcript.")

        # Check if there's a hardcoded query (for single-run mode)
        if HARDCODED_QUERY:
            break
        else:
            user_input = input("User: ")
            log_to_file(f"User input: {user_input}")

    log_to_file("CEO-Pro session ended")
    print("Thank you for using CEO-Pro!")

if __name__ == "__main__":
    main()
