echo "Running tests..."
pytest
echo "Running SonarQube analysis..."
pysonar --sonar-project-key=microblog
echo "Analysis complete. Check http://localhost:9000/dashboard?id=microblog"