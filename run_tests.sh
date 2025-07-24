
#!/bin/bash

echo "🧼 Limpiando reportes anteriores..."
coverage erase

echo "🧪 Ejecutando pruebas con cobertura..."
pytest --cov=app tests/ --cov-report=term-missing --cov-report=html -v

echo ""
echo "📊 Reporte HTML generado en: htmlcov/index.html"

# Abrir automáticamente si es posible
if command -v xdg-open &> /dev/null; then
  xdg-open htmlcov/index.html
elif command -v open &> /dev/null; then
  open htmlcov/index.html
fi
