# NETEssentials

Open-source **.NET** libraries for server and backend applications. This catalog maps a developer requirement to a focused NuGet package. It is the server-side sibling of [MauiEssentials](https://github.com/nuvyntralabs/MauiEssentials). Each product is its own repository, NuGet line, and git submodule.

**Hub:** https://github.com/nuvyntralabs/NETEssentials  
**Author:** [Niladri Prasad Padhy](https://github.com/NiladriPadhy)  
**License:** MIT  
**LLM index:** [llms.txt](llms.txt) · [AGENTS.md](AGENTS.md)

## What this catalog solves

ASP.NET Core and OpenTelemetry already record requests, traces, and metrics. NETEssentials packages sit above that and answer a developer question the raw telemetry does not: why this call was slow, failing, or doing too much work.

Install the package that matches the requirement. Do not pull a future package for a problem the first one does not own.

## Products

| Product | Purpose | Packages |
| --- | --- | --- |
| [ApiLens](ApiLens/) | Why an ASP.NET Core request was slow or failed. Development dashboard at `/_apilens`. | `NuvyntraLabs.NET.ApiLens.*` |

Plan: [docs/plans/apilens.md](docs/plans/apilens.md).  
Repository: https://github.com/nuvyntralabs/NuvyntraLabs.NET.ApiLens

## Design rules

1. One problem per product. Package descriptions name the problem, not "part of NETEssentials".
2. Prefer the framework. Do not replace ASP.NET Core diagnostics or OpenTelemetry.
3. Optional probes reference the core package only. They do not reference each other.
4. Publishing is pipeline-only. Do not `dotnet nuget push` from a local clone.
5. `net10.0` unless a product documents a wider set.

```bash
git clone --recurse-submodules https://github.com/nuvyntralabs/NETEssentials.git
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

## Continuous integration

The hub workflow at `.github/workflows/ci.yml` is **manual only** (`workflow_dispatch`). It does not run on push to the hub. A manual run dispatches each product submodule’s `CI` workflow and waits for the results. The hub does not build or publish packages.

Store a GitHub token that can dispatch workflows on `nuvyntralabs/NuvyntraLabs.NET.*` as the `HUB_DISPATCH_TOKEN` Actions secret on this hub. The optional **product** input limits the dispatch to one submodule folder (for example `ApiLens`).

Each product repository owns version alignment, `NUGET_KEY_NET`, tests, pack, and publish.
