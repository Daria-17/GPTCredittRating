from calls import get_credit_rating, get_credit_rating_example, get_credit_rating_cot
import pandas as pd
from time import sleep

def rating_distance(rating1, rating2):
    # Ordered list of ratings from highest to lowest
    ratings_order = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-',
                     'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-',
                     'B+', 'B', 'B-', 'CCC+', 'CCC', 'CCC-', 'CC', 'C', 'D', 'NRprelim']

    # Ensure both ratings are in the ratings list
    if rating1 not in ratings_order or rating2 not in ratings_order:
        return "Invalid rating(s)"

    # Calculate the distance
    distance = abs(ratings_order.index(rating1) - ratings_order.index(rating2))
    return distance

# this script tests the accuracy for the credit rating functions (default, few show, CoT)
if __name__ == "__main__":
    cr_footer = ""
    cre_footer = ""
    crcot_footer = ""

    # Arguments for each function
    func_args = {
        'get_credit_rating': {},
        'get_credit_rating_example': {},
        'get_credit_rating_cot': {'num_agents': 5, 'confidence_threshold': 0.75}
    }

    funcs_to_test = [get_credit_rating, get_credit_rating_example, get_credit_rating_cot]
    footer_prompts = [cr_footer, cre_footer, crcot_footer]

    # Load validation set
    validation_set = pd.read_csv("data/validation_set.csv")

    # Create a copy of the DataFrame to store results
    results_df = validation_set.copy()

    start_interval = 20
    end_interval = 30

    for test_func, footer_prompt in zip(funcs_to_test, footer_prompts):
        # Add new columns for each function
        func_name = test_func.__name__
        results_df[func_name + '_computed_rating'] = ""
        results_df[func_name + '_output_text'] = ""
        results_df[func_name + '_accuracy'] = ""

        for index, row in validation_set.iterrows():

            if index <= start_interval:
                continue
            if index > end_interval:
                break


            symbol, rating = row['Symbol'], row['most_common_rating']

            # Get additional args for the function
            additional_args = func_args[func_name]

            print(f"testing {func_name} for {symbol} (index {index})")

            try:
                computed_rating, output_text = test_func(symbol, footer_prompt, **additional_args)
            except Exception as e:
                print(f"Error testing {func_name} for {symbol}: {e}")
                continue

            actual_rating = row['most_common_rating']
            accuracy = rating_distance(computed_rating, actual_rating)

            # Store results in the DataFrame
            results_df.at[index, func_name + '_computed_rating'] = computed_rating
            results_df.at[index, func_name + '_output_text'] = output_text
            results_df.at[index, func_name + '_accuracy'] = accuracy

            # Save results to the CSV file after each update
            results_df.to_csv("final_results.csv", index=False)

            sleep(60)