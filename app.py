from dotenv import load_dotenv
import streamlit as st
import os
import sqlite3
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Set up the Gemini model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(question, prompt_list):
    model = genai.GenerativeModel('gemini-pro')
    
    # Combine all prompts in the prompt_list into a single string
    combined_prompt = "\n".join(prompt_list) + "\n" + question
    
    # Generate the response from Gemini model
    response = model.generate_content([combined_prompt])
    return response.text.strip()

def read_sql_query(sql, db):
    # Clean up the SQL query before executing it
    sql = sql.replace("```sql", "").replace("```", "").strip()  # Remove any code fences
    
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return rows

# Streamlit setup
st.set_page_config(page_title="SQL Retrieval System")
st.header("Gemini integrated app to retrieve SQL data")

# List of prompts for different types of queries (now as strings only)
prompts = [
    """
    You are an expert in converting natural language questions into SQL queries for a database. The database is named `output` and contains the following columns:
    - reviewerID: ID of the reviewer.
    - reviewerName: Name of the reviewer.
    - helpful: Number of helpful votes for the review.
    - reviewText: The content of the review.
    - overall: Rating of the item (1-5 scale).
    - summary: Summary of the review.
    - unixReviewTime: Review timestamp in UNIX format.
    - reviewTime: Review timestamp in human-readable format.
    - day_diff: Number of days since the review.
    - helpful_yes: Number of helpful votes marked as "yes".
    - total_vote: Total votes for the review.
    
    **Important Note**: The `asin` column has the same value across the entire table and should **not** be included in any SQL queries.

    Your task is to convert the following natural language questions into SQL queries, making sure the queries only involve the relevant columns (excluding `asin`) and return only the necessary results.

    Examples:
    - Question: "How many reviews of item X are present?"
    - SQL Query: "SELECT COUNT(*) FROM output;"

    - Question: "Give me the latest negative reviews."
    - SQL Query: "SELECT reviewText FROM output WHERE overall < 4 ORDER BY unixReviewTime DESC;"
    
    Please generate the SQL query only without any additional text. If the question does not correspond to a valid query, respond with "Invalid query."
    """
    ,
    """
    You are an expert in sentiment analysis. Given a review, determine if it's positive, neutral, or negative.
    The review text: {review_text}
    For example:
    - "Great product, would buy again!" - Positive
    - "Not bad, but could be better." - Neutral
    - "Terrible experience, do not buy!" - Negative
    
    Please output only the sentiment (Positive/Neutral/Negative) without any additional text.
    """
    ,
    """
    You are a chatbot that understands various types of database queries and can help users retrieve meaningful information from large datasets like reviews. Translate the user's query into SQL and execute it on a database.

    Please ensure the SQL query is valid and relevant to the available columns in the `output` table. The `asin` column should not appear in the SQL query.
    """
    ,
    """
    Input: "How many reviews does product X have?"
    Output: "SELECT COUNT(*) FROM output;"
    """
    ,
    """
    Input: "Give me all the reviews with a rating of 5."
    Output: "SELECT reviewText FROM output WHERE overall = 5;"
    """
    ,
    """
    Input: "What is the average rating for product Z?"
    Output: "SELECT AVG(overall) FROM output;"
    """
    ,
    """
    Input: "Retrieve the latest review."
    Output: "SELECT reviewText FROM output ORDER BY unixReviewTime DESC LIMIT 1;"
    """
    ,
    """
    Input: "Which reviewer has submitted the most reviews?"
    Output: "SELECT reviewerName, COUNT(*) as num_reviews FROM output GROUP BY reviewerName ORDER BY num_reviews DESC LIMIT 1;"
    """
    ,
    """
    Input: "Find all reviews that contain the word 'bad'."
    Output: "SELECT reviewText FROM output WHERE reviewText LIKE '%bad%';"
    """
    ,
    """
    Input: "Give me the reviews with a rating lower than 3."
    Output: "SELECT reviewText FROM output WHERE overall < 3;"
    """
    ,
    """
    Input: "How many helpful votes did the review with the highest rating receive?"
    Output: "SELECT helpful_yes FROM output WHERE overall = (SELECT MAX(overall) FROM output);"
    """
    ,
    """
    Input: "Which product has the most reviews?"
    Output: "SELECT asin, COUNT(*) as num_reviews FROM output GROUP BY asin ORDER BY num_reviews DESC LIMIT 1;"
    """
    ,
    """
    Input: "Find all reviews posted within the last week."
    Output: "SELECT reviewText FROM output WHERE unixReviewTime >= strftime('%s', 'now') - 604800;"
    """
    ,
    """
    Input: "Find all products where the average rating is below 3.5."
    Output: "SELECT asin FROM (SELECT asin, AVG(overall) as avg_rating FROM output GROUP BY asin) WHERE avg_rating < 3.5;"
    """
    ,
    """
    Input: "List the top 5 most helpful reviews."
    Output: "SELECT reviewText FROM output ORDER BY helpful_yes DESC LIMIT 5;"
    """
    ,
    """
    Input: "Which user has written the highest number of positive reviews?"
    Output: "SELECT reviewerName, COUNT(*) as num_reviews FROM output WHERE overall >= 4 GROUP BY reviewerName ORDER BY num_reviews DESC LIMIT 1;"
    """
    ,
    """
    Input: "Find all reviews that contain the word 'amazing'."
    Output: "SELECT reviewText FROM output WHERE reviewText LIKE '%amazing%';"
    """
    ,
    """
    Input: "Give me the top 3 most recent negative reviews."
    Output: "SELECT reviewText FROM output WHERE overall < 4 ORDER BY unixReviewTime DESC LIMIT 3;"
    """
    ,
    """
    Input: "Which product has the longest average review text?"
    Output: "SELECT asin FROM (SELECT asin, AVG(LENGTH(reviewText)) as avg_length FROM output GROUP BY asin) WHERE avg_length = (SELECT MAX(avg_length) FROM (SELECT asin, AVG(LENGTH(reviewText)) as avg_length FROM output GROUP BY asin));"
    """
    ,
    """
    Input: "How many reviews have no helpful votes?"
    Output: "SELECT COUNT(*) FROM output WHERE helpful_yes = 0;"
    """
    ,
    """
    Input: "Find all reviews with no text content."
    Output: "SELECT reviewText FROM output WHERE reviewText = '';"
    """
    ,
    """
    Input: "Which reviewers tend to give the lowest ratings?"
    Output: "SELECT reviewerName, AVG(overall) as avg_rating FROM output GROUP BY reviewerName ORDER BY avg_rating ASC LIMIT 1;"
    """
    ,
    """
    Input: "List all reviews that have a rating of 3 and contain the word 'average'."
    Output: "SELECT reviewText FROM output WHERE overall = 3 AND reviewText LIKE '%average%';"
    """
    ,
    """
    Input: "What is the total number of votes received by reviews?"
    Output: "SELECT SUM(total_vote) FROM output;"
    """
    ,
    """
    Input: "Which reviewer has the highest total votes?"
    Output: "SELECT reviewerName, SUM(total_vote) as total_votes FROM output GROUP BY reviewerName ORDER BY total_votes DESC LIMIT 1;"
    """
    ,
    """
    Input: "Find reviews with the word 'Samsung'."
    Output: "SELECT reviewText FROM output WHERE reviewText LIKE '%Samsung%';"
    """
]

# Streamlit UI
question = st.text_input("Enter your question:", key="input")
submit = st.button("Ask the question")

# When the button is pressed
if submit:
    # Get Gemini's response based on the provided list of prompts
    response = get_gemini_response(question, prompts)
    
    # Print the response
    st.write(f"Generated Response: {response}")
    
    # Clean the SQL query before executing
    if "SELECT" in response:
        response_clean = response.replace("```sql", "").replace("```", "").strip()  # Clean up unwanted formatting
        
        # Read and display SQL query result (if SQL query generated)
        data = read_sql_query(response_clean, "output.db")
        st.subheader("Database Query Results:")
        for row in data:
            st.write(row)
