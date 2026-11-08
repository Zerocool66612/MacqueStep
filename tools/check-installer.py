#!/usr/bin/env python3
"""Reject missing installer branding and image resources before building."""
from pathlib import Path
import sys
import yaml

def check(root):
    branding = root / 'config/includes.chroot/etc/calamares/branding/macaquestep'
    data = yaml.safe_load((branding / 'branding.desc').read_text())
    for key in ('componentName', 'strings', 'images', 'slideshow'):
        if not data.get(key):
            raise ValueError(f'Missing required branding setting: {key}')
    slides = data['slideshow']
    resources = list(data['images'].values())
    resources += slides if isinstance(slides, list) else [slides]
    for resource in resources:
        path = Path(resource)
        if path.is_absolute():
            path = root / 'config/includes.chroot' / path.relative_to('/')
        else:
            path = branding / path
        if not path.is_file():
            raise ValueError(f'Missing branding resource: {resource}')

if __name__ == '__main__':
    try:
        check(Path(__file__).resolve().parents[1])
    except (ValueError, OSError, yaml.YAMLError) as error:
        sys.exit(f'Installer branding check failed: {error}')
    print('Installer branding and slideshow resources: OK')
