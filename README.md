# Djavite

A Django library for seamless integration of Vite.js, enabling modern frontend tooling in Django projects.

## Features

- 🚀 Hot Module Replacement (HMR) in development
- 🎯 Automatic asset management for production builds
- 📦 Built-in Vite dev server integration
- 🔧 Simple Django template tags
- ⚡ Uses Honcho for running Django and Vite together

## Installation

```bash
pip install djavite
```

## Quick Start

1. Add `vite` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'vite',
]
```

2. Configure Vite settings in `settings.py`:

```python
VITE_DEV_MODE = DEBUG
VITE_DEV_SERVER_URL = "http://localhost:5173"
VITE_JS_ENTRYPOINT = f"{VITE_DEV_SERVER_URL}/src/index.ts"
VITE_CSS_ENTRYPOINT = f"{VITE_DEV_SERVER_URL}/src/style.css"
```

3. Load Vite assets in your template:

```html
{% load vite %}
<!DOCTYPE html>
<html>
<head>
    {% enable_vite %}
</head>
<body>
    <!-- Your content -->
</body>
</html>
```

4. Run development server:

```bash
python manage.py vite dev
```

This will start both Django and Vite dev servers using Honcho.

## Installing NPM Packages

You can install npm packages directly using Django management command:

```bash
python manage.py vite install <package-name>
```

Example:

```bash
python manage.py vite install axios
python manage.py vite install @types/node
```

This command will install the package into your Vite project directory.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `VITE_DEV_MODE` | `True` | Enable/disable dev mode |
| `VITE_DEV_SERVER_URL` | `http://localhost:5173` | Vite dev server URL |
| `VITE_JS_ENTRYPOINT` | `/src/index.ts` | JavaScript entry point |
| `VITE_CSS_ENTRYPOINT` | `/src/style.css` | CSS entry point |
| `NPM_BIN_PATH` | `npm` | Path to npm binary |

## Production Build

Build your Vite assets for production:

```bash
npm run build --prefix vite/src
```

The built assets will be automatically served in production when `DEBUG=False`.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Muhammad Iqbal (iqbal.adudu@gmail.com)

