from distutils.core import setup

with open("README.md", encoding="utf-8") as fp:
    long_description = fp.read()

setup(
    name='turbosnake',
    version='1.24.434-beta7',
    packages=['turbosnake', 'turbosnake.ttk', 'turbosnake.test_helpers'],
    url='https://github.com/AlexeyBond/turbosnake',
    author='Alexey Bondarenko',
    author_email='alexey.bond.94.55+turbosnake@gmail.com',
    description='React.js-like framework with components for native user interfaces',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['ui', 'reactive', 'tkinter'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: User Interfaces',
    ],
    license='MIT',
)
