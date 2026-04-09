import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import pickle

# Load data
df = pd.read_csv("spam.csv", encoding='ISO-8859-1')
df.rename(columns={"v1": "Category", "v2": "Message"}, inplace=True)
df.drop(columns=['Unnamed: 2','Unnamed: 3','Unnamed: 4'], inplace=True)
df['Spam'] = df['Category'].apply(lambda x: 1 if x == 'spam' else 0)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    df.Message, df.Spam, test_size=0.25, random_state=42
)

# Create pipeline
clf = Pipeline([
    ('vectorizer', CountVectorizer()),
    ('nb', MultinomialNB())
])

# Train model
clf.fit(X_train, y_train)

# Evaluate
train_acc = clf.score(X_train, y_train)
test_acc = clf.score(X_test, y_test)
print(f"Train Accuracy: {train_acc:.4f}")
print(f"Test Accuracy: {test_acc:.4f}")

# Save model
with open('spam_model.pkl', 'wb') as f:
    pickle.dump(clf, f)

print("Model saved as spam_model.pkl")