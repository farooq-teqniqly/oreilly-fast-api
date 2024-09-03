function Start-Server {
    param (
        [string]$App = "hello_world:app",
        [switch]$Reload
    )

    $uvicornArgs = @($App)
    if ($Reload) {
        $uvicornArgs += "--reload"
    }

    & uvicorn @uvicornArgs
}