# ============================================================================
# CTF Database Platform - Quick Start Script
# ============================================================================
# Usage:
#   .\start.ps1           - Start the platform
#   .\start.ps1 stop      - Stop the platform
#   .\start.ps1 restart   - Restart the platform
#   .\start.ps1 reset     - Trigger manual database reset
#   .\start.ps1 logs      - View logs
#   .\start.ps1 clean     - Stop and remove all data
# ============================================================================

param(
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "║        🎯 CTF Vulnerable Database Platform 🎯             ║" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "║           Educational Security Testing Environment         ║" -ForegroundColor Cyan
    Write-Host "║                                                            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# Check Docker is running
function Test-Docker {
    try {
        docker ps | Out-Null
        return $true
    }
    catch {
        Write-Error "❌ Docker is not running. Please start Docker Desktop."
        return $false
    }
}

# Start the platform
function Start-Platform {
    Show-Banner
    Write-Info "🚀 Starting CTF Database Platform..."
    Write-Host ""
    
    if (-not (Test-Docker)) { exit 1 }
    
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Success "✅ Platform started successfully!"
        Write-Host ""
        Write-Info "📊 Service Status:"
        docker-compose ps
        Write-Host ""
        Write-Info "🔗 Access Points:"
        Write-Host "   MySQL Database:  localhost:3306"
        Write-Host "   Database Name:   ctf_db"
        Write-Host "   Username:        ctf_player"
        Write-Host "   Password:        player_password_456"
        Write-Host ""
        Write-Host "   Reset API:       http://localhost:5001"
        Write-Host "   Health Check:    http://localhost:5001/health"
        Write-Host ""
        Write-Info "📝 Quick Commands:"
        Write-Host "   View logs:       .\start.ps1 logs"
        Write-Host "   Trigger reset:   .\start.ps1 reset"
        Write-Host "   Stop platform:   .\start.ps1 stop"
        Write-Host ""
    }
    else {
        Write-Error "❌ Failed to start platform. Check logs with: docker-compose logs"
    }
}

# Stop the platform
function Stop-Platform {
    Write-Info "🛑 Stopping CTF Database Platform..."
    docker-compose down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✅ Platform stopped successfully!"
    }
}

# Restart the platform
function Restart-Platform {
    Write-Info "🔄 Restarting CTF Database Platform..."
    docker-compose restart
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✅ Platform restarted successfully!"
        Write-Host ""
        docker-compose ps
    }
}

# View logs
function Show-Logs {
    Write-Info "📋 Viewing platform logs (Ctrl+C to exit)..."
    Write-Host ""
    docker-compose logs -f
}

# Trigger manual reset
function Trigger-Reset {
    Write-Info "🔄 Triggering manual database reset..."
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5001/reset" -Method Post
        Write-Success "✅ Database reset successful!"
        Write-Host ""
        Write-Host "Reset Count: $($response.reset_count)"
        Write-Host "Timestamp:   $($response.timestamp)"
    }
    catch {
        Write-Error "❌ Failed to trigger reset. Is the platform running?"
        Write-Host "   Try: .\start.ps1 start"
    }
}

# Check health
function Show-Health {
    Write-Info "🏥 Checking platform health..."
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5001/health"
        Write-Success "✅ Platform is healthy!"
        Write-Host ""
        Write-Host "Last Reset:           $($response.last_reset)"
        Write-Host "Total Resets:         $($response.reset_count)"
        Write-Host "Seconds Since Reset:  $($response.seconds_since_last_reset)"
        Write-Host "Reset Interval:       $($response.reset_interval_seconds) seconds"
    }
    catch {
        Write-Error "❌ Platform health check failed. Is the platform running?"
    }
}

# Clean everything
function Clean-Platform {
    Write-Warning "⚠️  This will stop the platform and remove ALL data!"
    $confirm = Read-Host "Are you sure? (yes/no)"
    
    if ($confirm -eq "yes") {
        Write-Info "🧹 Cleaning up platform..."
        docker-compose down -v
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Platform cleaned successfully!"
        }
    }
    else {
        Write-Info "Cancelled."
    }
}

# Main script logic
switch ($Action.ToLower()) {
    "start" { Start-Platform }
    "stop" { Stop-Platform }
    "restart" { Restart-Platform }
    "logs" { Show-Logs }
    "reset" { Trigger-Reset }
    "health" { Show-Health }
    "clean" { Clean-Platform }
    default {
        Write-Error "❌ Unknown action: $Action"
        Write-Host ""
        Write-Info "Available actions:"
        Write-Host "   start    - Start the platform"
        Write-Host "   stop     - Stop the platform"
        Write-Host "   restart  - Restart the platform"
        Write-Host "   logs     - View logs"
        Write-Host "   reset    - Trigger manual database reset"
        Write-Host "   health   - Check platform health"
        Write-Host "   clean    - Stop and remove all data"
        Write-Host ""
        Write-Host "Example: .\start.ps1 start"
    }
}
