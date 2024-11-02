from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """

Question: {question}

Do the following:

Look up the all the patient records. 

Answer: Let's think step by step.
"""

prompt = ChatPromptTemplate.from_template(template)

model = OllamaLLM(model="llama3.2")

chain = prompt | model

out = chain.invoke({"question": "?"})

print(out)