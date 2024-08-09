import openai
from find_titles import titles
from google_trans import transcription

# Set up OpenAI API key
openai.api_key = 'sk-proj-ZMpKDvb1RyFYblCD8t3TT3BlbkFJR7rzY4oFBN8TRwx8JdRF'

def generate_title_and_hashtags(transcription):
    # Prepare the prompt for OpenAI
    prompt = (
        f"Based on the following transcription, generate a suitable title and three hashtags for the video. "
        f"Make sure the title is similar in style and tone to these existing titles: {', '.join(titles)}.\n\n"
        f"Transcription:\n{transcription}\n\n"
        f"Title and Hashtags:"
    )

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates video titles and hashtags."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.7
    )

    output = response.choices[0].message.content.strip()
    return output

# Example usage
new_script = transcription
result = generate_title_and_hashtags(new_script)
print(result)

