---
name: instantly
display_name: "Instantly"
description: "Send cold email campaigns, add leads, check analytics, and manage outreach via Instantly.ai"
category: sales
icon: send
skill_type: sandbox
catalog_type: platform
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: INSTANTLY_API_KEY
    name: "Instantly API Key"
    description: "API key from Instantly.ai (Settings > API & Integrations > API Keys). Use a key with campaigns and leads scopes."
tool_schema:
  name: instantly
  description: "Send cold email campaigns, add leads, check analytics, and manage outreach via Instantly.ai"
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['list_campaigns', 'get_campaign', 'add_lead', 'add_leads_bulk', 'list_leads', 'launch_campaign', 'pause_campaign', 'campaign_analytics', 'list_accounts']
      campaign_id:
        type: "string"
        description: "Campaign ID — for get_campaign, add_lead, add_leads_bulk, list_leads, launch_campaign, pause_campaign, campaign_analytics"
        default: ""
      email:
        type: "string"
        description: "Lead email address — for add_lead"
        default: ""
      first_name:
        type: "string"
        description: "Lead first name — for add_lead"
        default: ""
      last_name:
        type: "string"
        description: "Lead last name — for add_lead"
        default: ""
      company_name:
        type: "string"
        description: "Lead company name — for add_lead"
        default: ""
      website:
        type: "string"
        description: "Lead company website — for add_lead"
        default: ""
      personalization:
        type: "string"
        description: "Custom personalization text — for add_lead (used in email templates as {{personalization}})"
        default: ""
      custom_variables:
        type: "string"
        description: "JSON object of custom variables — for add_lead (e.g. '{\"title\": \"CEO\", \"city\": \"Austin\"}')"
        default: ""
      leads_json:
        type: "string"
        description: "JSON array of lead objects — for add_leads_bulk. Each object: {email, first_name, last_name, company_name, personalization, custom_variables}"
        default: ""
      search:
        type: "string"
        description: "Search filter — for list_campaigns"
        default: ""
      status:
        type: "string"
        description: "Filter by status — for list_campaigns (e.g. 'active', 'paused', 'draft', 'completed')"
        default: ""
      limit:
        type: "integer"
        description: "Max results — for list_campaigns, list_leads"
        default: 10
    required: [action]
---
# Instantly

Send cold email campaigns, add leads, check analytics, and manage outreach via Instantly.ai.

## Recommended Workflow for AI SDR
1. Use Apollo to find leads (search_people → enrich_person for emails).
2. Use Hunter to verify emails (email_verifier).
3. Use **list_campaigns** to see existing campaigns.
4. Use **add_lead** or **add_leads_bulk** to add verified leads to a campaign.
5. Use **launch_campaign** to start sending.
6. Use **campaign_analytics** to monitor opens, replies, bounces.

## Be Proactive
- When the user has leads with verified emails, offer to add them to a campaign.
- When adding leads, include personalization text for better reply rates.
- After adding leads, suggest launching the campaign if it's paused.
- When checking analytics, highlight key metrics: open rate, reply rate, bounce rate.

## Actions

### list_campaigns
List all campaigns in the workspace.
```
action: list_campaigns
status: "active"
limit: 10
```
Returns: campaign ID, name, status, created date.

### get_campaign
Get details of a specific campaign.
```
action: get_campaign
campaign_id: "abc123"
```
Returns: full campaign details including sequences, schedule, and settings.

### add_lead
Add a single lead to a campaign. Include personalization for better outreach.
```
action: add_lead
campaign_id: "abc123"
email: "john@acme.com"
first_name: "John"
last_name: "Smith"
company_name: "Acme Inc"
personalization: "Noticed Acme recently launched a new product line — congrats!"
```

### add_leads_bulk
Add multiple leads to a campaign at once.
```
action: add_leads_bulk
campaign_id: "abc123"
leads_json: "[{\"email\":\"john@acme.com\",\"first_name\":\"John\",\"last_name\":\"Smith\",\"company_name\":\"Acme Inc\"},{\"email\":\"jane@example.com\",\"first_name\":\"Jane\"}]"
```

### list_leads
List leads in a campaign.
```
action: list_leads
campaign_id: "abc123"
limit: 20
```

### launch_campaign
Start sending emails for a campaign.
```
action: launch_campaign
campaign_id: "abc123"
```

### pause_campaign
Pause/stop a campaign.
```
action: pause_campaign
campaign_id: "abc123"
```

### campaign_analytics
Get campaign performance metrics.
```
action: campaign_analytics
campaign_id: "abc123"
```
Returns: total leads, contacted, opens, open rate, replies, reply rate, bounces, unsubscribes.

### list_accounts
List connected email accounts used for sending.
```
action: list_accounts
```
Returns: email address, warmup status, daily send limit.
