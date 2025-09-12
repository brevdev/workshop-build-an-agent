"""
Prompts for the report generation agent.
"""

from typing import Final

report_planner_instructions = """You are an expert technical writer. You must create a report structure and return it in JSON format.

TOPIC: {topic}

ORGANIZATION: {report_structure}

TASK: Create a report outline with the following fields for each section:
- name: Section name
- description: Brief overview of main topics and concepts
- research: true/false - whether web research is needed
- content: Leave empty string ""

IMPORTANT: You must respond ONLY with valid JSON wrapped in ```json blocks. Do not include any other text, explanations, or questions.

Example format (you must follow this exact structure):

```json
{{
    "title": "Report Title About {topic}",
    "sections": [
        {{
            "name": "Introduction",
            "description": "Overview and background information",
            "research": false,
            "content": ""
        }},
        {{
            "name": "Main Analysis",
            "description": "Detailed analysis of key concepts",
            "research": true,
            "content": ""
        }},
        {{
            "name": "Conclusion",
            "description": "Summary and final thoughts",
            "research": false,
            "content": ""
        }}
    ]
}}
```

Create 3-5 sections. Sections like introduction and conclusion typically don't need research. Body sections usually do need research.

RESPOND ONLY WITH THE JSON - NO OTHER TEXT."""

###############################################################################

research_prompt: Final[str] = """
Your goal is to generate targeted web search queries that will gather comprehensive
information for writing a technical report section.

Topic for this section:
{topic}

When generating {number_of_queries} search queries, ensure they:
1. Cover different aspects of the topic (e.g., core features, real-world applications, technical architecture)
2. Include specific technical terms related to the topic
3. Target recent information by including year markers where relevant (e.g., "2024")
4. Look for comparisons or differentiators from similar technologies/approaches
5. Search for both official documentation and practical implementation examples

Your queries should be:
- Specific enough to avoid generic results
- Technical enough to capture detailed implementation information
- Diverse enough to cover all aspects of the section plan
- Focused on authoritative sources (documentation, technical blogs, academic papers)"""

###############################################################################

section_research_prompt: Final[str] = """
Your goal is to generate targeted web search queries that will gather comprehensive
information for writing a specific section of a technical report.

Overall report topic: {overall_topic}
Section name: {section_name}
Section description: {section_description}

Generate 3-5 search queries that will help gather information specifically for this section.
Your queries should:
1. Be focused on the section's specific scope and requirements
2. Include technical terms relevant to both the overall topic and this section
3. Target recent information by including year markers where relevant (e.g., "2024")
4. Look for authoritative sources (documentation, technical blogs, academic papers)
5. Cover different aspects of the section topic (implementation details, best practices, real-world examples)

Make sure your queries are specific enough to avoid generic results but comprehensive enough to cover all aspects needed for this section.
"""

section_writing_prompt: Final[str] = """
You are an expert technical writer. You must write a complete section of a technical report.

REPORT TOPIC: {overall_topic}
SECTION NAME: {section_name}
SECTION DESCRIPTION: {section_description}

INSTRUCTIONS:
- Write ONLY the section content - no questions, no meta-commentary, no explanations
- Use research information from the conversation history if available
- For introduction/conclusion: Write 1-2 paragraphs
- For body sections: Write detailed content with subsections if needed
- Use professional technical writing style
- Include specific examples and implementation details
- Start writing immediately - do not ask questions or seek clarification

IMPORTANT: 
- Respond with ONLY the section content. Do not include phrases like "Would you like me to..." or "Should I focus on..."
- DO NOT write placeholder text like "Note: The actual section content will be drafted..."
- DO NOT write "TODO" items or notes about what will be written later
- Write the complete, detailed section content immediately using the research provided

Begin writing the section content:
"""
