import gradio as gr
from kerykeion import AstrologicalSubject, ReportGenerator
import ollama
import datetime
import os
from dotenv import load_dotenv

# Load environment variables if any
load_dotenv()

def generate_astrology_report(name, birth_date, birth_time, city):
    # Get GeoNames username from env
    geonames_user = os.getenv("GEONAMES_USERNAME", "demo") # 'demo' is a fallback but often limited
    
    try:
        # birth_date is expected in YYYY-MM-DD
        # birth_time is expected in HH:MM
        date_obj = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
        time_obj = datetime.datetime.strptime(birth_time, "%H:%M")
        
        # Create the astrological subject
        subject = AstrologicalSubject(
            name, 
            date_obj.year, 
            date_obj.month, 
            date_obj.day, 
            time_obj.hour, 
            time_obj.minute, 
            city,
            geonames_username=geonames_user
        )
        
        # Extract key Vedic/Jyotish information
        # Kerykeion is more Western-focused but provides the astronomical data needed.
        # We'll map these to Jyotish terms in the prompt.
        
        sun_sign = subject.sun.get("sign")
        moon_sign = subject.moon.get("sign")
        ascendant_sign = subject.rising.get("sign")
        
        planets_info = []
        for planet in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            p_data = getattr(subject, planet)
            planets_info.append(f"{planet.capitalize()}: {p_data.get('sign')} at {p_data.get('abs_pos'):.2f}°")

        # Prepare the prompt for Ollama
        prompt = f"""
        You are an expert Vedic Astrologer (Jyotish Acharya) with a friendly, spiritual, and insightful tone.
        Generate a detailed astrological interpretation for {name} based on the following birth data:
        - Birth City: {city}
        - Lagna (Ascendant): {ascendant_sign}
        - Surya (Sun) Rashi: {sun_sign}
        - Chandra (Moon) Rashi: {moon_sign}
        
        Planetary Positions:
        {chr(10).join(planets_info)}
        
        Please provide:
        1. A warm welcome and spiritual blessing.
        2. Interpretation of the Lagna (Self and Personality).
        3. Interpretation of the Moon Sign (Emotional Mind and Nakshatra influence).
        4. Brief insights on career, health, and relationships based on these positions.
        5. A concluding spiritual advice or 'Upaya' (simple remedy like meditation or mantra).
        
        Use Jyotish terms like 'Lagna', 'Rashi', 'Graha', and 'Bhavas' where appropriate. 
        Keep the tone encouraging and mystical.
        """

        # Call Ollama (Mistral model)
        response = ollama.chat(model='mistral', messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        interpretation = response['message']['content']
        
        # Format the summary for display
        summary = f"### Natal Chart Summary for {name}\n"
        summary += f"- **Lagna (Ascendant):** {ascendant_sign}\n"
        summary += f"- **Rashi (Moon Sign):** {moon_sign}\n"
        summary += f"- **Surya (Sun Sign):** {sun_sign}\n"
        summary += f"- **Birth Place:** {city}\n"
        
        return summary, interpretation

    except Exception as e:
        return f"Error occurred: {str(e)}", "Please ensure your birth data and city name are correct. Also, verify if Ollama is running with the 'mistral' model."

# Create Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🕉️ Jyotish AI: Your Vedic Astrology Assistant")
    gr.Markdown("Enter your birth details to receive a personalized astrological reading from our AI Acharya.")
    
    with gr.Row():
        name_input = gr.Textbox(label="Full Name", placeholder="e.g. Arjun Sharma")
        city_input = gr.Textbox(label="Birth City", placeholder="e.g. New Delhi")
    
    with gr.Row():
        date_input = gr.Textbox(label="Birth Date (YYYY-MM-DD)", placeholder="2000-01-01")
        time_input = gr.Textbox(label="Birth Time (HH:MM 24hr)", placeholder="14:30")
    
    generate_btn = gr.Button("Generate Chart & Reading", variant="primary")
    
    with gr.Column():
        summary_output = gr.Markdown(label="Chart Summary")
        reading_output = gr.Markdown(label="AI Interpretation")

    generate_btn.click(
        fn=generate_astrology_report,
        inputs=[name_input, date_input, time_input, city_input],
        outputs=[summary_output, reading_output]
    )

if __name__ == "__main__":
    demo.launch()
