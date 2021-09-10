from distutils.core import setup

with open("README.md", encoding="utf-8") as fp:
    long_description = fp.read()

setup(
    name='turbosnake',
    version='0.1.324-alpha6',
    packages=['turbosnake', 'turbosnake.ttk', 'turbosnake.test_helpers'],
    url='https://github.com/AlexeyBond/turbosnake',
    author='Alexey Bondarenko',
    author_email='alexey.bond.94.55@gmail.com',
    description='React.js-like framework with components for native user interfaces',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['ui', 'reactive', 'tkinter'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: User Interfaces',
    ],
    license='MIT',
)
