import streamlit as st
import pandas as pd
import re # For regular expressions to handle keywords
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

synonym_dict = {
    "ai": ["artificial intelligence", "machine intelligence", "algorithmic intelligence"],
    "artificial intelligence": ["ai", "machine intelligence", "algorithmic intelligence"],
    "machine learning": ["ml", "statistical learning", "predictive analytics"],
    "ml": ["machine learning"],
    "robotics": ["robot engineering", "robot science"],
    "robot": ["automaton", "machine"],
    "computer vision": ["vision systems", "image recognition"],
    "natural language processing": ["nlp", "language understanding"],
    "nlp": ["natural language processing"],
    "technology": ["tech", "innovation", "engineering", "machinery", "tools"],
    "engineering": ["technology", "design", "construction"],
    "sensor": ["detector", "probe"],
    "actuator": ["motor", "driver"],
    "big data": ["large datasets", "massive data"],
    "dataset": ["data collection", "data set"],
    "deep learning": ["deep neural networks"],
    "neural network": ["neural net", "nn"],
    "nn": ["neural network"],
    "cobot": ["collaborative robot"],
    "collaborative robot": ["cobot"],
    "swarming robotics": ["robot swarms", "swarm robotics"],
}

# --- Streamlit UI Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(page_title="AI & Robotics Chatbot", layout="centered")

# --- Configuration ---
EXCEL_FILE = 'ai_robotics_qa.xlsx'

# --- Load Data (cached for performance) ---
@st.cache_data
def load_qa_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip().str.lower()
        if 'question' not in df.columns or 'answer' not in df.columns:
            st.error(f"Error: Excel file must contain 'Question' and 'Answer' columns. Found: {df.columns.tolist()}")
            st.stop()
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please ensure it's in the same directory as the script.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading the Excel file: {e}")
        st.stop()

qa_df = load_qa_data(EXCEL_FILE)

# --- Chatbot Logic ---

def normalize_query(query, synonym_dict): #optimize for synonyms(syns) since we cannot know what shortforms/keywords the user will use, so are bot should be optimized to handle alternate keywords and map them to right answer
    query_lower = query.lower()
    for standardT, syns in synonym_dict.items():
        for syn in syns:
            query_lower = query_lower.replace(syn.lower(), standardT.lower())
    return query_lower

def get_answer(query, dataframe):
    query_lower = normalize_query(query, synonym_dict)
    
    # Try exact match first
    exact_match = dataframe[dataframe['question'].str.lower() == query_lower.lower()]
    if not exact_match.empty:
        return exact_match.iloc[0]['answer']
    
    # Then try keyword matching (more flexible)
    keywords = re.findall(r'\b\w+\b', query_lower)
    if keywords:
        for keyword in sorted(keywords, key=len, reverse=True):
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            matches = dataframe[dataframe['question'].str.contains(pattern)]
            if not matches.empty:
                return matches.iloc[0]['answer']
    
    #Fuzzy match logic
    questions_list = dataframe['question'].tolist()
    best_match, score = process.extractOne(
        query_lower,
        questions_list,
        scorer=fuzz.token_set_ratio 
    )
    
    if score >= 70:  # need to test with more scenarios and tweak
        return dataframe[dataframe['question'] == best_match].iloc[0]['answer']
    
    return "I'm sorry, I couldn't find a relevant answer. Could you please rephrase your question?"

# --- Streamlit UI Elements ---
st.title("🤖 AI & Robotics Chatbot 🧠")
st.write("Ask me anything about Artificial Intelligence and Robotics!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input
if prompt := st.chat_input("Your question..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get chatbot response
    with st.spinner("Thinking..."):
        response = get_answer(prompt, qa_df)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

st.sidebar.header("Instructions")
st.sidebar.write("Type your question in the chat box below and press Enter.")
st.sidebar.write("The chatbot will try to find the best answer from its knowledge base.")
st.sidebar.info(f"Loaded {len(qa_df)} questions and answers from '{EXCEL_FILE}'.")




