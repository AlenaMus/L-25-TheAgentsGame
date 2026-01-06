"""
Fallback HTML - Simple dashboard HTML when enhanced frontend not available.

Provides basic real-time monitoring functionality.
"""


def get_fallback_html() -> str:
    """Get fallback dashboard HTML."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Game Orchestrator Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .healthy { background-color: #d4edda; }
        .unhealthy { background-color: #f8d7da; }
        #agents, #tournament { margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Game Orchestrator Dashboard</h1>
    <div id="agents"></div>
    <div id="tournament"></div>
    <script>
        const ws = new WebSocket('ws://localhost:9000/ws');

        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            console.log('Update:', update);

            if (update.type === 'health') {
                displayAgents(update.data);
            } else if (update.type === 'standings') {
                displayStandings(update.data);
            }
        };

        function displayAgents(data) {
            const div = document.getElementById('agents');
            let html = '<h2>Agent Status</h2>';

            for (const [agentId, status] of Object.entries(data)) {
                const className = status === 'HEALTHY' ? 'healthy' : 'unhealthy';
                html += `<div class="status ${className}">${agentId}: ${status}</div>`;
            }

            div.innerHTML = html;
        }

        function displayStandings(data) {
            const div = document.getElementById('tournament');
            let html = '<h2>Tournament Standings</h2><table><tr><th>Rank</th><th>Player</th><th>Points</th><th>W-L-D</th></tr>';

            for (const entry of data) {
                html += `<tr><td>${entry.rank}</td><td>${entry.player_id}</td><td>${entry.points}</td><td>${entry.wins}-${entry.losses}-${entry.draws}</td></tr>`;
            }

            html += '</table>';
            div.innerHTML = html;
        }
    </script>
</body>
</html>
    """
