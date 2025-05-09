from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Crew, Agent, Task, LLM
from crewai_tools import SerperDevTool
from web_scraper import WebScraperTool
from write_tool import FileWriteTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
gem_key = os.getenv("GEMINI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

# Initialize LLMs and tools
gemini_llm = LLM(
    model="gemini/gemini-2.0-flash-exp",
    temperature=0.7,
    api_key=gem_key
)

groq_llm = LLM(
    model="groq/llama-3.1-8b-instant",
    temperature=0.7,
    api_key=groq_key
)

google_tool = SerperDevTool()
web_scraper = WebScraperTool()
write_tool = FileWriteTool()

# Flask setup
app = Flask(__name__)
CORS(app)

# Study material generator function
def create_study_material(topic):
    output_file = f"{topic.lower().replace(' ', '_')}_exam.md"

    # Define agents
    search_agent = Agent(
        name="Search Agent",
        role="Web Search Specialist",
        goal=f"Find the most relevant and authoritative resource on {topic}",
        backstory=f"You are an expert in finding high-quality information sources about {topic}.",
        tools=[google_tool],
        llm=gemini_llm
    )

    scraper_agent = Agent(
        name="Web Scraper",
        role="Content Extraction Specialist",
        goal=f"Extract and process valuable content about {topic}",
        backstory=f"You are skilled at extracting information from websites and organizing it.",
        tools=[web_scraper],
        llm=gemini_llm
    )

    exam_creator_agent = Agent(
        name="Exam Creator",
        role="Educational Content Developer",
        goal=f"Create structured study materials and questions on {topic}",
        backstory=f"You specialize in creating study content with relevant questions.",
        llm=gemini_llm
    )

    educational_formatter_agent = Agent(
        name="Educational Formatter",
        role="Learning Materials Designer",
        goal=f"Format content on {topic} into optimal learning structure",
        backstory=f"You are an expert in formatting and designing educational materials.",
        llm=gemini_llm,
        tools=[write_tool]
    )

    # Define tasks
    search_task = Task(
        agent=search_agent,
        description=f"""
        Search for ONLY ONE high-quality, authoritative resource on {topic}, covering:
        - Fundamentals
        - Current state
        - Applications
        - Future developments
        Return ONLY ONE URL.
        """,
        expected_output=f"A single high-quality URL about {topic}."
    )

    scraping_task = Task(
        agent=scraper_agent,
        description=f"""
        Use the web_scraper tool to extract content from the URL provided.
        Organize key concepts, definitions, applications, and developments.
        """,
        expected_output=f"A concise collection of organized information about {topic}.",
        context=[search_task]
    )

    exam_creation_task = Task(
        agent=exam_creator_agent,
        description=f"""
        Create study materials with:
        - Clear explanations
        - Key definitions
        - Core principles
        - Applications
        - 5-10 exam-style questions (MCQs, short answer, essay)
        Provide answers and explanations.
        """,
        expected_output=f"Structured study materials with questions and answers.",
        context=[scraping_task]
    )

    formatting_task = Task(
        agent=educational_formatter_agent,
        description=f"""
        Format study materials into markdown ({output_file}) with:
        - Table of contents
        - Proper headings
        - Highlighted key terms
        - Bullets/numbered lists
        - Q&A sections
        - Summary at the end
        Save to {output_file}.
        """,
        expected_output=f"Formatted markdown file ({output_file}).",
        tools=[write_tool],
        context=[exam_creation_task]
    )

    # Run the crew
    crew = Crew(
        agents=[search_agent, scraper_agent, exam_creator_agent, educational_formatter_agent],
        tasks=[search_task, scraping_task, exam_creation_task, formatting_task],
        max_rpm=5,
        verbose=True
    )

    result = crew.kickoff()

    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return result.raw if hasattr(result, 'raw') else "Failed to generate output"

# Flask route
@app.route("/generate", methods=["POST"])
def generate_material():
    data = request.get_json()
    topic = data.get("topic")

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    try:
        content = create_study_material(topic)
        return jsonify({"message": "Success", "markdown": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Start the server
if __name__ == "__main__":
    app.run(debug=True)
