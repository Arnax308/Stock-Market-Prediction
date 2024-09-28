---
Title: Binary Classification
Created: 12th September 2024 16:41
Last Modified: 12th September 2024 16:41
tags:
  - ML
cssclasses:
---
# Binary Classification
## Importing Libraries

```python
import pandas as pd
import numpy as np

from tensorflow import keras
from tensorflow.keras import layers
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
```

This section imports necessary libraries:
- pandas and numpy for data manipulation and numerical operations
- TensorFlow and Keras modules for building and training neural networks

## Loading and Preparing Data

```python
data = pd.read_csv('summary.csv')
data.head()

data['Intreset'].value_counts(normalize=True)
X, y = data['Summary'], data['Intreset'].values
```

These lines:
1. Load data from a CSV file named 'summary.csv'
2. Display the first few rows of the data
3. Calculate the normalized value counts of the 'Intreset' column
4. Prepare X (features) and y (target) from the data

## Text Preprocessing

```python
tokenizer = Tokenizer()
tokenizer.fit_on_texts(X)
word_indices = tokenizer.texts_to_sequences(X)

print(word_indices[0])

vocab = tokenizer.word_index

max_len = max(max(i) for i in word_indices)
word_indices_padded = pad_sequences(word_indices, maxlen=max_len, padding='post')
word_indices_np_padded = np.array(word_indices_padded)
```

This section preprocesses the text data:
1. Create a Tokenizer object and fit it on the text data (X) to create a vocabulary
2. Convert the text to sequences of integers using the vocabulary
3. Print the first sequence to see how it looks
4. Extract the word index (vocabulary) from the tokenizer
5. Find the maximum length of sequences
6. Pad all sequences to this maximum length
7. Convert the padded sequences to a numpy array

Read about [[Terms#Word Indices|Word Indices and Vocabulary]] 

## Preparing Training and Test Data

```python
one_hot_encoded = tokenizer.texts_to_matrix(X, mode='binary')
one_hot_encoded.shape
y_train = np.asarray(y).astype('float32')
x_test = word_indices_np_padded[-5:]
y_test = y_train[-5:]

word_indices_np_padded = word_indices_np_padded[:-5]
y_train = y_train[:-5]
```

These lines:
1. Create a one-hot encoded matrix of the text (not used further in this code)
2. Prepare the target variable as float32
3. Split the last 5 samples for testing
4. Remove the last 5 samples from the training data

Read about [[Terms#One-Hot Encoding|One-Hot Encoding]] 

## Defining and Training the Model

```python
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

model = Sequential([
    Dense(16, activation='relu'),
    Dense(16, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(word_indices_np_padded, y_train, epochs=10);
```

This section:
1. Imports additional TensorFlow modules for creating a Sequential model
2. Defines a simple neural network model with three Dense layers
3. Compiles the model with Adam optimizer and binary cross-entropy loss
4. Trains the model for 10 epochs

## Making Predictions and Evaluating the Model

```python
y_pred_prob = model.predict(x_test)

threshold = 0.5

y_pred_class = (y_pred_prob >= threshold).astype(int)
accuracy = np.mean(y_pred_class == y_test.reshape(-1, 1))
accuracy
```

These final lines:
1. Make predictions on the test set
2. Set a threshold of 0.5 to convert probabilities to class labels
3. Calculate and print the accuracy of the model on the test set

## Generating Confusion Matrix

```python
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y_test, y_pred_class)
cm
```

This section:
1. Imports the confusion_matrix function from scikit-learn
2. Calculates the confusion matrix by comparing the true labels (y_test) with the predicted labels (y_pred_class)
3. Displays the confusion matrix

The confusion matrix provides a tabular summary of the model's performance, showing the number of true positives, true negatives, false positives, and false negatives.

Read about [[Terms#Confusion Matrix|Confusion Matrix]] 

## Calculating Additional Evaluation Metrics

```python
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

precision = precision_score(y_test, y_pred_class)
recall = recall_score(y_test, y_pred_class)
f1 = f1_score(y_test, y_pred_class)
roc_auc = roc_auc_score(y_test, y_pred_prob)

print(f'Precision: {precision:.4f}')
print(f'Recall: {recall:.4f}')
print(f'F1 Score: {f1:.4f}')
print(f'ROC AUC: {roc_auc:.4f}')
```

This code block:
1. Imports additional metric functions from scikit-learn
2. Calculates various evaluation metrics:
   - Precision: The ratio of correctly predicted positive observations to the total predicted positive observations
   - Recall: The ratio of correctly predicted positive observations to all actual positive observations
   - F1 Score: The harmonic mean of precision and recall, providing a single score that balances both metrics
   - ROC AUC: Area Under the Receiver Operating Characteristic Curve, which represents the model's ability to distinguish between classes
3. Prints these metrics formatted to four decimal places

These metrics provide a more comprehensive evaluation of the model's performance beyond just accuracy:
- Precision indicates how many of the positively classified instances are actually positive
- Recall shows how many of the actual positive instances were correctly identified
- F1 Score provides a balance between precision and recall
- ROC AUC gives an aggregate measure of performance across all possible classification thresholds

By examining these metrics together, you can get a more nuanced understanding of your model's strengths and weaknesses in classifying the text data.

Read about [[Terms#Evaluation Metrics|Evaluation Metrics]] 