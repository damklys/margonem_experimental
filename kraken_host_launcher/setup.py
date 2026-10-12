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
        'battle_handler',
        'kill_object',
        'get_near_object',
        'get_near_e2',
        'enable_map',
        'move',
        'move_heros',
        'find_heros',
        'find_route',
        'select_heros',
        'kill_heros',
        'kill_e2',
        'create_profile',
        'select_config',
        'anti_afk',
        'discord_webhook',
        'captcha',
        'login',
        'hooks',
    ],
    'resources': [
        'styles',
        'world',
        'config',
        'heros',
        'exp',
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
