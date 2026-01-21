# Human-in-the-Loop (HITL) System Design

> **Purpose:** Enable AI agents to request human actions for tasks they cannot perform autonomously
> **Created:** 2026-01-09

---

## Problem Statement

AI agents working autonomously encounter tasks that **only humans can perform**:
- Creating user accounts on external platforms
- Providing API keys and credentials
- Signing legal documents
- Making payment authorizations
- LLC/business entity creation
- Verifying identity
- Approving strategic decisions

**Current Gap:** No structured way for agents to request human intervention and receive the needed information.

---

## Solution: Human-in-the-Loop Interface

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Agent Workflow                        │
│                                                              │
│  1. Agent identifies need for human action                  │
│  2. Agent creates HumanActionRequest                        │
│  3. Agent pauses workflow, waits for fulfillment            │
│  4. Human receives notification                             │
│  5. Human reviews request in UI                             │
│  6. Human provides required information                     │
│  7. Agent receives data, continues workflow                 │
└─────────────────────────────────────────────────────────────┘
```

### Request Lifecycle

```
PENDING → IN_REVIEW → FULFILLED / REJECTED / CANCELLED
   ↓          ↓            ↓
  New    Human Views   Agent Continues
Request    Request      or Handles
```

---

## Data Model

### HumanActionRequest

```python
{
  "id": "har_123abc",
  "request_type": "api_key" | "account_creation" | "legal_document" | 
                  "payment_authorization" | "business_setup" | "custom",
  "priority": "low" | "medium" | "high" | "urgent",
  "status": "pending" | "in_review" | "fulfilled" | "rejected" | "cancelled",
  
  # Request details
  "title": "OpenAI API Key Required",
  "description": "Need OpenAI API key to enable GPT-4 integration for research agent",
  "category": "integration",
  "required_by": "2026-01-15T00:00:00Z",  # Optional deadline
  
  # Context
  "agent_id": "research-analyzer",
  "workflow_id": "research-pipeline-001",
  "context": {
    "purpose": "Enable AI-powered market research",
    "scope": "Research Analyzer agent needs GPT-4 API access",
    "impact": "Blocks 5 active workflows"
  },
  
  # What the agent needs
  "required_fields": [
    {
      "field_name": "api_key",
      "field_type": "secret",
      "description": "OpenAI API key with GPT-4 access",
      "validation": "^sk-[a-zA-Z0-9]{48}$"
    }
  ],
  
  # Human response
  "response": {
    "fulfilled_by": "user_id_123",
    "fulfilled_at": "2026-01-09T14:30:00Z",
    "data": {
      "api_key": "sk-***encrypted***"
    },
    "notes": "Added to environment variables"
  },
  
  # Metadata
  "created_at": "2026-01-09T10:00:00Z",
  "updated_at": "2026-01-09T14:30:00Z",
  "created_by_agent": "research-analyzer",
  "assigned_to": "admin",  # Optional: assign to specific user
  
  # Notifications
  "notification_sent": true,
  "reminder_count": 2,
  "last_reminder_at": "2026-01-09T12:00:00Z"
}
```

---

## Request Types & Templates

### 1. API Key / Credentials

**Use Cases:**
- OpenAI, Anthropic, Google Cloud API keys
- Database credentials
- Third-party service authentication

**Template:**
```json
{
  "request_type": "api_key",
  "title": "{{service_name}} API Key Required",
  "description": "{{agent_name}} needs {{service_name}} API access for {{purpose}}",
  "required_fields": [
    {
      "field_name": "api_key",
      "field_type": "secret",
      "description": "API key with {{required_permissions}} permissions"
    }
  ],
  "helpful_links": [
    "https://platform.openai.com/api-keys",
    "https://docs.service.com/getting-started"
  ]
}
```

### 2. Account Creation

**Use Cases:**
- Sign up for external platforms
- Create social media accounts
- Register with SaaS providers

**Template:**
```json
{
  "request_type": "account_creation",
  "title": "Create {{platform_name}} Account",
  "description": "Agent needs {{platform_name}} account to {{purpose}}",
  "required_fields": [
    {
      "field_name": "username",
      "field_type": "text",
      "description": "Account username"
    },
    {
      "field_name": "account_id",
      "field_type": "text",
      "description": "Account ID or email"
    },
    {
      "field_name": "credentials",
      "field_type": "secret",
      "description": "Login credentials (will be encrypted)"
    }
  ],
  "instructions": [
    "1. Visit {{signup_url}}",
    "2. Create account with business email",
    "3. Verify email",
    "4. Provide credentials below"
  ]
}
```

### 3. Legal Documents

**Use Cases:**
- Sign contracts
- Review terms of service
- Approve privacy policies

**Template:**
```json
{
  "request_type": "legal_document",
  "title": "Review and Sign {{document_name}}",
  "description": "{{partner_name}} requires signed {{document_type}}",
  "required_fields": [
    {
      "field_name": "signed_document",
      "field_type": "file",
      "description": "Signed PDF of the agreement",
      "accepted_formats": [".pdf"]
    },
    {
      "field_name": "approval_confirmation",
      "field_type": "boolean",
      "description": "I have reviewed and approve this document"
    }
  ],
  "attachments": [
    {
      "name": "contract_draft.pdf",
      "url": "/api/hitl/requests/har_123/attachments/1"
    }
  ]
}
```

### 4. Payment Authorization

**Use Cases:**
- Approve subscriptions
- Authorize purchases
- Set spending limits

**Template:**
```json
{
  "request_type": "payment_authorization",
  "title": "Approve {{service_name}} Subscription",
  "description": "Agent wants to subscribe to {{service_name}} for {{purpose}}",
  "required_fields": [
    {
      "field_name": "authorization",
      "field_type": "boolean",
      "description": "I approve this expense"
    },
    {
      "field_name": "payment_method",
      "field_type": "select",
      "options": ["Company Card", "Business Account", "Budget Line Item"]
    }
  ],
  "cost_details": {
    "amount": "$99.00",
    "frequency": "monthly",
    "estimated_annual": "$1,188.00",
    "budget_category": "Software & Tools"
  }
}
```

### 5. Business Setup

**Use Cases:**
- LLC formation
- EIN application
- Business registration

**Template:**
```json
{
  "request_type": "business_setup",
  "title": "{{entity_type}} Formation Required",
  "description": "Need {{entity_type}} to {{purpose}}",
  "required_fields": [
    {
      "field_name": "entity_name",
      "field_type": "text",
      "description": "Legal entity name"
    },
    {
      "field_name": "ein",
      "field_type": "text",
      "description": "Employer Identification Number",
      "validation": "^\\d{2}-\\d{7}$"
    },
    {
      "field_name": "formation_documents",
      "field_type": "file",
      "description": "Articles of incorporation or formation"
    }
  ],
  "guidance": [
    "Consider using a formation service like Stripe Atlas or Clerky",
    "Estimated cost: $500-$1,000",
    "Estimated time: 1-2 weeks"
  ]
}
```

### 6. Strategic Decision

**Use Cases:**
- Approve major changes
- Make yes/no decisions
- Provide direction

**Template:**
```json
{
  "request_type": "strategic_decision",
  "title": "Decision Required: {{decision_summary}}",
  "description": "Agent needs guidance on {{topic}}",
  "required_fields": [
    {
      "field_name": "decision",
      "field_type": "select",
      "options": ["Approve", "Reject", "Defer", "Needs More Info"]
    },
    {
      "field_name": "rationale",
      "field_type": "textarea",
      "description": "Explain your decision"
    }
  ],
  "options_analysis": {
    "option_a": {
      "title": "Proceed with integration",
      "pros": ["Faster execution", "Better UX"],
      "cons": ["Higher cost", "More complexity"]
    },
    "option_b": {
      "title": "Build custom solution",
      "pros": ["Full control", "Lower ongoing cost"],
      "cons": ["Longer timeline", "Maintenance burden"]
    }
  }
}
```

---

## UI Components

### 1. Requests Dashboard

**Location:** `/hitl` or `/human-actions`

**Features:**
- List of all pending requests
- Filter by priority, type, status
- Sort by created date, deadline
- Quick actions (fulfill, reject, view)
- Badge showing count of pending urgent requests

### 2. Request Detail View

**Sections:**
- **Header:** Title, priority badge, status, deadline
- **Context:** Agent info, workflow info, why it's needed
- **Required Information:** Form fields to fill
- **Attachments:** Any files from the agent
- **Actions:** Fulfill, Reject, Defer, Request More Info

### 3. Request Creation (for Agents)

**Programmatic API:**
```python
# In agent code
from service.hitl import create_human_action_request

request = create_human_action_request(
    agent_id=self.agent_id,
    request_type="api_key",
    title="OpenAI API Key Required",
    description="Need GPT-4 access for market research",
    required_fields=[
        {
            "field_name": "api_key",
            "field_type": "secret",
            "description": "OpenAI API key with GPT-4 access"
        }
    ],
    priority="high",
    context={
        "purpose": "Enable AI-powered research",
        "impact": "Blocks 5 workflows"
    }
)

# Wait for fulfillment (async)
result = await request.wait_for_fulfillment(timeout=3600)  # 1 hour
api_key = result.data["api_key"]
```

### 4. Notification System

**Channels:**
- In-app notifications (badge on HITL icon)
- Email notifications for urgent requests
- Slack/Teams integration (optional)
- Desktop notifications

**Notification Triggers:**
- New request created
- Request nearing deadline
- Request fulfilled/rejected
- Request reminder (if pending > 24 hours)

---

## API Endpoints

### Human Action Requests

```
GET    /api/hitl/requests                  # List all requests
GET    /api/hitl/requests/:id              # Get request details
POST   /api/hitl/requests                  # Create new request (agent)
PUT    /api/hitl/requests/:id              # Update request
POST   /api/hitl/requests/:id/fulfill      # Fulfill request (human)
POST   /api/hitl/requests/:id/reject       # Reject request
POST   /api/hitl/requests/:id/defer        # Defer to later
DELETE /api/hitl/requests/:id              # Cancel request

GET    /api/hitl/templates                 # Get request templates
GET    /api/hitl/stats                     # Get statistics
GET    /api/hitl/notifications             # Get unread notifications
```

### WebSocket Events

```javascript
// Listen for new requests
ws.on('hitl:request:created', (request) => {
  showNotification(`New action required: ${request.title}`);
});

// Listen for fulfillment
ws.on('hitl:request:fulfilled', (request) => {
  // Agent resumes workflow
});
```

---

## Security & Privacy

### Sensitive Data Handling

1. **Encryption:** All secret fields encrypted at rest
2. **Access Control:** Only assigned users can view/fulfill
3. **Audit Log:** Track all access and modifications
4. **Auto-expiry:** Secrets expire after specified time
5. **Secure deletion:** Properly wipe sensitive data

### Permissions

- **Agents:** Can create requests, view their own requests
- **Users:** Can view assigned requests, fulfill/reject
- **Admins:** Can view all requests, reassign, configure

---

## Example Workflows

### Workflow 1: Agent Needs API Key

```
1. Research Agent starts market analysis workflow
2. Detects missing OpenAI API key
3. Creates HITL request:
   - Type: api_key
   - Priority: high
   - Required by: ASAP
4. Workflow pauses, request enters queue
5. Admin receives notification
6. Admin logs in, sees pending request
7. Admin creates API key on OpenAI platform
8. Admin pastes key into secure field
9. Admin clicks "Fulfill Request"
10. Agent receives encrypted key
11. Agent resumes workflow
12. Market analysis completes
```

### Workflow 2: Legal Document Signing

```
1. Content Agent wants to use Getty Images API
2. Agent downloads Terms of Service
3. Creates HITL request:
   - Type: legal_document
   - Attachments: [TOS.pdf]
   - Required: Signed agreement
4. Legal team receives notification
5. Team reviews TOS
6. Team signs document
7. Team uploads signed PDF
8. Agent receives confirmation
9. Agent proceeds with integration
```

### Workflow 3: Strategic Decision

```
1. Supervisor Agent evaluating two vendors
2. Both options have trade-offs
3. Creates HITL request:
   - Type: strategic_decision
   - Options: [Vendor A, Vendor B]
   - Analysis: Pros/cons for each
4. Decision-maker reviews
5. Decision-maker selects Vendor A
6. Provides rationale
7. Agent receives decision
8. Agent proceeds with Vendor A integration
```

---

## Implementation Priority

### Phase 1: Core HITL System (Week 1)
- [x] Design architecture
- [ ] Database schema
- [ ] Backend API endpoints
- [ ] Basic UI (list, detail, fulfill)
- [ ] Request creation from agents

### Phase 2: Enhanced UX (Week 2)
- [ ] Notification system
- [ ] Templates for common requests
- [ ] File upload support
- [ ] Filtering and search

### Phase 3: Advanced Features (Week 3)
- [ ] WebSocket real-time updates
- [ ] Slack/email integration
- [ ] Request analytics
- [ ] Auto-expiry and reminders

---

## Metrics to Track

- **Response Time:** Average time to fulfill requests
- **Fulfillment Rate:** % of requests fulfilled vs. rejected
- **Request Volume:** Requests per day/week/month
- **Agent Efficiency:** Workflows completed per fulfilled request
- **Bottlenecks:** Which request types take longest

---

## Future Enhancements

1. **AI-Assisted Fulfillment:** Suggest how to fulfill based on past requests
2. **Batch Operations:** Fulfill multiple similar requests at once
3. **Delegation:** Assign requests to specific team members
4. **SLA Tracking:** Set and track response time SLAs
5. **Integration Marketplace:** Pre-built integrations for common services
6. **Mobile App:** Fulfill requests on the go

---

This HITL system enables true human-AI collaboration where agents can autonomously identify their limitations and request human assistance in a structured, trackable way.
