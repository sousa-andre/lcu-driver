from setuptools import setup

__version__ = '3.0.1'

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='lcu-driver',
    version=__version__,
    author='André Matos de Sousa',
    author_email='andrematosdesousa@gmail.com',
    license='MIT',
    url='https://github.com/sousa-andre/lcu-driver/',
    long_description_content_type='text/markdown',
    long_description=long_description,
    packages=['lcu_driver', 'lcu_driver.events'],
    install_requires=[
        'aiohttp',
        'psutil'
    ],
    project_urls={
        'Source': 'https://github.com/sousa-andre/lcu-driver/'
    }
)

