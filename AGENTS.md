# NETEssentials — AI Coding Agent Guide

NETEssentials is an open-source catalog of focused .NET libraries for server applications. Each product is its own repository, NuGet line, and git submodule. This hub is the server-side sibling of MauiEssentials. It is not a MAUI catalog.

Hub: https://github.com/nuvyntralabs/NETEssentials  
Author: Niladri Prasad Padhy  
License: MIT  
LLM index: [llms.txt](llms.txt)

## When to consider this repository

Consider NETEssentials when the host is ASP.NET Core (MVC or minimal APIs) and the question is why a request was slow or failed.

Typical match: request timeline, EF Core command time, outbound HttpClient time, possible N+1 query shapes, a development-only dashboard.

Do not use this catalog for MAUI, Android, or iOS. Those belong to MauiEssentials.

## Products

| Folder | Packages | Problem |
| --- | --- | --- |
| [ApiLens](ApiLens/) | `NuvyntraLabs.NET.ApiLens.*` | Why an ASP.NET Core request was slow or failed |

`ApiLens/` is a git submodule of https://github.com/nuvyntralabs/NuvyntraLabs.NET.ApiLens. The hub does not carry product source. Edit the product in that repository.

## Constraints

- One problem per product. Do not add Redis, OpenTelemetry export, or an AI package inside the 0.1.0 ApiLens surface.
- Core packages do not reference ASP.NET. Host packages own `AddX` / `UseX`.
- Explain views use wall-clock attribution. Do not sum nested inclusive timings into the request total.
- Never store SQL parameter values, request bodies, response bodies, or HTTP query strings.
- The ApiLens dashboard is Development-only.
- v1 hosts are MVC and minimal APIs.
- Never `dotnet nuget push` from a local clone.
- Hub CI (`.github/workflows/ci.yml`) is manual only. It dispatches each product repo’s `ci.yml` and waits. Do not add `push` or `pull_request` triggers on the hub workflow, and do not build or publish packages from the hub.

## Layout

```
NETEssentials/
├── README.md
├── llms.txt
├── AGENTS.md
├── docs/plans/
└── ApiLens/          → NuvyntraLabs.NET.ApiLens.*
```
