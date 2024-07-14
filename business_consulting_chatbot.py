import os
import google.generativeai as genai
import anthropic
from pinecone import Pinecone
import logging
from prompts import *
from openai import OpenAI
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up API keys
GOOGLE_API_KEY = ""
ANTHROPIC_API_KEY = ""
PINECONE_API_KEY = "928752cc-c4b5-4d90-98f0-79227c7e37cc"
OPENAI_API_KEY = ""

# Initialize clients
genai.configure(api_key=GOOGLE_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Set up Pinecone index
INDEX_NAME = "corpus-anything-llm-2"
NAMESPACE = "pinecone"
index = pc.Index(INDEX_NAME)

# Hardcoded query option (set to None if you want to use user input)
HARDCODED_QUERY = """
SAMPLE SAMPE SAMPLE:

### GlobalTech Inc.: Escalating Challenges Requiring Strong Leadership

#### Company Overview
GlobalTech Inc. is a prominent multinational technology company excelling in consumer electronics and enterprise solutions. The company has seen significant growth by expanding into emerging markets driven by increased consumer demand and rapid digitalization. However, GlobalTech now faces an array of escalating and multifaceted challenges requiring immediate and strong leadership.

#### Specific Problems and Strategic Complications

1. **Environmental and Regulatory Scrutiny**:
   - **Problem**: The European Union has implemented a new regulation requiring a 50% reduction in carbon emissions for all manufacturing processes within the next two years. Non-compliance could result in fines up to €500 million and a potential ban on selling products in EU markets.
     - **Variable 1**: Key manufacturing partners are already operating at maximum capacity, making rapid changes difficult without significant downtime.
     - **Variable 2**: Competitors have been secretly lobbying for even stricter regulations, aiming to cripple GlobalTech's operations.
     - **Variable 3**: The company's largest European factory is located in a region currently experiencing political instability, further complicating compliance efforts.
     - **Variable 4**: Local environmental groups have threatened to initiate protests and legal actions against GlobalTech, potentially causing disruptions at manufacturing sites.

2. **Technological Advancements and Ethical Concerns**:
   - **Problem**: A major data breach occurred, exposing sensitive customer data and leading to a class-action lawsuit. This has raised ethical concerns regarding data privacy and security practices.
     - **Variable 1**: The breach involved high-profile customers, increasing the risk of significant media coverage and public outrage.
     - **Variable 2**: Internal investigations suggest that the breach may have been an inside job, leading to mistrust among employees and potential further security vulnerabilities.
     - **Variable 3**: The breach has led to an ongoing federal investigation, with the potential for severe legal repercussions and additional fines.
     - **Variable 4**: Several key clients have threatened to terminate contracts, citing loss of trust and security concerns.

3. **Investor and Employee Pressures**:
   - **Problem**: Investors have threatened to withdraw funding due to the perceived negative impact of sustainability initiatives on short-term profitability. Concurrently, employees have organized a walkout demanding greater transparency and involvement in decision-making processes.
     - **Variable 1**: The potential withdrawal of funding comes at a critical time when the company is negotiating a major acquisition.
     - **Variable 2**: The employee walkout is planned to coincide with a major product launch, threatening to disrupt operations and damage the launch's success.
     - **Variable 3**: A group of influential investors has started a campaign to replace the current CEO, citing poor management of the sustainability strategy.
     - **Variable 4**: Several top engineers have resigned in protest, causing delays in key R&D projects and creating talent shortages.

4. **Customer Demands and Competitive Threats**:
   - **Problem**: A major competitor has launched a product line made entirely from recycled materials, capturing significant market share and positioning itself as the leader in eco-friendly technology.
     - **Variable 1**: The competitor's product is also significantly cheaper, appealing to cost-sensitive customers and eroding GlobalTech's market share further.
     - **Variable 2**: The competitor has initiated an aggressive marketing campaign that highlights GlobalTech's perceived environmental shortcomings.
     - **Variable 3**: Customer feedback indicates a growing preference for the competitor's products, with a notable drop in GlobalTech's customer satisfaction ratings.
     - **Variable 4**: Key retailers have begun to prioritize shelf space for the competitor's products, reducing visibility and availability of GlobalTech's offerings.

5. **Economic Climate and Inflation**:
   - **Problem**: High inflation has increased the cost of raw materials by 20%, leading to higher production costs and reduced profit margins.
     - **Variable 1**: Key suppliers are facing financial difficulties, leading to supply chain disruptions and potential shortages of essential materials.
     - **Variable 2**: Inflation is also affecting consumer spending power, reducing overall demand for premium products.
     - **Variable 3**: A recent surge in energy prices has further exacerbated operational costs, impacting the bottom line.
     - **Variable 4**: GlobalTech's debt obligations have become more burdensome with rising interest rates, putting additional financial strain on the company.

6. **Regulatory Compliance**:
   - **Problem**: New regulations in North America mandate that 75% of all components used in manufacturing must be sourced domestically to qualify for government subsidies. Failure to comply could result in the loss of subsidies amounting to $200 million annually.
     - **Variable 1**: Domestic suppliers are struggling to meet the increased demand, leading to delays and potential production halts.
     - **Variable 2**: International suppliers, who are essential for certain specialized components, are threatening to end partnerships due to reduced order volumes.
     - **Variable 3**: The company's current inventory levels are critically low, risking immediate production stoppages.
     - **Variable 4**: Regulatory agencies are conducting surprise inspections, increasing the risk of sudden compliance failures and operational disruptions.

    #### Conclusion

    GlobalTech's leadership team is facing a convergence of severe challenges that require immediate, strong, and decisive action. Each issue is multifaceted and escalating, demanding an integrated and dynamic approach to navigate these turbulent times. The leadership must demonstrate exceptional strategic acumen, agility, and resilience to steer the company through these crises, ensuring long-term sustainability and growth while maintaining stakeholder trust and operational integrity.
   

"""

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
Summarize the following business consultation conversation, focusing on the key concepts, questions, and insights. Give more weight to the most recent exchanges. Capture the evolving context of the discussion while highlighting the core business issues. Ensure it's suitable for use in a vector search to find relevant business information. 

Conversation transcript:
{conversation_history}

Summary:
"""
    try:
        message = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=300,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        logging.info(f"Raw Claude API response: {message}")
        
        if isinstance(message.content, list):
            summary = message.content[0].text if message.content else "Error: Empty response from Claude API"
        elif isinstance(message.content, str):
            summary = message.content
        else:
            summary = f"Error: Unexpected response type from Claude API: {type(message.content)}"
        
        log_to_file(f"Generated conversation summary: {summary[:100]}...", print_to_console=False)
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
Please utilize the following data to assist in your answer:
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
        print("Please enter your business scenario or type 'exit' to quit.")
        user_input = input("User: ")
        log_to_file(f"User input: {user_input}")

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
        response_2 = process_gemini_prompt(chat, PROMPT_2, "continue with your response", query_pinecone(PROMPT_2, summary))
        log_to_file(f"Gemini response for PROMPT_2 received", print_to_console=False)
        log_transcript("Assistant", response_2)
        conversation_history += f"Assistant: {response_2}\n\n"

        # Process with Gemini using PROMPT_3
        response_3 = process_gemini_prompt(chat, PROMPT_3, "Continue with evaluations", query_pinecone(PROMPT_3, summary))
        log_to_file(f"Gemini response for PROMPT_3 received", print_to_console=False)
        log_transcript("Assistant", response_3)
        conversation_history += f"Assistant: {response_3}\n\n"

        # Process with Gemini using PROMPT_4
        response_4 = process_gemini_prompt(chat, PROMPT_4, "continue with your response", query_pinecone(PROMPT_4, summary))
        log_to_file(f"Gemini response for PROMPT_4 received", print_to_console=False)
        log_transcript("Assistant", response_4)
        conversation_history += f"Assistant: {response_4}\n\n"

        # Process with Gemini using PROMPT_5
        response_5 = process_gemini_prompt(chat, PROMPT_5, "continue with your response", query_pinecone(PROMPT_5, summary))
        log_to_file(f"Gemini response for PROMPT_5 received", print_to_console=False)
        log_transcript("Assistant", response_5)
        conversation_history += f"Assistant: {response_5}\n\n"

        # Critique and improvement process
        critique_response = process_gemini_prompt(chat, CRITIQUE_PROMPT, CONTINUE_CRITIQUE_PROMPT, query_pinecone(CRITIQUE_PROMPT, summary))
        log_to_file(f"Gemini response for CRITIQUE_PROMPT received", print_to_console=False)
        log_transcript("Assistant", critique_response)
        conversation_history += f"Assistant: {critique_response}\n\n"

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

        # Update summary for next iteration
        summary = summarize_conversation(conversation_history)

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
