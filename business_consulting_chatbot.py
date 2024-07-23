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
HARDCODED_QUERY = """ ### Business Scenario: Financial Crisis and Operational Overhaul for Industrial Solutions Inc.

**Company Overview:**

**Name:** Industrial Solutions Inc.  
**Industry:** Manufacturing  
**Location:** Midwest, USA  
**Founded:** 1985  
**Revenue:** $1.2 billion annually  
**Employees:** 4,500  
**Product Lines:** Heavy machinery for construction, agricultural equipment, and industrial tools  
**Market Share:** 10% in heavy machinery, 8% in agricultural equipment, 5% in industrial tools  
**Competitors:** Global Manufacturing Corp, Tech Tools Ltd., Agritech Solutions  

**Financial Situation:**

**Revenue:** $1.2 billion (down from $1.5 billion in the previous fiscal year)  
**Net Income:** -$50 million (loss)  
**Operating Margin:** -4.2%  
**Debt:** $400 million  
**Cash Reserves:** $50 million  
**Current Ratio:** 0.85 (indicating liquidity issues)  
**Stock Price:** $18 per share (down from $30 per share a year ago)

### Scenario: Severe Financial Crisis and Operational Inefficiencies

**Problem Statement:**

Industrial Solutions Inc. is at a critical juncture, facing two primary challenges that threaten its survival: a severe financial crisis and significant operational inefficiencies.

### Core Issues:

1. **Severe Financial Crisis:**

   - **Declining Revenue:** The company's revenue has dropped by 20% over the last fiscal year, primarily due to intensified competition and a loss of market share across all product lines. This sharp decline has severely impacted the bottom line, resulting in a net loss of $50 million.
   
   - **High Debt Burden:** Industrial Solutions Inc. is saddled with $400 million in debt. The interest payments on this debt are exerting immense pressure on the company's cash flow, limiting its ability to invest in necessary improvements or respond to market changes effectively.
   
   - **Liquidity Issues:** With cash reserves dwindling to $50 million and a current ratio of 0.85, the company is facing significant liquidity risks. The low current ratio indicates that Industrial Solutions Inc. may not be able to meet its short-term financial obligations, raising concerns about potential insolvency.

2. **Operational Inefficiencies:**

   - **Outdated Manufacturing Processes:** The company's manufacturing processes are outdated, leading to higher production costs, longer lead times, and reduced competitiveness. These inefficiencies are exacerbating the financial strain by increasing operational expenses and reducing profit margins.
   
   - **Supply Chain Disruptions:** Frequent disruptions in the supply chain have led to delays in production and delivery, further eroding customer confidence and satisfaction. The lack of a resilient and efficient supply chain is contributing to the operational bottlenecks and inefficiencies.

### Strategic Questions:

1. **Revenue and Market Position:**
   - What are the underlying reasons for the sharp decline in revenue, and how can the company address these issues to regain market share and stabilize revenue streams?

2. **Debt Management and Liquidity:**
   - How can Industrial Solutions Inc. manage its substantial debt burden while improving liquidity to ensure it can meet short-term obligations and avoid insolvency?

3. **Operational Overhaul:**
   - What specific changes are needed in the manufacturing processes to reduce costs and improve efficiency, and how can these changes be implemented without significant disruptions?

4. **Supply Chain Resilience:**
   - What steps can be taken to build a more resilient supply chain that can withstand disruptions and ensure timely production and delivery?

### Desired Outcomes:

- **Stabilized Revenue:** Achieve revenue stabilization and reverse the declining trend by addressing market share loss and improving sales performance.
- **Debt Reduction:** Implement strategies to manage and reduce the debt burden, alleviating financial pressure and improving cash flow.
- **Enhanced Liquidity:** Improve the current ratio to ensure the company can meet its short-term financial obligations and mitigate the risk of insolvency.
- **Operational Efficiency:** Streamline manufacturing processes to reduce costs, shorten lead times, and enhance overall operational efficiency.
- **Supply Chain Robustness:** Develop a resilient supply chain that minimizes disruptions and supports consistent production and delivery.

This scenario highlights the urgent need for Industrial Solutions Inc. to address its severe financial crisis and overhaul its operational inefficiencies. The company's survival depends on effectively managing these critical challenges to restore financial stability and operational excellence."""

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
    log_to_file("Starting Business Consulting AI Chatbot")
    print("Welcome to the Business Consulting AI Chatbot!")
    
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

    log_to_file("Business Consulting AI Chatbot session ended")
    print("Thank you for using the Business Consulting AI Chatbot!")

if __name__ == "__main__":
    main()