import numpy as np
import pandas as pd

# Set a random seed for reproducibility
np.random.seed(42)

# Define the number of samples
num_samples = 1000

# Generate synthetic data
age = np.random.randint(2, 5, size=num_samples)  # Random ages between 2 and 5
stepCount = np.random.randint(0, 100, size=num_samples)  # Random step counts between 0 and 100
duration = np.random.randint(30, 600, size=num_samples)  # Random durations between 30 and 600 seconds

# Generate labels (levels) based on some criteria
# Here, we're assuming higher age, lower stepCount, and shorter duration lead to higher levels (1 to 5)
# You can adjust this logic based on your game's mechanics
labels = np.where(age > 40, 5, np.where(stepCount < 30, 1, np.where(duration < 300, 4, np.where(age < 20, 2, 3))))

# Create a DataFrame
data = pd.DataFrame({'age': age, 'stepCount': stepCount, 'duration': duration, 'level': labels})

# Save the dataset to a CSV file
data.to_csv('game_dataset.csv', index=False)
