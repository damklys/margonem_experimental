from setuptools import setup

APP      = ['main_v3.py']
APP_NAME = 'Kraken'

OPTIONS = {
    'iconfile': 'styles/icon.icns',
    'packages': [
        'selenium',
        'PIL',
        'undetected_chromedriver',
    ],
    'includes': [
        'create_profile',
        'create_account',
        'captcha',
        'login',
    ],
    'resources': [
        'styles',
        'config',
    ],
    'plist': {
        'CFBundleName':             APP_NAME,
        'CFBundleDisplayName':      APP_NAME,
        'CFBundleIdentifier':       'com.kraken.margonem',
        'CFBundleVersion':          '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable':  True,
        'LSUIElement':              False,
    },
    'strip': False,
}

setup(
    name=APP_NAME,
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=[],
)
