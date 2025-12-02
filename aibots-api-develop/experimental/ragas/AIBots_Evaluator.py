import streamlit as st
import asyncio
import numpy as np

from src.RAG.LLM_Stack import AIBots
from src.evaluator.pipeline import Evaluator
from src.utils.utils import remove_short_prompts, check_all_var
from src.evaluator.recommendation import recommend
from src.utils.knowledge_base import KnowledgeBase
from src.utils.saved_data import FileLister
from datetime import datetime

async def st_evaluate():
    ## Initialize
    # region <--------- Streamlit App Header --------->
    st.title('AI Bots Evaluator')
    # endregion <--------- Streamlit App Header --------->
    # Display disclaimer message (Edit where necessary)
    st.warning("""**Please read the following before proceeding:**
               
• This application is currently in **Beta version** and supports data classified up to **Restricted and Sensitive (Normal)**. 

• This application is under active testing and your activites will be logged to improve your experience.

• By using this application, you acknowledge that you recognise the possibility of AI generating inaccurate or wrong responses, and you take full responsibility over how you use the generated output.""")
    # Display information section
    with st.expander("**HOW TO USE**", False):
        # EDIT DESCRIPTION
        st.info("""The purpose of this page is to evalute your AI Bots. 
                Ensure that you have set up your bot: https://aibots.data.tech.gov.sg/manage . 
                Enter your bot name into the field below. 
                Subsequently enter your test prompts into the AI Bot, each prompt seaprated by a line break.
                Please ensure that these test prompts are reflective of both your documents and the intention of the bot.""")
    st.info("""All you have to do is enter your bot name and questions you would ask. No need ground truth (expected answers) but that can be helpful.
You will receive scorings of how relevant things are and extracted text from the knowledge base.
The elements that are evaluated are:
1) Question entered by user
2) Context – what is extracted from knowledge base through RAG/semantic search/shortlisting
3) Response – what is returned by GPT
4) Ground truth – Supplied by user who is testing this. Optional, as ground truth is not always available.

What the scores mean:
1.	Context Relevancy: Whether the context is relevant to the question.
2.	Faithfulness: Evaluating if the response is related to the context.
3.	Answer Relevancy: How relevant the response is to the question.
4.	Response Correctness: If the ground truth corresponds to the response.""")
    # endregion <--------- Streamlit App Header --------->
    example_bot = st.selectbox(
        "**[Do not use] [For demo purposes only]** You may select an example bot as an example on how to utilize this tool.", 
        ("", "RAG Info bot", "About AIBots", "[Demo] Example Bot on RAG")
        )

    st.divider()
    
    bot_name = st.text_input("**Enter your bot name here.**", key="bot_name", value = example_bot)
    if example_bot == "RAG Info bot":
        example_q = "What is RAG?\nWhat is a LLM?"
        example_a = "RAG is retrieval augmented generation.\nLLM is a large language model."
    elif example_bot == "[Demo] Example Bot on RAG":
        example_q = "What is RAG?\nWhat is the step by step process for RAG?"
        example_a = "Retrieval-Augmented Generation (RAG) is the process of optimizing the output of a large language model, so it references an authoritative knowledge base outside of its training data sources before generating a response.\nGo to the Together website using your web browser. Sign up for an account if yo are new or log in with your existing credentials. Once logged in, find and access the API section within the website. Look for an option to generate an API key, usually through a button or a form. Follow the on-screen instructions to generate the API key, which might involve providing usage details or agreeing to terms. After generating the API key, it will be displayed on the screen. Copy it and securely store it. Set the API key as an environment variable in your code."
    elif example_bot == "About AIBots":
        example_q ="What is AIBots\nWhat is the difference between AIBots and Pair Chat?"
        example_a = ""
    else:
        example_q =""
        example_a = ""
    st.info("Instructions: Firstly, select how many times you would like a response to be generated. Note that if you select more than one, it may up to an hour to process. In the left text box, enter your test prompts for the AI bot to test. Each instruction separated by a line break or enter. [Optional] In the right text box, enter the ground truth reponse for each test prompt. Each ground truth should be separated by a line break or enter, and its order corresponds to each test prompt. If you choose not to enter, you must acknowledge that all information in your documents is accurate. ")
    n_loops = st.selectbox("Number of times you would like a response to be generated per prompt.", [1, 3, 5])
    
    col1, col2= st.columns(2)
    with col1:
        questions = st.text_area("[Mandatory] Test Prompts (in 3 or more words):", height= 500, key="question", value = example_q)
    with col2:
        ground_truth = st.text_area("[Optional] Ground truth response:", height= 500, key="ground_truth", value = example_a)
    submit_button = st.button(label='Submit')

    # Boto3 s3
    filelister = FileLister( 
        "dev-ai-bots-eval",
        f"data/{bot_name}.json",
        #local = True
        )
    
    if submit_button:
        if check_all_var() == 1:
            if bot_name:
                aibot = AIBots(bot_name)
                await aibot.get_bot_id()
                if aibot.bot_id == None:
                    st.warning("Ensure that you have entered the correct bot name or try again later.")
                elif aibot.bot_id ==";;;Duplicated;;;":
                    st.warning("Cannot process duplicated bot names. Change your bot name and try again.")
                else:
                    with st.spinner('Processing, it may take up to 3 minutes per prompt provided (do not close your browser)...'):
                        # Initialize evaluator
                        evaluator = Evaluator()

                        kb = KnowledgeBase(aibot.bot_id)
                        last_update_date = await kb.get_latest_date()

                        result_dict = filelister.read_json()

                        # Split question into line breaks
                        question_list = questions.split("\n")
                        question_list = [q for q in question_list if (len(q)>0)] # Check for accidental enters and double spaces

                        run_pipeline = True
                        if len(ground_truth)>0:
                            ground_truth_list = ground_truth.split("\n")
                            ground_truth_list = [q for q in ground_truth_list if (len(q)>0)] # Check for accidental enters and double spaces

                            if len(ground_truth_list) != len(question_list):
                                st.warning("You must enter the same number of test prompts and ground truth answers.")
                                run_pipeline = False
                        else:
                            ground_truth_list = [None]*len(question_list)

                        # Start looping across questions
                        if run_pipeline:
                            f_scores = []
                            a_scores = []
                            c_scores = []
                            a_corrs = [] 

                            ## For more than 1 runs                
                            if n_loops > 1:
                                for n, question in enumerate(question_list):

                                    current_ground_truth = ground_truth_list[n]
                                    if remove_short_prompts(question):
                                        loop_f_score = 0
                                        loop_a_score = 0
                                        loop_c_score = 0
                                        loop_a_corr = 0
                                        # For each loop
                                        for _ in range(n_loops):
                                            response = await aibot.chat(question)
                                            context, answer = aibot.get_context_ans(response)
                                            f_score, a_score, c_score, a_corr, _ = await evaluator.run_pipeline(question, answer, context, ground_truth = current_ground_truth)
                                            loop_f_score += f_score
                                            loop_a_score += a_score
                                            loop_c_score += c_score

                                            # Check if answer is stored
                                            if (current_ground_truth!=None) and (len(current_ground_truth)>0):
                                                loop_a_corr += a_corr
                                        f_scores.append(loop_f_score/n_loops)
                                        a_scores.append(loop_a_score/n_loops)
                                        c_scores.append(loop_c_score/n_loops)
                                        if (current_ground_truth!=None) and (len(current_ground_truth)>0):
                                            a_corrs.append(loop_a_corr/n_loops)
                                    else:
                                        st.warning(f"The following prompt is too short: {question}")

                            else:
                                saved_answers = []
                                saved_context = []
                                saved_ground_truth = []
                                faith_breakdowns = []
                                con_rel_breakdowns = []
                                ans_rel_breakdowns = []
                                ans_corr_breakdowns = []

                                for n, question in enumerate(question_list):
                                    use_past_data = False
                                    current_ground_truth = ground_truth_list[n]

                                    if remove_short_prompts(question):
                                        # Check if we are using past data
                                        if (current_ground_truth!=None) and  (len(current_ground_truth)>0):
                                            if (result_dict["update_timestamp"].replace("T", " ") > last_update_date) and (any(d.get("question") == question for d in result_dict["content"])) and (any(d.get("ground_truth") == current_ground_truth for d in result_dict["content"])):
                                                use_past_data = True     
                                        else:
                                            if (result_dict["update_timestamp"].replace("T", " ") > last_update_date) and (any(d.get("question") == question for d in result_dict["content"])):
                                                use_past_data = True

                                        if use_past_data:
                                            # Retrieve the results from the last run if there is no update from the bot and you can get the same question from the last run
                                            print("Retrieve past data...")
                                            data = next(item for item in result_dict["content"] if item["question"] == question)
                                            context = data["context"]
                                            answer =data["answer"]
                                            f_score =data["faithfulness"]
                                            a_score =data["answer relevance"]
                                            c_score =data["context relevance"]
                                            faith_breakdown = data["faith_breakdowns"]
                                            con_rel_breakdown = data["con_rel_breakdowns"]
                                            ans_rel_breakdown = data["ans_rel_breakdowns"]

                                            if current_ground_truth:
                                                a_corr = data["answer correctness"]
                                                ans_corr_breakdown = data["answer_correctness_breakdown"]
                                            
                                        else:
                                            # Perform RAG and analysis if either the bot is updated from the last run or there is same question in the past run
                                            print("Started RAG...")
                                            response = await aibot.chat(question)
                                            context, answer = aibot.get_context_ans(response)
                                            
                                            print("Started Evaluation")
                                            f_score, a_score, c_score, a_corr, breakdowns = await evaluator.run_pipeline(question, answer, context, ground_truth = current_ground_truth)

                                            faith_breakdown = breakdowns[0]
                                            con_rel_breakdown = breakdowns[2][0]
                                            ans_rel_breakdown = breakdowns[1]
                                            ans_corr_breakdown = breakdowns[3]
                                            

                                        # To save data
                                        saved_answers.append(answer)
                                        saved_context.append(context)
                                        
                                        faith_breakdowns.append(faith_breakdown)
                                        con_rel_breakdowns.append(con_rel_breakdown)
                                        ans_rel_breakdowns.append(ans_rel_breakdown)

                                        # Save Scores
                                        f_scores.append(f_score)
                                        a_scores.append(a_score)
                                        c_scores.append(c_score)

                                        if current_ground_truth:
                                            saved_ground_truth.append(current_ground_truth)
                                            ans_corr_breakdowns.append(ans_corr_breakdown)
                                            a_corrs.append(a_corr)
                                        else:
                                            a_corr = None                                         
                                    else: # Short instruction case
                                        with st.expander("**Warning**", False):
                                            st.write(f"The following instruction is too short and could not be processed: {question}")
                                    
                            if len(f_scores) > 0:

                                st.subheader("Summary Scores")
                                c_score_mean = np.round(np.mean(c_scores),3)
                                f_score_mean = np.round(np.mean(f_scores), 3)
                                a_score_mean = np.round(np.mean(a_scores),3)
                                if len(a_corrs)>0:
                                    a_corr_mean = np.round(np.mean(a_corrs),3)
                                else:
                                    a_corr_mean = None

                                if len(a_corrs)>0:
                                    st.write(f"How close is the answer to the ground truth: **{a_corr_mean}**")
                                else:
                                    st.write(f"How relevant is the answer to the retrieved context: **{f_score_mean}**")

                                with st.expander("Details"):
                                    st.write(f"**Context Relevance** (relevancy of the retrieved **context** to the **question**): **{c_score_mean}**")
                                    st.write(f"**Faithfulness** (factual consistency of the generated **answer** against the given **context**): **{f_score_mean}**")
                                    st.write(f"**Answer Relevance** (how pertinent the generated **answer** is to the given **prompt**): **{a_score_mean}**")
                                    if len(a_corrs)>0:
                                        st.write(f"**Answer Correctness** (how factually consistent and complete the generated **answer** is to the given **ground truth**): **{a_corr_mean}**")
                                # Write recommendation
                                recommendation = recommend(c_score_mean, f_score_mean, a_score_mean, a_corr_mean)
                                st.warning(recommendation)

                                if n_loops==1:

                                    ## Save file
                                    saved_json = filelister.update_entry(bot_name, question_list, saved_answers, saved_context, saved_ground_truth, f_scores, a_scores, c_scores, a_corrs, f_score_mean, a_score_mean, c_score_mean, a_corr_mean, faith_breakdowns, ans_rel_breakdowns, con_rel_breakdowns, ans_corr_breakdowns)
                                    st.session_state['saved_json'] = saved_json
                                    filelister.save_json(saved_json)
                                    st.divider()
                                    ### Display results for every question
                                    st.subheader("Calculation details for each prompt")
                                    for i in range(len(saved_answers)):
                                        c_score = c_scores[i]
                                        f_score = f_scores[i]
                                        a_score = a_scores[i]
                                        a_corr = a_corrs[i] if len(a_corrs) >i else None
                                        answer = saved_answers[i]
                                        context = saved_context[i]
                                        faith_breakdown = faith_breakdowns[i]
                                        con_rel_breakdown= con_rel_breakdowns[i]
                                        ans_corr_breakdown  = ans_corr_breakdowns[i] if len(ans_corr_breakdowns) >i else None

                                        # Recomendation
                                        q_recommendation = recommend(c_score, f_score, a_score, a_corr)

                                        st.write(f"**Prompt #{i+1}**")
                                        # Give Recommendations
                                        with st.expander(f"**Response**", False):
                                            st.info(f"{answer}")
                                        with st.expander(f"**Context**", False):                           
                                            st.write(f"{context}")

                                        with st.expander(f"**Faithfulness**", False):
                                            st.warning(f'Faithfulness: {np.round(f_score,3)}')
                                            
                                            st.write(f'Context: {context}')
                                            for faith in faith_breakdown:
                                                with st.container(border=True):
                                                    st.write(f"Answer part: {faith['claim']}")
                                                    st.write(f"Score: {faith['score']}")

                                        with st.expander(f"**Context Relevance**", False):
                                            st.warning(f'Context Relevance: {np.round(c_score,3)}')
                                            
                                            with st.container(border=True):
                                                st.write(f"Relevant Context: {con_rel_breakdown['relevant_context']}")
                                                st.write(f"Score: {con_rel_breakdown['score']}")

                                        with st.expander(f"**Answer Relevance**", False):
                                            st.warning(f'Answer Relevance: {np.round(a_score,3)}') 
                                            
                                            st.write(f"Instruction: {question}")

                                            for ans_rel in ans_rel_breakdown:
                                                with st.container(border=True):
                                                    st.write(f"Answer part: {ans_rel['claim']}")
                                                    st.write(f"Score: {ans_rel['score']}")

                                        if current_ground_truth:
                                            with st.expander(f"**Answer Correctness**", False):
                                                st.warning(f'Answer Correctness: {np.round(a_corr,3)}') 
                                                st.write(f"{str(ans_corr_breakdown)}")

                                        with st.expander(f"**Recommendation**", False):
                                            st.write(q_recommendation)
        else:
            st.warning("Environment error. Contact your system administrator.")

    # region <--------- Feedback Form --------->
    st.divider()
    feedback_filelister = FileLister(
        "dev-ai-bots-eval",
        f"feedback/{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}.json",
        #local = True
        )
    with st.expander("💬 Help us improve the application by sharing your feedback with us", expanded=False):
        with st.container():
            st.markdown('---')
            with st.form(key="feedback_form"):
                feedback_thumbs_updown = st.radio("How would you rate this particular experience?", ("positive", "negative"),
                                                format_func=lambda x: "👍🏽" if x == "positive" else "👎🏽", horizontal=True)
                st.write("")
                feedback_text = st.text_area("Please share your feedback with us", value="", height=150, max_chars=2500)
                feedback_email = st.text_input("Your email address (if you would like us to follow up with you)")
                st.write("")

                feedback_data = {
                    "feedback_thumbs_updown": feedback_thumbs_updown,
                    "feedback_text": feedback_text,
                    "feedback_email": feedback_email,
                }


                feedback_data["saved_data"] = st.session_state.get('saved_json')

                if st.form_submit_button("Submit"):
                    response = feedback_filelister.save_json(feedback_data)
                    if response:
                        st.success("Thank you for your feedback!")
                    else:
                        st.error("Oops! Something went wrong. Please try again later.")

    # endregion <--------- Feedback Form --------->       
if __name__ == '__main__':
    # region <--------- Streamlit App Configuration --------->
    st.set_page_config(
        layout="wide",
        page_title="AI Bots Evaluator",
        page_icon="🏗️"
    )

    # endregion <--------- Streamlit App Configuration --------->
    # Time to refresh page

    asyncio.run(st_evaluate())


    # Display application built from launchpad message
    st.caption(
        "🛠️ Built from [LaunchPad](https://go.gov.sg/launchpad)"
        )