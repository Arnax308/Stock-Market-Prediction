---
Title: Terms
Created: 12th September 2024 16:47
Last Modified: 12th September 2024 16:47
tags:
  - ML
cssclasses:
---

## Word Indices

Word indices, also known as integer encoding, is a technique used to convert words into numerical format that machine learning models can work with.

### **How it works:**

1. Create a vocabulary from all unique words in your corpus.
2. Assign a unique integer to each word.
3. Replace each word in your text with its corresponding integer.

### **Example:**

Given the sentence: "The cat sat on the mat"

Vocabulary: {"the": 1, "cat": 2, "sat": 3, "on": 4, "mat": 5}

Encoded sentence: [1, 2, 3, 4, 1, 5]

## One-Hot Encoding

One-hot encoding is a way to represent categorical variables as binary vectors. In NLP, it's used to represent words as vectors.

### **How it works:**

1. Create a vocabulary from all unique words.
2. For each word, create a vector of zeros with length equal to the vocabulary size.
3. Set the index corresponding to the word to 1.

### **Example:**

Using the same vocabulary as before:

"the" = [1, 0, 0, 0, 0]
"cat" = [0, 1, 0, 0, 0]
"sat" = [0, 0, 1, 0, 0]

# Confusion Matrix and Evaluation Metrics for Classification

## Confusion Matrix

A confusion matrix is a table that summarizes the performance of a classification model. It shows the counts of true positives, true negatives, false positives, and false negatives.

For a binary classification problem:

|        |          | Predicted |          |
| ------ | -------- |:---------:|:--------:|
|        |          | Positive  | Negative |
| Actual | Positive |    TP     |    FN    |
|        | Negative |    FP     |    TN    |
|        |          |           |          |

- TP (True Positive): Correctly predicted positive class
- TN (True Negative): Correctly predicted negative class
- FP (False Positive): Incorrectly predicted positive class
- FN (False Negative): Incorrectly predicted negative class

In your code:
```python
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y_test, y_pred_class)
```

This creates a 2x2 matrix for binary classification.

## Evaluation Metrics

### **1. Precision

Precision is the ratio of correctly predicted positive observations to the total predicted positive observations.

```
Precision = TP / (TP + FP)
```

- High precision indicates a low false positive rate.
- It answers: "Of all instances predicted as positive, how many actually are positive?"
- ==Use when the cost of false positives is high.

### **2. Recall (Sensitivity or True Positive Rate)

Recall is the ratio of correctly predicted positive observations to all actual positive observations.

```
Recall = TP / (TP + FN)
```

- High recall indicates a low false negative rate.
- It answers: "Of all actual positive instances, how many did we correctly identify?"
- ==Use when the cost of false negatives is high.

### **3. F1 Score

F1 Score is the harmonic mean of Precision and Recall, providing a single score that balances both metrics.

```
F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
```

- It provides a balanced measure for uneven class distribution.
- A perfect F1 score is 1, while the worst is 0.
- ==Use when you want a balance between Precision and Recall.
- 

### **4. ROC AUC (Receiver Operating Characteristic Area Under Curve)

ROC AUC represents the model's ability to distinguish between classes across all possible classification thresholds.

- ROC curve plots True Positive Rate against False Positive Rate at various threshold settings.
- AUC (Area Under Curve) provides an aggregate measure of performance across all possible classification thresholds.
- AUC of 1 represents a perfect classifier, while 0.5 represents a random classifier.
- ==Use when you need to evaluate the model's performance across various classification thresholds.


