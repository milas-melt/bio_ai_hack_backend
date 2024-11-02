from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

def summarise_test(summaries):
    # Create the prompt template
    template = """
    Summarize the following testimonials: {testimonials} in bullet points.
    """
    
    # Create a prompt from the template
    prompt = ChatPromptTemplate.from_template(template)
    
    # Initialize the model
    model = OllamaLLM(model="llama3.2")
    
    # Create the input string from summaries
    input_summaries = ",".join(summaries)
    
    # Chain the prompt and model
    chain = prompt | model
    
    # Invoke the model with the testimonials
    out = chain.invoke({"testimonials": input_summaries})
    
    return out

# Example usage
testimonials = [
    "I experienced nausea and dizziness after starting Ozempic.",
    "It caused me to have frequent headaches.",
    "I felt really fatigued, especially in the first few weeks.",
    "My appetite decreased significantly, which was a positive change.",
    "I had some digestive issues, including constipation.",
    "I noticed a rash on my skin that I hadn't had before.",
    "After taking Ozempic, I experienced some unusual cravings.",
    "There were moments when I felt lightheaded after my injections.",
    "I had trouble sleeping at night, which was unexpected.",
    "While I lost weight, I also experienced some stomach discomfort."
]

summary = summarise_test(testimonials)
print(summary)
