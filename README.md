# ATELIER AI — versión avanzada

Esta es una versión ampliada del simulacro AI Stylist: catálogo visual, filtros, accesorios, cambio de prendas, chat con Qwen, favoritos, comparación y analítica de uso.

## Instalación en Windows / VS Code

1. Copia todos los archivos a tu carpeta `AI_STYLIST`, conservando los anteriores como copia de seguridad. No copies `.venv`.
2. Abre la terminal PowerShell dentro de esa carpeta.
3. Si no existe el entorno: `python -m venv .venv`
4. Instala: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
5. Crea las ilustraciones: `.\.venv\Scripts\python.exe make_images.py`
6. Comprueba el modelo: `ollama list` (si no aparece, `ollama pull qwen3:1.7b`).
7. Inicia: `.\.venv\Scripts\python.exe -m streamlit run app.py`

## Fotos reales

Los archivos `images/1.png`, `images/2.png`, etc. son ilustraciones generadas para este prototipo, **no fotografías**. Sustituye cualquiera por una fotografía del producto correspondiente que tengas derecho a utilizar, manteniendo el mismo nombre de archivo. El cambio se verá en la web tras recargarla. No mezcles fotografías de otros productos con los nombres y precios ficticios.

## Límites

- Catálogo y precios ficticios; no existe conexión a inventario real.
- El chat da consejos, pero no modifica automáticamente el outfit; para cambiarlo utiliza los controles de la interfaz.
- Temporada y texto libre influyen en el prompt del LLM, no son filtros duros.
- Los accesorios se añaden de forma heurística; no es un recomendador comercial entrenado.
- La web depende del Ollama local. No funcionará directamente en Streamlit Community Cloud sin un backend de IA remoto.
- Las métricas son de recomendaciones, no de ventas.
