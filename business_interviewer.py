import google.generativeai as genai
from typing import Dict, Any
import json

class BusinessInterviewer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.chat = self.model.start_chat(history=[])
        self.business_info: Dict[str, Any] = {}

    def conduct_interview(self) -> str:
        print("Welcome to CEO-Pro!")
        print("I'm here to gather information about your business and help provide valuable insights.")
        print("Would you like to provide a detailed query upfront or go through a guided interview process?")
        choice = input("Enter 'query' for upfront query or 'interview' for guided process: ").lower()

        if choice == 'query':
            return self.handle_upfront_query()
        elif choice == 'interview':
            return self.guided_interview()
        else:
            print("Invalid choice. Proceeding with guided interview.")
            return self.guided_interview()

    def handle_upfront_query(self) -> str:
        query = input("Please provide your detailed business query or scenario: ")
        return self.process_query(query)

    def guided_interview(self) -> str:
        interview_sections = [
            self.company_overview,
            self.market_position,
            self.financial_health,
            self.operational_information,
            self.human_resources,
            self.technology_and_innovation,
            self.regulatory_environment,
            self.current_challenges,
            self.growth_plans,
            self.customer_insights,
            self.sustainability,
            self.competitive_landscape
        ]

        for section in interview_sections:
            section()

        return self.summarize_and_process()

    def ask_question(self, question: str) -> str:
        return input(f"{question}: ")

    def company_overview(self):
        print("\nLet's start with an overview of your company.")
        self.business_info['company_name'] = self.ask_question("What is your company's name?")
        self.business_info['industry'] = self.ask_question("What industry are you in?")
        self.business_info['years_in_operation'] = self.ask_question("How many years has your company been operating?")
        self.business_info['employee_count'] = self.ask_question("Approximately how many employees do you have?")
        self.business_info['annual_revenue'] = self.ask_question("What is your approximate annual revenue?")
        self.business_info['geographical_presence'] = self.ask_question("Describe your geographical presence (local, national, international)")

    def market_position(self):
        print("\nNow, let's discuss your market position.")
        self.business_info['market_share'] = self.ask_question("What is your estimated market share?")
        self.business_info['main_competitors'] = self.ask_question("Who are your main competitors?")
        self.business_info['unique_selling_proposition'] = self.ask_question("What is your unique selling proposition?")
        self.business_info['target_customers'] = self.ask_question("Describe your target customer segments")

    def financial_health(self):
        print("\nLet's talk about your company's financial health.")
        self.business_info['profit_margins'] = self.ask_question("What are your current profit margins?")
        self.business_info['debt_to_equity_ratio'] = self.ask_question("What is your company's debt-to-equity ratio?")
        self.business_info['cash_flow_status'] = self.ask_question("How would you describe your current cash flow status?")
        self.business_info['recent_financial_trends'] = self.ask_question("What are the recent financial trends in your business?")

    def operational_information(self):
        print("\nNow, let's discuss your operational information.")
        self.business_info['key_products_services'] = self.ask_question("What are your key products or services?")
        self.business_info['supply_chain_overview'] = self.ask_question("Can you provide a brief overview of your supply chain?")
        self.business_info['operational_challenges'] = self.ask_question("What are your major operational challenges?")
        self.business_info['recent_operational_changes'] = self.ask_question("Have there been any recent or planned major changes in operations?")

    def human_resources(self):
        print("\nLet's talk about your human resources.")
        self.business_info['employee_satisfaction'] = self.ask_question("How would you rate your employee satisfaction levels?")
        self.business_info['turnover_rate'] = self.ask_question("What is your current employee turnover rate?")
        self.business_info['key_skills_gaps'] = self.ask_question("Are there any key skills or talent gaps in your organization?")
        self.business_info['organizational_structure'] = self.ask_question("Can you briefly describe your organizational structure?")

    def technology_and_innovation(self):
        print("\nLet's discuss technology and innovation in your company.")
        self.business_info['tech_adoption_state'] = self.ask_question("How would you describe your current state of technology adoption?")
        self.business_info['rd_initiatives'] = self.ask_question("What are your current R&D initiatives?")
        self.business_info['innovation_pipeline'] = self.ask_question("Can you describe your innovation pipeline?")

    def regulatory_environment(self):
        print("\nNow, let's talk about your regulatory environment.")
        self.business_info['key_regulations'] = self.ask_question("What are the key regulations affecting your business?")
        self.business_info['compliance_challenges'] = self.ask_question("What are your main compliance challenges?")
        self.business_info['upcoming_regulatory_changes'] = self.ask_question("Are there any upcoming regulatory changes that concern you?")

    def current_challenges(self):
        print("\nLet's discuss your current business challenges.")
        self.business_info['immediate_issues'] = self.ask_question("What are your most pressing immediate issues?")
        self.business_info['long_term_concerns'] = self.ask_question("What are your long-term strategic concerns?")
        self.business_info['advice_needed'] = self.ask_question("In which specific areas do you need advice?")

    def growth_plans(self):
        print("\nLet's talk about your growth and expansion plans.")
        self.business_info['current_growth_strategies'] = self.ask_question("What are your current growth strategies?")
        self.business_info['potential_new_markets'] = self.ask_question("Are there any potential new markets or products you're considering?")
        self.business_info['ma_plans'] = self.ask_question("Do you have any merger or acquisition plans?")

    def customer_insights(self):
        print("\nNow, let's discuss your customer insights.")
        self.business_info['customer_satisfaction'] = self.ask_question("What are your current customer satisfaction metrics?")
        self.business_info['churn_rate'] = self.ask_question("What is your customer churn rate?")
        self.business_info['acquisition_costs'] = self.ask_question("What are your customer acquisition costs?")
        self.business_info['customer_lifetime_value'] = self.ask_question("What is the average lifetime value of your customers?")

    def sustainability(self):
        print("\nLet's talk about sustainability and corporate social responsibility.")
        self.business_info['sustainability_initiatives'] = self.ask_question("What are your current sustainability initiatives?")
        self.business_info['esg_goals'] = self.ask_question("What are your ESG (Environmental, Social, Governance) goals?")
        self.business_info['community_engagement'] = self.ask_question("How does your company engage with the community?")

    def competitive_landscape(self):
        print("\nFinally, let's discuss your competitive landscape.")
        self.business_info['recent_competitive_changes'] = self.ask_question("What recent changes have you observed in your competitive environment?")
        self.business_info['emerging_threats'] = self.ask_question("Are there any emerging threats or opportunities in your industry?")
        self.business_info['industry_leaders'] = self.ask_question("How do you benchmark against industry leaders?")

    def summarize_and_process(self) -> str:
        print("\nThank you for providing that information. Let me summarize what I've gathered:")
        
        summary_prompt = f"""
        Summarize the following business information in a clear, concise manner. Highlight key points and any areas that might need further clarification:

        {json.dumps(self.business_info, indent=2)}

        Provide the summary in a user-friendly format.
        """
        
        summary = self.chat.send_message(summary_prompt).text
        print(summary)
        
        confirmation = input("\nIs this summary accurate? (yes/no): ").lower()
        if confirmation != 'yes':
            print("I apologize for any inaccuracies. Let's go through the information again to make corrections.")
            return self.guided_interview()
        
        return self.process_query(json.dumps(self.business_info, indent=2))

    def process_query(self, query: str) -> str:
        intro_conversation_prompt = f"""
        You are an AI business consultant tasked with analyzing the following business information or query:

        {query}

        Based on this information, create a comprehensive and detailed business scenario that can be used as input for a sophisticated business analysis system. The scenario should:

        1. Capture all relevant details provided in the query or gathered information.
        2. Fill in any gaps with reasonable assumptions based on industry norms and best practices.
        3. Present a clear picture of the business's current state, challenges, and goals.
        4. Focus on the stated problem.
        5. Be written in a narrative format that a CEO or high-level executive would provide when seeking consulting services.
        6. Be approximately 500-800 words long.

        Your output will be used as the input for further in-depth analysis, so ensure it's thorough and well-structured.
        """

        response = self.chat.send_message(intro_conversation_prompt)
        processed_query = response.text

        print("\nBased on our conversation, I've prepared a detailed business scenario for analysis.")
        print("Here's a summary of what will be used for the in-depth consultation:")
        print(processed_query[:200] + "..." if len(processed_query) > 200 else processed_query)
        print("\nProceeding with the full analysis based on this information.")

        return processed_query

