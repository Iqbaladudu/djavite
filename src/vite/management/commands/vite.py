import os.path
import shutil
import subprocess

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from vite import NpmManager


class Command(BaseCommand):
    help = "Vite management command"

    @staticmethod
    def get_app_cwd(app_name):
        app_config = apps.get_app_config(app_name)
        app_path = app_config.path
        return os.path.abspath(app_path)

    def add_arguments(self, parser):
        parser.add_argument('package_name', type=str, help='NPM package name to install')

    def handle(self, *args, **options):
        subcommand = options.get("package_name")

        if subcommand == "dev":
            self.handle_dev()
        else:
            self.stdout.write(self.style.ERROR(f"Unknown subcommand: {subcommand}"))

    def handle_dev(self):
        django_dir = settings.BASE_DIR
        vite_dir = self.get_app_cwd(app_name="vite")
        vite_server = NpmManager(cwd=f'{vite_dir}/src')

        if not vite_server.is_npm_installed():
            self.stdout.write(self.style.ERROR('npm is not installed'))
            return

        # Check if Honcho is available
        if shutil.which('honcho'):
            try:
                self.stdout.write(self.style.SUCCESS('Starting Vite and Django with Honcho...'))
                self.stdout.write(self.style.WARNING('Press Ctrl+C to stop all processes.\n'))

                # Run honcho start in the project root
                subprocess.run(
                    ['honcho', 'start'],
                    cwd=django_dir,
                    check=True
                )
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n\nStopping processes...'))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f'Honcho failed with error: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
            finally:
                self.stdout.write(self.style.SUCCESS('Processes stopped.'))
        else:
            self.stdout.write(self.style.ERROR(
                'Honcho is not installed. Please install it with: uv add honcho'
            ))

    def handle_init(self, options):
        template = options.get('template')
        force = options.get('force')

        vite_dir = self.get_app_cwd(app_name="vite")
        vite_src_dir = os.path.join(vite_dir, 'src')

        self.stdout.write(self.style.SUCCESS(f'Initializing Vite project in: {vite_src_dir}'))

        # Check if npm is installed
        npm_manager = NpmManager(cwd=vite_src_dir)
        if not npm_manager.is_npm_installed():
            self.stdout.write(self.style.ERROR('npm is not installed. Please install Node.js and npm first.'))
            return

        # Check if directory already has files
        if os.path.exists(vite_src_dir) and os.listdir(vite_src_dir) and not force:
            self.stdout.write(self.style.WARNING(
                f'Directory {vite_src_dir} already contains files. Use --force to overwrite.'
            ))
            return

        # Create directory if it doesn't exist
        os.makedirs(vite_src_dir, exist_ok=True)

        try:
            # Initialize Vite project using npm create vite@latest
            self.stdout.write(self.style.SUCCESS(f'Creating Vite project with template: {template}'))

            # Use npm create vite to initialize the project
            result = subprocess.run(
                ['npm', 'create', 'vite@latest', '.', '--', '--template', template],
                cwd=vite_src_dir,
                check=True,
                capture_output=True,
                text=True
            )

            self.stdout.write(self.style.SUCCESS('Vite project created successfully!'))

            # Install dependencies
            self.stdout.write(self.style.SUCCESS('Installing dependencies...'))
            if npm_manager.npm_install():
                self.stdout.write(self.style.SUCCESS('Dependencies installed successfully!'))
            else:
                self.stdout.write(self.style.ERROR('Failed to install dependencies'))
                return

            # Update vite.config.js/ts to work with Django
            self.update_vite_config(vite_src_dir, template)

            # Display next steps
            self.stdout.write(self.style.SUCCESS('\n✓ Vite project initialized successfully!'))
            self.stdout.write(self.style.SUCCESS('\nNext steps:'))
            self.stdout.write('  1. Review the generated files in src/vite/src/')
            self.stdout.write('  2. Run: python manage.py vite dev (to start development server)')
            self.stdout.write('  3. Run: python manage.py vite install --package <package> (to install packages)')

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize Vite project: {e}'))
            if hasattr(e, 'stderr'):
                self.stdout.write(self.style.ERROR(f'Error output: {e.stderr}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))

    def update_vite_config(self, vite_src_dir, template):
        """Update vite.config.js/ts to work better with Django"""
        config_file = None

        # Determine config file name based on template
        if template.endswith('-ts'):
            config_file = os.path.join(vite_src_dir, 'vite.config.ts')
        else:
            config_file = os.path.join(vite_src_dir, 'vite.config.js')

        # If neither exists, try both
        if not os.path.exists(config_file):
            if os.path.exists(os.path.join(vite_src_dir, 'vite.config.js')):
                config_file = os.path.join(vite_src_dir, 'vite.config.js')
            elif os.path.exists(os.path.join(vite_src_dir, 'vite.config.ts')):
                config_file = os.path.join(vite_src_dir, 'vite.config.ts')
            else:
                # Create a basic config file
                config_file = os.path.join(vite_src_dir, 'vite.config.js')
                with open(config_file, 'w') as f:
                    f.write(self.get_default_vite_config())
                self.stdout.write(self.style.SUCCESS('Created vite.config.js'))
                return

        try:
            with open(config_file, 'r') as f:
                config_content = f.read()

            # Add Django-friendly configuration if not already present
            if 'manifest' not in config_content:
                # Insert build configuration
                django_config = """
  build: {
    manifest: true,
    outDir: '../static/dist',
    rollupOptions: {
      input: {
        main: './src/main.js',
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    origin: 'http://localhost:5173',
  },"""

                # Insert before the closing brace of defineConfig
                if 'export default defineConfig({' in config_content:
                    config_content = config_content.replace(
                        'export default defineConfig({',
                        f'export default defineConfig({{{django_config}'
                    )

                    with open(config_file, 'w') as f:
                        f.write(config_content)

                    self.stdout.write(self.style.SUCCESS('Updated vite.config with Django settings'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not update vite config automatically: {e}'))

    def get_default_vite_config(self):
        """Return a default Vite configuration for Django integration"""
        return """import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    manifest: true,
    outDir: '../static/dist',
    rollupOptions: {
      input: {
        main: './src/main.js',
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    origin: 'http://localhost:5173',
  },
})
"""

    def handle_install(self, package_name):
        vite_dir = self.get_app_cwd(app_name="vite")
        npm_manager = NpmManager(cwd=f'{vite_dir}/src')

        if not npm_manager.is_npm_installed():
            self.stdout.write(self.style.ERROR('npm is not installed'))
            return

        self.stdout.write(self.style.SUCCESS(f'Installing {package_name}...'))

        if npm_manager.npm_install_package(package_name):
            self.stdout.write(self.style.SUCCESS(f'Successfully installed {package_name}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to install {package_name}'))

