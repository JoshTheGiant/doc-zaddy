# ASI Alliance Hackathon: Zaddy Cove Project Plan

## Project Idea
**Decentralized Healthcare Triage Agent**
- **Description**: A uAgent that triages patient symptoms via natural language, reasons using MeTTa Knowledge Graph (symptom-disease mappings), and suggests actions (e.g., consult doctor). Agents collaborate on Agentverse, using Chat Protocol for ASI:One interaction.
- **Why?**: Solves healthcare access issues, leverages ASI tech (uAgents, MeTTa, Agentverse), and aligns with Zaddy Cove's Web3 vision.

## Objectives
- Build TriageAgent and ActionAgent using uAgents.
- Integrate MeTTa for symptom-disease reasoning.
- Deploy to Agentverse with Chat Protocol.
- Deliver real-world impact through decentralized healthcare.

## Tools & Setup
- **Python 3.11.32**: For uAgents/MeTTa.
- **uAgents**: Agent framework (`pip install uagents`, v0.22.10).
- **MeTTa**: Knowledge graph (see [SingularityNET docs](https://singularitynet.io/docs/metta)).
- **Agentverse**: For deployment (see [MCP Setup](https://fetch.ai/docs/agentverse-mcp)).
- **Git**: Version control (v2.51.0).
- **VS Code**: Code editing (v1.105.1).
- **GitHub**: Submission via public repo.

## Agent Architecture
1. **TriageAgent**: Processes symptoms, queries MeTTa, suggests actions.
2. **ActionAgent**: Triggers actions (e.g., mock API for booking).
3. **Agentverse**: Registers agents, enables Chat Protocol.
4. **MeTTa**: Stores symptom-disease rules (e.g., `(if (and fever cough) likely-flu)`).

## Next Steps
- Build agents (Stage 2, Oct 17–19).
- Deploy to Agentverse (Stage 3, Oct 20–22).
- Finalize demo/documentation (Stage 5, Oct 25).

<image-card alt="tag:innovationlab" src="https://img.shields.io/badge/innovationlab-3D8BD3" ></image-card>
<image-card alt="tag:hackathon" src="https://img.shields.io/badge/hackathon-5F43F1" ></image-card>
