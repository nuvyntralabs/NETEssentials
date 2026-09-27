# ApiLens — design plan

**Status:** 0.1.0 in the `ApiLens/` submodule. Not published.  
**Product:** Nuvyntra ApiLens — developer-first runtime diagnostics for ASP.NET Core.  
**Packages:** `NuvyntraLabs.NET.ApiLens`, `.AspNetCore`, `.EntityFrameworkCore`, `.Http`, `.UI`  
**Hub folder:** `ApiLens/` (git submodule)  
**GitHub:** https://github.com/nuvyntralabs/NuvyntraLabs.NET.ApiLens  
**TFM:** `net10.0`

This is a server product in NETEssentials, not a `Plugin.Maui.*` package. The short name collides with [endjin/ApiLens](https://github.com/endjin/ApiLens) (XML doc search). The NuGet id stays `NuvyntraLabs.NET.ApiLens`.

## Positioning

ASP.NET Core already exposes request, routing, and exception metrics. OpenTelemetry already collects traces and metrics. ApiLens sits above both and answers why a request was slow or failed. It reads `System.Diagnostics`. It does not ship a second telemetry pipeline.

## Locked decisions

1. NETEssentials is the hub. ApiLens is the first product. One git repository for the product, several NuGet packages inside it. Redis, OpenTelemetry export, and AI are later packages in that same repository, not extra submodules.
2. Package prefix is `NuvyntraLabs.NET.ApiLens.*`.
3. v1 is the request timeline, EF Core commands, outbound HTTP, a possible-N+1 heuristic, rule-based explain text, and the development dashboard.
4. Collection is DiagnosticSource / `Activity`. OpenTelemetry export is later and optional.
5. The dashboard is served only when the host environment is Development and `EnableDashboard` is true. There is no production dashboard switch.
6. SQL parameter values are never read. Request bodies, response bodies, and HTTP query strings are never stored. Development may store SQL text after literal redaction. Production drops that text after shape grouping.
7. v1 hosts are MVC and minimal APIs. SignalR, gRPC, and Blazor circuits are out. Work that leaves the request is not attributed.

## Time model

Middleware, the endpoint, EF, and HTTP are nested. Explain percentages are a share of wall-clock time from `TimelineAttributor`. Overlapping operations are counted once, awarded to the longer operation. Each operation still shows its own duration on the timeline. Do not sum inclusive durations into the request total.

N+1 is a heuristic: the same redacted SQL shape repeated at least `NPlusOneRepeatThreshold` times (default 8) in one request. The UI copy says "possible N+1". Estimated unnecessary queries are `count - 1`.

## Registration

```csharp
builder.Services.AddApiLens();
builder.Services.AddApiLensEntityFrameworkCore();
builder.Services.AddApiLensHttp();
app.UseApiLens();
```

`AddApiLens()` is on the ASP.NET Core package. Core has no hosting types. EF and HTTP reference core only and write into `RequestScope.Current`.

## Layout

```
ApiLens/
├── src/NuvyntraLabs.NET.ApiLens/
├── src/NuvyntraLabs.NET.ApiLens.AspNetCore/
├── src/NuvyntraLabs.NET.ApiLens.EntityFrameworkCore/
├── src/NuvyntraLabs.NET.ApiLens.Http/
├── src/NuvyntraLabs.NET.ApiLens.UI/
├── tests/
├── samples/ApiLens.Sample/
├── README.md
├── llms.txt
└── AGENTS.md
```

## Later

- StackExchange.Redis probe (client profiling, not a general diagnostic source)
- DNS / connect / TLS split when `SocketsHttpHandler` reports it
- Error grouping across requests
- Sampling and an OpenTelemetry exporter
- Optional AI package that reads `RequestExplanation` and does not collect its own data

## Publishing

Pipeline-only. Do not `dotnet nuget push` from a local clone. CI follows the MauiEssentials package order: version alignment, `NUGET_KEY_NET`, tests, `net10.0` pack (nupkg and snupkg), then nuget.org and GitHub Packages.
