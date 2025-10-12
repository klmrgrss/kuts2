# Smart-ID testing guide

This application authenticates against the Smart-ID demo environment (`https://sid.demo.sk.ee/smart-id-rp/v2/`). To make requests succeed you need to configure the relying party credentials that SK ID Solutions exposes for the demo tenant:

| Variable | Value | Notes |
| --- | --- | --- |
| `SMARTID_RP_UUID` | `00000000-0000-4000-8000-000000000000` | Default demo relying party UUID.
| `SMARTID_RP_NAME` | `DEMO` | Default demo relying party name.

> **Tip:** the demo UUID cannot access Smart-ID Basic accounts; stick to Qualified (`-Q`) demo certificates when picking a test identity.

## Recommended Estonian test personal codes

The Smart-ID team publishes auto-responder “mock” accounts for integration testing. The Estonian document numbers listed in their [test accounts table](https://github.com/SK-EID/smart-id-documentation/blob/master/docs/modules/ROOT/pages/test_accounts.adoc) correspond to national ID numbers that you can enter into the login form (strip the `PNOEE-` prefix and everything after the personal code). The most useful ones are:

| Personal code | Demo account behaviour |
| --- | --- |
| `40404040009` | Adult user with Qualified certificate (auto-approves). |
| `61101019999` | Minor account (auto-approves). |
| `50001029996` | Adult account issued with Qualified certificate (auto-approves). |
| `39901012239` | Account that simulates “user already has another active account”. |
| `30403039917` | Account that returns `USER_REFUSED`. |
| `30403039928` | Account that returns `USER_REFUSED_INTERACTION` for `displayTextAndPIN`. |
| `30403039972` | Account that returns `WRONG_VC`. |
| `30403039983` | Account that times out. |

These IDs work end-to-end without needing to run the Smart-ID mobile app. If you need to test other outcomes, consult the Smart-ID documentation linked above for additional mock document numbers and derive the personal code using the same rule.

## Why 60001019906 fails

The number `60001019906` belongs to a manual demo account that expects someone to approve the request inside the Smart-ID mobile application. Because our demo relying party credentials are not registered against that manual account, the Smart-ID API answers with `No suitable account found`. Switch to one of the auto-responder personal codes above to verify the integration locally.
