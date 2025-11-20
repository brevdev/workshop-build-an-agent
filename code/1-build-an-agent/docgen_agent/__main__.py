"""Main entry point for the report generation workflow.

This code is a simple example of how to use the report generation workflow.
"""

import logging

from . import write_report

logging.basicConfig(level=logging.INFO)
result = write_report(
    topic="Discuss the advantages of using GPUs for AI training",
    report_structure="""This report type focuses on comparative analysis.

The report structure should include:
1. Introduction (no research needed)
- Brief overview of the topic area
- Context for the comparison

2. Main Body Sections:
- One dedicated section for EACH offering being compared in the user-provided list
- Each section should examine:
- Core Features (bulleted list)
- Architecture & Implementation (2-3 sentences)
- One example use case (2-3 sentences)

3. No Main Body Sections other than the ones dedicated to each offering in the user-provided list

4. Conclusion with Comparison Table (no research needed)
- Structured comparison table that:
* Compares all offerings from the user-provided list across key dimensions
* Highlights relative strengths and weaknesses
- Final recommendations""",
)
if result:
    print("\n\n" + result["report"] + "\n\n")
