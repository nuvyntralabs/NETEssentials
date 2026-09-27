# NETEssentials architecture

NETEssentials is a catalog. Each product is an independent git repository and a set of NuGet packages. The hub maps a requirement to a product. Products do not PackageReference each other.

ApiLens is the first product. The hub folder `ApiLens/` is a submodule of https://github.com/nuvyntralabs/NuvyntraLabs.NET.ApiLens. The hub keeps the pointer only, the same way MauiEssentials points at each plugin.

```
Developer requirement
        │
        ▼
NETEssentials README
        │
        ▼
One product (ApiLens)
        │
        ├── Core (no ASP.NET)
        ├── AspNetCore (Add / Use, dashboard gate)
        ├── EntityFrameworkCore (optional probe)
        ├── Http (optional probe)
        └── UI (embedded page)
```

Framework diagnostics stay in place. ApiLens reads them and explains one request. It does not replace OpenTelemetry.
