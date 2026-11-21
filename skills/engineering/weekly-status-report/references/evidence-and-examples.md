# Evidence and examples

## Where to look

| Source | Search and verify | Do not infer |
| --- | --- | --- |
| Slack / Teams | Search in-scope messages by the person's identity, project names, artifact IDs, and terms such as deployed, decided, approved, blocked, fixed, and handoff. Open surrounding threads and corroborating owner updates. | An announcement equals rollout; a mention, reaction or channel membership is ownership. |
| Granola / Zoom or other meeting notes | Use approved connectors or supplied notes/exports; check date, speaker, decision, owner and action status. Prefer confirmed decisions or artifacts to an AI summary; use a calendar entry only to locate notes. | Attendance or an assigned action equals completed work; a summary proves a spoken commitment or completed task. |
| GitHub | Look at in-window PRs authored/coauthored, substantive reviews, approvals, and linked issues across the scoped repositories. Check older PRs updated/merged in the window; verify human role, merge state, environments and rollout separately. | PR count is impact, review is authorship, bot attribution is individual work, or merge means production. |
| Work email | Search sent and relevant received threads by date, collaborators and workstreams. Confirm decisions, deliveries or follow-through from replies and artifacts when needed. | Being copied, drafting a message, or a request implies action completed. |
| Trackers / logs / docs | Follow linked IDs to the outcome's strongest evidence: release and audit logs, measured results, accepted deliverables or dated decisions. | A stale “Done” label proves production, or raw activity counts prove business value. |

Use connector-specific skills and native filters where available. Report from authorized exports when a service is inaccessible; do not assume a connector exists for every tool or seek a broad export when a narrow excerpt would do.

## Examples

**One outcome, three sources.** A PR merged on Tuesday, Slack announced the rollout on Wednesday, and the deployment log shows production release Thursday. Report it once, using Thursday for production. If the person only verified rollback, say that instead of claiming they built or deployed the change.

**Unequal weight.** A customer-facing recovery and a routine housekeeping pass should not receive equal prominence. The recovery leads with the verified effect and scope; combine minor housekeeping only if it helps the audience understand the week. No outcome metric is better than a made-up one.

**Template and status conflict.** The old format says “Shipped / Next / Need.” The implementation merged and passed QA, but production approval is pending. Keep the format without putting it under “Shipped” as a production success; identify the finished QA milestone as such and use “Need” only for a real decision or help request. If the current audience wants a slipped milestone called out, that request wins over the example.

**Partial and quiet.** GitHub scope is limited, Teams was inaccessible, and supplied notes verify one audit checklist review. Report that one contribution and separately note the coverage gaps. Don't report zero contributions in the inaccessible areas or turn a planned rollout into a completed one.
