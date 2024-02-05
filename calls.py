import yfinance as yf
from openai import OpenAI
import json
from collections import Counter
client = OpenAI(api_key="EINFÜGEN")

credit_ratings_role_prompt = "You are a helpful financial advisor designed to output JSON. You provide credit ratings for various companies. In your json you always output a text and a rating. Your JSON output HAS TO have a 'text' key and a 'rating' key."
judge_role_prompt = "You are a knowledgeable critical financial advisor designed to output json. You pick the most accurate credit rating from a set of credit ratings for a company. In your json you always output a text ('text'), the index of the best rating ('index') and a confidence score ('confidence') between 0 and 1 that highlights how confident you are in your decision."
def call_prompt(role_prompt : str, input_text : str) -> str:
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": role_prompt},
            {"role": "user", "content": input_text}
        ]
    )
    return response.choices[0].message.content



import pandas as pd
def df2str(df):
    # Create a string buffer
    full_string = []

    # Convert column names (which may be Timestamps) to string and add to the string
    column_names = ', '.join([str(col) for col in df.columns])
    full_string.append('Index, ' + column_names)  # Add 'Index' to label the row names

    # Iterate through rows and add the index and row data to the string
    for index, row in df.iterrows():
        row_string = str(index) + ', ' + ', '.join([str(item) for item in row])
        full_string.append(row_string)

    # Join all parts of the string with newlines
    return '\n'.join(full_string)

def get_stock_info(ticker_symbol):
    # fetches balance sheet, income statement and cash flow statement if available
    # returns a concatenated string of all financial statements

    # income statement
    ticker = yf.Ticker(ticker_symbol)

    balance_sheet = ticker.balance_sheet
    # Fetch the income statement
    income_statement = ticker.financials
    # Fetch the cash-flow statement
    cashflow_statement = ticker.cashflow

    output = "BALANCE SHEET:\n"+df2str(balance_sheet)+"\n\nINCOME STATEMENT:\n"+df2str(income_statement)+"\n\nCASHFLOW STATEMENT:\n"+df2str(cashflow_statement)
    return output


def find_keys(node, key, found):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == key:
                if isinstance(found, dict):
                    found[key] = v  # If `found` is a dict, use key-value pairing.
                else:
                    found.append(v)  # If `found` is a list, append the value.
            else:
                find_keys(v, key, found)
    elif isinstance(node, list):
        for item in node:
            find_keys(item, key, found)


def parse_credit_rating(full_text):
    t = json.loads(full_text)
    ratings = []
    texts = []
    find_keys(t, 'rating', ratings)
    find_keys(t, 'text', texts)
    output_rating = ratings[0] if ratings else None
    output_text = texts[0] if texts else None
    return output_rating, output_text


def parse_response_picker(full_text):
    t = json.loads(full_text)
    found = {}  # Use a dictionary to store the found values.
    keys_to_find = ['text', 'index', 'confidence']
    for key in keys_to_find:
        find_keys(t, key, found)  # `found` will be updated with key-value pairs.
    output_text = found.get('text')
    index = found.get('index')
    confidence = found.get('confidence')
    return output_text, index, confidence


def get_credit_rating(ticker_str : str, footer_prompt : str) -> (str, str):
    """
    :param ticker_str: Stock ticker such as "TSLA" or "MSFT"
    :param attr_list: List of attributes that we would like to include in our analysis
    :param footer_prompt: Instructions on analyzing the stock's creditworthiness based on the given data
    :return: (credit_rating, full_text):
    credit_rating is a rating similar to moodys or S&P (AAA to CCC---)
    full_text contains the full response of the model for further analysis
    """
    # Get the info we need from our current stock
    header = get_stock_info(ticker_str)

    full_text = call_prompt(credit_ratings_role_prompt,header+footer_prompt)

    credit_rating, output_text = parse_credit_rating(full_text)

    return credit_rating, output_text

def generate_judge_prompt(agent_prompt, credit_ratings):
    all_ratings_string = f"Original Prompt: {agent_prompt}\n\n"
    for i,e in enumerate(credit_ratings):
        rating, text = e
        all_ratings_string+=f"Output of Agent {i}:\n"
        all_ratings_string+=f"Justification:{text}\n"
        all_ratings_string+=f"Rating: {rating}\n\n"
    all_ratings_string+="Which of these Agents provided the best response. Explain your choice before you answer. Think step by step."
    return all_ratings_string

def get_credit_rating_cot(ticker_str : str, footer_prompt : str, num_agents : int, confidence_threshold : float) -> (str, str):
    """
    This function implements the chain of thought approach described in https://storage.googleapis.com/deepmind-media/gemini/gemini_1_report.pdf

    Stage 1:
    CoT prompt - the model is urged to think step by step and justify its decisionmaking
    Stage 2:
    Judge prompt - another prompt is called on the previous outputs. The model picks the best response and outputs a confidence interval
    If the confidence is below a threshold, the majority vote is picked

    :return:
    """

    # get ratings of agents and store them in credit_ratings list
    header = get_stock_info(ticker_str)
    agent_prompt = header+footer_prompt
    print(agent_prompt)
    credit_ratings = []
    for _ in range(num_agents):
        raw_output = call_prompt(credit_ratings_role_prompt, agent_prompt)
        credit_ratings.append(parse_credit_rating(raw_output))

    # build input for next call
    all_ratings_string = generate_judge_prompt(agent_prompt, credit_ratings)
    print(all_ratings_string)
    # call judge prompt
    raw_output = call_prompt(judge_role_prompt, all_ratings_string)
    print(raw_output)
    text, index, conf = parse_response_picker(raw_output)

    # if confidence is high return best response
    if int(conf) >= confidence_threshold:
        return credit_ratings[int(index)]
    else:
        # majority vote
        rating_counts = Counter(credit_ratings)
        most_common_ratings = rating_counts.most_common()
        max_count = most_common_ratings[0][1]

        # Check for ties
        tied_ratings = [rating for rating, count in most_common_ratings if count == max_count]

        # Pick the rating with the lowest index in the original list in case of a tie
        for rating in credit_ratings:
            if rating in tied_ratings:
                return rating

def get_credit_rating_example(ticker_str : str, footer_prompt : str) -> (str, str):
    """
    :param ticker_str: Stock ticker such as "TSLA" or "MSFT"
    :param attr_list: List of attributes that we would like to include in our analysis
    :param footer_prompt: Instructions on analyzing the stock's creditworthiness based on the given data
    :return: (credit_rating, full_text):
    credit_rating is a rating similar to moodys or S&P (AAA to CCC---)
    full_text contains the full response of the model for further analysis
    """
    # generate the example
    example = open("data/credit_rating_few_shot_examples").read()
    few_shot_prompt = "\nAbove is an example of your task. Below is your actual task. Provide an accurate creditworthiness assessment for the company below. Your JSON output HAS TO have a 'text' key and a 'rating' key.\n"
    # Get the info we need from our current stock
    header = get_stock_info(ticker_str)
    prompt = example+few_shot_prompt+header+footer_prompt
    full_text = call_prompt(credit_ratings_role_prompt,prompt)
    credit_rating, output_text = parse_credit_rating(full_text)

    return credit_rating, output_text

if __name__ == '__main__':
    # Example usage
    footer = "Your JSON output HAS TO have a 'text' key and a 'rating' key."

    rating, text = get_credit_rating("MSFT", footer_prompt=footer)

    print(text)
    print(rating)
    print("getting COT rating")
    get_credit_rating_cot("MSFT", footer, 4, 0.4)
