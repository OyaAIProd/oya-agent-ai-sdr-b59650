---
name: linkedin
display_name: "LinkedIn"
description: "Get profile info, create posts, manage company pages, and engage with content on LinkedIn"
category: social
icon: linkedin
skill_type: sandbox
catalog_type: platform
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: LINKEDIN_ACCESS_TOKEN
    name: "LinkedIn Access Token"
    description: "OAuth access token (auto-provided by gateway connection)"
config_schema:
  properties:
    default_visibility:
      type: select
      label: "Default Post Visibility"
      description: "Who can see posts created by the agent"
      options: ["PUBLIC", "CONNECTIONS"]
      default: "PUBLIC"
      group: defaults
    organization_id:
      type: string
      label: "Organization ID"
      description: "LinkedIn organization/company page ID for company posts (numeric ID from your page URL)"
      placeholder: "12345678"
      group: defaults
    posting_rules:
      type: text
      label: "Posting Rules"
      description: "Rules for how the LLM should create posts"
      placeholder: "- Keep posts professional and concise\n- Always include relevant hashtags\n- Never post controversial content"
      group: rules
    safety_rules:
      type: text
      label: "Safety Rules"
      description: "Safety rules and constraints"
      placeholder: "- Always confirm with the user before posting\n- Never share confidential information"
      group: rules
tool_schema:
  name: linkedin
  description: "Get profile info, create posts, manage company pages, and engage with content on LinkedIn"
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['get_profile', 'create_post', 'delete_post', 'get_company', 'create_company_post', 'react_to_post', 'create_comment', 'get_connections_count', 'share_url']
      text:
        type: "string"
        description: "Post text content -- for create_post, create_company_post, create_comment"
        default: ""
      visibility:
        type: "string"
        description: "Post visibility: PUBLIC or CONNECTIONS -- for create_post, create_company_post"
        default: "PUBLIC"
      url:
        type: "string"
        description: "URL to share -- for share_url"
        default: ""
      title:
        type: "string"
        description: "Title for shared URL -- for share_url"
        default: ""
      post_urn:
        type: "string"
        description: "Post URN (e.g. urn:li:share:123 or urn:li:ugcPost:123) -- for delete_post, react_to_post, create_comment"
        default: ""
      reaction_type:
        type: "string"
        description: "Reaction type: LIKE, PRAISE, EMPATHY, INTEREST, APPRECIATION, ENTERTAINMENT, MAYBE -- for react_to_post"
        default: "LIKE"
      organization_id:
        type: "string"
        description: "LinkedIn organization/company page ID -- for get_company, create_company_post"
        default: ""
      comment:
        type: "string"
        description: "Comment text -- for create_comment"
        default: ""
    required: [action]
---
# LinkedIn

Get profile info, create posts, manage company pages, and engage with content on LinkedIn.

## Profile
- **get_profile** -- Get your LinkedIn profile info (name, headline, vanity name, profile picture).
- **get_connections_count** -- Get the number of 1st-degree connections.

## Posting
- **create_post** -- Create a text post on your LinkedIn feed. Provide `text` and optional `visibility` (PUBLIC or CONNECTIONS).
- **share_url** -- Share a URL with optional commentary. Provide `url`, optional `title`, `text`, and `visibility`.
- **delete_post** -- Delete a post. Provide `post_urn`.

## Company Pages
- **get_company** -- Get company page details. Provide `organization_id`.
- **create_company_post** -- Post on behalf of a company page (requires admin access). Provide `organization_id`, `text`, and optional `visibility`.

## Engagement
- **react_to_post** -- React to a post. Provide `post_urn` and `reaction_type` (LIKE, PRAISE, EMPATHY, INTEREST, APPRECIATION, ENTERTAINMENT, MAYBE).
- **create_comment** -- Comment on a post. Provide `post_urn` and `comment`.
