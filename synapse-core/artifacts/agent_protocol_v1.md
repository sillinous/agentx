# Synapse Agent Protocol (SAP) v1.0

This document serves as the "Constitution" for your ecosystem. It ensures that as we add 10, 50, or 100 agents, they don't become a chaotic noise machine. Instead, they operate as a synchronized orchestra.

## 🧬 Synapse Agent Protocol (SAP)
**Version:** 1.0
**Status:** Architecture Draft
**Objective:** To standardize communication, memory, and authority across the Synapse Autonomous Ecosystem.

### 1. The Agent Standard Definition (ASD)
Every agent in the ecosystem must adhere to a strict definition schema. This allows the Orchestrator (the brain) to know exactly who to call for what task.

We will define agents using a JSON Schema.

```json
{
  "agent_id": "marketing_01",
  "name": "Outreach Specialist",
  "domain": "growth",
  "capabilities": ["email_generation", "social_post_drafting", "audience_segmentation"],
  "tools": ["sendgrid_api", "twitter_api", "vector_db_search"],
  "permissions": {
    "read": ["user_content", "analytics_data"],
    "write": ["draft_folder"],
    "execute": ["internal_notification"] 
    // Note: This agent CANNOT "execute" a public post without approval.
  },
  "confidence_threshold": 0.85
}
```

**The Protocol Rule:**
"Least Privilege" Principle: Agents are born with restricted access. A Research Agent can read data but cannot write to the database. A Finance Agent is the only one who can touch the Stripe API.

### 2. The Communication Standard (The "Handshake")
Agents do not talk to each other in paragraphs. They talk in Structured Events. This reduces hallucination and ensures tasks don't get lost in translation.

**The Request Structure**
When the Orchestrator assigns a task (e.g., "Create a promo code"), it sends a standardized packet:

```json
{
  "event_type": "TASK_ASSIGNMENT",
  "trace_id": "task_9982_black_friday",
  "priority": "HIGH",
  "context": {
    "user_intent": "Create a 20% off code for the new course.",
    "deadline": "2025-11-25"
  },
  "constraints": {
    "max_discount": 25,
    "currency": "USD"
  }
}
```

**The Response Structure**
The Agent must return a structured result, not just text.

```json
{
  "status": "SUCCESS",
  "trace_id": "task_9982_black_friday",
  "output": {
    "code": "BF2025",
    "value": "20%",
    "stripe_id": "coupon_x7d89s"
  },
  "confidence_score": 0.98,
  "human_review_required": false
}
```

### 3. The Shared Memory Protocol (The "Context Lake")
Agents are stateless (they forget instantly). The Context Lake is the persistent state.

**Layer 1: The "Session Graph" (Short Term)**
*   **What it is:** A live JSON object tracking the current conversation/task.
*   **Function:** If the User says "Change the color to red," the Design Agent looks at the Session Graph to know what we are talking about (e.g., "The Landing Page Button").

**Layer 2: The "Embeddings Vault" (Long Term)**
*   **What it is:** A Vector Database (Pinecone/Weaviate).
*   **Protocol:** Before any agent writes copy, it runs a Retrieval Check:
    *   **Query:** "What is the brand's tone of voice?"
    *   **Retrieve:** Top 5 previous high-performing emails.
    *   **Synthesize:** "The brand voice is 'Professional but Witty'."
    *   **Action:** Generate text matching that voice.

### 4. The Authority Matrix (Guardrails)
This is critical for "Autonomous" systems. We don't want an agent accidentally refunding everyone or deleting the website.

*   **Level 1: Green Zone (Autonomous)**
    *   **Actions:** Drafting content, analyzing data, running simulations, internal tagging.
    *   **Protocol:** Execute immediately. Log to feed.
*   **Level 2: Amber Zone (Review)**
    *   **Actions:** Changing website CSS, Scheduling social posts, Updating customer records.
    *   **Protocol:** Execute only if confidence_score > 90%. Otherwise, create a "Pending Approval" card.
*   **Level 3: Red Zone (Restricted)**
    *   **Actions:** Charging credit cards, Sending bulk emails (>50 people), Deleting assets.
    *   **Protocol:** ALWAYS require Human Confirmation via the UI.

### 5. The Error Handling Protocol
If an agent fails (e.g., the Stripe API is down), it must not crash the system.

**The "Self-Correction" Loop:**
1.  **Detect Error:** "API Timeout."
2.  **Report:** Send ERROR status to Orchestrator.
3.  **Fallback:** The Orchestrator triggers the System Admin Agent.
4.  **Notify User:** "I tried to generate the code, but Stripe is unresponsive. I have queued this task to retry in 10 minutes."

### Summary of the SAP
By adopting this protocol, we transform SkillPlate from a "Website Builder" into a Deterministic Neural Network.
*   Standardized Inputs/Outputs = No confusion.
*   Shared Memory = Agents actually "know" the business.
*   Authority Levels = Safety and Trust.
