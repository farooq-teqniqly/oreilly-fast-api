function Start-Server {
    param (
        [string]$App = "hello_world:app",
        [string]$Address = "127.0.0.1",
        [switch]$Reload
    )

    $uvicornArgs = @($App)
    $uvicornArgs += "--host $Address"

    if ($Reload) {
        $uvicornArgs += "--reload"
    }

    uvicorn @uvicornArgs
}