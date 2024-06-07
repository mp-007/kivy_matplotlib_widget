import os
from setuptools import find_packages, setup

with open("README.md", "r") as f:
    readme = f.read()
    
def get_package_info():

    init_path = os.path.join(
        os.path.dirname(__file__), "kivy_matplotlib_widget", "__init__.py"
    )
    info_dic = {
        "__version__": "",
        "__description__": "",
        "__author__": "",
    }

    with open(init_path, "rt") as info:
        for line in info:
            for info in info_dic.keys():
                if line.startswith(info):
                    info_dic[info] = eval(line.split("=")[1])
                    continue
    return info_dic

package_info = get_package_info()

setup(
    name='kivy_matplotlib_widget',
    version=package_info["__version__"],    
    description=package_info["__description__"],
    long_description=readme,
    long_description_content_type="text/markdown",        
    url='https://github.com/mp-007/kivy_matplotlib_widget',
    author=package_info["__author__"],
    author_email='current.address@unknown.invalid',
    license='MIT',
    packages=find_packages(),
    package_data={
    'kivy_matplotlib_widget': ['fonts/*.ttf'],
    },
    install_requires=['kivy>=1.11.1',
                      'matplotlib',                     
                      ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],    
)