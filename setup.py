from setuptools import setup


with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='lcu-driver',
    version='1.0.0',
    author='André Matos de Sousa',
    author_email='andrematosdesousa@gmail.com',
    license='MIT',
    url='https://github.com/sousa-andre/lcu-driver/',
    long_description_content_type='text/markdown',
    long_description=long_description,
    packages=['lcu_driver'],
    install_requires=[
        'aiohttp',
        'psutil'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Operating System :: Microsoft :: Windows'
    ],
    project_urls={
        'Source': 'https://github.com/sousa-andre/lcu-driver/'
    }
)

