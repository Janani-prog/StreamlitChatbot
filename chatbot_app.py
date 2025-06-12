import streamlit as st
import pandas as pd
import re # For regular expressions to handle keywords

# --- Streamlit UI Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(page_title="AI & Robotics Chatbot", layout="centered")

# --- Configuration ---
EXCEL_FILE = 'ai_robotics_qa.xlsx'

# --- Load Data (cached for performance) ---
@st.cache_data
def load_qa_data(file_path):
    try:
        df = pd.read_excel(file_path)
        # Ensure column names are stripped of whitespace and converted to lowercase
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
def get_answer(query, dataframe):
    query_lower = query.lower()

    # Try exact match first
    for index, row in dataframe.iterrows():
        if query_lower == row['question'].lower():
            return row['answer']

    # Then try keyword matching (more flexible)
    # Tokenize the query into individual words and create a regex pattern
    keywords = re.findall(r'\b\w+\b', query_lower)
    if not keywords:
        return "I'm sorry, I couldn't understand your question. Please try rephrasing it."

    # Sort keywords by length descending to prioritize longer, more specific matches
    keywords.sort(key=len, reverse=True)

    for keyword in keywords:
        # Create a regex pattern to match whole words or parts of words within the question
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)

        for index, row in dataframe.iterrows():
            if pattern.search(row['question']):
                return row['answer']

    return "I'm sorry, I couldn't find an answer to your question. Can you please rephrase it or ask something different?"

# --- Streamlit UI Elements ---
# These can come AFTER st.set_page_config()
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