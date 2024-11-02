from openai import OpenAI
import os

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarise_test(testimonials):
    # Join the testimonials into a single string separated by commas
    input_summaries = ", ".join(testimonials)

    # Create the prompt template
    prompt = (
        f"Summarize the following testimonials in bullet points:\n\n{input_summaries}"
    )

    # Use the client to create a completion
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant who summarizes information in bullet points.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    # Extract and return the output
    return completion.choices[0].message["content"]


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
    "While I lost weight, I also experienced some stomach discomfort.",
]

summary = summarise_test(testimonials)
print(summary)
