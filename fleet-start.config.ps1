# Per-repo fleet start config for searchstudio-mcp
# Edit ports/backend target here - webapp/start.ps1 is fleet-standard and must not be customized.
@{
    Name         = 'searchstudio-mcp'
    BackendPort  = 11226
    FrontendPort = 11225
    HealthPath   = '/api/health'
    WebRoot      = 'D:\Dev\repos\searchstudio-mcp\webapp'

    Backend = @{
        Kind       = 'module-serve'
        Module     = 'super_search_mcp'
        SyncExtras = @('dev')
        Env        = @{WEB_PORT = '11226'}
    }

    Frontend = @{
        Kind           = 'vite-bun'
        PackageManager = 'bun'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
