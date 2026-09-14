#!/bin/bash
if [ -z "$SONAR_TOKEN" ]; then
  echo "ERROR: SONAR_TOKEN не встановлено. Виконай: export SONAR_TOKEN=твій_токен"
  exit 1
fi
echo "Running tests with coverage..."
pytest tests.py --cov=app --cov-report=xml
echo "Running SonarQube analysis..."
pysonar --sonar-project-key=microblog --sonar-token="$SONAR_TOKEN"
echo "Analysis complete. Check http://localhost:9000/dashboard?id=microblog"