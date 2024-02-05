import pandas as pd
from calls import get_stock_info
if __name__ == '__main__':
    # Load the validation results
    valid_df = pd.read_csv("data/final_results.csv")

    # Initialize accumulators for distances and correct prediction counts
    total_distances = {'default': 0, 'few_shot': 0, 'cot': 0}
    correct_predictions = {'default': 0, 'few_shot': 0, 'cot': 0}
    penalty_ctr = {'default': 0, 'few_shot': 0, 'cot': 0}
    total_samples = len(valid_df)
    penalty = 0 # penalty for invalid ratings
    # Iterate over each row in the DataFrame
    for i, row in valid_df.iterrows():
        # Update total distances
        try:
            #print(row['get_credit_rating_accuracy'])
            total_distances['default'] += int(float(row['get_credit_rating_accuracy']))
        except:
            total_distances['default'] += penalty
            penalty_ctr['default'] += 1
        try:
            total_distances['few_shot'] += int(float(row['get_credit_rating_example_accuracy']))
        except:
            total_distances['few_shot'] += penalty
            penalty_ctr['default'] += 1
        try:
            total_distances['cot'] += int(float(row['get_credit_rating_cot_accuracy']))
        except:
            total_distances['cot'] += penalty
            penalty_ctr['default'] += 1

        # Update correct prediction counts
        if row['get_credit_rating_accuracy'] == 0 or row['get_credit_rating_accuracy'] == '0':
            correct_predictions['default'] += 1
        if row['get_credit_rating_example_accuracy'] == 0 or row['get_credit_rating_example_accuracy'] == '0':
            correct_predictions['few_shot'] += 1
        if row['get_credit_rating_cot_accuracy'] == 0 or row['get_credit_rating_cot_accuracy'] == '0':
            correct_predictions['cot'] += 1

    # Calculate average distances
    average_distance = {method: total / total_samples for method, total in total_distances.items()}

    for func_name in ['default','few_shot','cot']:
        average_distance[func_name] = total_distances[func_name]/(total_samples-penalty_ctr[func_name])

    # Print average distances and number of correct predictions
    print(f"Average Distance (Default method): {average_distance['default']}")
    print(f"Correct Predictions (Default method): {correct_predictions['default']}\n")

    print(f"Average Distance (Few Shot method): {average_distance['few_shot']}")
    print(f"Correct Predictions (Few Shot method): {correct_predictions['few_shot']}\n")

    print(f"Average Distance (CoT method): {average_distance['cot']}")
    print(f"Correct Predictions (CoT method): {correct_predictions['cot']}")

