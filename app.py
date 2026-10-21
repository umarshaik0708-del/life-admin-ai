import base64
import json
import streamlit as st
from groq import Groq

st.set_page_config(page_title="Life Admin AI", page_icon="📸")

st.title("📸 Life Admin AI")
st.write("Upload a messy college notice screenshot and let AI organize it!")

# File uploader
uploaded_file = st.file_uploader("Upload a notice (PNG or JPG)", type=["png", "jpg", "jpeg"])

# Extract button
if st.button("Extract Task from Image"):
    if uploaded_file is None:
        st.warning("Please upload an image first!")
    else:
        # 1. Check for API key in Streamlit Secrets
        if "GROQ_API_KEY" not in st.secrets:
            st.error("⚠️ GROQ_API_KEY secret is not set in Streamlit Cloud Settings!")
            st.stop()

        groq_api_key = st.secrets["GROQ_API_KEY"]

        # 2. Process image with Groq
        with st.spinner("AI is reading the notice..."):
            client = Groq(api_key=groq_api_key)

            # Convert uploaded image to Base64
            image_bytes = uploaded_file.read()
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            prompt = """
            Read the text in this image carefully. Extract the key details.
            Return ONLY a valid JSON object with these exact keys: 
            "title", "category", "deadline", "action_required", "calendar_date".
            Make sure "calendar_date" is formatted strictly as YYYYMMDD based on the deadline.
            """

            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ]
            )

            # 3. Clean and parse JSON response
            raw_text = response.choices[0].message.content
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)

            st.success("Extraction Complete!")
            st.json(data)

            # 4. Generate downloadable .ics calendar file
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:{data.get('title', 'Task Deadline')}
DESCRIPTION:{data.get('action_required', '')}
DTSTART;VALUE=DATE:{data.get('calendar_date', '')}
END:VEVENT
END:VCALENDAR"""

            st.download_button(
                label="🗓️ Download Calendar Invite",
                data=ics_content,
                file_name="task_invite.ics",
                mime="text/calendar"
            )
