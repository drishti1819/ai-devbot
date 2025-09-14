# Python Programming Tutorial for AI Assistant

## Introduction

Welcome to the Python tutorial for your AI Developer Assistant. This guide is designed to teach the language from scratch with examples, explanations, and practical usage patterns. It assumes zero prior knowledge and emphasizes clarity, brevity, and AI relevance.

---

## 1. What is Python?

Python is a beginner-friendly, general-purpose programming language. It is readable, concise, and used in AI, web development, automation, data science, and more.

**Key features:**
- Clean and easy syntax
- Vast ecosystem of libraries (e.g., NumPy, Pandas, scikit-learn)
- Dynamically typed (you don’t declare variable types)
- Interpreted language (runs line by line)

---

## 2. Variables and Data Types

Variables store values.

```python
x = 5         # Integer
name = "abcd" # String
pi = 3.14     # Float
is_ai = True  # Boolean
```

Python infers the data type from the assigned value.

---

## 3. Basic Data Structures

### Lists  
An ordered collection of items.

```python
fruits = ["apple", "banana", "cherry"]
print(fruits[0])  # apple
```

### Dictionaries  
Key-value pairs.

```python
person = {"name": "ABCD", "age": 25}
print(person["name"])  # ABCD
```

### Tuples (Immutable)

```python
point = (10, 20)
```

### Sets (Unique items)

```python
unique = set([1, 2, 2, 3])
```

---

## 4. Control Flow

### If-Else

```python
if x > 0:
    print("Positive")
elif x == 0:
    print("Zero")
else:
    print("Negative")
```

### Loops

```python
# For loop
for fruit in fruits:
    print(fruit)

# While loop
count = 0
while count < 3:
    print(count)
    count += 1
```

---

## 5. Functions

Reusable blocks of code.

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("ABCD"))
```

---

## 6. Classes and Objects

Python is object-oriented.

```python
class Dog:
    def __init__(self, name):
        self.name = name

    def bark(self):
        return f"{self.name} says woof!"

d = Dog("Max")
print(d.bark())
```

---

## 7. Error Handling

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("You can't divide by zero!")
finally:
    print("Done")
```

---

## 8. File Handling

```python
# Writing
with open("example.txt", "w") as f:
    f.write("Hello file!")

# Reading
with open("example.txt", "r") as f:
    content = f.read()
    print(content)
```

---

## 9. Modules and Imports

Python files = modules.

```python
import math

print(math.sqrt(16))
```

Or create your own:

```python
# utils.py
def add(a, b):
    return a + b
```

```python
# main.py
from utils import add
print(add(2, 3))
```

---

## 10. Common Built-in Functions

```python
len("abc")         # 3
int("10")          # 10
str(123)           # "123"
type(5)            # <class 'int'>
range(5)           # 0 to 4
```

---

## 11. Python Packages

Install via pip:

```bash
pip install requests
```

Example use:

```python
import requests
response = requests.get("https://example.com")
print(response.status_code)
```

---

## 12. Virtual Environments

Keep dependencies isolated.

```bash
python3 -m venv devbot
source devbot/bin/activate  # Linux/macOS
devbot\Scripts\activate.bat # Windows
```

Deactivate with:

```bash
deactivate
```

---

## 13. NumPy Example (for AI)

```python
import numpy as np

a = np.array([1, 2, 3])
print(a * 2)  # [2 4 6]
```

---

## 14. Pandas Example (for DataFrames)

```python
import pandas as pd

df = pd.DataFrame({"name": ["ABCD", "Bot"], "age": [25, 2]})
print(df.head())
```

---

## 15. Writing Your First Script

Create `hello.py`:

```python
name = input("What is your name? ")
print(f"Hello, {name}!")
```

Run it:

```bash
python hello.py
```

---

## 16. Summary

- Python is easy to read and powerful.
- Use lists, dicts, and functions often.
- Practice writing and running small scripts.
- Learn by building — your AI assistant can help!

---

## 17. What’s Next?

You can now:
- Start building CLI tools
- Explore machine learning libraries
- Add your own tutorials and index them

Keep coding, and use the assistant when stuck!

