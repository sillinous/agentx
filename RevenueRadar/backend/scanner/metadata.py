"""Metadata extraction from project files."""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

def extract_metadata(project_path: Path) -> Dict[str, Any]:
    """Extract all metadata from a project directory."""
    metadata = {
        'has_readme': False,
        'has_docker': False,
        'has_tests': False,
        'has_ci_cd': False,
        'has_package_json': False,
        'has_requirements': False,
        'has_stripe': False,
        'has_auth': False,
        'has_api': False,
        'has_database': False,
        'has_typescript': False,
        'tech_stack': [],
        'description': '',
        'dependencies': [],
        'loc_estimate': 0,
    }

    if not project_path.exists():
        return metadata

    # Check for common files
    metadata['has_readme'] = any(
        (project_path / f).exists()
        for f in ['README.md', 'readme.md', 'README.rst', 'README']
    )

    metadata['has_docker'] = any(
        (project_path / f).exists()
        for f in ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml']
    )

    metadata['has_tests'] = any([
        (project_path / 'tests').exists(),
        (project_path / 'test').exists(),
        (project_path / '__tests__').exists(),
        (project_path / 'spec').exists(),
        # Only check top-level, not recursive (faster)
        any(project_path.glob('test_*.py')),
        any(project_path.glob('*.test.ts')),
    ])

    metadata['has_ci_cd'] = any([
        (project_path / '.github' / 'workflows').exists(),
        (project_path / '.gitlab-ci.yml').exists(),
        (project_path / 'Jenkinsfile').exists(),
        (project_path / '.circleci').exists(),
    ])

    # Parse package.json
    package_json = project_path / 'package.json'
    if package_json.exists():
        metadata['has_package_json'] = True
        try:
            data = json.loads(package_json.read_text(encoding='utf-8'))
            metadata['description'] = data.get('description', '')

            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            metadata['dependencies'] = list(deps.keys())

            # Detect tech stack from dependencies
            if 'next' in deps:
                metadata['tech_stack'].append('Next.js')
            if 'react' in deps:
                metadata['tech_stack'].append('React')
            if 'vue' in deps:
                metadata['tech_stack'].append('Vue')
            if 'express' in deps:
                metadata['tech_stack'].append('Express')
            if 'fastify' in deps:
                metadata['tech_stack'].append('Fastify')
            if 'stripe' in deps or '@stripe/stripe-js' in deps:
                metadata['has_stripe'] = True
                metadata['tech_stack'].append('Stripe')
            if 'supabase' in str(deps) or '@supabase/supabase-js' in deps:
                metadata['has_database'] = True
                metadata['tech_stack'].append('Supabase')
            if 'prisma' in deps or '@prisma/client' in deps:
                metadata['has_database'] = True
                metadata['tech_stack'].append('Prisma')
            if 'next-auth' in deps or '@auth/core' in deps:
                metadata['has_auth'] = True
            if 'typescript' in deps:
                metadata['has_typescript'] = True
                metadata['tech_stack'].append('TypeScript')
            if 'tailwindcss' in deps:
                metadata['tech_stack'].append('Tailwind CSS')

        except Exception:
            pass

    # Parse requirements.txt
    requirements_txt = project_path / 'requirements.txt'
    if requirements_txt.exists():
        metadata['has_requirements'] = True
        try:
            content = requirements_txt.read_text(encoding='utf-8')
            deps = [line.split('==')[0].split('>=')[0].strip()
                   for line in content.splitlines()
                   if line.strip() and not line.startswith('#')]
            metadata['dependencies'].extend(deps)

            deps_lower = content.lower()
            if 'fastapi' in deps_lower:
                metadata['tech_stack'].append('FastAPI')
                metadata['has_api'] = True
            if 'flask' in deps_lower:
                metadata['tech_stack'].append('Flask')
                metadata['has_api'] = True
            if 'django' in deps_lower:
                metadata['tech_stack'].append('Django')
                metadata['has_api'] = True
            if 'stripe' in deps_lower:
                metadata['has_stripe'] = True
                metadata['tech_stack'].append('Stripe')
            if 'sqlalchemy' in deps_lower or 'sqlmodel' in deps_lower:
                metadata['has_database'] = True
                metadata['tech_stack'].append('SQLAlchemy')
            if 'pytorch' in deps_lower or 'torch' in deps_lower:
                metadata['tech_stack'].append('PyTorch')
            if 'tensorflow' in deps_lower:
                metadata['tech_stack'].append('TensorFlow')
            if 'openai' in deps_lower:
                metadata['tech_stack'].append('OpenAI')
            if 'anthropic' in deps_lower:
                metadata['tech_stack'].append('Anthropic Claude')
            if 'celery' in deps_lower:
                metadata['tech_stack'].append('Celery')
            if 'redis' in deps_lower:
                metadata['tech_stack'].append('Redis')

        except Exception:
            pass

    # Check for API files (non-recursive for speed)
    if (project_path / 'api.py').exists() or (project_path / 'app' / 'api.py').exists():
        metadata['has_api'] = True
    if (project_path / 'routes.py').exists() or (project_path / 'app' / 'routes.py').exists():
        metadata['has_api'] = True

    # Check for auth patterns (non-recursive for speed)
    auth_paths = [
        project_path / 'auth.py',
        project_path / 'auth.ts',
        project_path / 'lib' / 'auth.ts',
        project_path / 'app' / 'auth.py',
        project_path / 'core' / 'auth.py',
    ]
    metadata['has_auth'] = any(p.exists() for p in auth_paths)

    # Quick LOC estimate based on src directory size
    try:
        src_dirs = ['src', 'app', 'lib', 'components', 'pages']
        file_count = 0
        for src_dir in src_dirs:
            src_path = project_path / src_dir
            if src_path.exists():
                # Count only direct children files
                file_count += len([f for f in src_path.iterdir() if f.is_file()])
        metadata['loc_estimate'] = max(file_count * 150, 500)  # Rough estimate
    except Exception:
        metadata['loc_estimate'] = 500

    # Dedupe tech stack
    metadata['tech_stack'] = list(set(metadata['tech_stack']))

    # Extract description from README if not found
    if not metadata['description']:
        readme_path = project_path / 'README.md'
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding='utf-8')
                # Get first paragraph after title
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#') and not line.startswith('!'):
                        metadata['description'] = line.strip()[:200]
                        break
            except Exception:
                pass

    return metadata

def detect_project_type(metadata: Dict) -> str:
    """Detect the type of project based on metadata."""
    tech = set(t.lower() for t in metadata.get('tech_stack', []))

    if 'next.js' in tech or 'react' in tech or 'vue' in tech:
        if metadata.get('has_api') or 'fastapi' in tech or 'express' in tech:
            return 'fullstack'
        return 'frontend'

    if 'fastapi' in tech or 'flask' in tech or 'django' in tech or 'express' in tech:
        return 'backend'

    if 'pytorch' in tech or 'tensorflow' in tech:
        return 'ml'

    if metadata.get('has_docker'):
        return 'infrastructure'

    return 'library'
