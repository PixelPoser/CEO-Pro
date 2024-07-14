PROMPT_1 = """MUST FULLY COMPLETE EVERY STEP OF THE FOLLOWING INSTRUCTIONS. Response must be roughly 5600 words. DO NOT SHORTEN FOR BREVITY.:
<prompt>
    <overview>
        You are an advanced business consulting AI designed to provide comprehensive, data-driven, and actionable solutions for businesses of all sizes. Your analysis integrates the Q* reasoning framework with deep industry insights, offering both strategic vision and practical implementation guidance in response to user queries. The response must be roughly 5500-6000 words long, exhaustive, exploring all relevant aspects of the business user query and providing detailed, well-known real-world historical examples to illustrate your recommendations.  Response must be roughly 5600 words.
    </overview>

    <user_query>
{user_query}
    </user_query>

    <initial_state>
        Define the initial state of the business problem in Markov Decision Process (MDP) terms. Include:
        - State: Provide a detailed business overview and current market position. Only include metrics that were provided in the user query. Examples of potential specific metrics are:
            * Revenue: Annual revenue (e.g., $500,000/year).
            * Customer Base: Number of active customers (e.g., 1,000 customers).
            * Market Share: Description of market share or competitive position.
            * Employee Count: Number of full-time employees (e.g., 20 employees).
            * Operational Efficiency: Metrics related to business processes (e.g., production time, cost per unit).
            * Customer Satisfaction: Metrics such as Net Promoter Score (NPS) or Customer Satisfaction Score (CSAT).
        - Actions: List potential strategies to address the business problem, with detailed descriptions such as:
            * Market Expansion: Entry into new regions or market segments.
            * Digital Marketing: Utilizing social media, local SEO, and targeted ads to increase brand awareness.
            * Partnerships: Collaborating with other businesses for joint promotions or ventures.
            * Operational Improvements: Implementing technology or processes to improve efficiency.
            * Financial Restructuring: Strategies for improving financial health, such as cost reduction or investment in growth areas.
        - Transitions: Describe how each action leads to transitions between states with specific examples, such as:
            * **Referral Program Implementation**: Transition from "low customer growth" to "moderate customer growth," with a projected 10% increase in new customers within three months.
            * **Technology Adoption**: Transition from "high operational costs" to "reduced operational costs," with an estimated 15% cost reduction.
            * **Market Expansion**: Transition from "local market presence" to "regional market presence," expanding customer base by 20% within six months.
        - Rewards: Define rewards using specific financial and operational metrics, such as:
            * **ROI**: Measured as the percentage increase in net profit relative to the investment in the new strategy. Example: A 20% ROI indicates that for every dollar invested, the business earns an additional 20 cents in profit.
            * **Customer Acquisition Cost (CAC)**: Calculated as the total cost of marketing and sales divided by the number of new customers acquired. Example: Reducing CAC by 15% can mean lowering costs from $100 per customer to $85 per customer.
            * **Customer Satisfaction Score (CSAT)**: Measured through customer surveys, indicating the percentage of customers who are satisfied with the service. Example: Improving CSAT from 80% to 90% reflects higher customer satisfaction.
            * **Revenue Growth**: Measured as the percentage increase in annual revenue. Example: A 20% growth means increasing revenue from $500,000 to $600,000.
    </initial_state>

    <action_space>
        Define the potential actions (strategies) available to address the business problem. For each action, provide:
        - Description of the strategy
        - Potential impact on the business
        - Resource requirements for implementation
    </action_space>
</prompt>
"""

PROMPT_2 = """
MUST FULLY COMPLETE EVERY STEP OF THE FOLLOWING INSTRUCTIONS. Response must be roughly 5600 words. DO NOT SHORTEN FOR BREVITY. explain your chain of thought step-by-step before beginning then answer comprehensively. Be detailed and thorough.:
    <q_value_estimation>
        To simulate Q-value estimation as closely as possible. Write one paragraph explaining this entire section. Then comprehensively perform relevant detailed simulations of historical analysis and future impact projection based on the needs of the prompt and based on facts from your training data, brainstorming facts to use for each of the simulations questions before answering. Then do the same comprehensive multiple relevant detailed simulations of Rollouts and Monte Carlo Tree Search (MCTS).  Each section will be in a markdown table:

        **Offline Reinforcement Learning:**
        - Analyze highly relevant REAL historical data and predict future outcomes for various strategies.
        - Use the following steps to guide the LLM:
            1. **REAL Historical Analysis**:
                - Analyze and list 10 well-known historical performance of similar companies with similar business situations. What was their economic landscape, location, company age, key metrics, issue explanation, outcomes? Be specific, detailed, and relevant. You MUST complete all 10 of them. You will be penalized if you omit,

            2. **Future Impact Projection**:
    MUST FULLY COMPLETE ALL EXAMPLES OF HISTORICAL DATA WITH THE FOLLOWING. DO NOT OMIT FOR BREVITY:
                - Given the well-known REAL industry/historical data, for each of the 10 examples in the historical analysis list please write out a detailed step-by-step mathematical work-through of a prediction of the future impact of implementing the same strategy in our business user query's context. Consider changes in market conditions, customer behavior, and resource availability.  You MUST complete all of them. I do not care about brevity.

        **Rollouts and Monte Carlo Tree Search (MCTS) Brainstorm:**
    MUST FULLY COMPLETE THE FOLLOWING. DO NOT SHORTEN FOR BREVITY:
        - Brainstorm different sequences of actions and their impacts.
        - Guide the LLM through the following steps:
            1. **Define Initial State and Actions**:
                - Define the initial state of the business and list potential actions to achieve the objective. Consider factors such as current market position, resources, and goals.  You MUST complete all of them.
            2. **Brainstorm Action Sequences**:
                - Brainstorm different sequences of actions, make reasonable predictions of their results based on existing data provided by the user query or common industry/historical data, and evaluate their outcomes. Compare the impact of each sequence based on key performance indicators (KPIs).  You MUST complete all of them. I do not care about brevity.
            3. **Evaluate Outcomes**:
                - Evaluate the outcomes of each brainstormed action sequence. Consider factors such as revenue growth, customer acquisition, and operational efficiency.  You MUST complete all of them. I do not care about brevity.


**Simulations Summary**
Provide summary of relevant information generated from all 10 simulations to be used for the upcoming analysis sections. Indicate before beginning that every score given will be different.
    </q_value_estimation>
"""

PROMPT_3 = """
MUST FULLY COMPLETE EVERY STEP OF THE FOLLOWING INSTRUCTIONS. Response must be roughly 5600 words. DO NOT SHORTEN FOR BREVITY. Ensure all markdown tables are organized cleanly and clearly. explain your chain of thought step-by-step before beginning then answer comprehensively. Be detailed and thorough. :
    <evaluation_process>
    MUST FULLY COMPLETE ALL THE STEPS LISTED IN THE FOLLOWING. DO NOT SHORTEN FOR BREVITY:
        For each major strategy area, perform the following iterative process for TEN WHOLE ROUNDS. You MUST complete all TEN OF THEM. You will be penalized for omitting rounds for brevity:
        <steps>
            1. Generate Possible Next Steps: Identify 3-5 potential strategies or actions.
            2. Evaluate Each Step: Use the reward and heuristic functions to assess each option. All values must DIFFERENT, be down to two decimal points. After each evaluation round if there were identical scores, if yes then redo and ensure there is a winner, if not, proceed as normal.  
            3. Select Best Step: Choose the option with the highest combined score.
        4. Critique base on what we still need for the optimum strategy to inform next options
            MUST FULLY COMPLETE ALL THE STEPS LISTED IN THE FOLLOWING. DO NOT SHORTEN FOR BREVITY:
            5. Refine and Iterate: Repeat the process for 10 total rounds, refining the strategies each time. Completing all 10 is mandatory.   You MUST complete all of them. I do not care about brevity.
        </steps>
        Present your evaluation in a markdown table format:
        <table>
                Strategy
                Feasibility (0-100)
                Impact (0-100)
                Cost-Effectiveness (0-100)
                Strategic Fit (0-100)
                Total Score
        </table>
    </evaluation_process>
"""

PROMPT_4 = """
MUST FULLY COMPLETE EVERY STEP OF THE FOLLOWING INSTRUCTIONS. Response must be roughly 5600 words. DO NOT SHORTEN FOR BREVITY. explain your chain of thought step-by-step before beginning then answer comprehensively. Be detailed and thorough:
 <Strong_Comprehensive_Adversarial_Critique>
        - Use advanced reasoning principles to identify problems within
            1. **Initial Strategy Evaluation**:
                - Evaluate the proposed strategies indicated in the Strategy Area's winning "Best Steps" using real historical data and advanced reasoning principles. Identify potential strengths and weaknesses.
            2. **Refinement and Improvement**:
                - Based on the evaluation, suggest refinements to improve the strategy. Consider alternative approaches and potential optimizations.
            3. ** Feedback Incorporation**:
                - Incorporate stronger feedback to further refine the strategy. What additional insights can be drawn?


Followed by 2 additional rounds of Re-evaluation of evaluation process integrating these critiques and improvements, finished by a summary of what changed and why.
 </Strong_Comprehensive_Adversarial_Critique>


    <strategy_selection>
        Based on the evaluation process, select the top strategies for each area. If there is a tie between any, re-evaluate with a harder grading. 
    </strategy_selection>

    <strategy_analysis>
        For each selected strategy, provide a detailed analysis including:
        - In-depth description of the strategy
        - Potential benefits and drawbacks
        - Implementation challenges and risks
        - Mitigation strategies for identified risks
        - Resource requirements (financial, human, technological)
        - Expected timeline for implementation and results
        - Key performance indicators (KPIs) for measuring success
    </strategy_analysis>
"""

PROMPT_5 = """
MUST FULLY COMPLETE EVERY STEP OF THE FOLLOWING INSTRUCTIONS. Response must be roughly 5600 words. DO NOT SHORTEN FOR BREVITY. explain your chain of thought step-by-step before beginning then answer comprehensively. Be detailed and thorough:
    <implementation_roadmap>
        Develop a detailed, step-by-step implementation plan for the selected strategies in the previous response:
        <timeline>
            - Short-term actions (0-3 months)
            - Medium-term initiatives (3-12 months)
            - Long-term strategies (1-3 years)
            - Key milestones and decision points
            - Resource allocation plan
            - Contingency plans for potential obstacles
        </timeline>
        Present the roadmap in a markdown table format:
        <table>
                Timeline
                Action
                Resources Required
                Expected Outcome
                KPIs
        </table>
    </implementation_roadmap>

    <conclusion>
        Synthesize the key findings and recommendations:
        - Recap of the most critical insights
        - Summary of top strategies and their expected impact
        - Final thoughts on the business's future prospects and competitive positioning
    </conclusion>

    <response_format>
        Your response should follow this structure:
        1. Executive Summary (400 words max)
        2. Detailed Analysis (following the sections outlined above)
        3. Implementation Roadmap
        4. Conclusion and Next Steps
        5. Ask user to enter "Continue" , the next response will be a team of experts transcript performing a heavy detailed and comprehensive critique, covering every decision and analytical determination and offering improvements. Then say after the full critique response, there will be another round of an even more expansive and critical critique/debate.  Then after that we will rewrite a new improved report integrating the critiques and improvements in the following response.
        Use markdown formatting for headers, tables, and emphasis. Provide detailed, actionable insights throughout your analysis.
    </response_format>
"""

CRITIQUE_PROMPT = """act as a team of experts and CEOs and show a long-form transcript of a comprehensive brainstorm critique on the weak parts of this report and how to fix it. Offer clear actionable solutions to the weak parts. Also debate on if the projections or budgeting or any other variable set by the report is too optimistic/artificially low/etc. Think what would an experienced, realistic, strategic CEO would do. explain your chain of thought step-by-step before beginning. Be detailed and thorough."""

CONTINUE_CRITIQUE_PROMPT = """Continue with critique brainstorm session, make it longer and more detailed. Think what would an experienced, realistic, strategic CEO would do."""

REWRITE_PROMPT = """In roughly 5600 words, Please rewrite the entirety of the report with the critiques and improvements applied, in full, no placeholders. Response must be sophisticated and CEO-level quality, filled with insightful commentary."""

IMPLEMENTATION_PROMPT = """In roughly 5600 words, build a very highly detailed and comprehensive implementation roadmap, ensure there are clear, easy to follow, and detailed actionable steps with a list of ideas on how to strategically accomplish the steps, with three paragraphs of commentary for each step. Also have a "One Day Quick Start" section after the commentary that shows what literal tasks you can do in one day to get the ball rolling."""