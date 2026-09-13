import os
import re
import logging
import psycopg2
from groq import Groq
from dotenv import load_dotenv
from database import get_db_connection

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Groq client
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in .env file")
    raise ValueError("GROQ_API_KEY is required")

client = Groq(api_key=GROQ_API_KEY)

# System prompt to guide the AI
SYSTEM_PROMPT = """
You are a helpful assistant that helps users query a fruit nutrition database.

The database table is called "clean_fruits" and has these columns:
- fruit_id (integer): Unique identifier
- name (varchar): Fruit name (e.g., 'Apple', 'Banana')
- family (varchar): Fruit family (e.g., 'Rosaceae', 'Musaceae')
- calories (numeric): Calories per 100g
- sugar (numeric): Sugar in grams per 100g
- carbohydrates (numeric): Carbs in grams per 100g
- protein (numeric): Protein in grams per 100g
- fat (numeric): Fat in grams per 100g

When the user asks a question about the data:
1. Convert their question to a SQL query
2. Return ONLY the SQL query, nothing else
3. Use proper SQL syntax for PostgreSQL
4. Use column names exactly as shown above
5. If the question is unclear, ask for clarification

Example:
User: "What is the average calories for berries?"
SQL: SELECT AVG(calories) FROM clean_fruits WHERE family = 'Rosaceae';

Example:
User: "Which fruit has the most sugar?"
SQL: SELECT name, sugar FROM clean_fruits ORDER BY sugar DESC LIMIT 1;

Example:
User: "Show me all fruits with less than 50 calories"
SQL: SELECT name, calories FROM clean_fruits WHERE calories < 50 ORDER BY calories;

If you cannot answer a question, respond with: "I cannot answer that question based on the available data."
"""

def generate_sql_from_question(question):
    """
    Use Groq to convert a natural language question to SQL.
    """
    try:
        # Build the prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]

        # Call Groq API
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Free, fast model
            messages=messages,
            temperature=0.1,  # Low temperature for consistent SQL
            max_tokens=200
        )

        sql_query = completion.choices[0].message.content.strip()

        # Clean up the SQL (remove markdown code blocks if present)
        sql_query = re.sub(r'```sql\n?', '', sql_query)
        sql_query = re.sub(r'```\n?', '', sql_query)
        sql_query = sql_query.strip()

        logger.info(f"Generated SQL: {sql_query}")
        return sql_query

    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return None

def execute_sql_query(sql_query):
    """
    Execute a SQL query and return results.
    """
    if not sql_query:
        return None, "No SQL query provided"

    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"

    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)

        # Check if query returns data
        if cursor.description:
            # SELECT query
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

            # Convert to list of dictionaries
            result_list = []
            for row in results:
                result_dict = dict(zip(column_names, row))
                result_list.append(result_dict)

            cursor.close()
            conn.close()

            return result_list, None
        else:
            # Non-SELECT query (INSERT, UPDATE, etc.)
            conn.commit()
            cursor.close()
            conn.close()
            return None, "Only SELECT queries are allowed"

    except psycopg2.Error as e:
        error_msg = f"SQL Error: {str(e)[:200]}"
        logger.error(f"{error_msg}")
        conn.rollback()
        conn.close()
        return None, error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)[:200]}"
        logger.error(f"{error_msg}")
        conn.rollback()
        conn.close()
        return None, error_msg

def generate_answer_from_results(results, question):
    """
    Use Groq to convert query results into a natural language answer.
    """
    if not results:
        return "I couldn't find any results for that question."

    try:
        # Convert results to a readable string
        if len(results) == 0:
            return "No data found for that query."

        # If there's only one result, format it nicely
        if len(results) == 1:
            row = results[0]
            result_text = ", ".join([f"{k}: {v}" for k, v in row.items() if v is not None])
        else:
            # Multiple results - show top 5 with summary
            rows_text = []
            for i, row in enumerate(results[:5]):
                rows_text.append(f"{i+1}. " + ", ".join([f"{k}: {v}" for k, v in row.items() if v is not None]))

            result_text = "\n".join(rows_text)
            if len(results) > 5:
                result_text += f"\n... and {len(results) - 5} more results."

        # Build prompt for Groq to generate a natural language answer
        messages = [
            {"role": "system", "content": f"""
You are a helpful assistant that answers questions about fruit nutrition data.
The user asked: "{question}"

Here are the results from the database:
{result_text}

Provide a clear, natural language answer to the user's question based on these results.
- Be specific and use the actual numbers from the results
- If there are multiple results, summarize them clearly
- Keep the answer concise but informative
- Write in plain English, not a list
"""}
        ]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=200
        )

        answer = completion.choices[0].message.content.strip()
        return answer

    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return "I found some data but couldn't format it properly. Please try rephrasing your question."

def ask_question(question):
    """
    Main function: Process a natural language question and return an answer.
    """
    logger.info(f"User question: {question}")

    # Step 1: Generate SQL
    sql_query = generate_sql_from_question(question)
    if not sql_query:
        return "I couldn't understand your question. Could you rephrase it?"

    # Step 2: Execute SQL
    results, error = execute_sql_query(sql_query)
    if error:
        return f"I encountered an issue: {error}"

    if results is None:
        return "I couldn't retrieve data for your question. Please try again."

    # Step 3: Generate answer
    answer = generate_answer_from_results(results, question)
    return answer

def interactive_chat():
    """
    Run an interactive chat session with the AI assistant.
    """
    print("\n" + "=" * 60)
    print("FRUIT NUTRITION AI ASSISTANT")
    print("=" * 60)
    print("Ask questions about fruit nutrition data.")
    print("Type 'exit' or 'quit' to end the session.")
    print("-" * 60)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Assistant: Goodbye!")
            break

        if not user_input:
            continue

        print("\nAssistant: ", end="")
        answer = ask_question(user_input)
        print(answer)

# Quick test
if __name__ == "__main__":
    # Test the assistant with sample questions
    test_questions = [
        "What is the average calories of all fruits?",
        "Which fruit has the most sugar?",
        "Show me fruits with less than 50 calories",
        "What are the top 5 fruits by protein?"
    ]

    print("Testing AI Assistant...")
    print("=" * 60)

    for q in test_questions:
        print(f"\nQuestion: {q}")
        answer = ask_question(q)
        print(f"Answer: {answer}")
        print("-" * 60)

    print("\nTesting complete!")
    print("\nTo start an interactive session, run:")
    print("   python -m src.ai_assistant")