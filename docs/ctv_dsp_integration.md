# Addendum: Programmatic CTV & DSP Integration

## Objective
Act as a Senior Ad-Tech Engineer. We need to expand OrchestraAI's publishing capabilities beyond traditional social walled gardens (Meta, Google) by integrating a Programmatic CTV node. This will allow the LangGraph engine to route Seedance 2.0 generated videos directly to streaming TV inventory via a DSP (Demand-Side Platform) like The Trade Desk.

## Execution Steps

### 1. The DSP Connector Setup
- Create a new file: `src/orchestra/connectors/dsp_client.py`.
- Implement a `DSPClient` class designed to interface with a standard programmatic REST API (modeling The Trade Desk API structure).
- **Required Methods:**
  - `authenticate()`: Handle token generation using `DSP_API_KEY` and `DSP_PARTNER_ID`.
  - `create_ctv_campaign(name, budget, start_date, end_date)`: Creates the parent campaign.
  - `create_ctv_ad_group(campaign_id, target_audience, bid_cpm)`: Configures the programmatic auction targeting (e.g., Connected TV devices only).
  - `upload_creative(video_url, compliance_status)`: Pushes the Seedance 2.0 video URL to the DSP. Must strictly check that `compliance_status` is `Passed` from the Vision Gate before uploading.

### 2. LangGraph Routing Updates
- Open `src/orchestra/core/orchestrator.py` (or where your LangGraph StateGraph is defined).
- Update the `Publish` node logic. 
- When the Strategy LLM selects `streaming_tv` or `ctv` as a destination platform, the node must route the payload to the new `DSPClient`.
- Ensure the budget allocated to the CTV node is strictly bound by the existing `FinancialGuardrails` module.

### 3. Strategy Engine Prompt Update
- Update the system prompt for the Strategy Engine (Together AI / Llama 3) to explicitly include CTV as a routing option.
- Add instruction: *"If the user requests high-brand awareness or television placement, and a Seedance 2.0 video asset has been generated and cleared by the Vision Gate, you may allocate budget to the 'ctv' platform to buy streaming TV inventory via our DSP."*

### 4. Frontend UI Additions
- Open `frontend/src/app/dashboard/page.tsx` (and relevant component files).
- Add "Streaming TV (CTV)" to the cross-platform analytics breakdown.
- Include mock metrics specific to CTV, such as **VCR (Video Completion Rate)** and **eCPM (Effective Cost Per Mille)**, alongside the standard clicks and impressions.

## Instructions for Cursor:
Please scan the backend connectors and LangGraph pipeline, then implement the `DSPClient` and wire it into the publishing state. Ensure the strict financial guardrails apply to the programmatic bids just as they do for the standard social APIs.


The resulting architecture is incredibly powerful:
User types: "Run a $5k brand awareness campaign on streaming TV."

LangGraph drafts the script.

Seedance 2.0 renders the commercial.

GPT-4o Vision verifies there is no copyrighted IP in the video.

The Trade Desk API creates a CTV campaign and starts bidding on Roku and Hulu inventory.

---

## Implementation status (codebase)

| Component | Location |
|-----------|----------|
| `DSPClient` | `src/orchestra/connectors/dsp_client.py` — `authenticate`, `create_ctv_campaign`, `create_ctv_ad_group`, `upload_creative` (compliance must be `Passed`) |
| Env vars | `DSP_API_KEY`, `DSP_PARTNER_ID`, `DSP_BASE_URL` in `src/orchestra/config.py` and `.env.example` |
| LangGraph publish branch | `src/orchestra/agents/orchestrator.py` → `platform_node` routes `ctv` / `streaming_tv` to `src/orchestra/agents/dsp_publish.py` |
| Financial guardrails | `check_all_guardrails` + tenant caps before DSP calls |
| Vision gate | `upload_creative` only when visual compliance `safe` for generated video URLs |
| Policy / content | `src/orchestra/agents/policy.py` (`ctv`, `streaming_tv`); `src/orchestra/agents/content.py` CTV strategy note; intent keywords in `orchestrator.py` |
| Analytics / dashboard | `ENGAGEMENT_BENCHMARKS["ctv"]`; overview sets `AnalyticsRequest.include_ctv_dashboard_preview=True` to merge an illustrative CTV row; `PlatformMetrics` VCR + eCPM; `frontend` dashboard tooltip + CTV panel |

